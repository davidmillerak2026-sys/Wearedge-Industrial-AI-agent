from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "benchmark_workflow_canvas_latency.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("benchmark_workflow_canvas_latency", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_latency_benchmark_replays_all_finals_cases_under_target() -> None:
    module = _load_module()

    result = module.run_latency_benchmark(iterations=2)

    assert result["ok"] is True
    assert result["mode"] == "in_process"
    assert result["case_count"] == 15
    assert result["sample_count"] == 30
    assert result["target_latency_ms"] == 500
    assert result["target_met"] is True
    assert result["wall_latency_ms"]["max"] <= 500


def test_latency_benchmark_report_states_boundary_and_http_upgrade() -> None:
    module = _load_module()
    result = module.run_latency_benchmark(iterations=1)

    report = module.render_report(result)

    assert "Finals Latency Benchmark Report" in report
    assert "Workflow Canvas" in report
    assert "--base-url" in report
    assert "deterministic local replay" in report


def test_latency_benchmark_writes_report_and_json(tmp_path: Path) -> None:
    module = _load_module()
    result = module.run_latency_benchmark(iterations=1)
    report_path = tmp_path / "report.md"
    json_path = tmp_path / "benchmark.json"

    module.write_outputs(result, report_path=report_path, json_path=json_path)

    assert "Target met: True" in report_path.read_text(encoding="utf-8")
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved["sample_count"] == 15
    assert saved["mode"] == "in_process"
