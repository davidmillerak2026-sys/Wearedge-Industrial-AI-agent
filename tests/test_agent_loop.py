from __future__ import annotations

import pytest

from jetson.agent_loop import (
    AGENT_LOOP_VERSION,
    ACTION_CARD_VERSION,
    INTEGRATION_EVENT_VERSION,
    build_action_card,
    build_agent_loop_metadata,
    build_integration_event,
    build_mode_contract_prompt,
    build_route_boundary_prompt_context,
    check_mode_contract,
    decide_action,
    decide_action_with_context_guard,
    mode_response_fields,
    resolve_agent_mode,
    select_agent_route,
)


def test_resolve_agent_mode_accepts_factory_aliases() -> None:
    assert resolve_agent_mode(None) == "hazard"
    assert resolve_agent_mode("safety_agent") == "hazard"
    assert resolve_agent_mode("lao-shi-fu") == "maintenance"
    assert resolve_agent_mode("quality_inspection") == "iqc"
    assert resolve_agent_mode("energy_agent") == "energy"
    assert resolve_agent_mode("work_instruction") == "wi"
    assert resolve_agent_mode("sku-changeover") == "changeover"

    with pytest.raises(ValueError):
        resolve_agent_mode("unsupported")


def test_mode_contract_prompt_and_response_fields_for_maintenance() -> None:
    answer = (
        "- Machine: Conveyor drive station with visible motor gearbox guard and nearby lubrication point.\n"
        "- Symptom: Visible oil staining and dust accumulation around the gearbox base suggest an abnormal condition requiring inspection.\n"
        "- Maintenance Risk: Leakage or poor lubrication could increase wear heat vibration and unplanned downtime if not checked promptly.\n"
        "- Evidence Needed: Inspect the lubrication point review gearbox temperature vibration history and confirm the released maintenance manual threshold.\n"
        "- Action: Inspect the gearbox area safely and report the condition to maintenance before increasing production speed today."
    )

    prompt = build_mode_contract_prompt("Check this machine.", "maintenance")
    contract = check_mode_contract(answer, "maintenance", min_words=16)

    assert "- Evidence Needed:" in prompt
    assert contract.ok
    assert contract.structured is not None
    fields = mode_response_fields(contract.structured, "maintenance")
    assert fields["machine"].startswith("Conveyor drive")
    assert fields["maintenance_risk"].startswith("Leakage")


def test_maintenance_contract_normalizes_chinese_action_starter() -> None:
    answer = (
        "- Machine: PKG-L3-GBX-03 packaging line drive station with visible gearbox motor and condition display.\n"
        "- Symptom: Visible oil staining high vibration trend yellow alarm and elevated gearbox temperature indicate abnormal machine condition.\n"
        "- Maintenance Risk: Continued running could increase gearbox bearing wear lubricant degradation vibration growth heat accumulation and unplanned downtime risk.\n"
        "- Evidence Needed: Review vibration history lubrication record temperature trend recent maintenance notes and manual alarm thresholds before release.\n"
        "- Action: 立即对驱动电机和齿轮箱润滑状态进行目视检查，并根据历史趋势安排维修人员评估关键部件。"
    )

    contract = check_mode_contract(answer, "maintenance", min_words=16)

    assert contract.ok
    assert contract.structured is not None
    fields = mode_response_fields(contract.structured, "maintenance")
    assert str(fields["action"]).startswith("Inspect ")


def test_iqc_disposition_routes_to_deterministic_action_channel() -> None:
    decision = decide_action(
        "iqc",
        {
            "disposition": "stop_production",
            "action": "Stop production and escalate containment to quality leadership before releasing more units.",
        },
    )

    assert decision.channel == "stop_production"
    assert decision.owner == "shift_lead"
    assert decision.requires_human


def test_route_selection_keeps_maintenance_out_of_hazard_analysis() -> None:
    route = select_agent_route("maintenance")
    prompt_context = build_route_boundary_prompt_context("maintenance")

    assert route.route == "maintenance"
    assert route.source == "analysis_mode"
    assert "Do not analyze EHS/personnel hazard exposure" in route.boundary
    assert "hazard agent" in prompt_context


def test_maintenance_and_changeover_action_routing() -> None:
    maintenance_decision = decide_action("maintenance", {"action": "Schedule maintenance window for inspection."})
    changeover_decision = decide_action("changeover", {"action": "Verify first-piece label and barcode before restart."})

    assert maintenance_decision.channel == "schedule_maintenance"
    assert maintenance_decision.owner == "maintenance_planner"
    assert changeover_decision.channel == "changeover_verification"
    assert changeover_decision.requires_human


def test_energy_route_and_action_card_require_meter_confirmation() -> None:
    fields = {
        "asset": "Packaging line three cartoner auxiliary drive and compressed air branch.",
        "energy_signal": "Meter trend shows twelve kilowatt idle load during a scheduled break window.",
        "optimization": "Reduce auxiliary load during verified idle time without changing product quality checks.",
        "verification": "Confirm meter baseline production schedule and line lead approval before changing load state.",
        "action": "Reduce auxiliary load only after meter baseline and production approval confirm the idle window.",
    }

    route = select_agent_route("energy")
    decision = decide_action("energy", fields)
    card = build_action_card("energy", fields, decision)

    assert route.route == "energy"
    assert "meter baseline" in route.boundary
    assert decision.channel == "energy_reduce_load"
    assert decision.owner == "energy_manager"
    assert decision.requires_human
    assert card.integration_target == "energy_management_event"
    assert card.required_confirmations == (
        "asset identity",
        "meter baseline",
        "production schedule",
        "energy manager approval",
        "production lead approval",
    )


def test_context_guard_requires_energy_asset_and_signal() -> None:
    decision = decide_action(
        "energy",
        {
            "asset": "Unknown utility branch from the current image.",
            "energy_signal": "Cannot determine whether the meter reading belongs to this line.",
            "optimization": "Possible idle load reduction needs confirmation.",
            "verification": "Confirm the meter baseline and production schedule.",
            "action": "Keep monitoring until the asset and signal source are confirmed.",
        },
    )

    assert decision.channel == "energy_review"
    assert decision.owner == "energy_manager"
    assert decision.requires_human


def test_maintenance_severity_rule_reports_yellow_alarm_with_condition_evidence() -> None:
    decision = decide_action(
        "maintenance",
        {
            "machine": "Packaging Line 3 Drive Station asset PKG-L3-GBX-03.",
            "symptom": "Yellow PLC alarm is active with visible VIB RMS high trend and oil stain near gearbox.",
            "maintenance_risk": "High vibration, rising gearbox temperature, and lubrication issue could increase wear risk.",
            "evidence_needed": "Confirm telemetry history, alarm log, manual thresholds, and work order history.",
            "action": "Inspect the yellow PLC alarm and associated condition monitoring display immediately.",
        },
    )

    assert decision.channel == "maintenance_report"
    assert decision.owner == "maintenance_engineer"
    assert decision.requires_human


def test_maintenance_severity_rule_escalates_critical_visible_indicators() -> None:
    decision = decide_action(
        "maintenance",
        {
            "machine": "Packaging Line 3 Drive Station asset PKG-L3-GBX-03.",
            "symptom": "Red alarm with smoke and severe leak is visible near the gearbox housing.",
            "maintenance_risk": "Burning odor and leaking lubricant could indicate immediate machine damage risk.",
            "action": "Inspect the area from a safe position and keep the operator outside the guarded zone.",
        },
    )

    assert decision.channel == "maintenance_escalation"
    assert decision.owner == "maintenance_engineer"
    assert decision.requires_human


def test_maintenance_escalates_when_inspect_action_contains_urgent_escalation() -> None:
    decision = decide_action(
        "maintenance",
        {
            "machine": "PKG-L3-GBX-03 packaging line drive station.",
            "symptom": "Operator reports noise vibration oil smell and visible guard shaking near the gearbox.",
            "maintenance_risk": "Significant risk of imminent mechanical failure and catastrophic component damage is possible.",
            "evidence_needed": "Review lubrication record, recent work history, and vibration trend before assigning final root cause.",
            "action": "Inspect the gearbox immediately and escalate the situation to a senior maintenance engineer for urgent assessment.",
        },
    )

    assert decision.channel == "maintenance_escalation"
    assert decision.owner == "maintenance_engineer"
    assert decision.requires_human


def test_maintenance_route_does_not_escalate_from_safety_hazard_words_only() -> None:
    decision = decide_action(
        "maintenance",
        {
            "machine": "PKG-L3-GBX-03 packaging line drive station.",
            "symptom": "Operator mentions a generic safety hazard phrase but provides no machine critical indicator or urgent escalation evidence.",
            "maintenance_risk": "Machine condition evidence is still limited and needs maintenance readings before severity can be raised.",
            "evidence_needed": "Collect HMI vibration trend temperature reading lubrication record and recent maintenance record.",
            "action": "Inspect the machine condition and collect missing maintenance evidence before assigning equipment severity.",
        },
    )

    assert decision.channel == "condition_inspection"
    assert decision.owner == "operator"
    assert decision.requires_human is False


def test_agent_loop_metadata_exposes_visible_stage_trace() -> None:
    decision = decide_action("hazard", {"action": "Stop entry until the area is controlled."})
    action_card = build_action_card("hazard", {"action": "Stop entry until the area is controlled."}, decision)

    metadata = build_agent_loop_metadata(
        mode="hazard",
        repaired=True,
        validation_attempts=2,
        initial_violations=["missing required line(s): action"],
        final_violations=[],
        decision=decision,
        action_card=action_card,
    )

    assert metadata["version"] == AGENT_LOOP_VERSION
    assert metadata["contract_repaired"] is True
    assert metadata["decision"]["channel"] == "stop_and_make_safe"
    assert [stage["name"] for stage in metadata["stages"]] == [
            "normalize_agent",
            "select_agent_route",
        "collect_evidence",
        "bounded_react_tools",
        "build_contract_prompt",
        "model_infer",
        "validate_contract",
        "repair_contract",
        "identify_context",
            "structure_action",
            "uncertainty_guard",
            "evaluate_iqc_quality_rules",
            "evaluate_released_source",
            "iqc_quality_guard",
            "released_source_guard",
            "maintenance_evaluation_guard",
            "build_action_card",
            "build_follow_up_plan",
        ]
    assert metadata["context_guard"]["status"] == "clear"
    assert metadata["tool_plan"]["status"] == "not_recorded"


def test_context_guard_blocks_unknown_changeover_from_controlled_step() -> None:
    guard = decide_action_with_context_guard(
        "changeover",
        {
            "machine": "Unknown machine near the labeler.",
            "sku": "Target SKU is not readable from the current M400 image.",
            "changeover_step": "Continue guide rail adjustment after line clearance.",
            "verification": "Check first piece before restart.",
            "action": "Continue controlled guide rail adjustment after line clearance.",
        },
    )

    assert guard.status == "human_confirm_required"
    assert guard.original_decision.channel == "controlled_changeover_step"
    assert guard.decision.channel == "changeover_identification_required"
    assert guard.decision.owner == "operator_quality"
    assert set(guard.blocked_fields) == {"machine", "sku"}


def test_context_guard_routes_iqc_pass_with_unknown_product_to_quality_review() -> None:
    decision = decide_action(
        "iqc",
        {
            "product": "Unknown product identity from the current frame.",
            "quality_risk": "No visible quality risk can be confirmed from this image alone.",
            "disposition": "pass",
            "action": "Continue production under current inspection controls.",
        },
    )

    assert decision.channel == "quality_review"
    assert decision.owner == "quality_engineer"
    assert decision.requires_human


def test_context_guard_requires_wi_source_before_guided_operation() -> None:
    fields = {
        "machine": "Cartoner station two",
        "work_instruction": "Unknown current work instruction revision.",
        "risk_control": "Guard door and product transfer controls remain required.",
        "action": "Follow the visible setup guidance at normal speed.",
    }
    decision = decide_action("wi", fields)
    card = build_action_card("wi", fields, decision)

    assert decision.channel == "wi_identification_required"
    assert card.priority == "medium"
    assert card.requires_human


def test_context_guard_requires_machine_identity_before_low_control_maintenance() -> None:
    decision = decide_action(
        "maintenance",
        {
            "machine": "Unknown machine in the current frame.",
            "symptom": "Residue is visible near the base.",
            "maintenance_risk": "Possible leak or lubrication issue needs bounded investigation.",
            "evidence_needed": "Check manual inspection points and recent alarm trend.",
            "action": "Inspect the area safely before increasing production speed.",
        },
    )

    assert decision.channel == "maintenance_identification_required"
    assert decision.owner == "maintenance_engineer"
    assert decision.requires_human


def test_context_guard_requires_hazard_context_before_downgrading_exposure() -> None:
    decision = decide_action(
        "hazard",
        {
            "scene": "Unknown scene context from the current image.",
            "risk": "Cannot determine whether the moving equipment exposure is controlled.",
            "action": "Keep controls in place while continuing the task.",
        },
    )

    assert decision.channel == "hazard_identification_required"
    assert decision.requires_human


def test_action_card_maps_iqc_stop_to_qms_package() -> None:
    fields = {
        "product": "Machined housing lot A",
        "quality_risk": "Visible burrs near the sealing face",
        "disposition": "stop_production",
        "action": "Stop production and escalate containment to quality leadership before releasing more units.",
    }
    decision = decide_action("iqc", fields)

    card = build_action_card("iqc", fields, decision)

    assert card.version == ACTION_CARD_VERSION
    assert card.priority == "critical"
    assert card.integration_target == "qms_quality_event"
    assert card.required_confirmations == (
        "product identity",
        "lot or batch",
        "quality authority",
        "shift lead approval",
    )
    assert card.evidence_fields == ("product", "quality_risk", "disposition")


def test_action_card_maps_maintenance_schedule_to_work_order_package() -> None:
    fields = {
        "machine": "Conveyor drive station",
        "evidence_needed": "Review vibration trend and released gearbox temperature threshold.",
        "action": "Schedule maintenance window for inspection.",
    }
    decision = decide_action("maintenance", fields)

    card = build_action_card("maintenance", fields, decision)

    assert card.priority == "medium"
    assert card.integration_target == "maintenance_work_order"
    assert card.owner == "maintenance_planner"
    assert "Evidence needed:" in card.operator_message


def test_integration_event_wraps_action_card_for_qms_dispatch() -> None:
    fields = {
        "product": "Machined housing lot A",
        "quality_risk": "Visible burrs near the sealing face",
        "disposition": "quality_hold",
        "action": "Hold suspect units and escalate containment to quality before continuing production.",
    }
    decision = decide_action("iqc", fields)
    card = build_action_card("iqc", fields, decision)

    event = build_integration_event(
        request_id="req-123",
        device={"device_id": "m400-demo-01", "location_hint": "line-3"},
        mode="iqc",
        fields=fields,
        action_card=card,
    )

    assert event.version == INTEGRATION_EVENT_VERSION
    assert event.event_type == "qms.quality_hold.requested"
    assert event.target == "qms_quality_event"
    assert event.status == "pending_human_confirmation"
    assert event.idempotency_key == "req-123:qms_quality_event:quality_hold"
    assert event.payload["evidence"] == {
        "product": "Machined housing lot A",
        "quality_risk": "Visible burrs near the sealing face",
        "disposition": "quality_hold",
    }


def test_integration_event_marks_pass_as_no_external_action() -> None:
    fields = {
        "product": "Clean visible product",
        "quality_risk": "No visible quality risk from the current inspection frame.",
        "disposition": "pass",
        "action": "Continue production under current inspection controls.",
    }
    decision = decide_action("iqc", fields)
    card = build_action_card("iqc", fields, decision)

    event = build_integration_event(
        request_id="req-456",
        device={"device_id": "m400-demo-01"},
        mode="iqc",
        fields=fields,
        action_card=card,
    )

    assert event.event_type == "none"
    assert event.target == "none"
    assert event.routing_key == "none"
    assert event.status == "no_external_action"
