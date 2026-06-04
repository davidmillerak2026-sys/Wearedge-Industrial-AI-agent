from __future__ import annotations

from fastapi.testclient import TestClient

import jetson.app as app_module
from jetson.competition import COMPETITION_TARGETS, build_competition_decision
from jetson.config import GatewayConfig


def _competition_payload() -> dict[str, object]:
    return {
        "stage": "final",
        "selected_directions": [
            "maintenance",
            "quality",
            "energy",
            "flexible_production",
            "workflow_canvas",
        ],
        "context": {
            "maintenance": {
                "f1_pct": 88.0,
                "warning_lead_time_hours": 30.0,
                "root_cause_top3_pct": 92.0,
                "vibration_rms_mm_s": 7.2,
                "has_threshold_evidence": True,
            },
            "quality": {
                "defect_rate_pct": 3.4,
                "detection_confidence_pct": 93.0,
                "relative_improvement_pct": 6.0,
                "has_detector_evidence": True,
            },
            "energy": {
                "forecast_accuracy_pct": 96.0,
                "saving_pct": 12.0,
                "idle_kw": 5.8,
                "has_meter_baseline": True,
            },
            "production": {
                "schedule_efficiency_gain_pct": 22.0,
                "component_reuse_pct": 76.0,
                "target_sku": "SKU-C500",
                "has_released_checklist": True,
            },
            "workflow_canvas": {
                "existing_component_use_pct": 72.0,
                "new_component_reuse_potential_pct": 80.0,
            },
        },
    }


def _auth_disabled_config() -> GatewayConfig:
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
        llama_image_min_tokens=560,
        llama_image_max_tokens=560,
        audio_fusion_runtime="llama.cpp",
        model_variant="E2B",
    )


def test_competition_decision_meets_final_joint_solution_targets() -> None:
    decision = build_competition_decision(_competition_payload())

    assert decision["ok"] is True
    assert decision["direction_count"] == 5
    assert decision["competition_metrics"]["latency_target_met"] is True
    assert decision["competition_metrics"]["final_min_agent_directions_met"] is True
    assert decision["compliance"]["final_round"]["at_least_three_directions"] is True
    assert decision["compliance"]["runtime_targets"]["decision_accuracy_target_met"] is True
    assert decision["competition_targets"]["maintenance_f1_pct_min"] == COMPETITION_TARGETS["maintenance_f1_pct_min"]

    by_direction = {item["direction"]: item for item in decision["evaluations"]}
    assert by_direction["maintenance"]["status"] == "target_met"
    assert by_direction["energy"]["status"] == "target_met"
    assert by_direction["quality"]["status"] == "target_met"
    assert by_direction["flexible_production"]["status"] == "target_met"
    assert by_direction["workflow_canvas"]["status"] == "target_met"

    workflow_canvas = decision["workflow_canvas"]
    assert workflow_canvas["python_function_block"]["path"] == "/v1/workflow-canvas/decision"
    assert "WearedgeAgentServiceResource" in workflow_canvas["function_blocks"]
    assert "CollaborativeDecisionGate" in workflow_canvas["function_blocks"]
    assert "HumanApprovalGate" in workflow_canvas["function_blocks"]


def test_workflow_canvas_decision_api_returns_competition_payload(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "config", _auth_disabled_config())

    client = TestClient(app_module.app)
    response = client.post("/v1/workflow-canvas/decision", json=_competition_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["stage"] == "final"
    assert body["competition_metrics"]["latency_target_met"] is True
    assert body["workflow_canvas"]["resource_block"]["name"] == "Wearedge Agent Service"
