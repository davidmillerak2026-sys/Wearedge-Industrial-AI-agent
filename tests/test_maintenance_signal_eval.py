from __future__ import annotations

from datetime import datetime, timezone

from jetson.maintenance_kb import retrieve_maintenance_kb_context
from jetson.maintenance_signal_eval import (
    MAINTENANCE_EVALUATION_VERSION,
    build_maintenance_condition_prompt_context,
    evaluate_maintenance_condition,
)


def test_maintenance_condition_evaluation_flags_kb_threshold_breaches() -> None:
    kb = retrieve_maintenance_kb_context(
        query_text="PKG-L3-GBX-03 vibration RMS 7.2 yellow alarm gearbox 78 bearing 71 oil smell"
    ).as_dict()
    result = evaluate_maintenance_condition(
        session_context={
            "accepted_evidence": [
                {
                    "evidence_type": "maintenance_condition_screen_photo",
                    "fields": {
                        "vibration_rms_mm_s": "7.2",
                        "alarm_color": "yellow",
                        "alarm_code": "GBX-VIB-HI",
                    },
                },
                {
                    "evidence_type": "maintenance_temperature_gauge_photo",
                    "fields": {
                        "gearbox_temperature_c": "78",
                        "bearing_temperature_c": "71",
                    },
                },
                {
                    "evidence_type": "maintenance_lubrication_record_photo",
                    "fields": {"lubrication_date": "2026-05-07"},
                },
                {
                    "evidence_type": "maintenance_operator_sensory_check",
                    "fields": {
                        "unusual_noise": "low-frequency abnormal rumble",
                        "unusual_smell": "slight warm oil smell",
                        "felt_shaking": "stronger guard vibration",
                    },
                },
            ]
        },
        knowledge_base=kb,
        now=datetime(2026, 5, 14, tzinfo=timezone.utc),
    )
    as_dict = result.as_dict()
    breach_signals = {breach["signal"] for breach in as_dict["breaches"]}
    prompt_context = build_maintenance_condition_prompt_context(result)

    assert as_dict["version"] == MAINTENANCE_EVALUATION_VERSION
    assert as_dict["status"] == "breach_detected"
    assert as_dict["risk_level"] == "high"
    assert as_dict["recommended_channel"] == "maintenance_report"
    assert "vibration_rms_mm_s" in breach_signals
    assert "gearbox_temperature_c" in breach_signals
    assert "bearing_temperature_c" in breach_signals
    assert "plc_alarm" in breach_signals
    assert "lubrication_interval_days" in breach_signals
    assert "PM-KB-2026.05-demo#GBX-VIB-01" in as_dict["threshold_source_ids"]
    assert "Deterministic maintenance condition evaluation" in prompt_context
    assert "no RCA, RUL, restart permission, or maintenance release" in prompt_context


def test_maintenance_condition_evaluation_blocks_when_kb_or_session_is_missing() -> None:
    result = evaluate_maintenance_condition(
        session_context=None,
        knowledge_base={"status": "no_match", "thresholds": {}, "hits": []},
        now=datetime(2026, 5, 14, tzinfo=timezone.utc),
    )

    assert result.status == "insufficient_evidence"
    assert result.risk_level == "low"
    assert result.recommended_channel == "maintenance_identification_required"
    assert "accepted maintenance session evidence" in result.missing_inputs
    assert "matched maintenance KB thresholds" in result.missing_inputs
