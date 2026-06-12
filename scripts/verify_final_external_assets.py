from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS_DIR = REPO_ROOT / "submission-assets" / "live-evidence"
DEFAULT_REPORT_NAME = "final-external-assets-quality-report.md"


@dataclass(frozen=True)
class ExternalAssetSpec:
    path: str
    title: str
    kind: str
    note: str


WFC_LIVE_REPLACEMENTS: tuple[ExternalAssetSpec, ...] = (
    ExternalAssetSpec(
        "gongyi-mofang/04-dashboard-decision-view.png",
        "Live WFC Dashboard decision view",
        "image",
        "Must be a live WFC screenshot, not a fallback/mock dashboard.",
    ),
    ExternalAssetSpec(
        "gongyi-mofang/05-run-log-ok-true.png",
        "Live WFC run log ok=true",
        "image",
        "Must show live execution success, function output, table writeback, or equivalent run log.",
    ),
    ExternalAssetSpec(
        "gongyi-mofang/06-human-approval-gate.png",
        "Live WFC HumanApprovalGate",
        "image",
        "Must show human approval state for high-risk recommendations.",
    ),
)

HUMAN_FINAL_ASSETS: tuple[ExternalAssetSpec, ...] = (
    ExternalAssetSpec(
        "legal/company-info-filled.md",
        "Filled company and contact information",
        "company_markdown",
        "Must be filled locally; this script reports only field status, not values.",
    ),
    ExternalAssetSpec(
        "legal/ip-and-no-dispute-signed.pdf",
        "Signed IP and no-dispute statement",
        "pdf",
        "Must be exported from the signed/stamped final statement.",
    ),
    ExternalAssetSpec(
        "legal/no-adverse-record-signed.pdf",
        "Signed no-adverse-record statement",
        "pdf",
        "Must be exported from the signed/stamped final statement.",
    ),
    ExternalAssetSpec(
        "legal/submission-contact-confirmation.md",
        "Submission contact confirmation",
        "contact_markdown",
        "Must confirm primary/backup contacts and platform account ownership.",
    ),
    ExternalAssetSpec(
        "submission/01-registration-form-filled.png",
        "Filled registration form screenshot",
        "image",
        "Must show filled official registration form with sensitive values redacted for reuse.",
    ),
    ExternalAssetSpec(
        "submission/02-submission-success.png",
        "Submission success screenshot",
        "image",
        "Must show official submitted/success status after final submission.",
    ),
)

VIDEO_ASSETS: tuple[ExternalAssetSpec, ...] = (
    ExternalAssetSpec(
        "video/wearedge-enterprise-demo-3-5min.mp4",
        "Final enterprise demo video",
        "mp4",
        "Must be the final 3-5 minute defense/submission video.",
    ),
    ExternalAssetSpec(
        "video/wearedge-enterprise-demo-script-final.md",
        "Final demo narration script",
        "nonempty_markdown",
        "Must match the submitted video.",
    ),
)

COMPANY_REQUIRED_FIELDS = (
    "Enterprise name",
    "Unified social credit code",
    "Registered address",
    "Enterprise type",
    "SME eligibility confirmed",
    "No adverse record confirmed",
    "Project owner",
    "Mobile",
    "Email",
    "Backup contact",
    "Backup mobile",
    "Backup email",
)

CONTACT_REQUIRED_FIELDS = (
    "Primary contact name",
    "Primary contact mobile",
    "Primary contact email",
    "Backup contact name",
    "Backup contact mobile",
    "Backup contact email",
    "Xcelerator account owner confirmed",
    "Gongyi Mofang account owner confirmed",
    "Final submitter confirmed",
)

REQUIRED_TEAM_ROLES = (
    "Project lead",
    "Technical lead",
    "IT/OT integration lead",
    "Edge deployment lead",
    "Business lead",
    "Delivery lead",
)

PLACEHOLDER_PATTERN = re.compile(r"\b(TBD|TODO|PLACEHOLDER|FILL ME|UNKNOWN)\b|待填|未填|占位", re.IGNORECASE)


def verify_final_external_assets(
    assets_dir: Path = DEFAULT_ASSETS_DIR,
    *,
    require_wfc_live: bool = True,
    require_video: bool = True,
) -> dict[str, Any]:
    assets_dir = _resolve_assets_dir(assets_dir)
    specs = list(HUMAN_FINAL_ASSETS)
    if require_wfc_live:
        specs.extend(WFC_LIVE_REPLACEMENTS)
    if require_video:
        specs.extend(VIDEO_ASSETS)

    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    for spec in specs:
        path = assets_dir / spec.path
        record_failures, record_warnings = _check_spec(spec, path)
        records.append(
            {
                "path": spec.path,
                "title": spec.title,
                "kind": spec.kind,
                "status": "ready" if not record_failures else "failed",
                "failure_count": len(record_failures),
                "warning_count": len(record_warnings),
                "note": spec.note,
            }
        )
        failures.extend(record_failures)
        warnings.extend(record_warnings)

    return {
        "assets_dir": str(assets_dir),
        "ready": not failures,
        "required_count": len(specs),
        "ready_count": sum(1 for record in records if record["status"] == "ready"),
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "failures": failures,
        "warnings": warnings,
        "items": records,
        "privacy": "This verifier reports only status and paths. It does not echo company/contact values.",
    }


def _check_spec(spec: ExternalAssetSpec, path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    failures: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    relative_path = spec.path
    if not path.exists() or not path.is_file() or path.stat().st_size == 0:
        failures.append(_failure(relative_path, "missing_or_empty", f"{spec.title} is missing or empty."))
        return failures, warnings

    fallback_meta = path.with_suffix(".fallback.json")
    if spec in WFC_LIVE_REPLACEMENTS and fallback_meta.exists():
        failures.append(
            _failure(
                relative_path,
                "fallback_marker_present",
                "Fallback metadata is still present; replace with reviewed live WFC evidence first.",
            )
        )

    if spec.kind == "image":
        failures.extend(_check_image(path, relative_path))
    elif spec.kind == "pdf":
        failures.extend(_check_pdf(path, relative_path))
    elif spec.kind == "mp4":
        failures.extend(_check_mp4(path, relative_path))
    elif spec.kind == "company_markdown":
        failures.extend(_check_company_markdown(path, relative_path))
    elif spec.kind == "contact_markdown":
        failures.extend(_check_contact_markdown(path, relative_path))
    elif spec.kind == "nonempty_markdown":
        failures.extend(_check_nonempty_markdown(path, relative_path))
    else:
        failures.append(_failure(relative_path, "unknown_kind", f"Unknown asset kind: {spec.kind}"))

    if path.suffix.lower() in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        if _contains_private_secret_shape(text):
            warnings.append(
                {
                    "path": relative_path,
                    "code": "possible_secret_shape",
                    "message": "Text contains a token/password-like pattern; keep this file ignored and do not reuse publicly.",
                }
            )
    return failures, warnings


def _check_image(path: Path, relative_path: str) -> list[dict[str, str]]:
    data = path.read_bytes()[:16]
    failures: list[dict[str, str]] = []
    if not (data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\xff\xd8\xff")):
        failures.append(_failure(relative_path, "invalid_image_magic", "Expected a PNG or JPEG screenshot."))
    if path.stat().st_size < 512:
        failures.append(_failure(relative_path, "image_too_small", "Screenshot is too small to be useful evidence."))
    return failures


def _check_pdf(path: Path, relative_path: str) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    if not path.read_bytes()[:5].startswith(b"%PDF-"):
        failures.append(_failure(relative_path, "invalid_pdf_magic", "Expected a PDF file."))
    if path.stat().st_size < 512:
        failures.append(_failure(relative_path, "pdf_too_small", "Signed PDF is too small to be useful evidence."))
    return failures


def _check_mp4(path: Path, relative_path: str) -> list[dict[str, str]]:
    header = path.read_bytes()[:64]
    failures: list[dict[str, str]] = []
    if b"ftyp" not in header:
        failures.append(_failure(relative_path, "invalid_mp4_magic", "Expected an MP4 file with an ftyp box."))
    if path.stat().st_size < 10_000:
        failures.append(_failure(relative_path, "mp4_too_small", "Demo video is too small to be a final 3-5 minute video."))
    return failures


def _check_nonempty_markdown(path: Path, relative_path: str) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    failures: list[dict[str, str]] = []
    if len(text.strip()) < 200:
        failures.append(_failure(relative_path, "markdown_too_short", "Markdown evidence is too short."))
    if PLACEHOLDER_PATTERN.search(text):
        failures.append(_failure(relative_path, "placeholder_text", "Markdown still contains placeholder text."))
    return failures


def _check_company_markdown(path: Path, relative_path: str) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    failures = _check_nonempty_markdown(path, relative_path)
    values = _extract_two_column_values(text)
    for field in COMPANY_REQUIRED_FIELDS:
        value = values.get(field, "")
        if not _is_filled(value):
            failures.append(_failure(relative_path, f"missing_field:{field}", f"Required field is empty: {field}"))

    rows = _extract_table_rows(text)
    for role in REQUIRED_TEAM_ROLES:
        role_rows = [row for row in rows if row and row[0] == role]
        if not role_rows:
            failures.append(_failure(relative_path, f"missing_role:{role}", f"Required team role is missing: {role}"))
            continue
        row = role_rows[0]
        name = row[1] if len(row) > 1 else ""
        confirmed = row[3] if len(row) > 3 else ""
        if not _is_filled(name) or not _is_filled(confirmed):
            failures.append(_failure(relative_path, f"incomplete_role:{role}", f"Required team role is incomplete: {role}"))
    return failures


def _check_contact_markdown(path: Path, relative_path: str) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    failures = _check_nonempty_markdown(path, relative_path)
    values = _extract_two_column_values(text)
    for field in CONTACT_REQUIRED_FIELDS:
        value = values.get(field, "")
        if not _is_filled(value):
            failures.append(_failure(relative_path, f"missing_field:{field}", f"Required field is empty: {field}"))
    return failures


def _extract_two_column_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in _extract_table_rows(text):
        if len(row) >= 2 and row[0] and row[0].lower() not in {"field", "---"}:
            values[row[0]] = row[1]
    return values


def _extract_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append(cells)
    return rows


def _is_filled(value: str) -> bool:
    stripped = value.strip()
    return bool(stripped) and not PLACEHOLDER_PATTERN.search(stripped)


def _contains_private_secret_shape(text: str) -> bool:
    return bool(
        re.search(r"\b(password|passwd|pwd|secret|token|cookie|session)\s*[:=]\s*\S+", text, re.IGNORECASE)
        or re.search(r"\bsk-[A-Za-z0-9_-]{12,}", text)
    )


def _failure(path: str, code: str, message: str) -> dict[str, str]:
    return {"path": path, "code": code, "message": message}


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Final External Assets Quality Report",
        "",
        f"- Assets dir: `{result['assets_dir']}`",
        f"- Ready: {result['ready']}",
        f"- Ready items: {result['ready_count']} / {result['required_count']}",
        f"- Failures: {result['failure_count']}",
        f"- Warnings: {result['warning_count']}",
        f"- Privacy: {result['privacy']}",
        "",
        "## Failures",
        "",
    ]
    if result["failures"]:
        for failure in result["failures"]:
            lines.append(f"- `{failure['path']}` [{failure['code']}]: {failure['message']}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Warnings", ""])
    if result["warnings"]:
        for warning in result["warnings"]:
            lines.append(f"- `{warning['path']}` [{warning['code']}]: {warning['message']}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Item Detail", "", "| Status | Path | Title | Kind |", "| --- | --- | --- | --- |"])
    for item in result["items"]:
        lines.append(f"| {item['status']} | `{item['path']}` | {item['title']} | {item['kind']} |")
    lines.append("")
    return "\n".join(lines)


def _resolve_assets_dir(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate final external/human-owned assets without printing sensitive field values."
    )
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    parser.add_argument("--skip-wfc-live", action="store_true", help="Skip live WFC replacement checks.")
    parser.add_argument("--skip-video", action="store_true", help="Skip final video/script checks.")
    parser.add_argument("--allow-incomplete", action="store_true", help="Exit zero even when final assets are incomplete.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--write-report",
        nargs="?",
        const=None,
        default=False,
        help="Write a Markdown quality report. Defaults to final-external-assets-quality-report.md in the assets dir.",
    )
    args = parser.parse_args(argv)

    assets_dir = _resolve_assets_dir(args.assets_dir)
    result = verify_final_external_assets(
        assets_dir,
        require_wfc_live=not args.skip_wfc_live,
        require_video=not args.skip_video,
    )

    if args.write_report is not False:
        report_path = Path(args.write_report) if args.write_report else assets_dir / DEFAULT_REPORT_NAME
        if not report_path.is_absolute():
            report_path = REPO_ROOT / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_report(result), encoding="utf-8")
        result["report_path"] = str(report_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ready={result['ready']}")
        print(f"ready_count={result['ready_count']}")
        print(f"failure_count={result['failure_count']}")
        print(f"warning_count={result['warning_count']}")
        if "report_path" in result:
            print(f"report_path={result['report_path']}")

    return 0 if result["ready"] or args.allow_incomplete else 1


if __name__ == "__main__":
    raise SystemExit(main())
