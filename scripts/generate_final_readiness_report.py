from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DEFAULT_ASSETS_DIR = REPO_ROOT / "submission-assets" / "live-evidence"
DEFAULT_REPORT = REPO_ROOT / "docs" / "submission" / "final-readiness-report.md"
DEFAULT_BUNDLE = (
    DEFAULT_ASSETS_DIR
    / "submission-bundle"
    / "wearedge-industrial-ai-agent-repo-controlled-submission-bundle.zip"
)
DEFAULT_BUNDLE_MANIFEST = DEFAULT_BUNDLE.with_suffix(".bundle-manifest.json")
DEFAULT_HUMAN_ACTION_MANIFEST = DEFAULT_ASSETS_DIR / "final-human-action-pack-manifest.json"
DEFAULT_EDGE_RUNTIME_EVIDENCE_MANIFEST = (
    DEFAULT_ASSETS_DIR / "edge-runtime" / "07-edge-runtime-evidence-manifest.md"
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def build_final_readiness(
    *,
    assets_dir: Path = DEFAULT_ASSETS_DIR,
    bundle_path: Path = DEFAULT_BUNDLE,
    bundle_manifest_path: Path = DEFAULT_BUNDLE_MANIFEST,
    human_action_manifest_path: Path = DEFAULT_HUMAN_ACTION_MANIFEST,
    edge_runtime_manifest_path: Path = DEFAULT_EDGE_RUNTIME_EVIDENCE_MANIFEST,
) -> dict[str, Any]:
    from verify_live_evidence import verify_live_evidence
    from verify_final_external_assets import verify_final_external_assets
    from verify_finals_foundation import verify_finals_foundation
    from verify_submission_package import verify_package

    repo = verify_package(REPO_ROOT)
    platform = verify_live_evidence(assets_dir, "platform")
    final = verify_live_evidence(assets_dir, "final")
    external_assets_quality = verify_final_external_assets(assets_dir)
    finals_foundation = verify_finals_foundation(assets_dir=assets_dir)

    bundle_manifest = load_json(bundle_manifest_path)
    human_manifest = load_json(human_action_manifest_path)
    bundle_present = bundle_path.is_file() and bundle_path.stat().st_size > 0

    status = {
        "repo_controlled_ready": bool(repo["repo_ready"]),
        "finals_foundation_ready": bool(finals_foundation["foundation_ready"]),
        "platform_evidence_ready": bool(platform["ready"]),
        "final_evidence_ready": bool(final["ready"]),
        "final_external_assets_quality_ready": bool(external_assets_quality["ready"]),
        "bundle_present": bundle_present,
        "human_templates_present": bool(human_manifest),
    }
    overall_ready = all(
        (
            status["repo_controlled_ready"],
            status["finals_foundation_ready"],
            status["platform_evidence_ready"],
            status["final_evidence_ready"],
            status["final_external_assets_quality_ready"],
            status["bundle_present"],
        )
    )

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "overall_ready_for_official_submission": overall_ready,
        "status": status,
        "repo": {
            "ready": repo["repo_ready"],
            "phase_count": len(repo["phases"]),
            "repo_failure_count": len(repo["repo_failures"]),
            "external_pending_count": len(repo["external_pending_items"]),
            "phases": repo["phases"],
            "repo_failures": repo["repo_failures"],
            "external_pending_items": repo["external_pending_items"],
        },
        "platform_evidence": {
            "ready": platform["ready"],
            "present_count": platform["present_count"],
            "expected_count": platform["expected_count"],
            "missing_count": platform["missing_count"],
            "warnings": platform["warnings"],
        },
        "finals_foundation": {
            "ready": finals_foundation["foundation_ready"],
            "finals_ready": finals_foundation["finals_ready"],
            "case_count": finals_foundation["performance"]["finals_case_count"],
            "decision_accuracy_pct_min": finals_foundation["performance"]["decision_accuracy_pct_min"],
            "latency_ms_max": finals_foundation["performance"]["latency_ms_max"],
            "latency_replay": finals_foundation["latency_replay"],
            "priority_gaps": finals_foundation["priority_gaps"],
        },
        "final_evidence": {
            "ready": final["ready"],
            "present_count": final["present_count"],
            "expected_count": final["expected_count"],
            "missing_count": final["missing_count"],
            "missing": final["missing"],
            "warnings": final["warnings"],
        },
        "final_external_assets_quality": {
            "ready": external_assets_quality["ready"],
            "ready_count": external_assets_quality["ready_count"],
            "required_count": external_assets_quality["required_count"],
            "failure_count": external_assets_quality["failure_count"],
            "warning_count": external_assets_quality["warning_count"],
            "failures": external_assets_quality["failures"],
            "warnings": external_assets_quality["warnings"],
        },
        "bundle": {
            "present": bundle_present,
            "path": str(bundle_path),
            "sha256": file_sha256(bundle_path) if bundle_present else None,
            "manifest_path": str(bundle_manifest_path),
            "manifest_file_count": bundle_manifest.get("file_count") if bundle_manifest else None,
            "manifest_bundle_sha256": bundle_manifest.get("bundle_sha256") if bundle_manifest else None,
        },
        "human_action_pack": {
            "manifest_present": bool(human_manifest),
            "manifest_path": str(human_action_manifest_path),
            "written_count": human_manifest.get("written_count") if human_manifest else None,
            "skipped_count": human_manifest.get("skipped_count") if human_manifest else None,
            "template_count": (
                int(human_manifest.get("written_count", 0)) + int(human_manifest.get("skipped_count", 0))
                if human_manifest
                else None
            ),
            "final_targets_not_created": human_manifest.get("final_targets_not_created", []) if human_manifest else [],
        },
        "edge_runtime_evidence": {
            "manifest_present": edge_runtime_manifest_path.is_file(),
            "manifest_path": str(edge_runtime_manifest_path),
        },
        "recommended_next_actions": recommended_next_actions(repo, final, external_assets_quality, bundle_present, human_manifest),
    }


def recommended_next_actions(
    repo: dict[str, Any],
    final: dict[str, Any],
    external_assets_quality: dict[str, Any],
    bundle_present: bool,
    human_manifest: dict[str, Any] | None,
) -> list[str]:
    actions: list[str] = []
    if not repo["repo_ready"]:
        actions.append("Fix repository-controlled failures reported by verify_submission_package.py.")
    if not bundle_present or not human_manifest:
        actions.append("Run python scripts/run_final_readiness_pipeline.py --json.")
    if final["missing"]:
        actions.append("Fill/capture the final live-evidence files listed under Final Missing Items.")
    if final["warnings"]:
        actions.append("Replace fallback-marked WFC evidence before claiming live WFC closure.")
    if not external_assets_quality["ready"]:
        actions.append("Run python scripts/verify_final_external_assets.py --write-report and clear all final asset quality failures.")
    if not actions:
        actions.append("Final verifier is green; submit before the internal 2026-07-08 target.")
    return actions


def render_readiness_report(result: dict[str, Any]) -> str:
    lines = [
        "# Final Readiness Report",
        "",
        f"Updated: {result['generated_at']}",
        "",
        "## Executive Status",
        "",
        f"- Official submission ready: {result['overall_ready_for_official_submission']}",
        f"- Repository-controlled package ready: {result['status']['repo_controlled_ready']}",
        f"- Finals foundation ready: {result['status']['finals_foundation_ready']}",
        f"- Platform evidence ready: {result['status']['platform_evidence_ready']}",
        f"- Final evidence ready: {result['status']['final_evidence_ready']}",
        f"- Final external assets quality ready: {result['status']['final_external_assets_quality_ready']}",
        f"- Repo-controlled bundle present: {result['status']['bundle_present']}",
        f"- Human-action templates present: {result['status']['human_templates_present']}",
        "",
        "## Current Counts",
        "",
        "| Area | Ready | Present / Expected | Missing | Warnings |",
        "| --- | --- | ---: | ---: | ---: |",
        (
            f"| Platform evidence | {result['platform_evidence']['ready']} | "
            f"{result['platform_evidence']['present_count']} / {result['platform_evidence']['expected_count']} | "
            f"{result['platform_evidence']['missing_count']} | {len(result['platform_evidence']['warnings'])} |"
        ),
        (
            f"| Finals foundation | {result['finals_foundation']['ready']} | "
            f"{result['finals_foundation']['case_count']} cases | "
            f"0 | {len(result['finals_foundation']['priority_gaps'])} |"
        ),
        (
            f"| Final evidence | {result['final_evidence']['ready']} | "
            f"{result['final_evidence']['present_count']} / {result['final_evidence']['expected_count']} | "
            f"{result['final_evidence']['missing_count']} | {len(result['final_evidence']['warnings'])} |"
        ),
        (
            f"| Final external asset quality | {result['final_external_assets_quality']['ready']} | "
            f"{result['final_external_assets_quality']['ready_count']} / {result['final_external_assets_quality']['required_count']} | "
            f"{result['final_external_assets_quality']['failure_count']} | {result['final_external_assets_quality']['warning_count']} |"
        ),
        "",
        "## Repository Phase Status",
        "",
        "| Phase | Status | Artifacts |",
        "| --- | --- | ---: |",
    ]
    for phase in result["repo"]["phases"]:
        lines.append(f"| {phase['name']} | {phase['status']} | {phase['present_count']} / {phase['artifact_count']} |")

    lines.extend(["", "## Final Missing Items", ""])
    if result["final_evidence"]["missing"]:
        for item in result["final_evidence"]["missing"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- None.")

    lines.extend(["", "## Final Asset Quality Failures", ""])
    quality_failures = result["final_external_assets_quality"]["failures"]
    if quality_failures:
        for failure in quality_failures:
            lines.append(f"- `{failure['path']}` [{failure['code']}]: {failure['message']}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Fallback Warnings", ""])
    warnings = result["final_evidence"]["warnings"]
    if warnings:
        for warning in warnings:
            lines.append(f"- `{warning['path']}`: {warning['warning']}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Finals Foundation", ""])
    lines.extend(
        [
            f"- Foundation ready: {result['finals_foundation']['ready']}",
            f"- Finals ready: {result['finals_foundation']['finals_ready']}",
            f"- Finals validation cases: {result['finals_foundation']['case_count']}",
            f"- Decision accuracy min: {result['finals_foundation']['decision_accuracy_pct_min']}%",
            f"- Rule decision latency max: {result['finals_foundation']['latency_ms_max']} ms",
            f"- Workflow Canvas evidence tier: {result['finals_foundation']['latency_replay']['evidence_tier']}",
            f"- Workflow Canvas replay mode: {result['finals_foundation']['latency_replay']['mode']}",
            f"- Workflow Canvas replay samples: {result['finals_foundation']['latency_replay']['sample_count']}",
            f"- Workflow Canvas replay p95/max: {result['finals_foundation']['latency_replay']['wall_latency_ms_p95']} / {result['finals_foundation']['latency_replay']['wall_latency_ms_max']} ms",
            f"- Workflow Canvas resource samples: {result['finals_foundation']['latency_replay']['resource_sample_count']}",
            f"- Workflow Canvas gateway RSS max: {result['finals_foundation']['latency_replay']['process_rss_mb_max']} MB",
            f"- Workflow Canvas evidence path: `{result['finals_foundation']['latency_replay']['path']}`",
            "",
            "Priority gaps:",
        ]
    )
    lines.extend(f"- {gap}" for gap in result["finals_foundation"]["priority_gaps"])

    lines.extend(
        [
            "",
            "## Generated Local Assets",
            "",
            f"- Submission bundle: `{result['bundle']['path']}`",
            f"- Bundle SHA256: `{result['bundle']['sha256']}`",
            f"- Bundle manifest file count: `{result['bundle']['manifest_file_count']}`",
            f"- Human action manifest: `{result['human_action_pack']['manifest_path']}`",
            f"- Human action template count: `{result['human_action_pack']['template_count']}`",
            f"- Human action templates written/skipped: `{result['human_action_pack']['written_count']} / {result['human_action_pack']['skipped_count']}`",
            f"- Edge runtime evidence manifest: `{result['edge_runtime_evidence']['manifest_path']}`",
            f"- Edge runtime evidence manifest present: {result['edge_runtime_evidence']['manifest_present']}",
            "",
            "## Recommended Next Actions",
            "",
        ]
    )
    lines.extend(f"- {action}" for action in result["recommended_next_actions"])

    lines.extend(
        [
            "",
            "## Verification Commands",
            "",
            "```powershell",
            "python scripts/run_final_readiness_pipeline.py --json",
            "python scripts/verify_finals_foundation.py --json",
            "python scripts/benchmark_workflow_canvas_latency.py",
            "python scripts/benchmark_local_gateway_latency.py",
            "$env:JETSON_SSH_PASSWORD = \"<set locally, do not commit>\"",
            "python scripts/collect_jetson_edge_evidence.py --host wearedge-pro.local --user ryn --iterations 20",
            "Remove-Item Env:\\JETSON_SSH_PASSWORD",
            "python scripts/verify_submission_package.py --write-manifest",
            "python scripts/verify_live_evidence.py --stage final --allow-missing --write-manifest",
            "python scripts/verify_final_external_assets.py --allow-incomplete --write-report",
            "python scripts/build_final_submission_bundle.py --json",
            "python scripts/prepare_final_human_action_pack.py --json",
            "python scripts/generate_final_readiness_report.py --write",
            "```",
            "",
            "## Boundary",
            "",
            "This report is a status controller. It does not make external/human-owned files complete. Final official submission requires the missing legal/contact and registration screenshots to be filled or captured under ignored `submission-assets/live-evidence/`.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the final Wearedge submission readiness report.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--write",
        nargs="?",
        const=str(DEFAULT_REPORT),
        default=None,
        help="Write Markdown report. Defaults to docs/submission/final-readiness-report.md.",
    )
    args = parser.parse_args(argv)

    result = build_final_readiness()
    if args.write:
        path = Path(args.write)
        if not path.is_absolute():
            path = REPO_ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_readiness_report(result), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_readiness_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
