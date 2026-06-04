from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from jetson.agently_orchestrator import run_m400_agently_workflow
from jetson.maintenance_kb import retrieve_maintenance_kb_context
from jetson.maintenance_signal_eval import evaluate_maintenance_condition


@dataclass(frozen=True)
class FakeModelResponse:
    answer: str
    latency_ms: int


def test_sensory_only_session_stays_insufficient_even_with_matched_kb() -> None:
    result = evaluate_maintenance_condition(
        session_context={
            "accepted_evidence": [
                {
                    "evidence_type": "maintenance_operator_sensory_check",
                    "fields": {
                        "unusual_noise": "low-frequency abnormal rumble near gearbox",
                        "felt_shaking": "stronger guard vibration after speed increase",
                    },
                }
            ]
        },
        knowledge_base=_matched_kb(),
        now=datetime(2026, 5, 14, tzinfo=timezone.utc),
    )

    assert result.status == "insufficient_evidence"
    assert result.risk_level == "low"
    assert result.recommended_channel == "maintenance_identification_required"
    assert result.requires_human is True
    assert result.breaches == ()
    assert "condition readings, alarm fields, or lubrication date" in result.missing_inputs
    assert {item["signal"] for item in result.observations} == {"operator_noise", "operator_vibration"}


def test_kb_no_match_blocks_threshold_breach_claims_even_with_readings() -> None:
    result = evaluate_maintenance_condition(
        session_context={
            "accepted_evidence": [
                {
                    "evidence_type": "maintenance_condition_screen_photo",
                    "fields": {
                        "vibration_rms_mm_s": "9.8",
                        "alarm_color": "yellow",
                        "alarm_code": "GBX-VIB-HI",
                    },
                },
                {
                    "evidence_type": "maintenance_temperature_gauge_photo",
                    "fields": {
                        "gearbox_temperature_c": "86",
                        "bearing_temperature_c": "77",
                    },
                },
            ]
        },
        knowledge_base={"status": "no_match", "thresholds": {}, "hits": []},
        now=datetime(2026, 5, 14, tzinfo=timezone.utc),
    )

    assert result.status == "insufficient_evidence"
    assert result.risk_level == "low"
    assert result.breaches == ()
    assert "matched maintenance KB thresholds" in result.missing_inputs
    assert result.recommended_channel == "maintenance_identification_required"


def test_within_bounds_readings_stay_condition_monitoring() -> None:
    result = evaluate_maintenance_condition(
        session_context={
            "accepted_evidence": [
                {
                    "evidence_type": "maintenance_condition_screen_photo",
                    "fields": {
                        "vibration_rms_mm_s": "4.2",
                        "alarm_color": "green",
                        "motor_current_a": "14.0",
                    },
                },
                {
                    "evidence_type": "maintenance_temperature_gauge_photo",
                    "fields": {
                        "gearbox_temperature_c": "65",
                        "bearing_temperature_c": "58",
                    },
                },
                {
                    "evidence_type": "maintenance_lubrication_record_photo",
                    "fields": {"lubrication_date": "2026-05-13"},
                },
            ]
        },
        knowledge_base=_matched_kb(),
        now=datetime(2026, 5, 14, tzinfo=timezone.utc),
    )

    assert result.status == "within_bounds"
    assert result.risk_level == "low"
    assert result.breaches == ()
    assert result.recommended_channel == "condition_monitoring"
    assert result.requires_human is False


def test_high_kb_breach_upgrades_soft_model_action_to_maintenance_report() -> None:
    seen_prompts: list[str] = []

    def infer_model(prompt: str) -> FakeModelResponse:
        seen_prompts.append(prompt)
        return FakeModelResponse(answer=_soft_monitor_answer(), latency_ms=5)

    workflow = run_m400_agently_workflow(
        prompt="Use the accepted PKG-L3-GBX-03 maintenance session evidence and stay inside maintenance route.",
        mode="maintenance",
        image_bytes=900_000,
        request_id="req-lao-shi-fu-high-guard",
        device={"device_id": "m400-robustness"},
        contract_min_words=16,
        contract_repair_enabled=True,
        current_image_min_tokens=560,
        current_image_max_tokens=560,
        audio_runtime="llama.cpp",
        model_variant="E2B",
        audio_seconds=0,
        needs_ocr=True,
        high_detail=True,
        infer_model=infer_model,
        session_context=_high_breach_session_context(),
    )

    assert workflow.contract.ok
    assert workflow.maintenance_evaluation is not None
    assert workflow.maintenance_evaluation["status"] == "breach_detected"
    assert workflow.maintenance_evaluation["risk_level"] == "high"
    assert workflow.action_card is not None
    assert workflow.action_card.channel == "maintenance_report"
    assert workflow.action_card.owner == "maintenance_engineer"
    assert workflow.integration_event is not None
    assert workflow.integration_event.target == "maintenance_work_order"
    assert "Deterministic maintenance condition evaluation" in seen_prompts[0]
    guard_stage = next(
        stage for stage in workflow.agently_trace["triggerflow"]["stages"] if stage["name"] == "maintenance_evaluation_guard"
    )
    assert guard_stage["status"] == "completed"
    assert guard_stage["final_channel"] == "maintenance_report"


def test_unknown_machine_keeps_human_confirmation_before_machine_specific_advice() -> None:
    workflow = run_m400_agently_workflow(
        prompt="Investigate the unknown drive station condition from operator note only.",
        mode="maintenance",
        image_bytes=400_000,
        request_id="req-lao-shi-fu-unknown-machine",
        device={"device_id": "m400-robustness"},
        contract_min_words=16,
        contract_repair_enabled=True,
        current_image_min_tokens=560,
        current_image_max_tokens=560,
        audio_runtime="llama.cpp",
        model_variant="E2B",
        audio_seconds=0,
        needs_ocr=True,
        high_detail=True,
        infer_model=lambda prompt: FakeModelResponse(answer=_unknown_machine_answer(), latency_ms=5),
        session_context={
            "session_id": "robustness-unknown",
            "prompt_context": (
                "Maintenance session evidence context:\n"
                "- Accepted evidence:\n"
                "  - maintenance_operator_sensory_check: abnormal noise near an unknown drive station."
            ),
            "evidence_state": {"accepted_evidence_ids": ["maintenance_operator_sensory_check"]},
            "accepted_evidence": [
                {
                    "evidence_type": "maintenance_operator_sensory_check",
                    "fields": {"unusual_noise": "abnormal noise near an unknown drive station"},
                }
            ],
        },
    )

    assert workflow.contract.ok
    assert workflow.action_card is not None
    assert workflow.action_card.channel == "maintenance_identification_required"
    assert workflow.action_card.requires_human is True
    assert workflow.integration_event is not None
    assert workflow.integration_event.target == "cmms_observation"
    assert workflow.maintenance_evaluation is not None
    assert workflow.maintenance_evaluation["status"] == "insufficient_evidence"
    assert workflow.agent_loop is not None
    assert workflow.agent_loop["context_guard"]["status"] == "human_confirm_required"


def test_full_session_prompt_stays_compact_for_jetson_context() -> None:
    seen_prompts: list[str] = []

    def infer_model(prompt: str) -> FakeModelResponse:
        seen_prompts.append(prompt)
        return FakeModelResponse(answer=_soft_monitor_answer(), latency_ms=5)

    workflow = run_m400_agently_workflow(
        prompt="Use full PKG-L3-GBX-03 evidence package before giving bounded lao-shi-fu advice.",
        mode="maintenance",
        image_bytes=2_665_413,
        request_id="req-lao-shi-fu-prompt-budget",
        device={"device_id": "m400-robustness"},
        contract_min_words=16,
        contract_repair_enabled=True,
        current_image_min_tokens=560,
        current_image_max_tokens=560,
        audio_runtime="llama.cpp",
        model_variant="E2B",
        audio_seconds=0,
        needs_ocr=True,
        high_detail=True,
        infer_model=infer_model,
        session_context=_high_breach_session_context(),
    )

    assert workflow.contract.ok
    assert seen_prompts
    assert len(seen_prompts[0]) < 8_000
    assert len(seen_prompts[0].split()) < 1_100
    assert "KB rule: reference evidence only" in seen_prompts[0]


def _matched_kb() -> dict[str, object]:
    result = retrieve_maintenance_kb_context(
        query_text="PKG-L3-GBX-03 gearbox vibration temperature bearing lubrication alarm"
    ).as_dict()
    assert result["status"] == "matched"
    return result


def _high_breach_session_context() -> dict[str, object]:
    accepted_evidence = [
        {
            "evidence_type": "maintenance_asset_identity_photo",
            "summary": "Asset plate identifies PKG-L3-GBX-03 packaging line three gearbox drive station.",
            "fields": {
                "asset_id": "PKG-L3-GBX-03",
                "line_id": "packaging-line-3",
                "station_id": "drive-station",
            },
        },
        {
            "evidence_type": "maintenance_condition_screen_photo",
            "summary": "Condition screen shows high vibration trend and yellow gearbox vibration alarm.",
            "fields": {
                "vibration_rms_mm_s": "7.2",
                "alarm_color": "yellow",
                "alarm_code": "GBX-VIB-HI",
                "motor_current_a": "18.4",
                "load_pct": "82",
                "speed_rpm": "1460",
            },
        },
        {
            "evidence_type": "maintenance_temperature_gauge_photo",
            "summary": "Temperature gauges show elevated gearbox and bearing values.",
            "fields": {
                "motor_temperature_c": "64",
                "bearing_temperature_c": "71",
                "gearbox_temperature_c": "78",
            },
        },
        {
            "evidence_type": "maintenance_lubrication_record_photo",
            "summary": "Lubrication record shows last service on 2026-05-07 for GBX-03.",
            "fields": {
                "lubrication_date": "2026-05-07",
                "lubrication_point": "GBX-03",
                "lubricant_type": "gear oil",
            },
        },
        {
            "evidence_type": "maintenance_recent_work_record_photo",
            "summary": "Recent work record says vibration inspection completed and bearing condition not confirmed.",
            "fields": {
                "last_maintenance_date": "2026-05-10",
                "last_repair_action": "vibration inspection",
                "open_issue": "monitor gearbox vibration",
            },
        },
        {
            "evidence_type": "maintenance_operator_sensory_check",
            "summary": "Operator reports abnormal rumble, warm oil smell, stronger guard vibration, and small oil stain.",
            "fields": {
                "unusual_noise": "low-frequency abnormal rumble near gearbox",
                "unusual_smell": "slight warm oil smell",
                "felt_heat": "gearbox housing feels warmer than usual but not burning hot",
                "felt_shaking": "stronger vibration felt on guard panel after speed increase",
                "visible_leak": "small oil stain near gearbox base",
            },
        },
    ]
    prompt_lines = [
        "Maintenance session evidence context:",
        "- Accepted evidence:",
        *[f"  - {item['evidence_type']}: {item['summary']}" for item in accepted_evidence],
    ]
    return {
        "session_id": "robustness-high-breach",
        "prompt_context": "\n".join(prompt_lines),
        "evidence_state": {"accepted_evidence_ids": [str(item["evidence_type"]) for item in accepted_evidence]},
        "accepted_evidence": accepted_evidence,
        "missing_requested_evidence_ids": [],
    }


def _soft_monitor_answer() -> str:
    return (
        "- Machine: Packaging Line Three drive station PKG-L3-GBX-03 with session evidence from the operator and M400 capture.\n"
        "- Symptom: The available session package describes a machine condition concern that should be reviewed without claiming a final cause.\n"
        "- Maintenance Risk: Continued operation may increase wear and downtime exposure if the accepted evidence package is ignored by maintenance.\n"
        "- Evidence Needed: Compare accepted session evidence with the released maintenance knowledge base and keep missing telemetry explicit before release.\n"
        "- Action: Monitor the gearbox condition at the station and keep the evidence package visible for the next maintenance review."
    )


def _unknown_machine_answer() -> str:
    return (
        "- Machine: Unknown equipment near the drive station because no readable asset plate or station identifier is available.\n"
        "- Symptom: Operator note describes abnormal noise near an unidentified drive area without confirmed readings or matched machine context.\n"
        "- Maintenance Risk: Machine-specific risk cannot be bounded until identity, condition readings, and released maintenance thresholds are confirmed by maintenance.\n"
        "- Evidence Needed: Capture the asset plate, station sign, condition screen, gauge readings, and released manual source before advice is trusted.\n"
        "- Action: Monitor from a safe observation point and confirm the machine identity before applying any machine-specific maintenance guidance."
    )
