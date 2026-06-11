from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import run_competition_eval
import smoke_edge_runtime_profile
import smoke_solution_profile
import smoke_workflow_canvas_decision


DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "submission" / "evidence"
DEFAULT_DATASET = REPO_ROOT / "evals" / "competition_offline_dataset.jsonl"
DEFAULT_PAYLOAD = REPO_ROOT / "workflows" / "wearedge_wfc_poc_payload.json"


def build_evidence(output_dir: Path, dataset_path: Path, payload_path: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    cases = run_competition_eval.load_dataset(dataset_path)
    eval_results, summary = run_competition_eval.evaluate_cases(cases)
    report = run_competition_eval.render_report(eval_results, summary)

    payload = smoke_workflow_canvas_decision.load_payload(payload_path)
    decision = smoke_workflow_canvas_decision.call_in_process(payload)
    failures = smoke_workflow_canvas_decision.validate_decision(decision)
    edge_profile = smoke_edge_runtime_profile._fetch_profile(None)
    edge_failures = smoke_edge_runtime_profile._validate_profile(edge_profile)
    solution_profile = smoke_solution_profile.fetch_profile(None)
    solution_failures = smoke_solution_profile.validate_profile(solution_profile)

    summary_path = output_dir / "competition-eval-summary.json"
    decision_path = output_dir / "workflow-canvas-decision.json"
    edge_profile_path = output_dir / "edge-runtime-profile.json"
    solution_profile_path = output_dir / "solution-profile.json"
    report_path = output_dir / "competition-offline-eval-report.snapshot.md"
    readme_path = output_dir / "README.md"

    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    decision_path.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    edge_profile_path.write_text(json.dumps(edge_profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    solution_profile_path.write_text(json.dumps(solution_profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(report, encoding="utf-8")
    readme_path.write_text(
        _render_readme(summary, decision, failures, edge_profile, edge_failures, solution_profile, solution_failures),
        encoding="utf-8",
    )

    return {
        "output_dir": str(output_dir),
        "summary_path": str(summary_path),
        "decision_path": str(decision_path),
        "edge_profile_path": str(edge_profile_path),
        "solution_profile_path": str(solution_profile_path),
        "report_path": str(report_path),
        "readme_path": str(readme_path),
        "all_target_checks_passed": bool(summary["all_target_checks_passed"]),
        "smoke_failures": failures,
        "edge_profile_failures": edge_failures,
        "solution_profile_failures": solution_failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build submission evidence snapshots.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--payload", type=Path, default=DEFAULT_PAYLOAD)
    args = parser.parse_args(argv)

    result = build_evidence(args.output_dir, args.dataset, args.payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if (
        not result["all_target_checks_passed"]
        or result["smoke_failures"]
        or result["edge_profile_failures"]
        or result["solution_profile_failures"]
    ):
        return 1
    return 0


def _render_readme(
    summary: dict[str, Any],
    decision: dict[str, Any],
    failures: list[str],
    edge_profile: dict[str, Any],
    edge_failures: list[str],
    solution_profile: dict[str, Any],
    solution_failures: list[str],
) -> str:
    collaborative = _object(decision.get("collaborative_decision"))
    metrics = _object(decision.get("competition_metrics"))
    workflow = _object(decision.get("workflow_canvas"))
    edge_node = _object(edge_profile.get("edge_node"))
    capabilities = _object(edge_profile.get("edge_capabilities"))
    problem = _object(solution_profile.get("industrial_problem"))
    model_runtime = _object(solution_profile.get("model_runtime"))
    decision_mechanism = _object(solution_profile.get("decision_mechanism"))
    return "\n".join(
        [
            "# Submission Evidence Snapshot",
            "",
            "Generated for the Wearedge Siemens Xcelerator / Gongyi Mofang competition package.",
            "",
            "## Offline Evaluation",
            "",
            f"- Cases: {summary['case_passed']} / {summary['case_count']} passed",
            f"- Decision accuracy estimate min: {summary['decision_accuracy_pct_min']}%",
            f"- Latency max: {summary['latency_ms_max']} ms",
            f"- All target checks passed: {summary['all_target_checks_passed']}",
            "",
            "Boundary: this is simulated/offline validation, not customer production data.",
            "",
            "## Workflow Canvas Smoke Decision",
            "",
            f"- Primary direction: {collaborative.get('primary_direction')}",
            f"- Priority: {collaborative.get('priority')}",
            f"- Requires human confirmation: {collaborative.get('requires_human_confirmation')}",
            f"- Accuracy estimate: {metrics.get('decision_accuracy_pct_estimate')}%",
            f"- Function blocks: {len(workflow.get('function_blocks', []))}",
            f"- Smoke failures: {failures if failures else 'none'}",
            "",
            "## Edge Runtime Profile",
            "",
            f"- Deployment mode: {edge_node.get('deployment_mode')}",
            f"- Local multimodal inference: {capabilities.get('local_multimodal_inference')}",
            f"- Workflow Canvas ready: {capabilities.get('workflow_canvas_ready')}",
            f"- Edge profile failures: {edge_failures if edge_failures else 'none'}",
            "",
            "## Industrial Agent Solution Profile",
            "",
            f"- Problem: {problem.get('name')}",
            f"- Primary model: {model_runtime.get('primary_model')} / {model_runtime.get('model_variant')}",
            f"- Decision mechanism: {decision_mechanism.get('type')}",
            f"- Decision model dependency: {decision_mechanism.get('model_dependency')}",
            f"- Solution profile failures: {solution_failures if solution_failures else 'none'}",
            "",
            "## Files",
            "",
            "- `competition-eval-summary.json`",
            "- `workflow-canvas-decision.json`",
            "- `edge-runtime-profile.json`",
            "- `solution-profile.json`",
            "- `competition-offline-eval-report.snapshot.md`",
            "",
        ]
    )


def _object(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


if __name__ == "__main__":
    raise SystemExit(main())
