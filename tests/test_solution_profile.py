from __future__ import annotations

from fastapi.testclient import TestClient

import jetson.app as app_module
from jetson.config import GatewayConfig
from jetson.solution_profile import RuntimeProfileInput, build_solution_profile


def _config() -> GatewayConfig:
    return GatewayConfig(
        llama_base_url="http://127.0.0.1:8080",
        model="gemma4",
        demo_token=None,
        max_image_mb=4,
        enable_thinking=False,
        max_tokens=160,
        temperature=0.0,
        timeout_seconds=10,
        upload_dir=None,
        event_log_path=None,
        auth_disabled=True,
        contract_min_words=16,
        contract_repair_enabled=True,
        llama_image_min_tokens=70,
        llama_image_max_tokens=70,
        audio_fusion_runtime="llama.cpp",
        model_variant="E2B",
        deployment_mode="ipc",
        edge_node_id="ipc-demo-01",
    )


def test_solution_profile_documents_model_and_decision_boundary() -> None:
    profile = build_solution_profile(
        RuntimeProfileInput(
            model="gemma4",
            model_variant="E2B",
            llama_base_url="http://127.0.0.1:8080",
            deployment_mode="jetson",
            edge_node_id="jetson-demo-01",
        )
    )

    assert profile["ok"] is True
    assert profile["model_runtime"]["primary_model"] == "gemma4"
    assert "Gemma 4 E2B" in profile["model_runtime"]["default_poc_model"]
    assert profile["decision_mechanism"]["model_dependency"] == "not required for /v1/workflow-canvas/decision"
    assert "maintenance" in profile["decision_mechanism"]["key_metrics_matrix"]
    assert "HumanApprovalGate" in profile["decision_mechanism"]["safety_boundary"]
    assert profile["platform_integration"]["gongyi_mofang"]["python_function_block"] == "CallWearedgeDecisionApi"


def test_solution_profile_api_uses_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "config", _config())

    client = TestClient(app_module.app)
    response = client.get("/v1/industrial-agent/solution-profile")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["edge_runtime"]["deployment_mode"] == "ipc"
    assert body["edge_runtime"]["node_id"] == "ipc-demo-01"
    assert body["model_runtime"]["primary_model"] == "gemma4"
    assert body["platform_integration"]["xcelerator"]["decision_endpoint"] == "/v1/workflow-canvas/decision"
