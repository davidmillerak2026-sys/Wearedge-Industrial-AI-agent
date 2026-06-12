from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from jetson.competition import COMPETITION_TARGETS
from run_competition_eval import CaseResult, evaluate_cases, load_dataset


DEFAULT_DATASET = REPO_ROOT / "evals" / "finals_validation_dataset.jsonl"
DEFAULT_REPORT = REPO_ROOT / "docs" / "finals-validation-report.md"
MIN_FINALS_CASES = 15


def run_finals_validation(dataset_path: Path = DEFAULT_DATASET) -> tuple[list[CaseResult], dict[str, Any]]:
    cases = load_dataset(dataset_path)
    results, summary = evaluate_cases(cases)
    coverage = build_finals_coverage(cases, results)
    summary = {
        **summary,
        "dataset_path": str(dataset_path),
        "min_finals_cases": MIN_FINALS_CASES,
        "finals_case_count_target_met": summary["case_count"] >= MIN_FINALS_CASES,
        "coverage": coverage,
        "finals_validation_ready": bool(
            summary["all_cases_passed"]
            and summary["all_target_checks_passed"]
            and summary["case_count"] >= MIN_FINALS_CASES
            and coverage["all_cases_meet_min_three_directions"]
            and coverage["all_five_directions_covered"]
            and coverage["all_five_primary_directions_covered"]
        ),
    }
    return results, summary


def build_finals_coverage(cases: list[dict[str, Any]], results: list[CaseResult]) -> dict[str, Any]:
    selected_directions: set[str] = set()
    min_direction_count = 999
    for case in cases:
        directions = {str(item) for item in case.get("selected_directions", [])}
        selected_directions.update(directions)
        min_direction_count = min(min_direction_count, len(directions))

    primary_counter = Counter(
        str(result.decision.get("collaborative_decision", {}).get("primary_direction"))
        for result in results
    )
    final_directions = {"quality", "energy", "maintenance", "flexible_production", "workflow_canvas"}
    return {
        "selected_directions": sorted(selected_directions),
        "primary_direction_counts": dict(sorted(primary_counter.items())),
        "case_min_direction_count": min_direction_count if cases else 0,
        "all_cases_meet_min_three_directions": bool(cases and min_direction_count >= 3),
        "all_five_directions_covered": final_directions.issubset(selected_directions),
        "all_five_primary_directions_covered": final_directions.issubset(primary_counter.keys()),
        "missing_selected_directions": sorted(final_directions - selected_directions),
        "missing_primary_directions": sorted(final_directions - set(primary_counter.keys())),
    }


def render_finals_report(results: list[CaseResult], summary: dict[str, Any]) -> str:
    coverage = summary["coverage"]
    lines = [
        "# Wearedge Finals Validation Report",
        "",
        "Generated: 2026-06-12",
        "",
        "## Boundary",
        "",
        (
            "This report is an expanded offline/simulated validation artifact for final-round preparation. "
            "It does not replace live Xcelerator or Gongyi Mofang workflow execution evidence."
        ),
        "",
        "## Executive Summary",
        "",
        f"- Finals validation ready: {summary['finals_validation_ready']}",
        f"- Case count: {summary['case_count']} / {summary['min_finals_cases']}",
        f"- Case pass rate: {summary['case_pass_rate_pct']:.1f}%",
        f"- Decision accuracy estimate: {summary['decision_accuracy_pct_min']:.1f}% min",
        f"- Latency: {summary['latency_ms_max']} ms max",
        f"- All cases have >=3 directions: {coverage['all_cases_meet_min_three_directions']}",
        f"- All five directions selected: {coverage['all_five_directions_covered']}",
        f"- All five primary directions represented: {coverage['all_five_primary_directions_covered']}",
        "",
        "## Final-Round KPI Checks",
        "",
        "| KPI | Current | Target | Status |",
        "| --- | ---: | ---: | --- |",
        (
            f"| Decision accuracy | {summary['decision_accuracy_pct_min']:.1f}% min | "
            f">= {COMPETITION_TARGETS['decision_accuracy_pct_min']:.1f}% | "
            f"{'PASS' if summary['target_checks']['decision_accuracy'] else 'REVIEW'} |"
        ),
        (
            f"| Response latency | {summary['latency_ms_max']} ms max | "
            f"<= {COMPETITION_TARGETS['latency_ms_max']} ms | "
            f"{'PASS' if summary['target_checks']['latency'] else 'REVIEW'} |"
        ),
        (
            f"| Agent directions per case | {coverage['case_min_direction_count']} min | "
            ">= 3 | "
            f"{'PASS' if coverage['all_cases_meet_min_three_directions'] else 'REVIEW'} |"
        ),
        (
            f"| Dataset size | {summary['case_count']} cases | "
            f">= {MIN_FINALS_CASES} cases | "
            f"{'PASS' if summary['finals_case_count_target_met'] else 'REVIEW'} |"
        ),
        "",
        "## Primary Direction Coverage",
        "",
        "| Primary direction | Case count |",
        "| --- | ---: |",
    ]
    for direction, count in coverage["primary_direction_counts"].items():
        lines.append(f"| {direction} | {count} |")

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Primary | Directions | Accuracy | Latency | Result |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for result in results:
        collaborative = result.decision.get("collaborative_decision", {})
        metrics = result.decision.get("competition_metrics", {})
        lines.append(
            "| "
            f"{result.case_id} | "
            f"{collaborative.get('primary_direction')} | "
            f"{result.decision.get('direction_count')} | "
            f"{metrics.get('decision_accuracy_pct_estimate')}% | "
            f"{result.decision.get('latency_ms')} ms | "
            f"{'PASS' if result.passed else 'REVIEW: ' + '; '.join(result.failures)} |"
        )

    lines.extend(
        [
            "",
            "## Next Evidence Upgrade",
            "",
            "- Replace WFC fallback Dashboard/run-log/HumanApprovalGate assets with live platform execution screenshots.",
            "- Add deployed API endpoint latency logs and edge-hardware replay logs.",
            "- Keep simulated/offline and live platform evidence explicitly separated in defense material.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Wearedge final-round offline validation.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results, summary = run_finals_validation(args.dataset)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_finals_report(results, summary), encoding="utf-8")

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"cases={summary['case_count']} passed={summary['case_passed']} report={args.report}")
        print(f"finals_validation_ready={summary['finals_validation_ready']}")
        print(f"decision_accuracy_pct_min={summary['decision_accuracy_pct_min']:.1f}")
        print(f"latency_ms_max={summary['latency_ms_max']}")
        print(f"primary_directions={','.join(summary['coverage']['primary_direction_counts'])}")

    return 0 if summary["finals_validation_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
