from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jetson.competition import COMPETITION_TARGETS, build_competition_decision


DEFAULT_DATASET = REPO_ROOT / "evals" / "competition_offline_dataset.jsonl"
DEFAULT_REPORT = REPO_ROOT / "docs" / "competition-offline-eval-report.md"


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    description: str
    passed: bool
    failures: tuple[str, ...]
    decision: dict[str, Any]
    expected: dict[str, Any]


def load_dataset(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no} is not valid JSON") from exc
        if not isinstance(case, dict):
            raise ValueError(f"{path}:{line_no} must be a JSON object")
        cases.append(case)
    if not cases:
        raise ValueError(f"{path} contains no evaluation cases")
    return cases


def evaluate_cases(cases: list[dict[str, Any]]) -> tuple[list[CaseResult], dict[str, Any]]:
    results: list[CaseResult] = []
    decisions: list[dict[str, Any]] = []

    for case in cases:
        decision = build_competition_decision(case)
        decisions.append(decision)
        expected = _object(case.get("expected"))
        failures = _check_expected(case, decision, expected)
        results.append(
            CaseResult(
                case_id=str(case.get("case_id", "unknown")),
                description=str(case.get("description", "")),
                passed=not failures,
                failures=tuple(failures),
                decision=decision,
                expected=expected,
            )
        )

    summary = _build_summary(cases, results, decisions)
    return results, summary


def render_report(results: list[CaseResult], summary: dict[str, Any]) -> str:
    metric_rows = [
        ("Decision case pass rate", f"{summary['case_pass_rate_pct']:.1f}%", ">= 90%", summary["case_pass_rate_pct"] >= 90.0),
        (
            "Decision accuracy estimate",
            f"{summary['decision_accuracy_pct_min']:.1f}% min",
            f">= {COMPETITION_TARGETS['decision_accuracy_pct_min']:.1f}%",
            summary["target_checks"]["decision_accuracy"],
        ),
        (
            "Interactive latency",
            f"{summary['latency_ms_max']} ms max",
            f"<= {COMPETITION_TARGETS['latency_ms_max']} ms",
            summary["target_checks"]["latency"],
        ),
        (
            "Maintenance F1",
            f"{summary['metrics']['maintenance_f1_pct']['min']:.1f}% min",
            f">= {COMPETITION_TARGETS['maintenance_f1_pct_min']:.1f}%",
            summary["target_checks"]["maintenance_f1"],
        ),
        (
            "Maintenance warning lead",
            f"{summary['metrics']['maintenance_warning_lead_time_hours']['min']:.1f} h min",
            f">= {COMPETITION_TARGETS['maintenance_warning_lead_hours_min']:.1f} h",
            summary["target_checks"]["maintenance_warning_lead_time"],
        ),
        (
            "Root cause Top 3",
            f"{summary['metrics']['root_cause_top3_pct']['min']:.1f}% min",
            f">= {COMPETITION_TARGETS['root_cause_top3_pct_min']:.1f}%",
            summary["target_checks"]["root_cause_top3"],
        ),
        (
            "Energy forecast accuracy",
            f"{summary['metrics']['energy_forecast_accuracy_pct']['min']:.1f}% min",
            f">= {COMPETITION_TARGETS['energy_forecast_accuracy_pct_min']:.1f}%",
            summary["target_checks"]["energy_forecast_accuracy"],
        ),
        (
            "Energy saving estimate",
            f"{summary['metrics']['energy_saving_pct']['min']:.1f}% min",
            f">= {COMPETITION_TARGETS['energy_saving_pct_min']:.1f}%",
            summary["target_checks"]["energy_saving"],
        ),
        (
            "Quality relative improvement",
            f"{summary['metrics']['quality_relative_improvement_pct']['min']:.1f}% min",
            f">= {COMPETITION_TARGETS['quality_relative_improvement_pct_min']:.1f}%",
            summary["target_checks"]["quality_relative_improvement"],
        ),
        (
            "Schedule efficiency gain",
            f"{summary['metrics']['schedule_efficiency_gain_pct']['min']:.1f}% min",
            f">= {COMPETITION_TARGETS['schedule_efficiency_gain_pct_min']:.1f}%",
            summary["target_checks"]["schedule_efficiency_gain"],
        ),
    ]

    lines = [
        "# Wearedge 赛事离线评估报告",
        "",
        "生成日期：2026-06-04",
        "",
        "## 结论",
        "",
        (
            f"本报告基于 `evals/competition_offline_dataset.jsonl` 中的 {summary['case_count']} 条模拟/离线样例，"
            "调用 `jetson.competition.build_competition_decision()` 评估多智能体协同决策输出。"
        ),
        "",
        "重要边界：这些结果用于初赛前的工程自测和指标对齐，**不是客户真实产线数据**；后续需要在工易魔方或西门子 Xcelerator PoC 环境中复现。",
        "",
        "## 指标摘要",
        "",
        "| 指标 | 离线结果 | 赛事目标 | 状态 |",
        "| --- | --- | --- | --- |",
    ]
    for name, value, target, passed in metric_rows:
        lines.append(f"| {name} | {value} | {target} | {'PASS' if passed else 'REVIEW'} |")

    lines.extend(
        [
            "",
            "## 样例结果",
            "",
            "| Case | Primary Direction | Direction Count | Accuracy Estimate | Latency | Human Confirmation | Result |",
            "| --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for result in results:
        decision = result.decision
        collaborative = _object(decision.get("collaborative_decision"))
        metrics = _object(decision.get("competition_metrics"))
        lines.append(
            "| "
            f"{result.case_id} | "
            f"{collaborative.get('primary_direction')} | "
            f"{decision.get('direction_count')} | "
            f"{metrics.get('decision_accuracy_pct_estimate')}% | "
            f"{decision.get('latency_ms')} ms | "
            f"{collaborative.get('requires_human_confirmation')} | "
            f"{'PASS' if result.passed else 'REVIEW: ' + '; '.join(result.failures)} |"
        )

    lines.extend(
        [
            "",
            "## 数据来源与下一步",
            "",
            "- 当前样例来自本仓库内的模拟 MES、质量、能源、维护和 Workflow Canvas 上下文表。",
            "- 下一步需要把同样 schema 接入工易魔方全局数据表、Dashboard 和真实或仿真的 SPIDR/IPC 运行日志。",
            "- 报名材料中引用本报告时，应写作“离线模拟验证”，不要写成“客户现场生产验证”。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Wearedge competition offline evaluation.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary.")
    args = parser.parse_args(argv)

    cases = load_dataset(args.dataset)
    results, summary = evaluate_cases(cases)
    report = render_report(results, summary)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"cases={summary['case_count']} passed={summary['case_passed']} report={args.report}")
        print(f"case_pass_rate_pct={summary['case_pass_rate_pct']:.1f}")
        print(f"decision_accuracy_pct_min={summary['decision_accuracy_pct_min']:.1f}")
        print(f"latency_ms_max={summary['latency_ms_max']}")
        print(f"all_target_checks_passed={summary['all_target_checks_passed']}")

    if not summary["all_cases_passed"] or not summary["all_target_checks_passed"]:
        return 1
    return 0


def _check_expected(case: dict[str, Any], decision: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    collaborative = _object(decision.get("collaborative_decision"))
    metrics = _object(decision.get("competition_metrics"))
    compliance = _object(decision.get("compliance"))
    runtime_targets = _object(_object(compliance.get("runtime_targets")).copy())
    by_direction = {
        str(item.get("direction")): item
        for item in _list(decision.get("evaluations"))
        if isinstance(item, dict)
    }

    expected_primary = expected.get("primary_direction")
    if expected_primary and collaborative.get("primary_direction") != expected_primary:
        failures.append(f"primary_direction expected {expected_primary} got {collaborative.get('primary_direction')}")

    min_direction_count = expected.get("min_direction_count")
    if isinstance(min_direction_count, int) and int(decision.get("direction_count", 0)) < min_direction_count:
        failures.append(f"direction_count below {min_direction_count}")

    expected_statuses = _object(expected.get("statuses"))
    for direction, expected_status in expected_statuses.items():
        actual = _object(by_direction.get(direction)).get("status")
        if actual != expected_status:
            failures.append(f"{direction} status expected {expected_status} got {actual}")

    if "requires_human_confirmation" in expected:
        actual = bool(collaborative.get("requires_human_confirmation"))
        if actual != bool(expected["requires_human_confirmation"]):
            failures.append(f"requires_human_confirmation expected {expected['requires_human_confirmation']} got {actual}")

    if expected.get("latency_target_met") and metrics.get("latency_target_met") is not True:
        failures.append("latency target not met")
    if expected.get("decision_accuracy_target_met") and runtime_targets.get("decision_accuracy_target_met") is not True:
        failures.append("decision accuracy target not met")

    return failures


def _build_summary(
    cases: list[dict[str, Any]],
    results: list[CaseResult],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    case_count = len(results)
    case_passed = sum(1 for result in results if result.passed)
    accuracy_estimates = [
        float(_object(decision.get("competition_metrics")).get("decision_accuracy_pct_estimate", 0.0))
        for decision in decisions
    ]
    latencies = [int(decision.get("latency_ms", 0)) for decision in decisions]
    metrics = _aggregate_context_metrics(cases)
    target_checks = {
        "decision_accuracy": min(accuracy_estimates) >= COMPETITION_TARGETS["decision_accuracy_pct_min"],
        "latency": max(latencies) <= COMPETITION_TARGETS["latency_ms_max"],
        "maintenance_f1": metrics["maintenance_f1_pct"]["min"] >= COMPETITION_TARGETS["maintenance_f1_pct_min"],
        "maintenance_warning_lead_time": metrics["maintenance_warning_lead_time_hours"]["min"]
        >= COMPETITION_TARGETS["maintenance_warning_lead_hours_min"],
        "root_cause_top3": metrics["root_cause_top3_pct"]["min"] >= COMPETITION_TARGETS["root_cause_top3_pct_min"],
        "energy_forecast_accuracy": metrics["energy_forecast_accuracy_pct"]["min"]
        >= COMPETITION_TARGETS["energy_forecast_accuracy_pct_min"],
        "energy_saving": metrics["energy_saving_pct"]["min"] >= COMPETITION_TARGETS["energy_saving_pct_min"],
        "quality_relative_improvement": metrics["quality_relative_improvement_pct"]["min"]
        >= COMPETITION_TARGETS["quality_relative_improvement_pct_min"],
        "schedule_efficiency_gain": metrics["schedule_efficiency_gain_pct"]["min"]
        >= COMPETITION_TARGETS["schedule_efficiency_gain_pct_min"],
    }
    return {
        "case_count": case_count,
        "case_passed": case_passed,
        "case_pass_rate_pct": round(case_passed / case_count * 100.0, 2),
        "all_cases_passed": case_passed == case_count,
        "decision_accuracy_pct_min": round(min(accuracy_estimates), 2),
        "decision_accuracy_pct_avg": round(sum(accuracy_estimates) / len(accuracy_estimates), 2),
        "latency_ms_max": max(latencies),
        "latency_ms_avg": round(sum(latencies) / len(latencies), 2),
        "metrics": metrics,
        "target_checks": target_checks,
        "all_target_checks_passed": all(target_checks.values()),
    }


def _aggregate_context_metrics(cases: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    values = {
        "maintenance_f1_pct": [],
        "maintenance_warning_lead_time_hours": [],
        "root_cause_top3_pct": [],
        "energy_forecast_accuracy_pct": [],
        "energy_saving_pct": [],
        "quality_relative_improvement_pct": [],
        "schedule_efficiency_gain_pct": [],
    }
    for case in cases:
        context = _object(case.get("context"))
        maintenance = _object(context.get("maintenance"))
        energy = _object(context.get("energy"))
        quality = _object(context.get("quality"))
        production = _object(context.get("production"))
        _append_number(values["maintenance_f1_pct"], maintenance.get("f1_pct"))
        _append_number(values["maintenance_warning_lead_time_hours"], maintenance.get("warning_lead_time_hours"))
        _append_number(values["root_cause_top3_pct"], maintenance.get("root_cause_top3_pct"))
        _append_number(values["energy_forecast_accuracy_pct"], energy.get("forecast_accuracy_pct"))
        _append_number(values["energy_saving_pct"], energy.get("saving_pct"))
        _append_number(values["quality_relative_improvement_pct"], quality.get("relative_improvement_pct"))
        _append_number(values["schedule_efficiency_gain_pct"], production.get("schedule_efficiency_gain_pct"))
    return {name: _stats(items) for name, items in values.items()}


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"count": 0.0, "min": 0.0, "avg": 0.0, "max": 0.0}
    return {
        "count": float(len(values)),
        "min": round(min(values), 3),
        "avg": round(sum(values) / len(values), 3),
        "max": round(max(values), 3),
    }


def _append_number(values: list[float], value: object) -> None:
    if value is None or value == "":
        return
    try:
        values.append(float(value))
    except (TypeError, ValueError):
        return


def _object(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


if __name__ == "__main__":
    raise SystemExit(main())
