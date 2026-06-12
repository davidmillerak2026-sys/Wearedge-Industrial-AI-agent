from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLOCK_ROOT = REPO_ROOT / "wfc-blocks" / "wearedge-agent-service"
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "submission-assets"
    / "live-evidence"
    / "gongyi-mofang"
    / "wfc-resource-package"
)
REQUIRED_FILES = (
    "info.json",
    "README.md",
    "function-blocks/CallWearedgeDecisionApi.py",
)
EXCLUDED_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip", ".tmp", ".log"}
SECRET_PATTERNS = (
    re.compile(r"AppSecret", re.IGNORECASE),
    re.compile(r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bpassword\s*[:=]\s*['\"]?[^'\"\s]+", re.IGNORECASE),
    re.compile(r"\bcookie\s*[:=]\s*['\"]?[^'\"\s]+", re.IGNORECASE),
)
ZIP_TIMESTAMP = (2026, 6, 11, 0, 0, 0)


@dataclass(frozen=True)
class PackageFile:
    source: Path
    archive_name: str
    size: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "archive_name": self.archive_name,
            "size": self.size,
            "sha256": self.sha256,
        }


def load_info(block_root: Path) -> dict[str, Any]:
    path = block_root / "info.json"
    try:
        info = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path}") from exc
    if not isinstance(info, dict):
        raise ValueError("info.json must contain a JSON object")
    for key in ("name", "version", "displayName", "type"):
        if not info.get(key):
            raise ValueError(f"info.json missing {key}")
    return info


def discover_package_files(block_root: Path) -> list[PackageFile]:
    block_root = block_root.resolve()
    missing = [path for path in REQUIRED_FILES if not (block_root / path).is_file()]
    if missing:
        raise ValueError(f"missing required file(s): {', '.join(missing)}")

    files: list[PackageFile] = []
    for path in sorted(block_root.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(block_root)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        archive_name = PurePosixPath(*relative.parts).as_posix()
        content = path.read_bytes()
        files.append(
            PackageFile(
                source=path,
                archive_name=archive_name,
                size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            )
        )
    return files


def scan_for_secrets(files: list[PackageFile]) -> list[str]:
    findings: list[str] = []
    for item in files:
        try:
            text = item.source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{item.archive_name}: matches {pattern.pattern}")
    return findings


def build_package_name(info: dict[str, Any]) -> str:
    name = str(info["name"]).strip().replace("/", "-").replace("\\", "-")
    version = str(info["version"]).strip().replace("/", "-").replace("\\", "-")
    return f"{name}-{version}.zip"


def write_zip(files: list[PackageFile], package_path: Path) -> None:
    package_path.parent.mkdir(parents=True, exist_ok=True)
    if package_path.exists():
        package_path.unlink()
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in files:
            info = zipfile.ZipInfo(item.archive_name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, item.source.read_bytes())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_manifest(
    *,
    info: dict[str, Any],
    files: list[PackageFile],
    package_path: Path,
    dry_run: bool,
) -> dict[str, Any]:
    archive_names = {item.archive_name for item in files}
    required_present = all(path in archive_names for path in REQUIRED_FILES)
    return {
        "ok": required_present,
        "dry_run": dry_run,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "resource": {
            "name": info["name"],
            "displayName": info["displayName"],
            "type": info["type"],
            "version": info["version"],
        },
        "package_path": str(package_path),
        "package_sha256": None if dry_run else sha256_file(package_path),
        "file_count": len(files),
        "files": [item.as_dict() for item in files],
        "required_files": list(REQUIRED_FILES),
        "required_files_present": required_present,
        "safety": {
            "secret_scan_patterns": len(SECRET_PATTERNS),
            "secret_findings": [],
            "notes": [
                "Generated package is an ignored local deliverable.",
                "Do not include WFC cookies, Xcelerator secrets, or API keys in the resource package.",
                "Install/upload only after backing up live WFC project state.",
            ],
        },
    }


def package_resource_block(
    *,
    block_root: Path = DEFAULT_BLOCK_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    package_name: str | None = None,
    write_manifest: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    info = load_info(block_root)
    files = discover_package_files(block_root)
    findings = scan_for_secrets(files)
    if findings:
        raise ValueError("possible secret(s) found in resource package: " + "; ".join(findings))

    package_path = output_dir / (package_name or build_package_name(info))
    if not dry_run:
        write_zip(files, package_path)

    manifest = create_manifest(info=info, files=files, package_path=package_path, dry_run=dry_run)
    if write_manifest and not dry_run:
        manifest_path = package_path.with_suffix(".package-manifest.json")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_summary(manifest: dict[str, Any]) -> str:
    resource = manifest["resource"]
    lines = [
        f"ok={manifest['ok']}",
        f"dry_run={manifest['dry_run']}",
        f"resource={resource['displayName']} ({resource['name']} {resource['version']})",
        f"package_path={manifest['package_path']}",
        f"file_count={manifest['file_count']}",
        f"required_files_present={manifest['required_files_present']}",
    ]
    if manifest.get("package_sha256"):
        lines.append(f"package_sha256={manifest['package_sha256']}")
    if manifest.get("manifest_path"):
        lines.append(f"manifest_path={manifest['manifest_path']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package the Wearedge Gongyi Mofang WFC resource block.")
    parser.add_argument("--block-root", type=Path, default=DEFAULT_BLOCK_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--package-name", default=None)
    parser.add_argument("--no-manifest", action="store_true", help="Do not write a package manifest JSON.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args(argv)

    try:
        manifest = package_resource_block(
            block_root=args.block_root,
            output_dir=args.output_dir,
            package_name=args.package_name,
            write_manifest=not args.no_manifest,
            dry_run=args.dry_run,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else render_summary(manifest))
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
