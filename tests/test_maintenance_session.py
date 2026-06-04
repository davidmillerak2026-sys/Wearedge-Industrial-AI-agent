from __future__ import annotations

import pytest

from jetson.maintenance_session import MaintenanceSessionStore, build_workflow_session_context, ensure_maintenance_mode


def test_maintenance_session_tracks_evidence_gaps_and_prompt_context() -> None:
    store = MaintenanceSessionStore()
    session = store.create_session(
        device={"device_id": "m400-demo-01", "location_hint": "line-3"},
        location_hint="line-3",
        operator_id="op-07",
        initial_prompt="Investigate abnormal gearbox condition.",
    )

    store.add_evidence(
        session.session_id,
        evidence_type="maintenance_asset_identity_photo",
        capture_type="photo",
        status="accepted",
        summary="Asset plate confirms PKG-L3-GBX-03 packaging line gearbox drive station.",
        fields={"asset_id": "PKG-L3-GBX-03"},
        image_bytes=128000,
        image_content_type="image/jpeg",
    )
    store.add_evidence(
        session.session_id,
        evidence_type="maintenance_temperature_gauge_photo",
        capture_type="photo",
        status="requires_human_confirm",
        summary="Gauge image is angled and the operator must confirm whether the gearbox reading is 78 C.",
    )

    session = store.record_inference(
        session.session_id,
        {
            "request_id": "req-maint-001",
            "action_card": {
                "channel": "maintenance_report",
                "priority": "high",
                "owner": "maintenance_engineer",
            },
            "follow_up_plan": {
                "status": "operator_evidence_required",
                "requests": [
                    {"id": "maintenance_asset_identity_photo"},
                    {"id": "maintenance_recent_work_record_photo"},
                    {"id": "maintenance_operator_sensory_check"},
                ],
            },
            "runtime_stream": {"closed": True},
        },
    )

    context = build_workflow_session_context(session)
    prompt_context = str(context["prompt_context"])

    assert context["session_id"] == session.session_id
    assert context["evidence_state"]["accepted_evidence_ids"] == [
        "maintenance_asset_identity_photo",
        "maintenance_condition_screen_photo",
        "maintenance_temperature_gauge_photo",
        "maintenance_lubrication_record_photo",
    ]
    assert session.missing_requested_evidence_ids() == (
        "maintenance_recent_work_record_photo",
        "maintenance_operator_sensory_check",
    )
    assert "PKG-L3-GBX-03" in prompt_context
    assert "Evidence requiring confirmation" in prompt_context
    assert "maintenance_recent_work_record_photo" in prompt_context
    assert session.trace()["events"][-1]["event"] == "maintenance_session.inference_completed"


def test_maintenance_session_rejects_unsupported_status_and_non_maintenance_mode() -> None:
    store = MaintenanceSessionStore()
    session = store.create_session(device={"device_id": "m400-demo-01"})

    with pytest.raises(ValueError, match="unsupported evidence status"):
        store.add_evidence(
            session.session_id,
            evidence_type="maintenance_operator_sensory_check",
            capture_type="operator_note",
            status="done",
            summary="Operator reports abnormal noise.",
        )

    evidence = store.add_evidence(
        session.session_id,
        evidence_type="maintenance_followup_frame",
        capture_type="photo",
        status="accepted",
        summary="One M400 frame includes HMI readings and visible temperature gauges.",
        image_bytes=128000,
        image_content_type="image/jpeg",
    )
    assert evidence.evidence_type == "maintenance_followup_frame"

    with pytest.raises(ValueError, match="unsupported maintenance evidence_type"):
        store.add_evidence(
            session.session_id,
            evidence_type="hazard_exposure_photo",
            capture_type="photo",
            status="accepted",
            summary="This should stay outside the maintenance session route.",
        )

    with pytest.raises(ValueError, match="maintenance sessions only support"):
        ensure_maintenance_mode("hazard")
