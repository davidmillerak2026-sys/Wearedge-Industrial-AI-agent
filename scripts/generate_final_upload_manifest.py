from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DEFAULT_ASSETS_DIR = REPO_ROOT / "submission-assets" / "live-evidence"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "submission" / "final-upload-manifest.md"
DEFAULT_SUBMISSION_BUNDLE = (
    DEFAULT_ASSETS_DIR
    / "submission-bundle"
    / "wearedge-industrial-ai-agent-repo-controlled-submission-bundle.zip"
)
DEFAULT_SUBMISSION_BUNDLE_MANIFEST = DEFAULT_SUBMISSION_BUNDLE.with_suffix(".bundle-manifest.json")
DEFAULT_WFC_PACKAGE = DEFAULT_ASSETS_DIR / "gongyi-mofang" / "wfc-resource-package" / "wearedge-agent-service-0.1.0.zip"
DEFAULT_SUBMISSION_BUNDLE_SOURCE = DEFAULT_SUBMISSION_BUNDLE.relative_to(REPO_ROOT).as_posix()
DEFAULT_WFC_PACKAGE_SOURCE = DEFAULT_WFC_PACKAGE.relative_to(REPO_ROOT).as_posix()


@dataclass(frozen=True)
class UploadItem:
    priority: str
    title: str
    source: str
    kind: str
    audience: str
    action: str


UPLOAD_ITEMS: tuple[UploadItem, ...] = (
    UploadItem(
        "P0",
        "Business plan",
        "docs/submission/business-plan.md",
        "repo",
        "Official submission attachment",
        "Convert to PDF/DOCX if the registration system requires a document format.",
    ),
    UploadItem(
        "P0",
        "Technical solution",
        "docs/submission/technical-solution.md",
        "repo",
        "Official submission attachment",
        "Convert to PDF/DOCX if the registration system requires a document format.",
    ),
    UploadItem(
        "P0",
        "Repo-controlled submission bundle",
        DEFAULT_SUBMISSION_BUNDLE_SOURCE,
        "generated_external",
        "Official submission attachment or internal archive",
        "Upload when attachment size allows; it excludes private live evidence by design.",
    ),
    UploadItem(
        "P0",
        "Final enterprise demo video",
        "submission-assets/live-evidence/video/wearedge-enterprise-demo-3-5min.mp4",
        "external_private",
        "Official submission attachment",
        "Use the generated 3-5 minute version; keep fallback boundaries visible.",
    ),
    UploadItem(
        "P0",
        "Registration field copy source",
        "docs/submission/registration-fields.md",
        "repo",
        "Copy/paste into registration system",
        "Use short/mid/long variants; fill only real enterprise/contact values manually.",
    ),
    UploadItem(
        "P1",
        "Offline evaluation report",
        "docs/competition-offline-eval-report.md",
        "repo",
        "Supporting attachment",
        "Use as proof of offline dataset validation and initial-round metric coverage.",
    ),
    UploadItem(
        "P1",
        "Final-round validation report",
        "docs/finals-validation-report.md",
        "repo",
        "Supporting attachment",
        "Use as foundation evidence for multi-direction decision accuracy and coverage.",
    ),
    UploadItem(
        "P1",
        "Jetson edge HTTP latency report",
        "docs/finals-jetson-gateway-latency-benchmark-report.md",
        "repo",
        "Supporting attachment",
        "Use with boundary wording: stdlib HTTP gateway fallback evidence on edge hardware.",
    ),
    UploadItem(
        "P1",
        "Xcelerator OpenAPI import spec",
        "openapi/wearedge-xcelerator-apiworld.openapi.json",
        "repo",
        "Technical appendix",
        "Attach if the platform reviewer wants to reproduce API World import.",
    ),
    UploadItem(
        "P1",
        "Gongyi Mofang WFC resource package",
        DEFAULT_WFC_PACKAGE_SOURCE,
        "generated_external",
        "Technical appendix",
        "Attach as reusable component prototype; do not describe it as live WFC run proof.",
    ),
    UploadItem(
        "P1",
        "Xcelerator screenshot pack",
        "submission-assets/live-evidence/xcelerator/",
        "external_private",
        "Supporting evidence",
        "Use reviewed screenshots; avoid AppID/AppSecret and private contact details.",
    ),
    UploadItem(
        "P1",
        "Gongyi Mofang screenshot pack",
        "submission-assets/live-evidence/gongyi-mofang/",
        "external_private",
        "Supporting evidence",
        "Replace WFC 04/05/06 fallback assets before claiming live WFC closure.",
    ),
    UploadItem(
        "P2",
        "Signed IP/no-dispute statement",
        "submission-assets/live-evidence/legal/ip-and-no-dispute-signed.pdf",
        "external_private",
        "Official submission attachment when required",
        "Upload only to the official registration system or approved internal archive.",
    ),
    UploadItem(
        "P2",
        "Signed no-adverse-record statement",
        "submission-assets/live-evidence/legal/no-adverse-record-signed.pdf",
        "external_private",
        "Official submission attachment when required",
        "Upload only to the official registration system or approved internal archive.",
    ),
)


def build_final_upload_manifest(
    *,
    assets_dir: Path = DEFAULT_ASSETS_DIR,
    repo_root: Path = REPO_ROOT,
    submission_bundle: Path = DEFAULT_SUBMISSION_BUNDLE,
    submission_bundle_manifest: Path = DEFAULT_SUBMISSION_BUNDLE_MANIFEST,
    wfc_package: Path = DEFAULT_WFC_PACKAGE,
) -> dict[str, Any]:
    from verify_final_external_assets import verify_final_external_assets
    from verify_live_evidence import verify_live_evidence
    from verify_submission_package import verify_package

    assets_dir = _resolve_path(assets_dir, repo_root)
    submission_bundle = _resolve_path(submission_bundle, repo_root)
    submission_bundle_manifest = _resolve_path(submission_bundle_manifest, repo_root)
    wfc_package = _resolve_path(wfc_package, repo_root)

    repo = verify_package(repo_root)
    live = verify_live_evidence(assets_dir, "final")
    external_quality = verify_final_external_assets(assets_dir)
    bundle_manifest = _load_json(submission_bundle_manifest)
    live_item_map = {item["path"]: item for item in live["items"]}
    external_quality_map = {item["path"]: item for item in external_quality["items"]}

    items = [
        _status_for_item(
            item,
            repo_root=repo_root,
            assets_dir=assets_dir,
            live_item_map=live_item_map,
            external_quality_map=external_quality_map,
            submission_bundle=submission_bundle,
            wfc_package=wfc_package,
        )
        for item in UPLOAD_ITEMS
    ]
    blocking = _blocking_items(live, external_quality)
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo_ready": bool(repo["repo_ready"]),
        "live_evidence_ready": bool(live["ready"]),
        "external_assets_quality_ready": bool(external_quality["ready"]),
        "official_submission_ready": bool(repo["repo_ready"]) and bool(live["ready"]) and bool(external_quality["ready"]),
        "assets_dir": str(assets_dir),
        "bundle": {
            "path": str(submission_bundle),
            "present": submission_bundle.is_file() and submission_bundle.stat().st_size > 0,
            "manifest_path": str(submission_bundle_manifest),
            "manifest_present": bool(bundle_manifest),
            "sha256": bundle_manifest.get("bundle_sha256") if bundle_manifest else None,
            "file_count": bundle_manifest.get("file_count") if bundle_manifest else None,
        },
        "wfc_package": {
            "path": str(wfc_package),
            "present": wfc_package.is_file() and wfc_package.stat().st_size > 0,
        },
        "status_counts": _status_counts(items),
        "blocking_items": blocking,
        "items": items,
        "privacy_boundary": [
            "This manifest lists paths and statuses only; it does not include enterprise identifiers or contact values.",
            "Do not commit files under submission-assets/live-evidence/.",
            "Upload signed legal files and registration screenshots only to the official registration system or approved private archive.",
        ],
    }


def _status_for_item(
    item: UploadItem,
    *,
    repo_root: Path,
    assets_dir: Path,
    live_item_map: dict[str, dict[str, Any]],
    external_quality_map: dict[str, dict[str, Any]],
    submission_bundle: Path,
    wfc_package: Path,
) -> dict[str, Any]:
    source = item.source
    normalized_source = source.replace("\\", "/")
    if source == DEFAULT_SUBMISSION_BUNDLE_SOURCE:
        present = submission_bundle.is_file() and submission_bundle.stat().st_size > 0
        status = "ready" if present else "missing"
    elif source == DEFAULT_WFC_PACKAGE_SOURCE:
        present = wfc_package.is_file() and wfc_package.stat().st_size > 0
        status = "ready" if present else "missing"
    elif item.kind == "repo":
        path = repo_root / source
        present = path.is_file() and path.stat().st_size > 0
        status = "ready" if present else "missing"
    elif item.kind == "external_private":
        relative = _strip_live_evidence_prefix(normalized_source)
        if normalized_source.endswith("/"):
            group = relative.strip("/")
            group_items = [value for key, value in live_item_map.items() if key.startswith(f"{group}/")]
            present = bool(group_items) and any(group_item["present"] for group_item in group_items)
            has_fallback = any(group_item["fallback"] for group_item in group_items)
            has_missing = any(not group_item["present"] for group_item in group_items)
            status = "fallback" if has_fallback else ("partial" if has_missing else ("ready" if present else "missing"))
        else:
            live_item = live_item_map.get(relative)
            quality_item = external_quality_map.get(relative)
            present = bool(live_item and live_item["present"])
            if quality_item:
                status = "ready" if quality_item["status"] == "ready" else "blocked"
            elif live_item:
                status = "fallback" if live_item.get("fallback") else ("ready" if live_item["present"] else "missing")
            else:
                path = assets_dir / relative
                present = path.is_file() and path.stat().st_size > 0
                status = "ready" if present else "missing"
    else:
        path = repo_root / source
        present = path.exists()
        status = "ready" if present else "missing"

    return {
        "priority": item.priority,
        "title": item.title,
        "source": item.source,
        "kind": item.kind,
        "audience": item.audience,
        "status": status,
        "present": present,
        "action": item.action,
    }


def _strip_live_evidence_prefix(path: str) -> str:
    prefix = "submission-assets/live-evidence/"
    return path[len(prefix) :] if path.startswith(prefix) else path


def _blocking_items(live: dict[str, Any], external_quality: dict[str, Any]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for item in live["missing"]:
        blockers.append({"path": item, "reason": "missing final live-evidence file"})
    for warning in live["warnings"]:
        blockers.append({"path": warning["path"], "reason": "fallback marker still present"})
    for failure in external_quality["failures"]:
        blockers.append({"path": failure["path"], "reason": f"quality failure: {failure['code']}"})
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for blocker in blockers:
        unique[(blocker["path"], blocker["reason"])] = blocker
    return list(unique.values())


def _status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return dict(sorted(counts.items()))


def render_upload_manifest(manifest: dict[str, Any]) -> str:
    lines = [
        "# Final Upload Manifest",
        "",
        f"Updated: {manifest['generated_at']}",
        "",
        "## Gate",
        "",
        f"- Repository ready: {manifest['repo_ready']}",
        f"- Live evidence ready: {manifest['live_evidence_ready']}",
        f"- External asset quality ready: {manifest['external_assets_quality_ready']}",
        f"- Official submission ready: {manifest['official_submission_ready']}",
        f"- Bundle present: {manifest['bundle']['present']}",
        f"- Bundle SHA256: `{manifest['bundle']['sha256']}`",
        f"- Bundle file count: `{manifest['bundle']['file_count']}`",
        f"- WFC resource package present: {manifest['wfc_package']['present']}",
        "",
        "## Upload Queue",
        "",
        "| Priority | Status | Attachment | Source | Audience | Action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in manifest["items"]:
        lines.append(
            f"| {item['priority']} | {item['status']} | {item['title']} | "
            f"`{item['source']}` | {item['audience']} | {item['action']} |"
        )

    lines.extend(["", "## Blocking Items", ""])
    if manifest["blocking_items"]:
        for item in manifest["blocking_items"]:
            lines.append(f"- `{item['path']}`: {item['reason']}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Privacy Boundary", ""])
    lines.extend(f"- {line}" for line in manifest["privacy_boundary"])

    lines.extend(
        [
            "",
            "## Final Checks",
            "",
            "```powershell",
            "python scripts/run_final_readiness_pipeline.py --json",
            "python scripts/verify_live_evidence.py --stage final --write-manifest",
            "python scripts/verify_final_external_assets.py --write-report",
            "python scripts/generate_final_upload_manifest.py --write",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _resolve_path(path: Path, repo_root: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else repo_root / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the final upload manifest from current verifiers.")
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--submission-bundle", type=Path, default=DEFAULT_SUBMISSION_BUNDLE)
    parser.add_argument("--submission-bundle-manifest", type=Path, default=DEFAULT_SUBMISSION_BUNDLE_MANIFEST)
    parser.add_argument("--wfc-package", type=Path, default=DEFAULT_WFC_PACKAGE)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    manifest = build_final_upload_manifest(
        assets_dir=args.assets_dir,
        submission_bundle=args.submission_bundle,
        submission_bundle_manifest=args.submission_bundle_manifest,
        wfc_package=args.wfc_package,
    )
    output = _resolve_path(args.output, REPO_ROOT)
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_upload_manifest(manifest), encoding="utf-8")
        manifest["output_path"] = str(output)

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else render_upload_manifest(manifest))
    return 0 if manifest["repo_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
