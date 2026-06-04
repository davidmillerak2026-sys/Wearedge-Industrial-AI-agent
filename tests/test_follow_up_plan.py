from __future__ import annotations

from jetson.agent_loop import build_action_card, build_integration_event, decide_action
from jetson.evidence_plan import build_evidence_plan
from jetson.follow_up_plan import FOLLOW_UP_PLAN_VERSION, build_follow_up_plan
from jetson.tool_plan import build_bounded_tool_plan


def test_maintenance_follow_up_plan_prompts_operator_for_missing_evidence() -> None:
    fields = {
        "machine": "Packaging Line Drive Station PKG-L3-GBX-03",
        "symptom": "Yellow PLC alarm is visible but vibration, current, load, speed, and alarm code are not stable.",
        "maintenance_risk": "Possible heat, bearing, gearbox, lubrication, or alarm-related risk needs confirmation.",
        "evidence_needed": "Request lubrication record, recent maintenance history, condition readings, and operator notes.",
        "action": "Inspect the station immediately and report the visible alarm condition to maintenance.",
    }
    evidence_plan = build_evidence_plan(
        mode="maintenance",
        device={"device_id": "m400-demo-01"},
        image_bytes=1_200_000,
        needs_ocr=True,
        high_detail=True,
    )
    tool_plan = build_bounded_tool_plan(evidence_plan)
    decision = decide_action("maintenance", fields)

    follow_up = build_follow_up_plan(
        mode="maintenance",
        fields=fields,
        evidence_plan=evidence_plan.as_dict(),
        tool_plan=tool_plan.as_dict(),
        decision_channel=decision.channel,
    ).as_dict()

    assert follow_up["version"] == FOLLOW_UP_PLAN_VERSION
    assert follow_up["status"] == "operator_evidence_required"
    assert follow_up["next_action"] == "collect_visual_evidence_gaps"
    request_ids = {request["id"] for request in follow_up["requests"]}
    assert all(request["capture_type"] == "photo" for request in follow_up["requests"])
    assert "maintenance_condition_screen_photo" in request_ids
    assert "maintenance_temperature_gauge_photo" in request_ids
    assert "maintenance_lubrication_record_photo" in request_ids
    assert "maintenance_recent_work_record_photo" in request_ids
    assert "maintenance_operator_sensory_check" not in request_ids
    assert "may satisfy multiple visual evidence points" in follow_up["summary"]
    assert "remaining useful life" in follow_up["blocked_claims"]


def test_follow_up_plan_is_added_to_integration_event_payload() -> None:
    fields = {
        "machine": "Packaging Line Drive Station PKG-L3-GBX-03",
        "symptom": "Yellow alarm is visible and the HMI details are not readable.",
        "maintenance_risk": "Condition should be reviewed before increasing operating load.",
        "evidence_needed": "Capture alarm detail, operator observation, and recent work record.",
        "action": "Inspect the station immediately and report the visible alarm condition to maintenance.",
    }
    evidence_plan = build_evidence_plan(
        mode="maintenance",
        device={"device_id": "m400-demo-01"},
        image_bytes=1_200_000,
        needs_ocr=True,
        high_detail=True,
    )
    tool_plan = build_bounded_tool_plan(evidence_plan)
    decision = decide_action("maintenance", fields)
    action_card = build_action_card("maintenance", fields, decision)
    follow_up = build_follow_up_plan(
        mode="maintenance",
        fields=fields,
        evidence_plan=evidence_plan.as_dict(),
        tool_plan=tool_plan.as_dict(),
        decision_channel=decision.channel,
    ).as_dict()

    event = build_integration_event(
        request_id="req-maint-001",
        device={"device_id": "m400-demo-01"},
        mode="maintenance",
        fields=fields,
        action_card=action_card,
        follow_up_plan=follow_up,
    )

    assert event.payload["follow_up_plan"]["status"] == "operator_evidence_required"
    assert event.payload["follow_up_plan"]["requests"]


def test_non_maintenance_follow_up_plan_is_not_required() -> None:
    follow_up = build_follow_up_plan(
        mode="iqc",
        fields={"action": "Hold suspect units for quality review."},
        evidence_plan={"missing_tools": ["visual_defect_detector"]},
        tool_plan={"skipped_tools": []},
        decision_channel="quality_hold",
    ).as_dict()

    assert follow_up["status"] == "not_required"
    assert follow_up["requests"] == []


def test_maintenance_follow_up_plan_filters_session_evidence_already_accepted() -> None:
    fields = {
        "machine": "Packaging Line Drive Station PKG-L3-GBX-03",
        "symptom": "Yellow PLC alarm with high vibration trend and elevated gearbox temperature needs review.",
        "maintenance_risk": "Gearbox heat vibration and lubrication risk could worsen unplanned downtime.",
        "evidence_needed": "Review condition monitor lubrication record recent work record and operator observations.",
        "action": "Inspect the station immediately and report the visible alarm condition to maintenance.",
    }
    evidence_plan = build_evidence_plan(
        mode="maintenance",
        device={"device_id": "m400-demo-01"},
        image_bytes=1_200_000,
        needs_ocr=True,
        high_detail=True,
    )
    tool_plan = build_bounded_tool_plan(evidence_plan)
    decision = decide_action("maintenance", fields)

    follow_up = build_follow_up_plan(
        mode="maintenance",
        fields=fields,
        evidence_plan=evidence_plan.as_dict(),
        tool_plan=tool_plan.as_dict(),
        decision_channel=decision.channel,
        accepted_evidence_ids=[
            "maintenance_asset_identity_photo",
            "maintenance_condition_screen_photo",
            "maintenance_temperature_gauge_photo",
            "maintenance_lubrication_record_photo",
            "maintenance_recent_work_record_photo",
            "maintenance_operator_sensory_check",
        ],
    ).as_dict()

    assert follow_up["status"] == "ready_for_human_confirmation"
    assert follow_up["next_action"] == "review_action_card"
    assert follow_up["requests"] == []


def test_maintenance_follow_up_plan_asks_sensory_after_visual_evidence() -> None:
    fields = {
        "machine": "Packaging Line Drive Station PKG-L3-GBX-03",
        "symptom": "Yellow PLC alarm with high vibration trend and elevated gearbox temperature needs review.",
        "maintenance_risk": "Gearbox heat vibration and lubrication risk could worsen unplanned downtime.",
        "evidence_needed": "Review condition monitor lubrication record recent work record and operator observations.",
        "action": "Inspect the station immediately and report the visible alarm condition to maintenance.",
    }
    evidence_plan = build_evidence_plan(
        mode="maintenance",
        device={"device_id": "m400-demo-01"},
        image_bytes=1_200_000,
        needs_ocr=True,
        high_detail=True,
    )
    tool_plan = build_bounded_tool_plan(evidence_plan)
    decision = decide_action("maintenance", fields)

    follow_up = build_follow_up_plan(
        mode="maintenance",
        fields=fields,
        evidence_plan=evidence_plan.as_dict(),
        tool_plan=tool_plan.as_dict(),
        decision_channel=decision.channel,
        accepted_evidence_ids=[
            "maintenance_asset_identity_photo",
            "maintenance_condition_screen_photo",
            "maintenance_temperature_gauge_photo",
            "maintenance_lubrication_record_photo",
            "maintenance_recent_work_record_photo",
        ],
    ).as_dict()

    assert follow_up["status"] == "operator_evidence_required"
    assert follow_up["next_action"] == "collect_operator_sensory_evidence"
    assert [request["id"] for request in follow_up["requests"]] == ["maintenance_operator_sensory_check"]


def test_maintenance_follow_up_plan_treats_one_image_as_multiple_visual_evidence_points() -> None:
    fields = {
        "machine": "Packaging Line Drive Station PKG-L3-GBX-03",
        "symptom": (
            "HMI shows speed 1460 RPM, current 18.6 A, and load 82%. "
            "Motor temperature is 82 C, bearing temperature is 78 C, and gearbox temperature is 91 C."
        ),
        "maintenance_risk": "Condition and temperature readings are visible; lubrication and work history still need context.",
        "evidence_needed": "Request lubrication record and recent maintenance history before final judgment.",
        "action": "Inspect the station and collect the remaining maintenance records.",
    }
    evidence_plan = build_evidence_plan(
        mode="maintenance",
        device={"device_id": "m400-demo-01"},
        image_bytes=1_200_000,
        needs_ocr=True,
        high_detail=True,
    )
    tool_plan = build_bounded_tool_plan(evidence_plan)
    decision = decide_action("maintenance", fields)

    follow_up = build_follow_up_plan(
        mode="maintenance",
        fields=fields,
        evidence_plan=evidence_plan.as_dict(),
        tool_plan=tool_plan.as_dict(),
        decision_channel=decision.channel,
    ).as_dict()

    request_ids = {request["id"] for request in follow_up["requests"]}

    assert follow_up["next_action"] == "collect_visual_evidence_gaps"
    assert "maintenance_condition_screen_photo" not in request_ids
    assert "maintenance_temperature_gauge_photo" not in request_ids
    assert "maintenance_lubrication_record_photo" in request_ids
    assert "maintenance_recent_work_record_photo" in request_ids
