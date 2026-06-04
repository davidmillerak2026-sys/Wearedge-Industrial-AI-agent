from __future__ import annotations

from dataclasses import dataclass

import pytest

from jetson.agently_orchestrator import run_m400_agently_workflow


@dataclass(frozen=True)
class FakeModelResponse:
    answer: str
    latency_ms: int


@dataclass(frozen=True)
class MaintenanceExample:
    name: str
    prompt: str
    session_context: dict[str, object]
    answer: str
    expected_kb_status: str
    expected_eval_status: str
    expected_risk_level: str
    expected_channel: str
    expected_target: str
    expected_requires_human: bool


def _examples() -> list[MaintenanceExample]:
    return [
        MaintenanceExample(
            name="normal_green_shift_check",
            prompt="Assess routine condition evidence for PKG-L3-GBX-03 before the next production speed increase.",
            session_context=_session(
                "normal-green",
                _asset("PKG-L3-GBX-03"),
                _condition(vibration="4.1", alarm_color="green", load="64", speed="1320"),
                _temperature(gearbox="62", bearing="55", motor="59"),
                _operator_note(noise="no unusual noise", smell="no oil smell", shaking="normal guard vibration"),
            ),
            answer=_answer(
                machine="Packaging Line Three drive station PKG-L3-GBX-03 with asset plate and normal operator observation evidence.",
                symptom="Session readings show normal vibration, normal housing temperature, green alarm state, and no abnormal operator sensory report.",
                risk="Current evidence suggests low equipment wear risk, but trend should remain visible because conditions can change after speed increase.",
                evidence="Keep the condition screen, temperature gauge, asset identity, and operator note attached for the next routine comparison.",
                action="Monitor the gearbox trend during the next production interval and keep routine evidence attached for maintenance visibility.",
            ),
            expected_kb_status="matched",
            expected_eval_status="within_bounds",
            expected_risk_level="low",
            expected_channel="condition_monitoring",
            expected_target="cmms_observation",
            expected_requires_human=False,
        ),
        MaintenanceExample(
            name="vibration_high_without_alarm",
            prompt="Assess vibration rise on PKG-L3-GBX-03 while PLC alarm remains normal.",
            session_context=_session(
                "vibration-only",
                _asset("PKG-L3-GBX-03"),
                _condition(vibration="6.9", alarm_color="green", load="78", speed="1460"),
                _temperature(gearbox="66", bearing="61", motor="60"),
            ),
            answer=_answer(
                machine="Packaging Line Three drive station PKG-L3-GBX-03 with condition monitor and asset identity evidence.",
                symptom="Vibration trend is above the normal watch band while alarm state and temperature readings remain otherwise stable.",
                risk="Single-signal vibration rise may indicate early imbalance, looseness, coupling wear, or process load change requiring confirmation.",
                evidence="Compare the current vibration value against manual threshold, trend history, mounting condition, and recent operating load.",
                action="Inspect mounting bolts, coupling alignment, and vibration trend before approving any further speed increase on this station.",
            ),
            expected_kb_status="matched",
            expected_eval_status="breach_detected",
            expected_risk_level="medium",
            expected_channel="condition_inspection",
            expected_target="cmms_observation",
            expected_requires_human=False,
        ),
        MaintenanceExample(
            name="yellow_alarm_no_high_temperature",
            prompt="Assess yellow PLC warning evidence for PKG-L3-GBX-03 with temperatures still normal.",
            session_context=_session(
                "yellow-alarm",
                _asset("PKG-L3-GBX-03"),
                _condition(vibration="5.8", alarm_color="yellow", alarm_code="GBX-VIB-HI", load="70", speed="1400"),
                _temperature(gearbox="65", bearing="60", motor="58"),
            ),
            answer=_answer(
                machine="Packaging Line Three drive station PKG-L3-GBX-03 with warning screen and asset plate evidence.",
                symptom="The session package shows a warning state while temperature and visible load evidence have not crossed high limits.",
                risk="The warning state may represent early vibration abnormality, sensor threshold approach, or process change needing inspection evidence.",
                evidence="Compare warning code, vibration trend, alarm history, and manual alarm threshold before assigning a machine cause.",
                action="Keep the machine under observation and request a condition inspection before any planned speed or load increase.",
            ),
            expected_kb_status="matched",
            expected_eval_status="breach_detected",
            expected_risk_level="medium",
            expected_channel="condition_inspection",
            expected_target="cmms_observation",
            expected_requires_human=False,
        ),
        MaintenanceExample(
            name="gearbox_temperature_at_limit",
            prompt="Assess gearbox heat on PKG-L3-GBX-03 with vibration still controlled.",
            session_context=_session(
                "gearbox-temp",
                _asset("PKG-L3-GBX-03"),
                _condition(vibration="5.1", alarm_color="green", load="76", speed="1440"),
                _temperature(gearbox="75", bearing="63", motor="62"),
                _operator_note(heat="housing feels warmer than morning baseline"),
            ),
            answer=_answer(
                machine="Packaging Line Three drive station PKG-L3-GBX-03 with temperature gauge, condition screen, and operator note.",
                symptom="Gearbox housing temperature is at the maintenance watch threshold while vibration and bearing temperature are less severe.",
                risk="Temperature at threshold can indicate lubricant condition, load, cooling, or alignment stress and needs bounded confirmation.",
                evidence="Compare manual temperature threshold, operating load, lubricant record, repeated gauge reading, and technician inspection before assigning cause.",
                action="Keep the current operating condition bounded and request inspection of lubrication state and repeated temperature reading.",
            ),
            expected_kb_status="matched",
            expected_eval_status="breach_detected",
            expected_risk_level="medium",
            expected_channel="condition_inspection",
            expected_target="cmms_observation",
            expected_requires_human=False,
        ),
        MaintenanceExample(
            name="bearing_heat_with_vibration",
            prompt="Assess combined bearing heat and vibration evidence for PKG-L3-GBX-03.",
            session_context=_session(
                "bearing-heat-vibration",
                _asset("PKG-L3-GBX-03"),
                _condition(vibration="7.1", alarm_color="green", load="82", speed="1460"),
                _temperature(gearbox="69", bearing="72", motor="63"),
                _operator_note(noise="low rumble near bearing side", shaking="stronger guard vibration"),
            ),
            answer=_answer(
                machine="Packaging Line Three drive station PKG-L3-GBX-03 with bearing temperature and vibration evidence attached.",
                symptom="The session package shows elevated vibration and bearing-side heat with operator rumble and stronger guard vibration observations.",
                risk="Combined vibration and bearing heat create increased risk of accelerated bearing wear and unplanned gearbox downtime.",
                evidence="Confirm bearing temperature trend, vibration history, alignment state, lubrication condition, recent maintenance record, and technician inspection.",
                action="Monitor the gearbox condition and keep the evidence package visible while maintenance reviews the combined condition.",
            ),
            expected_kb_status="matched",
            expected_eval_status="breach_detected",
            expected_risk_level="high",
            expected_channel="maintenance_report",
            expected_target="maintenance_work_order",
            expected_requires_human=True,
        ),
        MaintenanceExample(
            name="overdue_lubrication_oil_smell",
            prompt="Assess oil smell and lubrication record evidence for PKG-L3-GBX-03.",
            session_context=_session(
                "overdue-lube",
                _asset("PKG-L3-GBX-03"),
                _condition(vibration="5.4", alarm_color="green", load="72", speed="1380"),
                _temperature(gearbox="67", bearing="61", motor="60"),
                _lubrication("2000-01-01"),
                _operator_note(smell="warm oil smell near gearbox base", leak="small oil stain near GBX-03"),
            ),
            answer=_answer(
                machine="Packaging Line Three drive station PKG-L3-GBX-03 with lubrication record and operator sensory evidence.",
                symptom="Lubrication record appears overdue while operator reports warm oil smell and a small oil stain near the base.",
                risk="Delayed lubrication with oil smell can increase gear mesh wear, seal leakage, heat buildup, and follow-on downtime risk.",
                evidence="Compare lubrication interval, oil level, seal condition, lubricant type, and recent work record before assigning cause.",
                action="Keep the condition bounded and request inspection of lubricant level, seal area, and lubrication record accuracy.",
            ),
            expected_kb_status="matched",
            expected_eval_status="breach_detected",
            expected_risk_level="medium",
            expected_channel="condition_inspection",
            expected_target="cmms_observation",
            expected_requires_human=False,
        ),
        MaintenanceExample(
            name="full_high_risk_schedule_window",
            prompt="Assess full high-risk evidence package for PKG-L3-GBX-03 and recommend bounded maintenance action.",
            session_context=_session(
                "full-high-risk",
                _asset("PKG-L3-GBX-03"),
                _condition(vibration="7.2", alarm_color="yellow", alarm_code="GBX-VIB-HI", load="82", speed="1460"),
                _temperature(gearbox="78", bearing="71", motor="64"),
                _lubrication("2000-01-01"),
                _work_record("2026-05-10", "vibration inspection", "bearing condition not yet confirmed"),
                _operator_note(
                    noise="low-frequency rumble near gearbox",
                    smell="slight warm oil smell",
                    heat="housing warmer than usual",
                    shaking="stronger guard vibration after speed increase",
                ),
            ),
            answer=_answer(
                machine="Packaging Line Three drive station PKG-L3-GBX-03 with full session evidence and matched maintenance KB.",
                symptom="Evidence shows elevated vibration, warning alarm, elevated gearbox and bearing heat, overdue lubrication, and abnormal operator observations.",
                risk="Multiple concurrent condition breaches create high risk of accelerated gearbox or bearing wear and unplanned downtime.",
                evidence="Confirm manual thresholds, telemetry trend, lubrication condition, alignment state, and open work order history before release.",
                action="Schedule a maintenance window and keep production from increasing speed until maintenance engineering reviews the evidence package.",
            ),
            expected_kb_status="matched",
            expected_eval_status="breach_detected",
            expected_risk_level="high",
            expected_channel="schedule_maintenance",
            expected_target="maintenance_work_order",
            expected_requires_human=True,
        ),
        MaintenanceExample(
            name="wrong_asset_blocks_kb_thresholds",
            prompt="Assess high readings for PKG-L4-GBX-99 without applying another machine knowledge base.",
            session_context=_session(
                "wrong-asset",
                _asset("PKG-L4-GBX-99"),
                _condition(vibration="8.0", alarm_color="yellow", alarm_code="GBX-VIB-HI", load="83", speed="1460"),
                _temperature(gearbox="80", bearing="74", motor="66"),
            ),
            answer=_answer(
                machine="Packaging Line Four drive station PKG-L4-GBX-99 with high readings but no matched released KB.",
                symptom="Visible readings look abnormal, but the machine identity does not match the available PKG-L3 maintenance knowledge source.",
                risk="Applying the wrong threshold source could create an unsafe recommendation or false work order for this different asset.",
                evidence="Confirm the correct asset knowledge base, released manual thresholds, maintenance authority, station identity, and calibration source before interpreting readings.",
                action="Monitor the condition from the station and hold machine-specific recommendation until the correct asset knowledge base is confirmed.",
            ),
            expected_kb_status="no_match",
            expected_eval_status="insufficient_evidence",
            expected_risk_level="low",
            expected_channel="maintenance_identification_required",
            expected_target="cmms_observation",
            expected_requires_human=True,
        ),
        MaintenanceExample(
            name="no_asset_plate_blocks_machine_specific_advice",
            prompt="Assess high gearbox readings without readable asset plate or station sign.",
            session_context=_session(
                "no-asset",
                _condition(vibration="7.8", alarm_color="yellow", alarm_code="GBX-VIB-HI", load="80", speed="1450"),
                _temperature(gearbox="79", bearing="72", motor="65"),
                _operator_note(noise="abnormal rumble near unidentified gearbox station"),
            ),
            answer=_answer(
                machine="Unknown gearbox drive station because no readable asset plate or station sign is visible in evidence.",
                symptom="Readings appear abnormal, but the equipment identity is not confirmed and no machine-specific KB can be trusted.",
                risk="Machine-specific risk cannot be bounded because thresholds, allowed load, station identity, and maintenance authority are missing.",
                evidence="Capture asset plate, station sign, released manual source, and repeated condition screen before applying machine-specific guidance.",
                action="Monitor from a safe observation point and confirm the machine identity before applying any maintenance recommendation.",
            ),
            expected_kb_status="no_match",
            expected_eval_status="insufficient_evidence",
            expected_risk_level="low",
            expected_channel="maintenance_identification_required",
            expected_target="cmms_observation",
            expected_requires_human=True,
        ),
        MaintenanceExample(
            name="red_trip_with_temperature_spike",
            prompt="Assess red trip and heat evidence for PKG-L3-GBX-03 within the maintenance route.",
            session_context=_session(
                "red-trip-temp",
                _asset("PKG-L3-GBX-03"),
                _condition(vibration="5.9", alarm_color="red", alarm_code="GBX-TRIP", load="88", speed="1460"),
                _temperature(gearbox="79", bearing="67", motor="68"),
                _operator_note(smell="hot oil smell near gearbox guard", heat="housing feels hot compared with baseline"),
            ),
            answer=_answer(
                machine="Packaging Line Three drive station PKG-L3-GBX-03 with red trip evidence and temperature gauge reading.",
                symptom="The station shows a red trip condition with gearbox heat and operator hot-oil smell observation near the guard.",
                risk="Trip condition with heat can indicate severe machine condition escalation and must not be treated as routine monitoring.",
                evidence="Confirm trip log, released alarm meaning, repeated temperature reading, and maintenance authority before any restart discussion.",
                action="Stop the machine condition review path and escalate the evidence package to maintenance engineering before restart consideration.",
            ),
            expected_kb_status="matched",
            expected_eval_status="breach_detected",
            expected_risk_level="medium",
            expected_channel="maintenance_stop",
            expected_target="maintenance_work_order",
            expected_requires_human=True,
        ),
    ]


def _session(session_id: str, *items: dict[str, object]) -> dict[str, object]:
    evidence = list(items)
    prompt_lines = [
        "Maintenance session evidence context:",
        "- Accepted evidence:",
        *[f"  - {item['evidence_type']}: {item['summary']}" for item in evidence],
    ]
    return {
        "session_id": session_id,
        "prompt_context": "\n".join(prompt_lines),
        "evidence_state": {"accepted_evidence_ids": [str(item["evidence_type"]) for item in evidence]},
        "accepted_evidence": evidence,
        "missing_requested_evidence_ids": [],
    }


def _asset(asset_id: str) -> dict[str, object]:
    return {
        "evidence_type": "maintenance_asset_identity_photo",
        "summary": f"Asset plate identifies {asset_id} at the gearbox drive station.",
        "fields": {"asset_id": asset_id, "station_id": "drive-station"},
    }


def _condition(
    *,
    vibration: str,
    alarm_color: str,
    alarm_code: str = "",
    load: str,
    speed: str,
) -> dict[str, object]:
    fields = {
        "vibration_rms_mm_s": vibration,
        "alarm_color": alarm_color,
        "load_pct": load,
        "speed_rpm": speed,
    }
    if alarm_code:
        fields["alarm_code"] = alarm_code
    return {
        "evidence_type": "maintenance_condition_screen_photo",
        "summary": f"Condition screen shows vibration RMS {vibration} mm/s, {alarm_color} alarm state, load {load} percent, speed {speed} rpm.",
        "fields": fields,
    }


def _temperature(*, gearbox: str, bearing: str, motor: str) -> dict[str, object]:
    return {
        "evidence_type": "maintenance_temperature_gauge_photo",
        "summary": f"Temperature gauge shows gearbox {gearbox} C, bearing {bearing} C, and motor {motor} C.",
        "fields": {
            "gearbox_temperature_c": gearbox,
            "bearing_temperature_c": bearing,
            "motor_temperature_c": motor,
        },
    }


def _lubrication(date: str) -> dict[str, object]:
    return {
        "evidence_type": "maintenance_lubrication_record_photo",
        "summary": f"Lubrication record lists last gearbox service date as {date}.",
        "fields": {
            "lubrication_date": date,
            "lubrication_point": "GBX-03",
            "lubricant_type": "gear oil",
        },
    }


def _work_record(date: str, action: str, note: str) -> dict[str, object]:
    return {
        "evidence_type": "maintenance_recent_work_record_photo",
        "summary": f"Recent work record from {date} shows {action}, with note: {note}.",
        "fields": {
            "last_maintenance_date": date,
            "last_repair_action": action,
            "technician_note": note,
        },
    }


def _operator_note(
    *,
    noise: str = "",
    smell: str = "",
    heat: str = "",
    shaking: str = "",
    leak: str = "",
) -> dict[str, object]:
    fields = {
        "unusual_noise": noise,
        "unusual_smell": smell,
        "felt_heat": heat,
        "felt_shaking": shaking,
        "visible_leak": leak,
    }
    clean_fields = {key: value for key, value in fields.items() if value}
    summary = "; ".join(clean_fields.values()) if clean_fields else "Operator reports no abnormal sensory observation."
    return {
        "evidence_type": "maintenance_operator_sensory_check",
        "summary": summary,
        "fields": clean_fields,
    }


def _answer(*, machine: str, symptom: str, risk: str, evidence: str, action: str) -> str:
    return (
        f"- Machine: {machine}\n"
        f"- Symptom: {symptom}\n"
        f"- Maintenance Risk: {risk}\n"
        f"- Evidence Needed: {evidence}\n"
        f"- Action: {action}"
    )


@pytest.mark.parametrize("example", _examples(), ids=lambda example: example.name)
def test_lao_shi_fu_realistic_examples_route_safely(example: MaintenanceExample) -> None:
    workflow = run_m400_agently_workflow(
        prompt=example.prompt,
        mode="maintenance",
        image_bytes=1_200_000,
        request_id=f"req-{example.name}",
        device={"device_id": "m400-realistic-examples", "location_hint": "line-3-drive-station"},
        contract_min_words=16,
        contract_repair_enabled=True,
        current_image_min_tokens=560,
        current_image_max_tokens=560,
        audio_runtime="llama.cpp",
        model_variant="E2B",
        audio_seconds=0,
        needs_ocr=True,
        high_detail=True,
        infer_model=lambda prompt: FakeModelResponse(answer=example.answer, latency_ms=5),
        session_context=example.session_context,
    )

    assert workflow.contract.ok
    assert workflow.knowledge_base is not None
    assert workflow.knowledge_base["status"] == example.expected_kb_status
    assert workflow.maintenance_evaluation is not None
    assert workflow.maintenance_evaluation["status"] == example.expected_eval_status
    assert workflow.maintenance_evaluation["risk_level"] == example.expected_risk_level
    assert workflow.action_card is not None
    assert workflow.action_card.channel == example.expected_channel
    assert workflow.action_card.integration_target == example.expected_target
    assert workflow.action_card.requires_human is example.expected_requires_human
    assert workflow.integration_event is not None
    assert workflow.integration_event.target == example.expected_target
    assert workflow.runtime_stream["closed"] is True
