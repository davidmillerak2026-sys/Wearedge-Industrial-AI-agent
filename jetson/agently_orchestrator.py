from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from .agent_loop import (
    ActionCard,
    ActionDecision,
    IntegrationEvent,
    SUPPORTED_AGENT_MODES,
    build_action_card,
    build_agent_loop_metadata,
    build_integration_event,
    build_mode_contract_prompt,
    build_mode_repair_prompt,
    build_route_boundary_prompt_context,
    check_mode_contract,
    decide_action_with_context_guard,
    get_mode_runtime,
    mode_response_fields,
    resolve_agent_mode,
    select_agent_route,
)
from .evidence_plan import build_evidence_plan, build_evidence_prompt_context
from .follow_up_plan import build_contract_failure_follow_up_plan, build_follow_up_plan
from .iqc_detector import (
    build_iqc_detector_prompt_context,
    normalize_iqc_detector_evidence,
)
from .iqc_quality_eval import evaluate_iqc_quality_condition
from .iqc_quality_plan import (
    build_iqc_quality_plan_prompt_context,
    retrieve_iqc_quality_plan_context,
)
from .maintenance_kb import (
    build_maintenance_kb_prompt_context,
    retrieve_maintenance_kb_context,
)
from .maintenance_signal_eval import (
    build_maintenance_condition_prompt_context,
    evaluate_maintenance_condition,
)
from .modality_pipeline import build_modality_plan
from .output_contract import (
    ChangeoverStructuredAnswer,
    ContractCheck,
    EnergyStructuredAnswer,
    IQCStructuredAnswer,
    MaintenanceStructuredAnswer,
    StructuredAnswer,
    WIStructuredAnswer,
)
from .released_source import (
    build_released_source_prompt_context,
    evaluate_released_source_condition,
    retrieve_released_source_context,
)
from .tool_plan import build_bounded_tool_plan, build_tool_action_logs, build_tool_prompt_context


AGENTLY_TRACE_VERSION = "wear-edge-agently-trace.v1"
AGENTLY_FLOW_DEFINITION_VERSION = "wear-edge-agently-flow.v1"
AGENTLY_RUNTIME_STREAM_VERSION = "wear-edge-runtime-stream.v1"
AGENTLY_FLOW_ID = "m400_infer"


class ModelInferenceResult(Protocol):
    answer: str
    latency_ms: int


ModelInference = Callable[[str], ModelInferenceResult]
StructuredContractAnswer = (
    StructuredAnswer | IQCStructuredAnswer | WIStructuredAnswer | ChangeoverStructuredAnswer | MaintenanceStructuredAnswer | EnergyStructuredAnswer
)


@dataclass(frozen=True)
class WearEdgeWorkflowRun:
    mode: str
    answer: str
    structured: StructuredContractAnswer | None
    fields: dict[str, object]
    contract: ContractCheck
    repaired: bool
    latency_ms: int
    modality_plan: dict[str, object]
    evidence_plan: dict[str, object]
    tool_plan: dict[str, object]
    knowledge_base: dict[str, object] | None
    detector_evidence: dict[str, object] | None
    maintenance_evaluation: dict[str, object] | None
    quality_evaluation: dict[str, object] | None
    source_evaluation: dict[str, object] | None
    follow_up_plan: dict[str, object]
    action_card: ActionCard | None
    integration_event: IntegrationEvent | None
    agent_loop: dict[str, object] | None
    agently_trace: dict[str, object]
    runtime_stream: dict[str, object]


def run_m400_agently_workflow(
    *,
    prompt: str,
    mode: str,
    image_bytes: int,
    request_id: str,
    device: dict[str, object],
    contract_min_words: int,
    contract_repair_enabled: bool,
    current_image_min_tokens: int,
    current_image_max_tokens: int,
    audio_runtime: str,
    model_variant: str,
    audio_seconds: int,
    needs_ocr: bool,
    high_detail: bool,
    infer_model: ModelInference,
    session_context: dict[str, object] | None = None,
    detector_evidence: dict[str, object] | None = None,
) -> WearEdgeWorkflowRun:
    stages: list[dict[str, object]] = []
    action_logs: list[dict[str, object]] = []

    resolved_mode = resolve_agent_mode(mode)
    _stage(stages, "normalize_agent", "workflow", mode=resolved_mode)
    route_selection = select_agent_route(resolved_mode)
    _stage(
        stages,
        "select_agent_route",
        "workflow",
        route=route_selection.route,
        source=route_selection.source,
    )
    iqc_detector_result = (
        normalize_iqc_detector_evidence(detector_evidence)
        if resolved_mode == "iqc"
        else None
    )
    detector_evidence_dict = (
        iqc_detector_result.as_dict() if iqc_detector_result is not None else None
    )
    detector_tool_available = (
        iqc_detector_result is not None
        and iqc_detector_result.status in {"available", "clear"}
    )

    modality_plan = build_modality_plan(
        analysis_mode=resolved_mode,
        image_bytes=image_bytes,
        current_image_min_tokens=current_image_min_tokens,
        current_image_max_tokens=current_image_max_tokens,
        audio_runtime=audio_runtime,
        model_variant=model_variant,
        audio_seconds=audio_seconds,
        needs_ocr=needs_ocr,
        high_detail=high_detail,
    )
    _stage(
        stages,
        "plan_modality",
        "workflow",
        visual_status=str(modality_plan["visual_token_budget"]["status"]),
    )

    evidence_plan = build_evidence_plan(
        mode=resolved_mode,
        device=device,
        image_bytes=image_bytes,
        needs_ocr=needs_ocr,
        high_detail=high_detail,
        available_tools=("visual_defect_detector",) if detector_tool_available else (),
    )
    evidence_plan_dict = evidence_plan.as_dict()
    _stage(
        stages,
        "collect_evidence",
        "workflow",
        current_sources=[item["name"] for item in evidence_plan_dict["current_sources"]],
        missing_tools=list(evidence_plan_dict["missing_tools"]),
    )

    session_prompt_context = _session_prompt_context(session_context)
    _stage(
        stages,
        "load_session_evidence",
        "workflow",
        status="completed" if session_prompt_context else "skipped",
        **_session_stage_payload(session_context),
    )

    kb_query_text = "\n\n".join(part for part in (prompt.strip(), session_prompt_context) if part)
    maintenance_kb_result = (
        retrieve_maintenance_kb_context(query_text=kb_query_text)
        if resolved_mode == "maintenance"
        else None
    )
    iqc_quality_plan_result = (
        retrieve_iqc_quality_plan_context(query_text=kb_query_text)
        if resolved_mode == "iqc"
        else None
    )
    released_source_result = (
        retrieve_released_source_context(mode=resolved_mode, query_text=kb_query_text)
        if resolved_mode in {"wi", "changeover"}
        else None
    )
    knowledge_base = (
        maintenance_kb_result.as_dict()
        if maintenance_kb_result is not None
        else iqc_quality_plan_result.as_dict()
        if iqc_quality_plan_result is not None
        else released_source_result.as_dict()
        if released_source_result is not None
        else None
    )
    if maintenance_kb_result is not None:
        _stage(
            stages,
            "retrieve_maintenance_kb",
            "agent",
            status="completed" if maintenance_kb_result.status == "matched" else "skipped",
            kb_status=maintenance_kb_result.status,
            hit_count=len(maintenance_kb_result.hits),
            source_ids=[f"{hit.revision}#{hit.section_id}" for hit in maintenance_kb_result.hits],
        )
        if maintenance_kb_result.status == "matched":
            _action_log(
                action_logs,
                "retrieve_maintenance_kb",
                "tool_call",
                "completed",
                tool="manual_kb",
                tool_kind="rag_tool",
                hit_count=len(maintenance_kb_result.hits),
                source_ids=[f"{hit.revision}#{hit.section_id}" for hit in maintenance_kb_result.hits],
            )
    else:
        _stage(stages, "retrieve_maintenance_kb", "agent", status="skipped", kb_status="not_applicable")

    if iqc_quality_plan_result is not None:
        _stage(
            stages,
            "retrieve_iqc_quality_plan",
            "agent",
            status="completed" if iqc_quality_plan_result.status == "matched" else "skipped",
            kb_status=iqc_quality_plan_result.status,
            hit_count=len(iqc_quality_plan_result.hits),
            source_ids=[f"{hit.revision}#{hit.section_id}" for hit in iqc_quality_plan_result.hits],
        )
        if iqc_quality_plan_result.status == "matched":
            _action_log(
                action_logs,
                "retrieve_iqc_quality_plan",
                "tool_call",
                "completed",
                tool="quality_plan",
                tool_kind="rag_tool",
                hit_count=len(iqc_quality_plan_result.hits),
                source_ids=[f"{hit.revision}#{hit.section_id}" for hit in iqc_quality_plan_result.hits],
            )
    else:
        _stage(stages, "retrieve_iqc_quality_plan", "agent", status="skipped", kb_status="not_applicable")

    if resolved_mode == "iqc":
        _stage(
            stages,
            "load_visual_defect_detector_evidence",
            "agent",
            status="completed" if detector_tool_available else "skipped",
            detector_status=(
                str(iqc_detector_result.status)
                if iqc_detector_result is not None
                else "missing"
            ),
            detection_count=(
                len(iqc_detector_result.detections)
                if iqc_detector_result is not None
                else 0
            ),
        )
        if detector_tool_available and iqc_detector_result is not None:
            _action_log(
                action_logs,
                "load_visual_defect_detector_evidence",
                "tool_call",
                "completed",
                tool="visual_defect_detector",
                tool_kind="vision_tool",
                detection_count=len(iqc_detector_result.detections),
                detector_status=iqc_detector_result.status,
            )
    else:
        _stage(
            stages,
            "load_visual_defect_detector_evidence",
            "agent",
            status="skipped",
            detector_status="not_applicable",
        )

    if released_source_result is not None:
        stage_name = "retrieve_released_wi_source" if resolved_mode == "wi" else "retrieve_changeover_checklist"
        tool_name = "wi_repository" if resolved_mode == "wi" else "changeover_checklist"
        _stage(
            stages,
            stage_name,
            "agent",
            status="completed" if released_source_result.status == "matched" else "skipped",
            source_status=released_source_result.status,
            hit_count=len(released_source_result.hits),
            source_ids=[f"{hit.revision}#{hit.section_id}" for hit in released_source_result.hits],
        )
        if released_source_result.status == "matched":
            _action_log(
                action_logs,
                stage_name,
                "tool_call",
                "completed",
                tool=tool_name,
                tool_kind="rag_tool",
                hit_count=len(released_source_result.hits),
                source_ids=[f"{hit.revision}#{hit.section_id}" for hit in released_source_result.hits],
            )
    else:
        _stage(stages, "retrieve_released_wi_source", "agent", status="skipped", source_status="not_applicable")
        _stage(stages, "retrieve_changeover_checklist", "agent", status="skipped", source_status="not_applicable")

    maintenance_evaluation_result = (
        evaluate_maintenance_condition(session_context=session_context, knowledge_base=knowledge_base)
        if resolved_mode == "maintenance"
        else None
    )
    maintenance_evaluation = (
        maintenance_evaluation_result.as_dict() if maintenance_evaluation_result is not None else None
    )
    if maintenance_evaluation_result is not None:
        _stage(
            stages,
            "evaluate_maintenance_thresholds",
            "agent",
            status="completed",
            evaluation_status=maintenance_evaluation_result.status,
            risk_level=maintenance_evaluation_result.risk_level,
            breach_count=len(maintenance_evaluation_result.breaches),
            recommended_channel=maintenance_evaluation_result.recommended_channel,
        )
    else:
        _stage(
            stages,
            "evaluate_maintenance_thresholds",
            "agent",
            status="skipped",
            evaluation_status="not_applicable",
        )

    tool_plan = build_bounded_tool_plan(evidence_plan)
    tool_plan_dict = tool_plan.as_dict()
    for log in build_tool_action_logs(tool_plan):
        action_logs.append(log)
    _stage(
        stages,
        "bounded_react_tools",
        "agent",
        tool_status=tool_plan.status,
        selected_tools=list(tool_plan.selected_tools),
        used_tool_calls=tool_plan.used_tool_calls,
        max_tool_calls=tool_plan.max_tool_calls,
    )

    evidence_prompt = "\n\n".join(
        part
        for part in (
            prompt.strip(),
            build_route_boundary_prompt_context(resolved_mode),
            session_prompt_context,
            build_maintenance_kb_prompt_context(maintenance_kb_result),
            build_iqc_detector_prompt_context(iqc_detector_result),
            build_iqc_quality_plan_prompt_context(iqc_quality_plan_result),
            build_released_source_prompt_context(released_source_result),
            build_maintenance_condition_prompt_context(maintenance_evaluation_result),
            build_evidence_prompt_context(evidence_plan),
            build_tool_prompt_context(tool_plan),
        )
        if part
    )
    contract_prompt = build_mode_contract_prompt(evidence_prompt, resolved_mode)
    _stage(stages, "build_contract_prompt", "agent", output_contract=resolved_mode)

    response = infer_model(contract_prompt)
    total_latency_ms = response.latency_ms
    _action_log(action_logs, "model_infer", "llama_chat_completion", "completed", latency_ms=response.latency_ms)
    _stage(stages, "model_infer", "model", attempts=1)

    contract = check_mode_contract(response.answer, resolved_mode, min_words=contract_min_words)
    validation_attempts = 1
    initial_violations: list[str] = []
    _stage(stages, "validate_contract", "agent", ok=contract.ok, violations=list(contract.violations))

    repaired = False
    answer = response.answer
    if not contract.ok and contract_repair_enabled:
        repaired = True
        validation_attempts += 1
        initial_violations = list(contract.violations)
        repair_prompt = build_mode_repair_prompt(response.answer, resolved_mode)
        repair_response = infer_model(repair_prompt)
        total_latency_ms += repair_response.latency_ms
        answer = repair_response.answer
        _action_log(
            action_logs,
            "repair_contract",
            "llama_chat_completion",
            "completed",
            latency_ms=repair_response.latency_ms,
            initial_violations=initial_violations,
        )
        _stage(stages, "repair_contract", "agent", status="completed", initial_violations=initial_violations)
        contract = check_mode_contract(repair_response.answer, resolved_mode, min_words=contract_min_words)
        _stage(stages, "validate_repair_contract", "agent", ok=contract.ok, violations=list(contract.violations))
    else:
        _stage(stages, "repair_contract", "agent", status="skipped")

    if not contract.ok or contract.structured is None:
        _stage(stages, "close_execution", "workflow", execution_state="closed", contract_ok=False)
        follow_up_plan = build_contract_failure_follow_up_plan(resolved_mode).as_dict()
        agently_trace = _build_trace(stages, action_logs, execution_state="closed")
        return WearEdgeWorkflowRun(
            mode=resolved_mode,
            answer=answer,
            structured=None,
            fields={},
            contract=contract,
            repaired=repaired,
            latency_ms=total_latency_ms,
            modality_plan=modality_plan,
            evidence_plan=evidence_plan_dict,
            tool_plan=tool_plan_dict,
            knowledge_base=knowledge_base,
            detector_evidence=detector_evidence_dict,
            maintenance_evaluation=maintenance_evaluation,
            quality_evaluation=None,
            source_evaluation=None,
            follow_up_plan=follow_up_plan,
            action_card=None,
            integration_event=None,
            agent_loop=None,
            agently_trace=agently_trace,
            runtime_stream=_build_runtime_stream(
                request_id=request_id,
                mode=resolved_mode,
                stages=stages,
                action_logs=action_logs,
                execution_state="closed",
            ),
        )

    fields = mode_response_fields(contract.structured, resolved_mode)
    context_guard = decide_action_with_context_guard(resolved_mode, fields)
    _stage(
        stages,
        "identify_context",
        "agent",
        fields=list(fields),
        blocked_fields=list(context_guard.blocked_fields),
    )
    if resolved_mode == "iqc" and not _knowledge_base_is_matched(knowledge_base):
        field_query_text = "\n\n".join(
            part for part in (kb_query_text, _fields_prompt_context(fields)) if part
        )
        iqc_quality_plan_from_fields = retrieve_iqc_quality_plan_context(query_text=field_query_text)
        if iqc_quality_plan_from_fields.status == "matched":
            knowledge_base = iqc_quality_plan_from_fields.as_dict()
            _stage(
                stages,
                "resolve_iqc_quality_plan_from_fields",
                "agent",
                status="completed",
                kb_status=iqc_quality_plan_from_fields.status,
                hit_count=len(iqc_quality_plan_from_fields.hits),
                source_ids=[f"{hit.revision}#{hit.section_id}" for hit in iqc_quality_plan_from_fields.hits],
            )
            _action_log(
                action_logs,
                "resolve_iqc_quality_plan_from_fields",
                "tool_call",
                "completed",
                tool="quality_plan",
                tool_kind="rag_tool",
                hit_count=len(iqc_quality_plan_from_fields.hits),
                source_ids=[f"{hit.revision}#{hit.section_id}" for hit in iqc_quality_plan_from_fields.hits],
            )
        else:
            _stage(
                stages,
                "resolve_iqc_quality_plan_from_fields",
                "agent",
                status="skipped",
                kb_status=iqc_quality_plan_from_fields.status,
            )
    else:
        _stage(
            stages,
            "resolve_iqc_quality_plan_from_fields",
            "agent",
            status="skipped",
            kb_status="not_applicable",
        )
    if resolved_mode in {"wi", "changeover"} and not _knowledge_base_is_matched(knowledge_base):
        field_query_text = "\n\n".join(
            part for part in (kb_query_text, _fields_prompt_context(fields)) if part
        )
        released_source_from_fields = retrieve_released_source_context(
            mode=resolved_mode,
            query_text=field_query_text,
        )
        if released_source_from_fields.status == "matched":
            knowledge_base = released_source_from_fields.as_dict()
            _stage(
                stages,
                "resolve_released_source_from_fields",
                "agent",
                status="completed",
                source_status=released_source_from_fields.status,
                hit_count=len(released_source_from_fields.hits),
                source_ids=[f"{hit.revision}#{hit.section_id}" for hit in released_source_from_fields.hits],
            )
            _action_log(
                action_logs,
                "resolve_released_source_from_fields",
                "tool_call",
                "completed",
                tool="wi_repository" if resolved_mode == "wi" else "changeover_checklist",
                tool_kind="rag_tool",
                hit_count=len(released_source_from_fields.hits),
                source_ids=[f"{hit.revision}#{hit.section_id}" for hit in released_source_from_fields.hits],
            )
        else:
            _stage(
                stages,
                "resolve_released_source_from_fields",
                "agent",
                status="skipped",
                source_status=released_source_from_fields.status,
            )
    else:
        _stage(
            stages,
            "resolve_released_source_from_fields",
            "agent",
            status="skipped",
            source_status="not_applicable",
        )
    _stage(stages, "structure_action", "action", channel=context_guard.original_decision.channel)
    _stage(
        stages,
        "uncertainty_guard",
        "action",
        status="completed" if context_guard.status != "clear" else "skipped",
        guard_status=context_guard.status,
        blocked_fields=list(context_guard.blocked_fields),
        final_channel=context_guard.decision.channel,
    )

    iqc_quality_evaluation_result = (
        evaluate_iqc_quality_condition(
            fields=fields,
            knowledge_base=knowledge_base,
            tool_plan=tool_plan_dict,
            detector_evidence=detector_evidence_dict,
        )
        if resolved_mode == "iqc"
        else None
    )
    quality_evaluation = (
        iqc_quality_evaluation_result.as_dict() if iqc_quality_evaluation_result is not None else None
    )
    if iqc_quality_evaluation_result is not None:
        _stage(
            stages,
            "evaluate_iqc_quality_rules",
            "agent",
            status="completed",
            evaluation_status=iqc_quality_evaluation_result.status,
            risk_level=iqc_quality_evaluation_result.risk_level,
            detector_status=iqc_quality_evaluation_result.detector_status,
            finding_count=len(iqc_quality_evaluation_result.findings),
            recommended_channel=iqc_quality_evaluation_result.recommended_channel,
        )
    else:
        _stage(
            stages,
            "evaluate_iqc_quality_rules",
            "agent",
            status="skipped",
            evaluation_status="not_applicable",
        )

    released_source_evaluation_result = (
        evaluate_released_source_condition(
            mode=resolved_mode,
            fields=fields,
            knowledge_base=knowledge_base,
        )
        if resolved_mode in {"wi", "changeover"}
        else None
    )
    source_evaluation = (
        released_source_evaluation_result.as_dict()
        if released_source_evaluation_result is not None
        else None
    )
    if released_source_evaluation_result is not None:
        _stage(
            stages,
            "evaluate_released_source",
            "agent",
            status="completed",
            evaluation_status=released_source_evaluation_result.status,
            source_status=released_source_evaluation_result.source_status,
            recommended_channel=released_source_evaluation_result.recommended_channel,
        )
    else:
        _stage(
            stages,
            "evaluate_released_source",
            "agent",
            status="skipped",
            evaluation_status="not_applicable",
        )

    decision, maintenance_guard_applied = _apply_maintenance_evaluation_guard(
        mode=resolved_mode,
        decision=context_guard.decision,
        maintenance_evaluation=maintenance_evaluation,
    )
    _stage(
        stages,
        "maintenance_evaluation_guard",
        "action",
        status="completed" if maintenance_guard_applied else "skipped",
        evaluation_status=(
            str(maintenance_evaluation.get("status", "not_recorded"))
            if isinstance(maintenance_evaluation, dict)
            else "not_applicable"
        ),
        risk_level=(
            str(maintenance_evaluation.get("risk_level", "not_recorded"))
            if isinstance(maintenance_evaluation, dict)
            else "not_applicable"
        ),
        final_channel=decision.channel,
    )
    decision, iqc_guard_applied = _apply_iqc_quality_guard(
        mode=resolved_mode,
        decision=decision,
        quality_evaluation=quality_evaluation,
    )
    _stage(
        stages,
        "iqc_quality_guard",
        "action",
        status="completed" if iqc_guard_applied else "skipped",
        evaluation_status=(
            str(quality_evaluation.get("status", "not_recorded"))
            if isinstance(quality_evaluation, dict)
            else "not_applicable"
        ),
        risk_level=(
            str(quality_evaluation.get("risk_level", "not_recorded"))
            if isinstance(quality_evaluation, dict)
            else "not_applicable"
        ),
        final_channel=decision.channel,
    )
    decision, source_guard_applied = _apply_released_source_guard(
        mode=resolved_mode,
        decision=decision,
        source_evaluation=source_evaluation,
    )
    _stage(
        stages,
        "released_source_guard",
        "action",
        status="completed" if source_guard_applied else "skipped",
        evaluation_status=(
            str(source_evaluation.get("status", "not_recorded"))
            if isinstance(source_evaluation, dict)
            else "not_applicable"
        ),
        source_status=(
            str(source_evaluation.get("source_status", "not_recorded"))
            if isinstance(source_evaluation, dict)
            else "not_applicable"
        ),
        final_channel=decision.channel,
    )

    action_card = build_action_card(resolved_mode, fields, decision)
    _stage(stages, "build_action_card", "action", priority=action_card.priority)

    follow_up_plan = build_follow_up_plan(
        mode=resolved_mode,
        fields=fields,
        evidence_plan=evidence_plan_dict,
        tool_plan=tool_plan_dict,
        decision_channel=decision.channel,
        accepted_evidence_ids=_accepted_session_evidence_ids(session_context),
    ).as_dict()
    _stage(
        stages,
        "build_follow_up_plan",
        "action",
        follow_up_status=str(follow_up_plan["status"]),
        request_count=len(follow_up_plan["requests"]) if isinstance(follow_up_plan.get("requests"), list) else 0,
        next_action=str(follow_up_plan["next_action"]),
    )

    integration_event = build_integration_event(
        request_id=request_id,
        device=device,
        mode=resolved_mode,
        fields=fields,
        action_card=action_card,
        follow_up_plan=follow_up_plan,
        knowledge_base=knowledge_base,
        detector_evidence=detector_evidence_dict,
        maintenance_evaluation=maintenance_evaluation,
        quality_evaluation=quality_evaluation,
        source_evaluation=source_evaluation,
    )
    _stage(stages, "build_integration_event", "action", target=integration_event.target, status=integration_event.status)

    agent_loop = build_agent_loop_metadata(
        mode=resolved_mode,
        repaired=repaired,
        validation_attempts=validation_attempts,
        initial_violations=initial_violations,
        final_violations=contract.violations,
        decision=decision,
        action_card=action_card,
        context_guard=context_guard,
        tool_plan=tool_plan_dict,
        knowledge_base=knowledge_base,
        maintenance_evaluation=maintenance_evaluation,
        quality_evaluation=quality_evaluation,
        source_evaluation=source_evaluation,
        maintenance_evaluation_guard_applied=maintenance_guard_applied,
        iqc_quality_guard_applied=iqc_guard_applied,
        source_guard_applied=source_guard_applied,
        follow_up_plan=follow_up_plan,
    )
    _stage(stages, "close_execution", "workflow", execution_state="closed")

    agently_trace = _build_trace(stages, action_logs, execution_state="closed")
    runtime_stream = _build_runtime_stream(
        request_id=request_id,
        mode=resolved_mode,
        stages=stages,
        action_logs=action_logs,
        execution_state="closed",
    )

    return WearEdgeWorkflowRun(
        mode=resolved_mode,
        answer=answer,
        structured=contract.structured,
        fields=fields,
        contract=contract,
        repaired=repaired,
        latency_ms=total_latency_ms,
        modality_plan=modality_plan,
        evidence_plan=evidence_plan_dict,
        tool_plan=tool_plan_dict,
        knowledge_base=knowledge_base,
        detector_evidence=detector_evidence_dict,
        maintenance_evaluation=maintenance_evaluation,
        quality_evaluation=quality_evaluation,
        source_evaluation=source_evaluation,
        follow_up_plan=follow_up_plan,
        action_card=action_card,
        integration_event=integration_event,
        agent_loop=agent_loop,
        agently_trace=agently_trace,
        runtime_stream=runtime_stream,
    )


def export_m400_flow_definition() -> dict[str, object]:
    stages = [
        {
            "name": "normalize_agent",
            "layer": "workflow",
            "purpose": "Normalize aliases into one supported WearEdge agent mode.",
            "inputs": ["analysis_mode"],
            "outputs": ["mode"],
        },
        {
            "name": "select_agent_route",
            "layer": "workflow",
            "purpose": "Lock the request to one WearEdge agent route and expose its domain boundary before prompting.",
            "inputs": ["analysis_mode"],
            "outputs": ["route_selection"],
        },
        {
            "name": "plan_modality",
            "layer": "workflow",
            "purpose": "Choose visual token and audio fusion plan before model inference.",
            "inputs": ["mode", "image_bytes", "needs_ocr", "high_detail", "audio_seconds"],
            "outputs": ["modality_plan"],
        },
        {
            "name": "collect_evidence",
            "layer": "workflow",
            "purpose": "Collect current edge evidence and declare missing external tools before prompt construction.",
            "inputs": ["mode", "device", "image_bytes", "needs_ocr", "high_detail"],
            "outputs": ["evidence_plan"],
        },
        {
            "name": "load_session_evidence",
            "layer": "workflow",
            "purpose": "Load accepted maintenance session evidence and unresolved follow-up gaps before tool planning.",
            "inputs": ["mode", "session_context"],
            "outputs": ["session_evidence_context"],
            "condition": "session_context is present",
        },
        {
            "name": "retrieve_maintenance_kb",
            "layer": "agent",
            "purpose": "Retrieve machine-specific predictive-maintenance KB sections before model inference.",
            "inputs": ["mode", "session_evidence_context", "prompt"],
            "outputs": ["maintenance_kb_context"],
            "condition": "mode == maintenance",
            "action_log": "manual_kb",
        },
        {
            "name": "retrieve_iqc_quality_plan",
            "layer": "agent",
            "purpose": "Retrieve released IQC quality-plan rules, detector requirements, sampling scope, and disposition authority before model inference.",
            "inputs": ["mode", "prompt"],
            "outputs": ["iqc_quality_plan_context"],
            "condition": "mode == iqc",
            "action_log": "quality_plan",
        },
        {
            "name": "load_visual_defect_detector_evidence",
            "layer": "agent",
            "purpose": "Load detector boxes, classes, and scores supplied by the M400 or an edge detector before IQC interpretation.",
            "inputs": ["mode", "detector_evidence_json"],
            "outputs": ["detector_evidence"],
            "condition": "mode == iqc",
            "action_log": "visual_defect_detector",
        },
        {
            "name": "retrieve_released_wi_source",
            "layer": "agent",
            "purpose": "Retrieve released WI revision and source sections before trusted operator guidance.",
            "inputs": ["mode", "prompt"],
            "outputs": ["released_source_context"],
            "condition": "mode == wi",
            "action_log": "wi_repository",
        },
        {
            "name": "retrieve_changeover_checklist",
            "layer": "agent",
            "purpose": "Retrieve released changeover checklist sections by machine and target SKU before continuation or restart guidance.",
            "inputs": ["mode", "prompt"],
            "outputs": ["released_source_context"],
            "condition": "mode == changeover",
            "action_log": "changeover_checklist",
        },
        {
            "name": "evaluate_maintenance_thresholds",
            "layer": "agent",
            "purpose": "Compare accepted maintenance session readings against retrieved KB thresholds deterministically.",
            "inputs": ["mode", "session_evidence_context", "maintenance_kb_context"],
            "outputs": ["maintenance_evaluation"],
            "condition": "mode == maintenance",
        },
        {
            "name": "bounded_react_tools",
            "layer": "agent",
            "purpose": "Run a bounded evidence-tool plan before model inference, with missing tools logged instead of hallucinated.",
            "inputs": [
                "evidence_plan",
                "session_evidence_context",
                "maintenance_kb_context",
                "iqc_quality_plan_context",
                "detector_evidence",
                "released_source_context",
                "maintenance_evaluation",
            ],
            "outputs": ["tool_plan"],
            "max_iterations": 1,
            "max_tool_calls": 3,
        },
        {
            "name": "build_contract_prompt",
            "layer": "agent",
            "purpose": "Attach evidence, tool context, and the mode-specific output contract to the operator prompt.",
            "inputs": [
                "prompt",
                "mode",
                "session_evidence_context",
                "maintenance_kb_context",
                "iqc_quality_plan_context",
                "detector_evidence",
                "released_source_context",
                "maintenance_evaluation",
                "evidence_plan",
                "tool_plan",
            ],
            "outputs": ["contract_prompt"],
        },
        {
            "name": "model_infer",
            "layer": "model",
            "purpose": "Run one multimodal model call against llama.cpp, vLLM, or another OpenAI-compatible backend.",
            "inputs": ["contract_prompt", "image"],
            "outputs": ["answer"],
            "action_log": "llama_chat_completion",
        },
        {
            "name": "validate_contract",
            "layer": "agent",
            "purpose": "Parse and validate required fields, word counts, and action starters.",
            "inputs": ["answer", "mode"],
            "outputs": ["contract"],
        },
        {
            "name": "repair_contract",
            "layer": "agent",
            "purpose": "Run a bounded repair call only when the first output fails validation.",
            "inputs": ["answer", "contract.violations"],
            "outputs": ["answer", "contract"],
            "condition": "contract.ok == false and repair_enabled == true",
            "action_log": "llama_chat_completion",
        },
        {
            "name": "identify_context",
            "layer": "agent",
            "purpose": "Identify machine, SKU, product, WI source, and scene context from validated fields.",
            "inputs": ["contract.structured", "mode"],
            "outputs": ["context_fields", "blocked_fields"],
        },
        {
            "name": "resolve_iqc_quality_plan_from_fields",
            "layer": "agent",
            "purpose": "Fallback-retrieve the IQC quality plan from the validated product fields when the original prompt did not identify the product.",
            "inputs": ["mode", "context_fields", "prompt"],
            "outputs": ["iqc_quality_plan_context"],
            "condition": "mode == iqc and prompt retrieval did not match a quality plan",
            "action_log": "quality_plan",
        },
        {
            "name": "resolve_released_source_from_fields",
            "layer": "agent",
            "purpose": "Fallback-retrieve released WI or changeover source from validated structured fields when the original prompt did not identify it.",
            "inputs": ["mode", "context_fields", "prompt"],
            "outputs": ["released_source_context"],
            "condition": "mode in [wi, changeover] and prompt retrieval did not match a released source",
            "action_log": "wi_repository_or_changeover_checklist",
        },
        {
            "name": "structure_action",
            "layer": "action",
            "purpose": "Map validated structured fields into deterministic decision channel and owner.",
            "inputs": ["contract.structured"],
            "outputs": ["decision"],
        },
        {
            "name": "uncertainty_guard",
            "layer": "action",
            "purpose": "Require human confirmation when context uncertainty would otherwise allow a final or low-control action.",
            "inputs": ["decision", "context_fields"],
            "outputs": ["guarded_decision"],
        },
        {
            "name": "evaluate_iqc_quality_rules",
            "layer": "agent",
            "purpose": "Compare IQC product, defect, detector, and quality-plan evidence before allowing pass, hold, or containment actions.",
            "inputs": ["mode", "context_fields", "iqc_quality_plan_context", "detector_evidence", "tool_plan"],
            "outputs": ["quality_evaluation"],
            "condition": "mode == iqc",
        },
        {
            "name": "evaluate_released_source",
            "layer": "agent",
            "purpose": "Check whether WI or changeover guidance is backed by a matched released source before allowing trusted guidance or continuation.",
            "inputs": ["mode", "context_fields", "released_source_context"],
            "outputs": ["source_evaluation"],
            "condition": "mode in [wi, changeover]",
        },
        {
            "name": "maintenance_evaluation_guard",
            "layer": "action",
            "purpose": "Upgrade or block low-control maintenance actions when deterministic KB/session evaluation finds high breach risk or missing required evidence.",
            "inputs": ["decision", "maintenance_evaluation"],
            "outputs": ["guarded_decision"],
            "condition": "mode == maintenance and maintenance_evaluation.requires_human or high breach risk",
        },
        {
            "name": "iqc_quality_guard",
            "layer": "action",
            "purpose": "Block release or upgrade containment when deterministic IQC quality-plan evaluation finds missing detector evidence or severe defect rules.",
            "inputs": ["decision", "quality_evaluation"],
            "outputs": ["guarded_decision"],
            "condition": "mode == iqc and quality_evaluation.requires_human or severe defect rule",
        },
        {
            "name": "released_source_guard",
            "layer": "action",
            "purpose": "Block low-control WI or changeover actions when released source evidence is missing or unmatched.",
            "inputs": ["decision", "source_evaluation"],
            "outputs": ["guarded_decision"],
            "condition": "mode in [wi, changeover] and source_evaluation.requires_human",
        },
        {
            "name": "build_action_card",
            "layer": "action",
            "purpose": "Build operator-facing action package with priority, owner, confirmations, and integration target.",
            "inputs": ["decision", "fields"],
            "outputs": ["action_card"],
        },
        {
            "name": "build_follow_up_plan",
            "layer": "action",
            "purpose": "Build deterministic M400 follow-up capture tasks when operator evidence is still required.",
            "inputs": ["mode", "fields", "evidence_plan", "tool_plan", "decision"],
            "outputs": ["follow_up_plan"],
        },
        {
            "name": "build_integration_event",
            "layer": "action",
            "purpose": "Wrap action card, follow-up plan, and evidence into idempotent QMS/CMMS/EHS/MES event envelope.",
            "inputs": ["request_id", "device", "action_card", "follow_up_plan", "fields"],
            "outputs": ["integration_event"],
        },
        {
            "name": "close_execution",
            "layer": "workflow",
            "purpose": "Close the synchronous request and return traceable outputs to M400.",
            "inputs": ["all stage outputs"],
            "outputs": ["agently_trace", "runtime_stream"],
        },
    ]
    return {
        "id": AGENTLY_FLOW_ID,
        "version": AGENTLY_FLOW_DEFINITION_VERSION,
        "supported_modes": sorted(SUPPORTED_AGENT_MODES),
        "runtime_mapping": {
            "agently": "TriggerFlow definition plus Action Runtime logs",
            "current_runtime": "local deterministic Python orchestrator",
            "migration_note": "Each stage is already named and layered for direct TriggerFlow migration.",
        },
        "entrypoint": "m400_infer",
        "lifecycle": {
            "start_state": "open",
            "terminal_state": "closed",
            "repair_is_bounded": True,
        },
        "stages": stages,
        "mode_contracts": {
            mode: {
                "output_fields": list(get_mode_runtime(mode).output_fields),
                "prompt_contract": "mode-specific prompt contract",
                "repair_prompt": "bounded contract repair prompt",
            }
            for mode in sorted(SUPPORTED_AGENT_MODES)
        },
        "contracts": {
            "output_contract": "mode-specific structured contract from jetson.output_contract",
            "action_card": "wear-edge-action-card.v1",
            "follow_up_plan": "wear-edge-follow-up-plan.v1",
            "detector_evidence": "wear-edge-iqc-detector-evidence.v1",
            "maintenance_evaluation": "wear-edge-maintenance-condition-eval.v1",
            "quality_evaluation": "wear-edge-iqc-quality-eval.v1",
            "source_evaluation": "wear-edge-released-source-eval.v1",
            "integration_event": "wear-edge-integration-event.v1",
            "trace": AGENTLY_TRACE_VERSION,
            "runtime_stream": AGENTLY_RUNTIME_STREAM_VERSION,
        },
        "runtime_stream": {
            "events": [
                "workflow.stage.completed",
                "workflow.stage.skipped",
                "model.call.completed",
                "tool.call.completed",
                "tool.call.skipped",
                "contract.validation.completed",
                "action.card.created",
                "follow_up.plan.created",
                "integration.event.created",
                "workflow.closed",
            ],
            "consumer": "M400 operator UI, audit log, and later Agently DevTools bridge",
        },
        "determinism": {
            "model_calls": "one primary multimodal call plus at most one bounded repair call",
            "output_validation": "required fields, word counts, and action starters are checked before actions",
            "action_mapping": "decision channel, owner, priority, and integration target are pure rule mappings",
            "evidence_boundary": "external tools are declared as missing until connected and audited",
            "route_boundary": "analysis_mode selects one route before prompting; maintenance does not analyze EHS hazard exposure",
            "tool_budget": "bounded_react_tools allows at most one iteration and three tool calls before model inference",
            "follow_up": "operator evidence requests are deterministic action outputs, not unbounded model chat",
            "session_evidence": "maintenance sessions load accepted operator evidence before prompting and keep gaps explicit",
            "maintenance_kb": "manual_kb retrieval is explicit evidence and still cannot authorize release without human confirmation",
            "maintenance_thresholds": "accepted session readings are compared to retrieved KB thresholds before model inference",
            "maintenance_evaluation_guard": "high threshold breach upgrades low-control maintenance action to maintenance_report; insufficient KB/session evidence blocks low-control machine-specific advice",
            "iqc_quality_plan": "released quality-plan retrieval is explicit evidence and detector evidence is required before any automated pass path",
            "iqc_detector_evidence": "visual_defect_detector evidence can be loaded as a structured contract so detector-first IQC does not depend on VLM text guesses",
            "iqc_quality_guard": "missing or invalid detector evidence blocks pass into quality_review; severe defect rules upgrade low-control IQC actions",
            "released_source_guard": "WI and changeover low-control actions require matched released source evidence; otherwise they route to human source confirmation",
            "idempotency": "integration_event.idempotency_key is request_id:target:channel",
        },
    }


def _session_prompt_context(session_context: dict[str, object] | None) -> str:
    if not isinstance(session_context, dict):
        return ""
    prompt_context = session_context.get("prompt_context")
    if prompt_context is None:
        return ""
    return str(prompt_context).strip()


def _session_stage_payload(session_context: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(session_context, dict):
        return {
            "session_id": None,
            "accepted_evidence_count": 0,
            "missing_requested_evidence_ids": [],
        }
    evidence_state = session_context.get("evidence_state")
    accepted = []
    if isinstance(evidence_state, dict):
        raw_accepted = evidence_state.get("accepted_evidence_ids")
        accepted = raw_accepted if isinstance(raw_accepted, list) else []
    raw_missing = session_context.get("missing_requested_evidence_ids")
    missing = raw_missing if isinstance(raw_missing, list) else []
    return {
        "session_id": session_context.get("session_id"),
        "accepted_evidence_count": len(accepted),
        "missing_requested_evidence_ids": list(missing),
    }


def _accepted_session_evidence_ids(session_context: dict[str, object] | None) -> tuple[str, ...]:
    if not isinstance(session_context, dict):
        return ()
    evidence_state = session_context.get("evidence_state")
    if not isinstance(evidence_state, dict):
        return ()
    raw_accepted = evidence_state.get("accepted_evidence_ids")
    if not isinstance(raw_accepted, list):
        return ()
    return tuple(str(item) for item in raw_accepted if str(item).strip())


def _knowledge_base_is_matched(knowledge_base: dict[str, object] | None) -> bool:
    return isinstance(knowledge_base, dict) and str(knowledge_base.get("status") or "") == "matched"


def _fields_prompt_context(fields: dict[str, object]) -> str:
    lines = ["Structured field context:"]
    for key in sorted(fields):
        value = str(fields.get(key) or "").strip()
        if value:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines) if len(lines) > 1 else ""


def _apply_maintenance_evaluation_guard(
    *,
    mode: str,
    decision: ActionDecision,
    maintenance_evaluation: dict[str, object] | None,
) -> tuple[ActionDecision, bool]:
    if mode != "maintenance" or not isinstance(maintenance_evaluation, dict):
        return decision, False
    if str(maintenance_evaluation.get("status")) != "breach_detected":
        if (
            str(maintenance_evaluation.get("status")) == "insufficient_evidence"
            and bool(maintenance_evaluation.get("requires_human"))
            and not decision.requires_human
        ):
            missing = maintenance_evaluation.get("missing_inputs")
            missing_text = ", ".join(str(item) for item in missing) if isinstance(missing, list) else "required evidence"
            return (
                ActionDecision(
                    "maintenance_identification_required",
                    "maintenance_engineer",
                    True,
                    f"{decision.reason}; deterministic maintenance evaluation requires human confirmation: missing {missing_text}",
                ),
                True,
            )
        return decision, False

    risk_level = str(maintenance_evaluation.get("risk_level") or "")
    if risk_level == "high" and decision.channel not in {
        "maintenance_stop",
        "maintenance_escalation",
        "maintenance_report",
        "schedule_maintenance",
    }:
        return (
            ActionDecision(
                "maintenance_report",
                "maintenance_engineer",
                True,
                f"{decision.reason}; deterministic maintenance evaluation found high KB threshold breach",
            ),
            True,
        )
    if risk_level == "medium" and decision.channel == "continue_with_monitoring":
        return (
            ActionDecision(
                "condition_inspection",
                "operator",
                False,
                f"{decision.reason}; deterministic maintenance evaluation found medium KB threshold breach",
            ),
            True,
        )
    return decision, False


def _apply_iqc_quality_guard(
    *,
    mode: str,
    decision: ActionDecision,
    quality_evaluation: dict[str, object] | None,
) -> tuple[ActionDecision, bool]:
    if mode != "iqc" or not isinstance(quality_evaluation, dict):
        return decision, False
    recommended = str(quality_evaluation.get("recommended_channel") or "")
    status = str(quality_evaluation.get("status") or "")
    if not recommended or recommended == decision.channel:
        return decision, False
    if status in {"insufficient_evidence", "insufficient_detector_evidence"} and not decision.requires_human:
        missing = quality_evaluation.get("missing_inputs")
        missing_text = ", ".join(str(item) for item in missing) if isinstance(missing, list) else "required IQC evidence"
        return (
            ActionDecision(
                "quality_review",
                "quality_engineer",
                True,
                f"{decision.reason}; deterministic IQC evaluation requires human confirmation: missing {missing_text}",
            ),
            True,
        )
    if _iqc_channel_rank(recommended) > _iqc_channel_rank(decision.channel):
        owner, requires_human = _iqc_owner_for(recommended)
        return (
            ActionDecision(
                recommended,
                owner,
                requires_human,
                f"{decision.reason}; deterministic IQC quality-plan evaluation recommends {recommended}",
            ),
            True,
        )
    return decision, False


def _apply_released_source_guard(
    *,
    mode: str,
    decision: ActionDecision,
    source_evaluation: dict[str, object] | None,
) -> tuple[ActionDecision, bool]:
    if mode not in {"wi", "changeover"} or not isinstance(source_evaluation, dict):
        return decision, False
    if str(source_evaluation.get("source_status") or "") == "matched":
        return decision, False
    recommended = str(source_evaluation.get("recommended_channel") or "")
    if not recommended:
        return decision, False
    if decision.requires_human:
        return (
            ActionDecision(
                decision.channel,
                decision.owner,
                True,
                f"{decision.reason}; released-source guard: {source_evaluation.get('status')}",
            ),
            False,
        )
    owner = "line_lead" if mode == "wi" else "operator_quality"
    return (
        ActionDecision(
            recommended,
            owner,
            True,
            f"{decision.reason}; released-source guard: {source_evaluation.get('status')}",
        ),
        True,
    )


def _iqc_channel_rank(channel: str) -> int:
    ranks = {
        "continue_production": 0,
        "quality_review": 1,
        "expand_inspection": 2,
        "rework_hold": 2,
        "scrap_review": 3,
        "quality_hold": 3,
        "capa_request": 3,
        "stop_production": 4,
    }
    return ranks.get(channel, 1)


def _iqc_owner_for(channel: str) -> tuple[str, bool]:
    owners = {
        "continue_production": ("operator", False),
        "quality_review": ("quality_engineer", True),
        "expand_inspection": ("quality_engineer", True),
        "rework_hold": ("quality_engineer", True),
        "scrap_review": ("quality_engineer", True),
        "quality_hold": ("quality_engineer", True),
        "capa_request": ("quality_engineer", True),
        "stop_production": ("shift_lead", True),
    }
    return owners.get(channel, ("quality_engineer", True))


def _stage(
    stages: list[dict[str, object]],
    name: str,
    layer: str,
    status: str = "completed",
    **extra: object,
) -> None:
    stage = {"name": name, "layer": layer, "status": status}
    stage.update(extra)
    stages.append(stage)


def _action_log(
    action_logs: list[dict[str, object]],
    stage: str,
    action_type: str,
    status: str,
    **extra: object,
) -> None:
    log = {"stage": stage, "action_type": action_type, "status": status}
    log.update(extra)
    action_logs.append(log)


def _build_trace(
    stages: list[dict[str, object]],
    action_logs: list[dict[str, object]],
    *,
    execution_state: str,
) -> dict[str, object]:
    return {
        "version": AGENTLY_TRACE_VERSION,
        "triggerflow": {
            "definition_id": AGENTLY_FLOW_ID,
            "definition_version": AGENTLY_FLOW_DEFINITION_VERSION,
            "entrypoint": "m400_infer",
            "execution_state": execution_state,
            "stages": stages,
        },
        "action_runtime": {
            "action_logs": action_logs,
        },
    }


def _build_runtime_stream(
    *,
    request_id: str,
    mode: str,
    stages: list[dict[str, object]],
    action_logs: list[dict[str, object]],
    execution_state: str,
) -> dict[str, object]:
    events: list[dict[str, object]] = []
    logs_by_stage: dict[str, list[dict[str, object]]] = {}
    for log in action_logs:
        logs_by_stage.setdefault(str(log["stage"]), []).append(log)

    sequence = 1
    for stage in stages:
        events.append(_runtime_stage_event(sequence, stage))
        sequence += 1
        for log in logs_by_stage.get(str(stage["name"]), []):
            events.append(_runtime_action_event(sequence, log))
            sequence += 1

    return {
        "version": AGENTLY_RUNTIME_STREAM_VERSION,
        "definition_id": AGENTLY_FLOW_ID,
        "definition_version": AGENTLY_FLOW_DEFINITION_VERSION,
        "request_id": request_id,
        "mode": mode,
        "execution_state": execution_state,
        "closed": execution_state == "closed",
        "events": events,
    }


def _runtime_stage_event(sequence: int, stage: dict[str, object]) -> dict[str, object]:
    name = str(stage["name"])
    status = str(stage["status"])
    payload = {key: value for key, value in stage.items() if key not in {"name", "layer", "status"}}
    return {
        "sequence": sequence,
        "event": _runtime_event_type_for_stage(name, status),
        "stage": name,
        "layer": stage["layer"],
        "status": status,
        "payload": payload,
    }


def _runtime_action_event(sequence: int, action_log: dict[str, object]) -> dict[str, object]:
    payload = {key: value for key, value in action_log.items() if key not in {"stage", "action_type", "status"}}
    action_type = str(action_log["action_type"])
    status = str(action_log["status"])
    return {
        "sequence": sequence,
        "event": _runtime_event_type_for_action(action_type, status),
        "stage": action_log["stage"],
        "action_type": action_type,
        "status": status,
        "payload": payload,
    }


def _runtime_event_type_for_stage(name: str, status: str) -> str:
    if status == "skipped":
        return "workflow.stage.skipped"
    if name in {"validate_contract", "validate_repair_contract"}:
        return "contract.validation.completed"
    if name == "build_action_card":
        return "action.card.created"
    if name == "build_follow_up_plan":
        return "follow_up.plan.created"
    if name == "build_integration_event":
        return "integration.event.created"
    if name == "close_execution":
        return "workflow.closed"
    return "workflow.stage.completed"


def _runtime_event_type_for_action(action_type: str, status: str) -> str:
    if action_type == "llama_chat_completion":
        return "model.call.completed"
    if status == "skipped":
        return "tool.call.skipped"
    return "tool.call.completed"
