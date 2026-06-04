from __future__ import annotations

from dataclasses import dataclass

import pytest

from jetson.agently_orchestrator import (
    AGENTLY_FLOW_DEFINITION_VERSION,
    AGENTLY_RUNTIME_STREAM_VERSION,
    AGENTLY_TRACE_VERSION,
    export_m400_flow_definition,
    run_m400_agently_workflow,
)


@dataclass(frozen=True)
class FakeModelResponse:
    answer: str
    latency_ms: int


@pytest.mark.parametrize(
    ("mode", "answer", "expected_fields", "expected_target"),
    [
        (
            "hazard",
            (
                "- Scene: Operator is working beside a guarded press station with boxes, loose packaging, and a narrow walking path near the controls.\n"
                "- Risk: Trip obstruction and hand placement near the guarded motion area could increase exposure during material handling or restart.\n"
                "- Action: Inspect the walking path, remove loose packaging, and confirm the guard and controls are clear before continuing the task."
            ),
            ("scene", "risk", "action"),
            "safety_observation",
        ),
        (
            "maintenance",
            (
                "- Machine: Stamping press line station three with visible hydraulic hoses, guard panels, operator controls, and accumulated residue near the base.\n"
                "- Symptom: Visible residue and staining near the hydraulic area suggest a possible leak indicator but no hidden pressure readings are available.\n"
                "- Maintenance Risk: Potential hydraulic leakage or lubrication degradation could create uptime risk, contamination, and escalating component wear if ignored.\n"
                "- Evidence Needed: Inspect the maintenance manual leak points, recent alarm logs, pressure trend, and operator observations before assigning cause.\n"
                "- Action: Inspect the hose fittings, residue source, and recent pressure trend before deciding whether maintenance scheduling is required."
            ),
            ("machine", "symptom", "maintenance_risk", "evidence_needed", "action"),
            "cmms_observation",
        ),
        (
            "iqc",
            (
                "- Product: Machined aluminum housing shows visible edge burrs, uneven surface marks, and possible handling contamination near the sealing face.\n"
                "- Quality Risk: Burrs or contamination on the sealing face could create assembly leakage, downstream rework, and customer escape risk.\n"
                "- Disposition: expand_inspection\n"
                "- Action: Expand inspection to adjacent units from the same station lot and shift while holding suspect housings for quality engineer review."
            ),
            ("product", "quality_risk", "disposition", "action"),
            "qms_quality_event",
        ),
        (
            "wi",
            (
                "- Machine: Cartoner station two appears visible with operator panel, infeed guide, guard door, and product transfer area in view.\n"
                "- Work Instruction: Verify the visible guide alignment, confirm the correct work instruction revision, and keep hands outside guarded transfer areas.\n"
                "- Risk Control: Safety guard status, product orientation, tooling clearance, and escalation rules must be respected before touching machine settings.\n"
                "- Action: Confirm the machine identity and current work instruction revision before following the visible setup guidance at the station."
            ),
            ("machine", "work_instruction", "risk_control", "action"),
            "wi_reference",
        ),
        (
            "changeover",
            (
                "- Machine: Filling line station one with change parts, control panel, label reference, and product guide rails visible near the operator.\n"
                "- SKU: Target SKU is not fully readable, but a visible label reference and change part tray indicate conversion activity.\n"
                "- Changeover Step: Confirm line clearance, match the visible change parts to the approved checklist, and avoid changing hidden recipe parameters.\n"
                "- Verification: Check machine identity, target SKU evidence, guide alignment, label match, and first-piece verification before restart authorization.\n"
                "- Action: Confirm the target SKU evidence and checklist step with operator quality before restarting the converted station."
            ),
            ("machine", "sku", "changeover_step", "verification", "action"),
            "changeover_checklist",
        ),
    ],
)
def test_agently_workflow_accepts_all_five_agent_modes(
    mode: str,
    answer: str,
    expected_fields: tuple[str, ...],
    expected_target: str,
) -> None:
    workflow = run_m400_agently_workflow(
        prompt="Assess the current M400 image.",
        mode=mode,
        image_bytes=900_000,
        request_id=f"req-{mode}",
        device={"device_id": "m400-demo-01"},
        contract_min_words=16,
        contract_repair_enabled=True,
        current_image_min_tokens=560,
        current_image_max_tokens=560,
        audio_runtime="llama.cpp",
        model_variant="E2B",
        audio_seconds=0,
        needs_ocr=True,
        high_detail=True,
        infer_model=lambda prompt: FakeModelResponse(answer=answer, latency_ms=9),
    )

    assert workflow.mode == mode
    assert workflow.contract.ok
    assert set(expected_fields).issubset(workflow.fields)
    assert workflow.action_card is not None
    assert workflow.action_card.integration_target == expected_target
    assert workflow.evidence_plan["mode"] == mode
    assert workflow.evidence_plan["missing_tools"]
    assert workflow.tool_plan["mode"] == mode
    assert workflow.tool_plan["status"] == "missing_tool_connections"
    assert workflow.integration_event is not None
    assert workflow.integration_event.target == expected_target
    assert workflow.agent_loop is not None
    assert workflow.agent_loop["mode"] == mode
    assert workflow.agently_trace["version"] == AGENTLY_TRACE_VERSION
    assert workflow.agently_trace["triggerflow"]["definition_id"] == "m400_infer"
    assert workflow.agently_trace["triggerflow"]["execution_state"] == "closed"
    assert workflow.runtime_stream["version"] == AGENTLY_RUNTIME_STREAM_VERSION
    assert workflow.runtime_stream["mode"] == mode
    assert workflow.runtime_stream["closed"] is True


def test_agently_workflow_returns_trace_and_action_outputs() -> None:
    answer = (
        "- Product: Machined aluminum housing shows visible edge burrs uneven surface marks and possible handling contamination near the sealing face.\n"
        "- Quality Risk: Burrs or contamination on the sealing face could create assembly leakage escapes and downstream rework risk.\n"
        "- Disposition: quality_hold\n"
        "- Action: Hold suspect housings from the same station lot and shift while quality reviews containment evidence before release."
    )

    workflow = run_m400_agently_workflow(
        prompt="Assess product quality.",
        mode="iqc",
        image_bytes=900_000,
        request_id="req-001",
        device={"device_id": "m400-demo-01"},
        contract_min_words=16,
        contract_repair_enabled=True,
        current_image_min_tokens=70,
        current_image_max_tokens=70,
        audio_runtime="llama.cpp",
        model_variant="E2B",
        audio_seconds=0,
        needs_ocr=False,
        high_detail=False,
        infer_model=lambda prompt: FakeModelResponse(answer=answer, latency_ms=11),
    )

    assert workflow.contract.ok
    assert workflow.fields["disposition"] == "quality_hold"
    assert workflow.action_card is not None
    assert workflow.action_card.integration_target == "qms_quality_event"
    assert workflow.integration_event is not None
    assert workflow.integration_event.idempotency_key == "req-001:qms_quality_event:quality_hold"
    assert workflow.modality_plan["visual_token_budget"]["status"] == "requires_server_restart"
    assert workflow.agently_trace["version"] == AGENTLY_TRACE_VERSION
    assert workflow.agently_trace["triggerflow"]["definition_version"] == AGENTLY_FLOW_DEFINITION_VERSION
    assert workflow.runtime_stream["request_id"] == "req-001"
    assert workflow.runtime_stream["definition_version"] == AGENTLY_FLOW_DEFINITION_VERSION
    runtime_events = [event["event"] for event in workflow.runtime_stream["events"]]
    assert "model.call.completed" in runtime_events
    assert "tool.call.skipped" in runtime_events
    assert "contract.validation.completed" in runtime_events
    assert "action.card.created" in runtime_events
    assert "follow_up.plan.created" in runtime_events
    assert "integration.event.created" in runtime_events
    assert runtime_events[-1] == "workflow.closed"
    stage_names = [stage["name"] for stage in workflow.agently_trace["triggerflow"]["stages"]]
    assert stage_names == [
        "normalize_agent",
        "select_agent_route",
        "plan_modality",
        "collect_evidence",
        "load_session_evidence",
        "retrieve_maintenance_kb",
        "retrieve_iqc_quality_plan",
        "load_visual_defect_detector_evidence",
        "retrieve_released_wi_source",
        "retrieve_changeover_checklist",
        "evaluate_maintenance_thresholds",
        "bounded_react_tools",
        "build_contract_prompt",
        "model_infer",
        "validate_contract",
        "repair_contract",
        "identify_context",
        "resolve_iqc_quality_plan_from_fields",
        "resolve_released_source_from_fields",
        "structure_action",
        "uncertainty_guard",
        "evaluate_iqc_quality_rules",
        "evaluate_released_source",
        "maintenance_evaluation_guard",
        "iqc_quality_guard",
        "released_source_guard",
        "build_action_card",
        "build_follow_up_plan",
        "build_integration_event",
        "close_execution",
    ]


def test_agently_workflow_uses_iqc_detector_evidence_for_quality_guard() -> None:
    answer = (
        "- Product: AL-HOUSING-L3 machined aluminum housing from line three machining output station under M400 inspection with visible lot label.\n"
        "- Quality Risk: Detector evidence shows edge burr and sealing face scratch on the inspected product, creating leakage and assembly escape risk.\n"
        "- Disposition: needs_review\n"
        "- Action: Inspect suspect units and hold them while quality reviews detector boxes and confirms containment scope for this station lot."
    )
    seen_prompts: list[str] = []

    def infer_model(prompt: str) -> FakeModelResponse:
        seen_prompts.append(prompt)
        return FakeModelResponse(answer=answer, latency_ms=12)

    workflow = run_m400_agently_workflow(
        prompt="Assess IQC product AL-HOUSING-L3 using detector evidence.",
        mode="iqc",
        image_bytes=900_000,
        request_id="req-iqc-detector",
        device={"device_id": "m400-demo-01"},
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
        detector_evidence={
            "source": "simulated_m400_detector",
            "product_id": "AL-HOUSING-L3",
            "detections": [
                {
                    "class": "edge_burr",
                    "confidence": 0.73,
                    "bbox": [180, 450, 330, 535],
                },
                {
                    "class": "sealing_face_scratch",
                    "confidence": 0.84,
                    "bbox": [610, 335, 775, 435],
                },
            ],
        },
    )

    assert "Visual defect detector evidence" in seen_prompts[0]
    assert workflow.detector_evidence is not None
    assert workflow.detector_evidence["status"] == "available"
    assert workflow.tool_plan["used_tool_calls"] == 2
    assert workflow.quality_evaluation is not None
    assert workflow.quality_evaluation["detector_status"] == "provided"
    assert workflow.quality_evaluation["recommended_channel"] == "quality_hold"
    assert workflow.action_card is not None
    assert workflow.action_card.channel == "quality_hold"
    assert workflow.integration_event is not None
    assert workflow.integration_event.payload["detector_evidence"]["detection_count"] == 2
    action_logs = workflow.agently_trace["action_runtime"]["action_logs"]
    assert any(
        log["stage"] == "load_visual_defect_detector_evidence" and log["status"] == "completed"
        for log in action_logs
    )


def test_agently_workflow_uses_released_wi_source_for_guidance() -> None:
    answer = (
        "- Machine: CARTONER-ST2 cartoner station two with visible operator panel infeed guide guard door and carton transfer area.\n"
        "- Work Instruction: Follow the released guide alignment instruction for the infeed rails and confirm the current WI revision before adjustment.\n"
        "- Risk Control: Keep guards closed verify no active alarm preserve tooling clearance and escalate repeated jams or abnormal vibration.\n"
        "- Action: Follow the released guide marks while keeping guards closed and reporting repeated carton skew to the line lead."
    )
    seen_prompts: list[str] = []

    def infer_model(prompt: str) -> FakeModelResponse:
        seen_prompts.append(prompt)
        return FakeModelResponse(answer=answer, latency_ms=10)

    workflow = run_m400_agently_workflow(
        prompt="Operator asks about Cartoner station two guide alignment near the guard door.",
        mode="wi",
        image_bytes=700_000,
        request_id="req-wi-source",
        device={"device_id": "m400-demo-01"},
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
    )

    assert "Released WI source context" in seen_prompts[0]
    assert workflow.knowledge_base is not None
    assert workflow.knowledge_base["status"] == "matched"
    assert workflow.source_evaluation is not None
    assert workflow.source_evaluation["status"] == "released_source_matched"
    assert workflow.action_card is not None
    assert workflow.action_card.channel == "guided_operation"
    assert workflow.integration_event is not None
    assert workflow.integration_event.payload["source_evaluation"]["source_status"] == "matched"


def test_agently_workflow_blocks_changeover_without_released_source() -> None:
    answer = (
        "- Machine: Filling line station one labeler with visible HMI recipe screen guide rails label roll and change part tray.\n"
        "- SKU: Target SKU is SKU-X999 from the traveler but no released checklist source is visible in the frame.\n"
        "- Changeover Step: Set the guide rails label roll and HMI recipe according to the visible target SKU conversion context.\n"
        "- Verification: Check label match barcode readability guide alignment and first piece before restart authorization is considered by operator quality.\n"
        "- Action: Set the guide rails and recipe for SKU-X999 before restarting after operator visual confirmation and checklist approval."
    )

    workflow = run_m400_agently_workflow(
        prompt="Guide changeover on filling line station one labeler for SKU-X999.",
        mode="changeover",
        image_bytes=800_000,
        request_id="req-changeover-source",
        device={"device_id": "m400-demo-01"},
        contract_min_words=16,
        contract_repair_enabled=True,
        current_image_min_tokens=560,
        current_image_max_tokens=560,
        audio_runtime="llama.cpp",
        model_variant="E2B",
        audio_seconds=0,
        needs_ocr=True,
        high_detail=True,
        infer_model=lambda prompt: FakeModelResponse(answer=answer, latency_ms=10),
    )

    assert workflow.knowledge_base is not None
    assert workflow.knowledge_base["status"] == "no_match"
    assert workflow.source_evaluation is not None
    assert workflow.source_evaluation["status"] == "blocked_completion_claim"
    assert workflow.action_card is not None
    assert workflow.action_card.channel == "changeover_source_required"
    assert workflow.action_card.requires_human is True
    assert workflow.integration_event is not None
    assert workflow.integration_event.idempotency_key == "req-changeover-source:changeover_checklist:changeover_source_required"


def test_agently_workflow_repairs_invalid_first_answer() -> None:
    answers = [
        "- Product: Part.\n- Quality Risk: Unknown.",
        (
            "- Product: Machined aluminum housing shows visible edge burrs uneven surface marks and possible handling contamination near the sealing face.\n"
            "- Quality Risk: Burrs or contamination on the sealing face could create assembly leakage escapes and downstream rework risk.\n"
            "- Disposition: expand_inspection\n"
            "- Action: Expand inspection to adjacent units from the same station lot and shift while holding suspect housings for quality engineer review."
        ),
    ]

    def infer_model(prompt: str) -> FakeModelResponse:
        return FakeModelResponse(answer=answers.pop(0), latency_ms=7)

    workflow = run_m400_agently_workflow(
        prompt="Assess product quality.",
        mode="iqc",
        image_bytes=900_000,
        request_id="req-002",
        device={"device_id": "m400-demo-01"},
        contract_min_words=16,
        contract_repair_enabled=True,
        current_image_min_tokens=280,
        current_image_max_tokens=280,
        audio_runtime="llama.cpp",
        model_variant="E2B",
        audio_seconds=0,
        needs_ocr=False,
        high_detail=False,
        infer_model=infer_model,
    )

    assert workflow.contract.ok
    assert workflow.repaired
    assert workflow.latency_ms == 14
    action_logs = workflow.agently_trace["action_runtime"]["action_logs"]
    model_logs = [log for log in action_logs if log["action_type"] == "llama_chat_completion"]
    tool_logs = [log for log in action_logs if log["action_type"] == "tool_call"]
    assert [log["stage"] for log in model_logs] == ["model_infer", "repair_contract"]
    assert tool_logs
    assert {log["status"] for log in tool_logs} == {"completed", "skipped"}
    assert any(log["stage"] == "resolve_iqc_quality_plan_from_fields" for log in tool_logs)
    runtime_events = workflow.runtime_stream["events"]
    model_events = [event for event in runtime_events if event["event"] == "model.call.completed"]
    assert [event["stage"] for event in model_events] == ["model_infer", "repair_contract"]


def test_agently_workflow_loads_maintenance_session_context() -> None:
    answer = (
        "- Machine: Packaging Line Three drive station PKG-L3-GBX-03 with gearbox motor condition display and asset plate evidence.\n"
        "- Symptom: Prior session evidence identifies an abnormal machine condition package that requires maintenance review before further load increase.\n"
        "- Maintenance Risk: Continued operation could worsen equipment wear and unplanned downtime risk if the accepted evidence package is ignored.\n"
        "- Evidence Needed: Review manual thresholds telemetry history lubrication record recent work record and operator sensory notes before final root cause.\n"
        "- Action: Inspect the gearbox and bearing condition immediately and report the session evidence package to maintenance engineering for review."
    )
    seen_prompts: list[str] = []

    def infer_model(prompt: str) -> FakeModelResponse:
        seen_prompts.append(prompt)
        return FakeModelResponse(answer=answer, latency_ms=13)

    workflow = run_m400_agently_workflow(
        prompt="Use the accumulated maintenance evidence before giving advice.",
        mode="maintenance",
        image_bytes=900_000,
        request_id="req-maint-session",
        device={"device_id": "m400-demo-01"},
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
        session_context={
            "session_id": "session-001",
            "prompt_context": (
                "Maintenance session evidence context:\n"
                "- Accepted evidence:\n"
                "  - maintenance_asset_identity_photo: PKG-L3-GBX-03 asset plate confirmed.\n"
                "  - maintenance_operator_sensory_check: abnormal noise and warm gearbox reported."
            ),
            "evidence_state": {
                "accepted_evidence_ids": [
                    "maintenance_asset_identity_photo",
                    "maintenance_condition_screen_photo",
                    "maintenance_temperature_gauge_photo",
                    "maintenance_operator_sensory_check",
                ]
            },
            "accepted_evidence": [
                {
                    "evidence_type": "maintenance_asset_identity_photo",
                    "fields": {"asset_id": "PKG-L3-GBX-03"},
                    "summary": "PKG-L3-GBX-03 asset plate confirmed.",
                },
                {
                    "evidence_type": "maintenance_condition_screen_photo",
                    "fields": {
                        "vibration_rms_mm_s": "7.2",
                        "alarm_color": "yellow",
                        "alarm_code": "GBX-VIB-HI",
                    },
                    "summary": "Yellow PLC alarm and high vibration trend.",
                },
                {
                    "evidence_type": "maintenance_temperature_gauge_photo",
                    "fields": {
                        "gearbox_temperature_c": "78",
                        "bearing_temperature_c": "71",
                    },
                    "summary": "Elevated gearbox and bearing temperatures.",
                },
            ],
            "missing_requested_evidence_ids": ["maintenance_recent_work_record_photo"],
        },
    )

    assert workflow.contract.ok
    assert "Maintenance session evidence context" in seen_prompts[0]
    assert "Maintenance KB context" in seen_prompts[0]
    assert "GBX-VIB-01" in seen_prompts[0]
    assert "Deterministic maintenance condition evaluation" in seen_prompts[0]
    assert workflow.knowledge_base is not None
    assert workflow.knowledge_base["status"] == "matched"
    assert workflow.maintenance_evaluation is not None
    assert workflow.maintenance_evaluation["status"] == "breach_detected"
    assert workflow.maintenance_evaluation["risk_level"] == "high"
    assert workflow.action_card is not None
    assert workflow.action_card.channel == "maintenance_report"
    assert workflow.action_card.owner == "maintenance_engineer"
    assert workflow.tool_plan["used_tool_calls"] == 1
    session_stage = next(
        stage for stage in workflow.agently_trace["triggerflow"]["stages"] if stage["name"] == "load_session_evidence"
    )
    kb_stage = next(
        stage for stage in workflow.agently_trace["triggerflow"]["stages"] if stage["name"] == "retrieve_maintenance_kb"
    )
    eval_stage = next(
        stage
        for stage in workflow.agently_trace["triggerflow"]["stages"]
        if stage["name"] == "evaluate_maintenance_thresholds"
    )
    assert session_stage["status"] == "completed"
    assert session_stage["session_id"] == "session-001"
    assert session_stage["accepted_evidence_count"] == 4
    assert session_stage["missing_requested_evidence_ids"] == ["maintenance_recent_work_record_photo"]
    assert kb_stage["status"] == "completed"
    assert kb_stage["hit_count"] >= 1
    assert eval_stage["status"] == "completed"
    assert eval_stage["evaluation_status"] == "breach_detected"
    assert eval_stage["breach_count"] >= 3
    guard_stage = next(
        stage
        for stage in workflow.agently_trace["triggerflow"]["stages"]
        if stage["name"] == "maintenance_evaluation_guard"
    )
    assert guard_stage["status"] == "completed"
    assert guard_stage["final_channel"] == "maintenance_report"


def test_agently_flow_definition_is_exportable_for_triggerflow_mapping() -> None:
    definition = export_m400_flow_definition()

    assert definition["id"] == "m400_infer"
    assert definition["version"] == AGENTLY_FLOW_DEFINITION_VERSION
    assert definition["supported_modes"] == ["changeover", "energy", "hazard", "iqc", "maintenance", "wi"]
    assert definition["runtime_mapping"]["current_runtime"] == "local deterministic Python orchestrator"
    assert definition["contracts"]["runtime_stream"] == AGENTLY_RUNTIME_STREAM_VERSION
    assert definition["mode_contracts"]["maintenance"]["output_fields"] == [
        "machine",
        "symptom",
        "maintenance_risk",
        "evidence_needed",
        "action",
    ]
    assert definition["mode_contracts"]["energy"]["output_fields"] == [
        "asset",
        "energy_signal",
        "optimization",
        "verification",
        "action",
    ]
    assert "workflow.stage.skipped" in definition["runtime_stream"]["events"]
    assert "tool.call.skipped" in definition["runtime_stream"]["events"]
    assert "follow_up.plan.created" in definition["runtime_stream"]["events"]
    assert "workflow.closed" in definition["runtime_stream"]["events"]
    assert definition["determinism"]["action_mapping"].startswith("decision channel")
    stage_names = [stage["name"] for stage in definition["stages"]]
    assert stage_names == [
        "normalize_agent",
        "select_agent_route",
        "plan_modality",
        "collect_evidence",
        "load_session_evidence",
        "retrieve_maintenance_kb",
        "retrieve_iqc_quality_plan",
        "load_visual_defect_detector_evidence",
        "retrieve_released_wi_source",
        "retrieve_changeover_checklist",
        "evaluate_maintenance_thresholds",
        "bounded_react_tools",
        "build_contract_prompt",
        "model_infer",
        "validate_contract",
        "repair_contract",
        "identify_context",
        "resolve_iqc_quality_plan_from_fields",
        "resolve_released_source_from_fields",
        "structure_action",
        "uncertainty_guard",
        "evaluate_iqc_quality_rules",
        "evaluate_released_source",
        "maintenance_evaluation_guard",
        "iqc_quality_guard",
        "released_source_guard",
        "build_action_card",
        "build_follow_up_plan",
        "build_integration_event",
        "close_execution",
    ]
    model_stage = next(stage for stage in definition["stages"] if stage["name"] == "model_infer")
    assert model_stage["action_log"] == "llama_chat_completion"
