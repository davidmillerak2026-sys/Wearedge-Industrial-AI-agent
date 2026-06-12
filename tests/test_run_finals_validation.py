from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_finals_validation.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_finals_validation", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_finals_validation_dataset_covers_all_primary_directions() -> None:
    module = _load_module()

    results, summary = module.run_finals_validation()

    assert len(results) == 15
    assert summary["finals_validation_ready"] is True
    assert summary["coverage"]["all_cases_meet_min_three_directions"] is True
    assert summary["coverage"]["all_five_directions_covered"] is True
    assert summary["coverage"]["all_five_primary_directions_covered"] is True
    assert summary["coverage"]["primary_direction_counts"] == {
        "energy": 3,
        "flexible_production": 3,
        "maintenance": 3,
        "quality": 3,
        "workflow_canvas": 3,
    }
    assert summary["decision_accuracy_pct_min"] >= 90.0
    assert summary["latency_ms_max"] <= 500


def test_finals_validation_report_states_offline_boundary() -> None:
    module = _load_module()
    results, summary = module.run_finals_validation()

    report = module.render_finals_report(results, summary)

    assert "Finals validation ready: True" in report
    assert "offline/simulated validation artifact" in report
    assert "does not replace live Xcelerator or Gongyi Mofang" in report
    assert "| workflow_canvas | 3 |" in report
