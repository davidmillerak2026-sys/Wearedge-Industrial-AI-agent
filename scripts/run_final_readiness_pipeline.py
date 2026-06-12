from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DEFAULT_ASSETS_DIR = REPO_ROOT / "submission-assets" / "live-evidence"
DEFAULT_SUBMISSION_MANIFEST = REPO_ROOT / "docs" / "submission" / "submission-package-manifest.md"
DEFAULT_LIVE_EVIDENCE_MANIFEST = DEFAULT_ASSETS_DIR / "live-evidence-manifest.md"
DEFAULT_READINESS_REPORT = REPO_ROOT / "docs" / "submission" / "final-readiness-report.md"
DEFAULT_BUNDLE_DIR = DEFAULT_ASSETS_DIR / "submission-bundle"
DEFAULT_WFC_PACKAGE_DIR = DEFAULT_ASSETS_DIR / "gongyi-mofang" / "wfc-resource-package"


def run_pipeline(
    *,
    assets_dir: Path = DEFAULT_ASSETS_DIR,
    submission_manifest_path: Path = DEFAULT_SUBMISSION_MANIFEST,
    live_evidence_manifest_path: Path | None = None,
    readiness_report_path: Path = DEFAULT_READINESS_REPORT,
    bundle_output_dir: Path = DEFAULT_BUNDLE_DIR,
    wfc_package_output_dir: Path = DEFAULT_WFC_PACKAGE_DIR,
    overwrite_templates: bool = False,
    strict_final: bool = False,
) -> dict[str, Any]:
    from build_final_submission_bundle import build_final_submission_bundle
    from generate_final_readiness_report import build_final_readiness, render_readiness_report
    from package_wfc_resource_block import package_resource_block
    from prepare_final_human_action_pack import prepare_templates
    from verify_live_evidence import render_manifest as render_live_manifest
    from verify_live_evidence import verify_live_evidence
    from verify_submission_package import render_manifest as render_submission_manifest
    from verify_submission_package import verify_package

    assets_dir = _resolve_path(assets_dir)
    submission_manifest_path = _resolve_path(submission_manifest_path)
    readiness_report_path = _resolve_path(readiness_report_path)
    bundle_output_dir = _resolve_path(bundle_output_dir)
    wfc_package_output_dir = _resolve_path(wfc_package_output_dir)
    live_evidence_manifest_path = _resolve_path(live_evidence_manifest_path or assets_dir / "live-evidence-manifest.md")

    human_action_pack = prepare_templates(
        assets_dir,
        overwrite=overwrite_templates,
        write_manifest=True,
    )
    wfc_package = package_resource_block(output_dir=wfc_package_output_dir, write_manifest=True)
    submission_package = build_final_submission_bundle(output_dir=bundle_output_dir)

    repo_verification = verify_package(REPO_ROOT)
    submission_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    submission_manifest_path.write_text(render_submission_manifest(repo_verification), encoding="utf-8")

    final_evidence = verify_live_evidence(assets_dir, "final")
    live_evidence_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    live_evidence_manifest_path.write_text(render_live_manifest(final_evidence), encoding="utf-8")

    readiness = build_final_readiness(
        assets_dir=assets_dir,
        bundle_path=Path(submission_package["bundle_path"]),
        bundle_manifest_path=Path(submission_package["manifest_path"]),
        human_action_manifest_path=Path(human_action_pack["manifest_path"]),
    )
    readiness_report_path.parent.mkdir(parents=True, exist_ok=True)
    readiness_report_path.write_text(render_readiness_report(readiness), encoding="utf-8")

    result = {
        "ok": bool(repo_verification["repo_ready"]) and (bool(final_evidence["ready"]) or not strict_final),
        "strict_final": strict_final,
        "repo_ready": bool(repo_verification["repo_ready"]),
        "platform_ready": bool(readiness["platform_evidence"]["ready"]),
        "final_ready": bool(final_evidence["ready"]),
        "final_missing_count": int(final_evidence["missing_count"]),
        "fallback_warning_count": len(final_evidence["warnings"]),
        "bundle_sha256": submission_package.get("bundle_sha256"),
        "bundle_path": submission_package["bundle_path"],
        "wfc_package_path": wfc_package["package_path"],
        "submission_manifest_path": str(submission_manifest_path),
        "live_evidence_manifest_path": str(live_evidence_manifest_path),
        "readiness_report_path": str(readiness_report_path),
        "human_action_manifest_path": human_action_pack.get("manifest_path"),
        "recommended_next_actions": readiness["recommended_next_actions"],
    }
    if strict_final and not final_evidence["ready"]:
        result["blocking_reason"] = "Final external/human-owned evidence is incomplete."
    return result


def render_summary(result: dict[str, Any]) -> str:
    lines = [
        f"ok={result['ok']}",
        f"strict_final={result['strict_final']}",
        f"repo_ready={result['repo_ready']}",
        f"platform_ready={result['platform_ready']}",
        f"final_ready={result['final_ready']}",
        f"final_missing_count={result['final_missing_count']}",
        f"fallback_warning_count={result['fallback_warning_count']}",
        f"bundle_sha256={result['bundle_sha256']}",
        f"readiness_report={result['readiness_report_path']}",
        "recommended_next_actions:",
    ]
    lines.extend(f"- {action}" for action in result["recommended_next_actions"])
    if result.get("blocking_reason"):
        lines.append(f"blocking_reason={result['blocking_reason']}")
    return "\n".join(lines)


def _resolve_path(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh the final Wearedge submission readiness assets in the safe order."
    )
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    parser.add_argument("--submission-manifest", type=Path, default=DEFAULT_SUBMISSION_MANIFEST)
    parser.add_argument("--live-evidence-manifest", type=Path, default=None)
    parser.add_argument("--readiness-report", type=Path, default=DEFAULT_READINESS_REPORT)
    parser.add_argument("--bundle-output-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    parser.add_argument("--wfc-package-output-dir", type=Path, default=DEFAULT_WFC_PACKAGE_DIR)
    parser.add_argument("--overwrite-templates", action="store_true")
    parser.add_argument(
        "--strict-final",
        action="store_true",
        help="Exit non-zero until the six external/human-owned final evidence files are complete.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = run_pipeline(
        assets_dir=args.assets_dir,
        submission_manifest_path=args.submission_manifest,
        live_evidence_manifest_path=args.live_evidence_manifest,
        readiness_report_path=args.readiness_report,
        bundle_output_dir=args.bundle_output_dir,
        wfc_package_output_dir=args.wfc_package_output_dir,
        overwrite_templates=args.overwrite_templates,
        strict_final=args.strict_final,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_summary(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
