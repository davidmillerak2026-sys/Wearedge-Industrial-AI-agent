from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run_competition_eval import load_dataset
from run_finals_validation import DEFAULT_DATASET, MIN_FINALS_CASES, run_finals_validation
from verify_live_evidence import DEFAULT_ASSETS_DIR, verify_live_evidence


FINAL_DIRECTIONS = {
    "quality",
    "energy",
    "maintenance",
    "flexible_production",
    "workflow_canvas",
}
MIN_REQUIRED_DIRECTIONS = 3
TARGET_DECISION_ACCURACY_PCT = 90.0
TARGET_LATENCY_MS = 500

REQUIRED_FOUNDATION_FILES = {
    "decision_context": [
        "evals/finals_validation_dataset.jsonl",
        "evals/competition_offline_dataset.jsonl",
        "workflows/wearedge_wfc_poc_payload.json",
        "docs/workflow-canvas-api-schema.md",
    ],
    "platform_execution": [
        "openapi/wearedge-xcelerator-apiworld.openapi.json",
        "docs/xcelerator-apiworld-onboarding.md",
        "wfc-blocks/wearedge-agent-service/info.json",
        "wfc-blocks/wearedge-agent-service/function-blocks/CallWearedgeDecisionApi.py",
        "workflows/wfc_call_wearedge_decision_fb_main.py",
        "scripts/smoke_workflow_canvas_decision.py",
    ],
    "performance_eval": [
        "scripts/run_competition_eval.py",
        "scripts/run_finals_validation.py",
        "scripts/benchmark_workflow_canvas_latency.py",
        "docs/finals-validation-report.md",
        "docs/finals-latency-benchmark-report.md",
        "docs/competition-offline-eval-report.md",
        "docs/submission/evidence/finals-latency-benchmark.json",
        "tests/test_competition_eval.py",
        "tests/test_run_finals_validation.py",
        "tests/test_benchmark_workflow_canvas_latency.py",
    ],
    "hmi_foundation": [
        "jetson/app.py",
        "jetson/output_contract.py",
        "docs/submission/finals-hmi-console.html",
        "docs/submission/dashboard-mock.html",
        "docs/submission/evidence/workflow-canvas-decision.json",
        "docs/submission/demo-script.md",
    ],
    "edge_runtime": [
        "docs/edge-agent-runtime-for-xcelerator.md",
        "scripts/smoke_edge_runtime_profile.py",
        "docs/edge-runtime-benchmark.md",
    ],
}


def verify_finals_foundation(
    *,
    dataset_path: Path = DEFAULT_DATASET,
    assets_dir: Path = DEFAULT_ASSETS_DIR,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    cases = load_dataset(dataset_path)
    _, summary = run_finals_validation(dataset_path)
    coverage = _direction_coverage(cases)
    files = _verify_foundation_files(repo_root)
    platform = verify_live_evidence(assets_dir, "platform")
    latency_replay = _load_latency_replay(repo_root)

    performance = {
        "decision_accuracy_pct_min": summary["decision_accuracy_pct_min"],
        "decision_accuracy_target_pct": TARGET_DECISION_ACCURACY_PCT,
        "decision_accuracy_target_met": summary["decision_accuracy_pct_min"] >= TARGET_DECISION_ACCURACY_PCT,
        "latency_ms_max": summary["latency_ms_max"],
        "latency_target_ms": TARGET_LATENCY_MS,
        "latency_target_met": summary["latency_ms_max"] <= TARGET_LATENCY_MS,
        "offline_cases_passed": summary["all_cases_passed"],
        "offline_targets_passed": summary["all_target_checks_passed"],
        "finals_validation_ready": summary["finals_validation_ready"],
        "finals_case_count": summary["case_count"],
        "min_finals_cases": MIN_FINALS_CASES,
    }
    hmi = {
        "natural_language_api_foundation": (repo_root / "jetson" / "app.py").is_file(),
        "natural_language_console_foundation": (repo_root / "docs" / "submission" / "finals-hmi-console.html").is_file(),
        "decision_visualization_foundation": (repo_root / "docs" / "submission" / "dashboard-mock.html").is_file(),
        "live_wfc_dashboard_ready": not any(
            warning["path"].startswith("gongyi-mofang/04")
            for warning in platform["warnings"]
        ),
        "live_wfc_human_approval_ready": not any(
            warning["path"].startswith("gongyi-mofang/06")
            for warning in platform["warnings"]
        ),
    }

    foundation_ready = all(
        (
            coverage["selected_direction_count"] >= MIN_REQUIRED_DIRECTIONS,
            coverage["all_cases_meet_min_required_directions"],
            files["all_required_files_present"],
            performance["decision_accuracy_target_met"],
            performance["latency_target_met"],
            performance["offline_cases_passed"],
            performance["offline_targets_passed"],
            performance["finals_validation_ready"],
            latency_replay["ready"],
            latency_replay["target_met"],
            hmi["natural_language_api_foundation"],
            hmi["natural_language_console_foundation"],
            hmi["decision_visualization_foundation"],
        )
    )

    return {
        "foundation_ready": foundation_ready,
        "finals_ready": False,
        "finals_ready_boundary": (
            "Foundation-ready does not mean finals-ready. Finals still require live Xcelerator/WFC "
            "end-to-end execution evidence, a production-grade natural-language HMI, and final signed/submitted assets."
        ),
        "direction_coverage": coverage,
        "performance": performance,
        "platform_evidence": {
            "platform_ready": platform["ready"],
            "present_count": platform["present_count"],
            "expected_count": platform["expected_count"],
            "fallback_warning_count": len(platform["warnings"]),
            "fallback_warning_paths": [warning["path"] for warning in platform["warnings"]],
        },
        "hmi": hmi,
        "latency_replay": latency_replay,
        "required_files": files,
        "priority_gaps": _priority_gaps(coverage, performance, platform, hmi, files, latency_replay),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Finals Foundation Verification",
        "",
        f"- Foundation ready: {result['foundation_ready']}",
        f"- Finals ready: {result['finals_ready']}",
        f"- Boundary: {result['finals_ready_boundary']}",
        "",
        "## Direction Coverage",
        "",
        f"- Selected direction count: {result['direction_coverage']['selected_direction_count']}",
        f"- Selected directions: {', '.join(result['direction_coverage']['selected_directions'])}",
        f"- All cases meet >= 3 directions: {result['direction_coverage']['all_cases_meet_min_required_directions']}",
        f"- Finals validation cases: {result['performance']['finals_case_count']} / {result['performance']['min_finals_cases']}",
        "",
        "## Performance Foundation",
        "",
        "| Metric | Current | Target | Status |",
        "| --- | ---: | ---: | --- |",
        (
            f"| Decision accuracy | {result['performance']['decision_accuracy_pct_min']:.1f}% min | "
            f">= {TARGET_DECISION_ACCURACY_PCT:.1f}% | "
            f"{'PASS' if result['performance']['decision_accuracy_target_met'] else 'REVIEW'} |"
        ),
        (
            f"| Latency | {result['performance']['latency_ms_max']} ms max | "
            f"<= {TARGET_LATENCY_MS} ms | "
            f"{'PASS' if result['performance']['latency_target_met'] else 'REVIEW'} |"
        ),
        "",
        "## Platform And HMI Foundation",
        "",
        f"- Platform evidence ready: {result['platform_evidence']['platform_ready']}",
        f"- Platform fallback warnings: {result['platform_evidence']['fallback_warning_count']}",
        f"- Natural-language API foundation: {result['hmi']['natural_language_api_foundation']}",
        f"- Natural-language console foundation: {result['hmi']['natural_language_console_foundation']}",
        f"- Decision visualization foundation: {result['hmi']['decision_visualization_foundation']}",
        f"- Live WFC dashboard ready: {result['hmi']['live_wfc_dashboard_ready']}",
        f"- Live WFC human approval ready: {result['hmi']['live_wfc_human_approval_ready']}",
        "",
        "## Latency Replay Evidence",
        "",
        f"- Replay ready: {result['latency_replay']['ready']}",
        f"- Replay mode: {result['latency_replay']['mode']}",
        f"- Replay samples: {result['latency_replay']['sample_count']}",
        f"- Wall latency max: {result['latency_replay']['wall_latency_ms_max']} ms",
        f"- Wall latency p95: {result['latency_replay']['wall_latency_ms_p95']} ms",
        f"- Target met: {result['latency_replay']['target_met']}",
        f"- Boundary: {result['latency_replay']['boundary']}",
        "",
        "## Priority Gaps",
        "",
    ]
    if result["priority_gaps"]:
        lines.extend(f"- {gap}" for gap in result["priority_gaps"])
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def _direction_coverage(cases: list[dict[str, Any]]) -> dict[str, Any]:
    selected: set[str] = set()
    case_rows: list[dict[str, Any]] = []
    for case in cases:
        case_directions = [str(item) for item in case.get("selected_directions", [])]
        selected.update(case_directions)
        case_rows.append(
            {
                "case_id": case.get("case_id", "unknown"),
                "direction_count": len(set(case_directions)),
                "meets_min_required_directions": len(set(case_directions)) >= MIN_REQUIRED_DIRECTIONS,
            }
        )
    return {
        "selected_directions": sorted(selected),
        "selected_direction_count": len(selected),
        "missing_final_directions": sorted(FINAL_DIRECTIONS - selected),
        "case_min_direction_count": min(row["direction_count"] for row in case_rows),
        "all_cases_meet_min_required_directions": all(row["meets_min_required_directions"] for row in case_rows),
        "cases": case_rows,
    }


def _verify_foundation_files(repo_root: Path) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for group, paths in REQUIRED_FOUNDATION_FILES.items():
        records = []
        for path in paths:
            present = (repo_root / path).is_file()
            records.append({"path": path, "present": present})
            if not present:
                missing.append(path)
        groups[group] = {
            "present_count": sum(1 for record in records if record["present"]),
            "expected_count": len(records),
            "items": records,
        }
    return {
        "all_required_files_present": not missing,
        "missing": missing,
        "groups": groups,
    }


def _load_latency_replay(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "docs" / "submission" / "evidence" / "finals-latency-benchmark.json"
    if not path.is_file():
        return {
            "ready": False,
            "path": str(path),
            "mode": "missing",
            "sample_count": 0,
            "target_met": False,
            "wall_latency_ms_max": 0,
            "wall_latency_ms_p95": 0,
            "boundary": "Latency replay evidence has not been generated yet.",
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "ready": False,
            "path": str(path),
            "mode": "invalid-json",
            "sample_count": 0,
            "target_met": False,
            "wall_latency_ms_max": 0,
            "wall_latency_ms_p95": 0,
            "boundary": "Latency replay JSON could not be parsed.",
        }

    wall = data.get("wall_latency_ms", {})
    return {
        "ready": bool(data.get("ok")) and int(data.get("sample_count", 0)) > 0,
        "path": str(path),
        "mode": str(data.get("mode", "unknown")),
        "endpoint": str(data.get("endpoint", "unknown")),
        "sample_count": int(data.get("sample_count", 0)),
        "target_met": bool(data.get("target_met")),
        "wall_latency_ms_max": int(wall.get("max", 0)),
        "wall_latency_ms_p95": int(wall.get("p95", 0)),
        "boundary": str(data.get("boundary", "")),
    }


def _priority_gaps(
    coverage: dict[str, Any],
    performance: dict[str, Any],
    platform: dict[str, Any],
    hmi: dict[str, Any],
    files: dict[str, Any],
    latency_replay: dict[str, Any],
) -> list[str]:
    gaps: list[str] = []
    if coverage["selected_direction_count"] < MIN_REQUIRED_DIRECTIONS:
        gaps.append("Select at least three finals directions in the offline dataset and WFC payload.")
    if coverage["missing_final_directions"]:
        gaps.append("Optional winning upgrade: keep all five finals directions covered, not only the minimum three.")
    if not performance["decision_accuracy_target_met"] or not performance["latency_target_met"]:
        gaps.append("Strengthen the benchmark harness until decision accuracy >=90% and latency <=500ms.")
    if not latency_replay["ready"] or not latency_replay["target_met"]:
        gaps.append("Run the finals latency replay benchmark until the Workflow Canvas path is <=500ms.")
    elif latency_replay["mode"] != "http":
        gaps.append("Replace in-process latency replay with deployed FastAPI/edge-hardware benchmark before final defense.")
    if not platform["ready"]:
        gaps.append("Complete platform-stage Xcelerator/WFC evidence before treating the platform path as stable.")
    if platform["warnings"]:
        gaps.append("Replace fallback WFC dashboard/run-log/HumanApprovalGate assets with live WFC execution screenshots.")
    if not hmi["natural_language_api_foundation"] or not hmi["decision_visualization_foundation"]:
        gaps.append("Build the natural-language HMI and decision-process visualization as first-class product surfaces.")
    if files["missing"]:
        gaps.append("Restore missing foundation files before relying on the finals roadmap.")
    if performance["finals_case_count"] < MIN_FINALS_CASES:
        gaps.append("Expand the offline dataset from 5 seed cases to a larger labeled finals validation set before the defense.")
    return gaps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Wearedge finals foundation readiness.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict-finals", action="store_true", help="Exit non-zero until finals_ready is true.")
    args = parser.parse_args(argv)

    result = verify_finals_foundation(dataset_path=args.dataset, assets_dir=args.assets_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_markdown(result))
    if args.strict_finals:
        return 0 if result["finals_ready"] else 1
    return 0 if result["foundation_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
