from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "benchmark_edge_stdlib_gateway.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("benchmark_edge_stdlib_gateway", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_stdlib_gateway_benchmark_runs_decision_path() -> None:
    module = _load_module()

    result = module.run_edge_stdlib_gateway_benchmark(
        iterations=1,
        collect_resources=False,
        final_edge_node=True,
        edge_node_id="jetson-test-node",
    )

    assert result["ok"] is True
    assert result["target_met"] is True
    assert result["evidence_tier"] == "final_edge_stdlib_http_gateway"
    assert result["gateway"]["dependency_profile"] == "python_stdlib_no_fastapi_uvicorn"
    assert result["gateway"]["edge_node_id"] == "jetson-test-node"
    assert result["sample_count"] == result["case_count"]
    assert result["wall_latency_ms"]["max"] <= result["target_latency_ms"]


def test_stdlib_profiles_expose_wfc_ready_boundary(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setenv("WEAREDGE_DEPLOYMENT_MODE", "jetson_edge_stdlib_http_gateway_benchmark")
    monkeypatch.setenv("WEAREDGE_EDGE_NODE_ID", "jetson-orin-nano-8gb")

    healthz = module.build_healthz()
    profile = module.build_edge_runtime_profile()

    assert healthz["ok"] is True
    assert healthz["competition"]["workflow_canvas_endpoint"] == "/v1/workflow-canvas/decision"
    assert profile["ok"] is True
    assert profile["capabilities"]["workflow_canvas_ready"] is True
    assert profile["safety_boundary"]["model_direct_ot_control"] is False
