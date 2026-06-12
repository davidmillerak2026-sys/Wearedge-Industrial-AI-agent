from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from capture_submission_screenshots import find_browser, render_markdown  # noqa: E402


DEFAULT_OUTPUT_DIR = REPO_ROOT / "submission-assets" / "live-evidence" / "official-attachment-pack"
DEFAULT_PACK_NAME = "wearedge-official-attachment-pack.zip"
ZIP_TIMESTAMP = (2026, 6, 12, 0, 0, 0)
SECRET_PATTERNS = (
    re.compile(r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\b(password|passwd|pwd)\s*[:=]\s*['\"]?[^'\"\s<>]+", re.IGNORECASE),
    re.compile(r"\b(cookie|sessionid|authorization)\s*[:=]\s*['\"][^'\"\s<>]+", re.IGNORECASE),
)


@dataclass(frozen=True)
class AttachmentSpec:
    slug: str
    title: str
    source: str
    priority: str
    audience: str
    note: str


ATTACHMENTS: tuple[AttachmentSpec, ...] = (
    AttachmentSpec(
        "business-plan",
        "Business Plan",
        "docs/submission/business-plan.md",
        "P0",
        "Official submission attachment",
        "Print-ready HTML; export to PDF/DOCX if the official system requires a file format.",
    ),
    AttachmentSpec(
        "technical-solution",
        "Technical Solution",
        "docs/submission/technical-solution.md",
        "P0",
        "Official submission attachment",
        "Technical narrative for multi-agent architecture, edge runtime, WFC/Xcelerator integration, and safety boundary.",
    ),
    AttachmentSpec(
        "registration-fields",
        "Registration Field Copy Source",
        "docs/submission/registration-fields.md",
        "P0",
        "Copy/paste source",
        "Human-owned enterprise/contact values remain blank or template-only until final submitter fills them.",
    ),
    AttachmentSpec(
        "offline-evaluation-report",
        "Offline Evaluation Report",
        "docs/competition-offline-eval-report.md",
        "P1",
        "Supporting attachment",
        "Initial-round offline validation evidence; simulated/offline boundary must remain visible.",
    ),
    AttachmentSpec(
        "finals-validation-report",
        "Final-Round Validation Report",
        "docs/finals-validation-report.md",
        "P1",
        "Supporting attachment",
        "Finals foundation evidence for direction coverage and decision accuracy.",
    ),
    AttachmentSpec(
        "jetson-edge-latency-report",
        "Jetson Edge HTTP Latency Report",
        "docs/finals-jetson-gateway-latency-benchmark-report.md",
        "P1",
        "Supporting attachment",
        "Edge-hardware HTTP decision-path evidence with stdlib gateway fallback boundary.",
    ),
    AttachmentSpec(
        "first-round-attachment-index",
        "First-Round Attachment Index",
        "docs/submission/first-round-submission-attachment-index.md",
        "P1",
        "Submission operator checklist",
        "Helps the final submitter choose which files to upload.",
    ),
    AttachmentSpec(
        "final-upload-manifest",
        "Final Upload Manifest",
        "docs/submission/final-upload-manifest.md",
        "P1",
        "Submission operator checklist",
        "Current upload queue and blocking items; does not contain private company/contact values.",
    ),
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_official_attachment_pack(
    *,
    repo_root: Path = REPO_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    pack_name: str = DEFAULT_PACK_NAME,
    include_pdf: bool = False,
    browser_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = _resolve_path(output_dir, repo_root)
    html_dir = output_dir / "html"
    pdf_dir = output_dir / "pdf"
    zip_path = output_dir / pack_name

    missing = [spec.source for spec in ATTACHMENTS if not (repo_root / spec.source).is_file()]
    if missing:
        raise ValueError(f"missing official attachment source(s): {', '.join(missing)}")

    source_findings = detect_secret_findings([repo_root / spec.source for spec in ATTACHMENTS], repo_root=repo_root)
    if source_findings:
        raise ValueError("possible secret(s) found in attachment sources: " + "; ".join(source_findings))

    manifest = {
        "ok": True,
        "dry_run": dry_run,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "output_dir": str(output_dir),
        "zip_path": str(zip_path),
        "zip_sha256": None,
        "include_pdf": include_pdf,
        "attachments": [],
        "privacy_boundary": [
            "This pack is repo-controlled and excludes signed legal files, company identifiers, and registration screenshots.",
            "Print-ready HTML can be exported to PDF/DOCX by the final submitter if the official system requires it.",
            "Fallback-marked WFC screenshots remain outside this pack and must not be described as live WFC closure.",
        ],
    }
    if dry_run:
        return manifest

    output_dir.mkdir(parents=True, exist_ok=True)
    html_dir.mkdir(parents=True, exist_ok=True)
    if include_pdf:
        pdf_dir.mkdir(parents=True, exist_ok=True)
    browser = find_browser(browser_path) if include_pdf else None

    files_for_zip: list[Path] = []
    for index, spec in enumerate(ATTACHMENTS, start=1):
        source_path = repo_root / spec.source
        html_path = html_dir / f"{index:02d}-{spec.slug}.html"
        html_path.write_text(render_attachment_html(spec, source_path), encoding="utf-8")
        files_for_zip.append(html_path)
        item = {
            "slug": spec.slug,
            "title": spec.title,
            "priority": spec.priority,
            "audience": spec.audience,
            "source": spec.source,
            "source_sha256": file_sha256(source_path),
            "html_path": str(html_path),
            "html_sha256": file_sha256(html_path),
            "pdf_path": None,
            "pdf_sha256": None,
            "pdf_status": "not_requested",
            "note": spec.note,
        }
        if include_pdf:
            pdf_path = pdf_dir / f"{index:02d}-{spec.slug}.pdf"
            if browser:
                pdf_result = render_pdf(browser=browser, html_path=html_path, pdf_path=pdf_path)
                item["pdf_status"] = "ready" if pdf_result["ok"] else "failed"
                item["pdf_path"] = str(pdf_path)
                if pdf_result["ok"]:
                    item["pdf_sha256"] = file_sha256(pdf_path)
                    files_for_zip.append(pdf_path)
                item["pdf_error"] = pdf_result.get("error")
            else:
                item["pdf_status"] = "browser_not_found"
        manifest["attachments"].append(item)

    manifest_path = output_dir / "OFFICIAL_ATTACHMENT_PACK_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    files_for_zip.append(manifest_path)
    write_zip(zip_path, files_for_zip, output_dir)
    manifest["zip_sha256"] = file_sha256(zip_path)
    manifest["manifest_path"] = str(manifest_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def render_attachment_html(spec: AttachmentSpec, source_path: Path) -> str:
    body = render_markdown(source_path.read_text(encoding="utf-8"))
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '  <meta charset="utf-8">',
            f"  <title>{html.escape(spec.title)}</title>",
            "  <style>",
            "    @page { size: A4; margin: 18mm 16mm; }",
            "    body { font-family: 'Segoe UI', Arial, sans-serif; color: #17202a; line-height: 1.55; }",
            "    header { border-bottom: 2px solid #0f3557; margin-bottom: 18px; padding-bottom: 10px; }",
            "    h1 { margin: 0 0 6px; font-size: 26px; color: #102a43; }",
            "    .meta { color: #586574; font-size: 12px; }",
            "    h2 { margin-top: 22px; color: #0f3557; font-size: 20px; }",
            "    h3 { margin-top: 18px; color: #133f65; font-size: 16px; }",
            "    p, li { font-size: 12.5px; }",
            "    table { width: 100%; border-collapse: collapse; margin: 10px 0 16px; font-size: 11px; }",
            "    th, td { border: 1px solid #d8e0e8; padding: 6px 7px; vertical-align: top; }",
            "    th { background: #eef4fa; }",
            "    code { background: #eef3f7; padding: 1px 4px; border-radius: 3px; }",
            "    pre { white-space: pre-wrap; background: #0f1720; color: #e6edf3; padding: 10px; border-radius: 6px; font-size: 11px; }",
            "    .boundary { margin-top: 20px; padding: 10px 12px; border-left: 4px solid #155a9c; background: #f4f8fb; font-size: 12px; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <header>",
            f"    <h1>{html.escape(spec.title)}</h1>",
            f"    <div class=\"meta\">Priority: {html.escape(spec.priority)} | Audience: {html.escape(spec.audience)} | Source: {html.escape(spec.source)}</div>",
            "  </header>",
            f"  {body}",
            f"  <div class=\"boundary\">Boundary: {html.escape(spec.note)}</div>",
            "</body>",
            "</html>",
        ]
    )


def render_pdf(*, browser: Path, html_path: Path, pdf_path: Path) -> dict[str, Any]:
    command = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_path.resolve().as_uri(),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=90)
    ok = completed.returncode == 0 and pdf_path.is_file() and pdf_path.stat().st_size > 0
    return {
        "ok": ok,
        "returncode": completed.returncode,
        "error": completed.stderr.strip() if not ok else None,
    }


def write_zip(zip_path: Path, files: list[Path], output_dir: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            relative = path.relative_to(output_dir)
            info = zipfile.ZipInfo(PurePosixPath(*relative.parts).as_posix(), date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def detect_secret_findings(paths: list[Path], *, repo_root: Path = REPO_ROOT) -> list[str]:
    findings: list[str] = []
    repo_root = repo_root.resolve()
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                try:
                    display = path.resolve().relative_to(repo_root).as_posix()
                except ValueError:
                    display = str(path)
                findings.append(f"{display}: matches {pattern.pattern}")
    return findings


def render_summary(manifest: dict[str, Any]) -> str:
    lines = [
        f"ok={manifest['ok']}",
        f"dry_run={manifest['dry_run']}",
        f"output_dir={manifest['output_dir']}",
        f"zip_path={manifest['zip_path']}",
        f"zip_sha256={manifest.get('zip_sha256')}",
        f"attachment_count={len(manifest['attachments'])}",
        f"include_pdf={manifest['include_pdf']}",
    ]
    return "\n".join(lines)


def _resolve_path(path: Path, repo_root: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else repo_root / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build print-ready official submission attachment HTML/PDF pack.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--pack-name", default=DEFAULT_PACK_NAME)
    parser.add_argument("--include-pdf", action="store_true")
    parser.add_argument("--browser", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest = build_official_attachment_pack(
            output_dir=args.output_dir,
            pack_name=args.pack_name,
            include_pdf=args.include_pdf,
            browser_path=args.browser,
            dry_run=args.dry_run,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else render_summary(manifest))
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
