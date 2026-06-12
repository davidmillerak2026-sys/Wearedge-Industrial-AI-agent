from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "benchmark_local_gateway_latency.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("benchmark_local_gateway_latency", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_local_gateway_latency_benchmark_uses_real_http_endpoint() -> None:
    module = _load_module()

    result = module.run_local_gateway_latency_benchmark(iterations=1)

    assert result["ok"] is True
    assert result["mode"] == "http"
    assert result["evidence_tier"] == "local_fastapi_http_gateway"
    assert result["case_count"] == 15
    assert result["sample_count"] == 15
    assert result["target_met"] is True
    assert result["wall_latency_ms"]["max"] <= 500
    assert result["endpoint"].endswith("/v1/workflow-canvas/decision")
    assert result["gateway"]["healthz_ok"] is True


def test_local_gateway_latency_benchmark_writes_outputs(tmp_path: Path) -> None:
    module = _load_module()
    result = module.run_local_gateway_latency_benchmark(iterations=1)
    report_path = tmp_path / "local-gateway-report.md"
    json_path = tmp_path / "local-gateway.json"

    module.write_outputs(result, report_path=report_path, json_path=json_path)

    report = report_path.read_text(encoding="utf-8")
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert "Mode: http" in report
    assert "Target met: True" in report
    assert saved["evidence_tier"] == "local_fastapi_http_gateway"


def test_find_free_port_returns_candidate_port() -> None:
    module = _load_module()

    port = module.find_free_port()

    assert isinstance(port, int)
    assert 0 < port < 65536
