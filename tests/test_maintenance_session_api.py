from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

import jetson.app as app_module
from jetson.config import GatewayConfig
from jetson.llama_client import LlamaResponse
from jetson.maintenance_session import MaintenanceSessionStore


def test_maintenance_session_api_runs_full_evidence_loop(monkeypatch) -> None:
    monkeypatch.setattr(
        app_module,
        "config",
        GatewayConfig(
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
        ),
    )
    monkeypatch.setattr(app_module, "maintenance_session_store", MaintenanceSessionStore())
    seen_prompts: list[str] = []

    def fake_inference(*, prompt: str, image_bytes: bytes, image_content_type: str) -> LlamaResponse:
        seen_prompts.append(prompt)
        return LlamaResponse(
            answer=(
                "- Machine: Packaging Line Three drive station PKG-L3-GBX-03 with readable asset plate condition monitor and maintenance records.\n"
                "- Symptom: Session evidence shows yellow PLC alarm high vibration trend elevated gearbox temperature delayed lubrication and abnormal operator rumble.\n"
                "- Maintenance Risk: Continued operation could worsen bearing wear lubrication degradation heat accumulation vibration growth and unplanned downtime risk.\n"
                "- Evidence Needed: Compare the accepted readings against manual thresholds telemetry history and authorized maintenance engineer judgment before final cause.\n"
                "- Action: Inspect the gearbox bearing and lubrication condition immediately and report the compiled session evidence package to maintenance engineering."
            ),
            raw={"fake": True},
            latency_ms=5,
        )

    monkeypatch.setattr(app_module, "_run_multimodal_inference", fake_inference)

    client = TestClient(app_module.app)
    create_response = client.post(
        "/v1/maintenance-sessions",
        data={
            "device_id": "m400-api-test",
            "location_hint": "line-3-drive-station",
            "capture_mode": "api-test",
            "operator_id": "operator-api-test",
            "initial_prompt": "Investigate gearbox vibration evidence.",
        },
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["maintenance_session"]["session_id"]

    evidence_items = [
        (
            "maintenance_asset_identity_photo",
            "Asset plate confirms PKG-L3-GBX-03 packaging line three gearbox drive station.",
            {"asset_id": "PKG-L3-GBX-03"},
        ),
        (
            "maintenance_condition_screen_photo",
            "Condition monitor shows vibration RMS high trend yellow PLC alarm current load and speed context.",
            {"vibration_rms_mm_s": "7.2", "alarm_color": "yellow", "alarm_code": "GBX-VIB-HI"},
        ),
        (
            "maintenance_temperature_gauge_photo",
            "Temperature gauges show elevated gearbox and bearing readings needing manual threshold comparison.",
            {"gearbox_temperature_c": "78", "bearing_temperature_c": "71"},
        ),
        (
            "maintenance_lubrication_record_photo",
            "Lubrication record shows the last gearbox lubrication is older than the weekly check interval.",
            {"lubrication_date": "2026-05-07"},
        ),
        (
            "maintenance_recent_work_record_photo",
            "Recent maintenance record shows prior vibration inspection and no confirmed bearing replacement.",
            {"last_maintenance_date": "2026-05-10"},
        ),
    ]

    for evidence_type, summary, fields in evidence_items:
        response = client.post(
            f"/v1/maintenance-sessions/{session_id}/evidence",
            data={
                "evidence_type": evidence_type,
                "capture_type": "photo",
                "status": "accepted",
                "summary": summary,
                "fields_json": json.dumps(fields),
            },
            files={"image": ("evidence.jpg", b"fake-image", "image/jpeg")},
        )
        assert response.status_code == 200
        assert response.json()["evidence"]["status"] == "accepted"

    sensory_response = client.post(
        f"/v1/maintenance-sessions/{session_id}/evidence",
        data={
            "evidence_type": "maintenance_operator_sensory_check",
            "capture_type": "operator_note",
            "status": "accepted",
            "summary": "Operator reports abnormal rumble warm oil smell stronger vibration and small oil stain after speed increase.",
            "fields_json": json.dumps(
                {
                    "unusual_noise": "low-frequency abnormal rumble",
                    "unusual_smell": "slight warm oil smell",
                    "felt_shaking": "stronger guard vibration",
                    "visible_leak": "small oil stain",
                }
            ),
        },
    )
    assert sensory_response.status_code == 200

    infer_response = client.post(
        f"/v1/maintenance-sessions/{session_id}/infer",
        data={
            "prompt": "Use accumulated session evidence and do not analyze EHS hazard exposure.",
            "device_id": "m400-api-test",
            "location_hint": "line-3-drive-station",
        },
        files={"image": ("initial.jpg", b"fake-initial-image", "image/jpeg")},
    )

    assert infer_response.status_code == 200
    body = infer_response.json()
    assert body["ok"] is True
    assert body["analysis_mode"] == "maintenance"
    assert body["follow_up_plan"]["status"] == "ready_for_human_confirmation"
    assert body["follow_up_plan"]["requests"] == []
    assert body["knowledge_base"]["status"] == "matched"
    assert len(body["knowledge_base"]["hits"]) >= 1
    assert body["maintenance_evaluation"]["status"] == "breach_detected"
    assert body["maintenance_evaluation"]["risk_level"] == "high"
    assert len(body["maintenance_evaluation"]["breaches"]) >= 3
    assert body["action_card"]["channel"] == "maintenance_report"
    assert body["action_card"]["owner"] == "maintenance_engineer"
    assert body["tool_plan"]["used_tool_calls"] == 1
    assert body["integration_event"]["payload"]["maintenance_evaluation"]["status"] == "breach_detected"
    assert body["maintenance_session"]["missing_requested_evidence_ids"] == []
    assert len(body["maintenance_session"]["evidence_state"]["accepted_evidence_ids"]) == 6
    assert "Maintenance session evidence context" in seen_prompts[0]
    session_stage = next(
        stage for stage in body["agently_trace"]["triggerflow"]["stages"] if stage["name"] == "load_session_evidence"
    )
    assert session_stage["status"] == "completed"
    assert session_stage["accepted_evidence_count"] == 6
    assert body["runtime_stream"]["closed"] is True

    trace_response = client.get(f"/v1/maintenance-sessions/{session_id}/trace")
    assert trace_response.status_code == 200
    trace_body = trace_response.json()
    assert trace_body["trace"]["events"][-1]["event"] == "maintenance_session.inference_completed"
    assert Path("scripts/run_maintenance_session_poc.sh").exists()
