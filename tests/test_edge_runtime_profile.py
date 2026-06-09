from __future__ import annotations

from fastapi.testclient import TestClient

import jetson.app as app_module
from jetson.config import GatewayConfig


def _edge_config() -> GatewayConfig:
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
        deployment_mode="jetson",
        edge_node_id="jetson-demo-01",
    )


def test_edge_runtime_profile_exposes_edge_and_platform_readiness(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "config", _edge_config())

    client = TestClient(app_module.app)
    response = client.get("/v1/edge/runtime-profile")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["edge_node"]["deployment_mode"] == "jetson"
    assert body["runtime"]["workflow_decision_api"] == "/v1/workflow-canvas/decision"
    assert body["edge_capabilities"]["local_multimodal_inference"] is True
    assert body["edge_capabilities"]["workflow_canvas_ready"] is True
    assert body["platform_integration"]["gongyi_mofang"]["resource_block"] == "Wearedge Agent Service"
    assert "OPC UA" in body["platform_integration"]["industrial_connectors"]
    assert body["safety_boundary"]["model_direct_ot_control"] is False
    assert body["safety_boundary"]["required_gate"] == "HumanApprovalGate"
