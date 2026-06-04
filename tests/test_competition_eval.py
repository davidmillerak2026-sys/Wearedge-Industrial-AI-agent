from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_competition_eval.py"


def _load_eval_module():
    spec = importlib.util.spec_from_file_location("run_competition_eval", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_competition_offline_dataset_passes_targets() -> None:
    module = _load_eval_module()

    cases = module.load_dataset(REPO_ROOT / "evals" / "competition_offline_dataset.jsonl")
    results, summary = module.evaluate_cases(cases)

    assert len(cases) >= 5
    assert summary["all_cases_passed"] is True
    assert summary["all_target_checks_passed"] is True
    assert summary["case_pass_rate_pct"] == 100.0
    assert summary["decision_accuracy_pct_min"] >= 90.0
    assert all(result.passed for result in results)


def test_competition_eval_report_marks_simulated_boundary(tmp_path) -> None:
    module = _load_eval_module()
    report_path = tmp_path / "competition-report.md"

    exit_code = module.main(
        [
            "--dataset",
            str(REPO_ROOT / "evals" / "competition_offline_dataset.jsonl"),
            "--report",
            str(report_path),
        ]
    )

    report = report_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "模拟/离线样例" in report
    assert "不是客户真实产线数据" in report
    assert "| Maintenance F1 |" in report
    assert "| Energy forecast accuracy |" in report
