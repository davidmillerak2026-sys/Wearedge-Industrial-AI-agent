from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DEFAULT_OUTPUT_DIR = REPO_ROOT / "submission-assets" / "live-evidence" / "submission-bundle"
DEFAULT_BUNDLE_NAME = "wearedge-industrial-ai-agent-repo-controlled-submission-bundle.zip"
ZIP_TIMESTAMP = (2026, 6, 11, 0, 0, 0)

INCLUDE_PATHS = (
    "README.md",
    "docs/siemens-xcelerator-co-creation-onepager.md",
    "docs/siemens-industrial-agent-track-memory-20260521.md",
    "docs/gongyi-mofang-workflow-canvas-memory-202604.md",
    "docs/gongyi-mofang-official-completion-paths.md",
    "docs/edge-agent-runtime-for-xcelerator.md",
    "docs/competition-offline-eval-report.md",
    "docs/finals-validation-report.md",
    "docs/workflow-canvas-poc-runbook.md",
    "docs/workflow-canvas-api-schema.md",
    "docs/xcelerator-apiworld-onboarding.md",
    "docs/submission/business-plan.md",
    "docs/submission/technical-solution.md",
    "docs/submission/finals-foundation-roadmap.md",
    "docs/submission/finals-hmi-console.html",
    "docs/submission/enterprise-winning-strategy.md",
    "docs/submission/judging-scorecard-evidence-map.md",
    "docs/submission/defense-qna-playbook.md",
    "docs/submission/registration-fields.md",
    "docs/submission/final-checklist.md",
    "docs/submission/final-human-action-runbook.md",
    "docs/submission/submission-package-manifest.md",
    "docs/submission/poc-evidence-index.md",
    "docs/submission/demo-script.md",
    "docs/submission/demo-shot-list.md",
    "docs/submission/video-production-plan.md",
    "docs/submission/live-platform-evidence-runbook.md",
    "docs/submission/platform-live-evidence-status-20260609.md",
    "docs/submission/ip-and-compliance-statement.md",
    "docs/submission/company-info-and-compliance-intake.md",
    "docs/submission/team-and-company-info-template.md",
    "docs/submission/dashboard-mock.html",
    "docs/submission/evidence",
    "evals/finals_validation_dataset.jsonl",
    "evals/competition_offline_dataset.jsonl",
    "openapi/wearedge-xcelerator-apiworld.openapi.json",
    "workflows/wearedge_wfc_poc_payload.json",
    "workflows/wfc_call_wearedge_decision_fb_main.py",
    "wfc-blocks/wearedge-agent-service",
    "scripts/run_competition_eval.py",
    "scripts/run_finals_validation.py",
    "scripts/verify_finals_foundation.py",
    "scripts/smoke_workflow_canvas_decision.py",
    "scripts/smoke_edge_runtime_profile.py",
    "scripts/smoke_solution_profile.py",
    "scripts/verify_submission_package.py",
    "scripts/verify_live_evidence.py",
    "scripts/build_final_submission_bundle.py",
    "scripts/prepare_final_human_action_pack.py",
    "scripts/generate_final_readiness_report.py",
    "scripts/run_final_readiness_pipeline.py",
    "scripts/package_wfc_resource_block.py",
    "scripts/wfc_private_api_probe.py",
)

EXTERNAL_EXCLUDED_ITEMS = (
    "submission-assets/live-evidence/legal/company-info-filled.md",
    "submission-assets/live-evidence/legal/ip-and-no-dispute-signed.pdf",
    "submission-assets/live-evidence/legal/no-adverse-record-signed.pdf",
    "submission-assets/live-evidence/legal/submission-contact-confirmation.md",
    "submission-assets/live-evidence/submission/01-registration-form-filled.png",
    "submission-assets/live-evidence/submission/02-submission-success.png",
    "submission-assets/live-evidence/xcelerator/",
    "submission-assets/live-evidence/gongyi-mofang/",
    "submission-assets/live-evidence/edge-runtime/",
    "submission-assets/live-evidence/video/",
)

EXCLUDED_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".log", ".pid"}
SECRET_PATTERNS = (
    re.compile(r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}"),
    re.compile(r"\b(password|passwd|pwd)\s*[:=]\s*['\"]?[^'\"\s<>]+", re.IGNORECASE),
    re.compile(r"\b(cookie|sessionid)\s*[:=]\s*['\"][^'\"\s<>]+", re.IGNORECASE),
)


@dataclass(frozen=True)
class BundleFile:
    source: Path
    archive_name: str
    size: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "archive_name": self.archive_name,
            "source": str(self.source),
            "size": self.size,
            "sha256": self.sha256,
        }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(repo_root: Path = REPO_ROOT, include_paths: Iterable[str] = INCLUDE_PATHS) -> list[BundleFile]:
    repo_root = repo_root.resolve()
    files: list[BundleFile] = []
    missing: list[str] = []
    seen: set[str] = set()

    for item in include_paths:
        path = (repo_root / item).resolve()
        if not path.exists():
            missing.append(item)
            continue
        if path.is_file():
            candidates = [path]
        else:
            candidates = sorted(child for child in path.rglob("*") if child.is_file())
        for candidate in candidates:
            relative = candidate.relative_to(repo_root)
            if any(part in EXCLUDED_DIRS for part in relative.parts):
                continue
            if candidate.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            archive_name = PurePosixPath(*relative.parts).as_posix()
            if archive_name in seen:
                continue
            seen.add(archive_name)
            files.append(
                BundleFile(
                    source=candidate,
                    archive_name=archive_name,
                    size=candidate.stat().st_size,
                    sha256=file_sha256(candidate),
                )
            )

    if missing:
        raise ValueError(f"missing bundle source(s): {', '.join(missing)}")
    return sorted(files, key=lambda item: item.archive_name)


def detect_secret_findings(files: list[BundleFile]) -> list[str]:
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


def write_zip(files: list[BundleFile], bundle_path: Path, manifest: dict[str, Any]) -> None:
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    if bundle_path.exists():
        bundle_path.unlink()
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in files:
            info = zipfile.ZipInfo(item.archive_name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, item.source.read_bytes())
        manifest_info = zipfile.ZipInfo("SUBMISSION_BUNDLE_MANIFEST.json", date_time=ZIP_TIMESTAMP)
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        manifest_info.external_attr = 0o644 << 16
        archive.writestr(manifest_info, json.dumps(manifest, ensure_ascii=False, indent=2))


def make_wfc_package(output_dir: Path, *, dry_run: bool) -> dict[str, Any]:
    from package_wfc_resource_block import package_resource_block

    return package_resource_block(output_dir=output_dir, write_manifest=True, dry_run=dry_run)


def build_manifest(
    *,
    files: list[BundleFile],
    bundle_path: Path,
    wfc_package_manifest: dict[str, Any] | None,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "ok": True,
        "dry_run": dry_run,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "bundle_path": str(bundle_path),
        "bundle_sha256": None,
        "file_count": len(files),
        "files": [item.as_dict() for item in files],
        "wfc_resource_package": wfc_package_manifest,
        "excluded_external_items": list(EXTERNAL_EXCLUDED_ITEMS),
        "safety": {
            "secret_scan_patterns": len(SECRET_PATTERNS),
            "secret_findings": [],
            "notes": [
                "Default bundle is repo-controlled and safe for technical review.",
                "Live screenshots, signed PDFs, company identifiers, and final registration screenshots stay outside this bundle.",
                "Fallback-marked WFC screenshots must not be described as live WFC ok=true evidence.",
            ],
        },
    }


def build_final_submission_bundle(
    *,
    repo_root: Path = REPO_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    bundle_name: str = DEFAULT_BUNDLE_NAME,
    include_wfc_package: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    local_files = collect_files(repo_root)
    wfc_manifest: dict[str, Any] | None = None
    if include_wfc_package:
        generated_dir = output_dir / "generated" / "wfc-resource-package"
        wfc_manifest = make_wfc_package(generated_dir, dry_run=dry_run)
        if not dry_run:
            package_path = Path(wfc_manifest["package_path"])
            manifest_path = Path(wfc_manifest["manifest_path"])
            local_files.extend(
                [
                    BundleFile(
                        source=package_path,
                        archive_name=f"generated/wfc-resource-package/{package_path.name}",
                        size=package_path.stat().st_size,
                        sha256=file_sha256(package_path),
                    ),
                    BundleFile(
                        source=manifest_path,
                        archive_name=f"generated/wfc-resource-package/{manifest_path.name}",
                        size=manifest_path.stat().st_size,
                        sha256=file_sha256(manifest_path),
                    ),
                ]
            )
    files = sorted(local_files, key=lambda item: item.archive_name)
    findings = detect_secret_findings(files)
    if findings:
        raise ValueError("possible secret(s) found in bundle: " + "; ".join(findings))

    bundle_path = output_dir / bundle_name
    manifest = build_manifest(files=files, bundle_path=bundle_path, wfc_package_manifest=wfc_manifest, dry_run=dry_run)
    if not dry_run:
        write_zip(files, bundle_path, {**manifest, "bundle_sha256": None})
        manifest["bundle_sha256"] = file_sha256(bundle_path)
        manifest_path = bundle_path.with_suffix(".bundle-manifest.json")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_summary(manifest: dict[str, Any]) -> str:
    lines = [
        f"ok={manifest['ok']}",
        f"dry_run={manifest['dry_run']}",
        f"bundle_path={manifest['bundle_path']}",
        f"file_count={manifest['file_count']}",
        f"excluded_external_items={len(manifest['excluded_external_items'])}",
    ]
    if manifest.get("bundle_sha256"):
        lines.append(f"bundle_sha256={manifest['bundle_sha256']}")
    if manifest.get("manifest_path"):
        lines.append(f"manifest_path={manifest['manifest_path']}")
    if manifest.get("wfc_resource_package"):
        lines.append(f"wfc_package={manifest['wfc_resource_package']['package_path']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the repo-controlled Wearedge final submission bundle.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--bundle-name", default=DEFAULT_BUNDLE_NAME)
    parser.add_argument("--skip-wfc-package", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest = build_final_submission_bundle(
            output_dir=args.output_dir,
            bundle_name=args.bundle_name,
            include_wfc_package=not args.skip_wfc_package,
            dry_run=args.dry_run,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else render_summary(manifest))
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
