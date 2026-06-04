from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .agent_profiles import AGENT_PROFILES, normalize_agent_mode
from .output_contract import (
    ChangeoverStructuredAnswer,
    ContractCheck,
    EnergyStructuredAnswer,
    IQCStructuredAnswer,
    MaintenanceStructuredAnswer,
    StructuredAnswer,
    WIStructuredAnswer,
    build_changeover_contract_prompt,
    build_changeover_repair_prompt,
    build_contract_prompt,
    build_energy_contract_prompt,
    build_energy_repair_prompt,
    build_iqc_contract_prompt,
    build_iqc_repair_prompt,
    build_maintenance_contract_prompt,
    build_maintenance_repair_prompt,
    build_repair_prompt,
    build_wi_contract_prompt,
    build_wi_repair_prompt,
    check_changeover_output_contract,
    check_energy_output_contract,
    check_iqc_output_contract,
    check_maintenance_output_contract,
    check_output_contract,
    check_wi_output_contract,
)


AGENT_LOOP_VERSION = "wear-edge-agent-loop.v1"
ACTION_CARD_VERSION = "wear-edge-action-card.v1"
INTEGRATION_EVENT_VERSION = "wear-edge-integration-event.v1"
SUPPORTED_AGENT_MODES = set(AGENT_PROFILES)

PromptBuilder = Callable[[str], str]
ContractChecker = Callable[[str, int], ContractCheck]


@dataclass(frozen=True)
class AgentModeRuntime:
    mode: str
    output_fields: tuple[str, ...]
    build_contract_prompt: PromptBuilder
    build_repair_prompt: PromptBuilder
    check_contract: ContractChecker


@dataclass(frozen=True)
class AgentRouteSelection:
    mode: str
    route: str
    source: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "route": self.route,
            "source": self.source,
            "boundary": self.boundary,
        }


@dataclass(frozen=True)
class ActionDecision:
    channel: str
    owner: str
    requires_human: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel,
            "owner": self.owner,
            "requires_human": self.requires_human,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ContextGuardResult:
    status: str
    blocked_fields: tuple[str, ...]
    reasons: tuple[str, ...]
    original_decision: ActionDecision
    decision: ActionDecision

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "blocked_fields": list(self.blocked_fields),
            "reasons": list(self.reasons),
            "original_decision": self.original_decision.as_dict(),
            "decision": self.decision.as_dict(),
            "applied": self.decision != self.original_decision,
        }


@dataclass(frozen=True)
class ActionCard:
    version: str
    mode: str
    channel: str
    title: str
    priority: str
    owner: str
    requires_human: bool
    operator_message: str
    integration_target: str
    required_confirmations: tuple[str, ...]
    evidence_fields: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "mode": self.mode,
            "channel": self.channel,
            "title": self.title,
            "priority": self.priority,
            "owner": self.owner,
            "requires_human": self.requires_human,
            "operator_message": self.operator_message,
            "integration_target": self.integration_target,
            "required_confirmations": list(self.required_confirmations),
            "evidence_fields": list(self.evidence_fields),
        }


@dataclass(frozen=True)
class IntegrationEvent:
    version: str
    event_type: str
    target: str
    routing_key: str
    status: str
    idempotency_key: str
    requires_human: bool
    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "event_type": self.event_type,
            "target": self.target,
            "routing_key": self.routing_key,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
            "requires_human": self.requires_human,
            "payload": self.payload,
        }


def _check_hazard(answer: str, min_words: int) -> ContractCheck:
    return check_output_contract(answer, min_words=min_words)


def _check_iqc(answer: str, min_words: int) -> ContractCheck:
    return check_iqc_output_contract(answer, min_words=min_words)


def _check_wi(answer: str, min_words: int) -> ContractCheck:
    return check_wi_output_contract(answer, min_words=min_words)


def _check_changeover(answer: str, min_words: int) -> ContractCheck:
    return check_changeover_output_contract(answer, min_words=min_words)


def _check_maintenance(answer: str, min_words: int) -> ContractCheck:
    return check_maintenance_output_contract(answer, min_words=min_words)


def _check_energy(answer: str, min_words: int) -> ContractCheck:
    return check_energy_output_contract(answer, min_words=min_words)


MODE_RUNTIMES: dict[str, AgentModeRuntime] = {
    "hazard": AgentModeRuntime(
        mode="hazard",
        output_fields=("scene", "risk", "action"),
        build_contract_prompt=build_contract_prompt,
        build_repair_prompt=build_repair_prompt,
        check_contract=_check_hazard,
    ),
    "maintenance": AgentModeRuntime(
        mode="maintenance",
        output_fields=("machine", "symptom", "maintenance_risk", "evidence_needed", "action"),
        build_contract_prompt=build_maintenance_contract_prompt,
        build_repair_prompt=build_maintenance_repair_prompt,
        check_contract=_check_maintenance,
    ),
    "iqc": AgentModeRuntime(
        mode="iqc",
        output_fields=("product", "quality_risk", "disposition", "action"),
        build_contract_prompt=build_iqc_contract_prompt,
        build_repair_prompt=build_iqc_repair_prompt,
        check_contract=_check_iqc,
    ),
    "energy": AgentModeRuntime(
        mode="energy",
        output_fields=("asset", "energy_signal", "optimization", "verification", "action"),
        build_contract_prompt=build_energy_contract_prompt,
        build_repair_prompt=build_energy_repair_prompt,
        check_contract=_check_energy,
    ),
    "wi": AgentModeRuntime(
        mode="wi",
        output_fields=("machine", "work_instruction", "risk_control", "action"),
        build_contract_prompt=build_wi_contract_prompt,
        build_repair_prompt=build_wi_repair_prompt,
        check_contract=_check_wi,
    ),
    "changeover": AgentModeRuntime(
        mode="changeover",
        output_fields=("machine", "sku", "changeover_step", "verification", "action"),
        build_contract_prompt=build_changeover_contract_prompt,
        build_repair_prompt=build_changeover_repair_prompt,
        check_contract=_check_changeover,
    ),
}


def resolve_agent_mode(value: str | None) -> str:
    mode = normalize_agent_mode(value)
    if mode not in MODE_RUNTIMES:
        raise ValueError(f"unsupported analysis_mode: {value}")
    return mode


def get_mode_runtime(mode: str) -> AgentModeRuntime:
    return MODE_RUNTIMES[resolve_agent_mode(mode)]


def select_agent_route(mode: str) -> AgentRouteSelection:
    resolved = resolve_agent_mode(mode)
    boundaries = {
        "maintenance": (
            "Predictive-maintenance route: evaluate equipment identity, visible symptoms, machine-condition risk, "
            "and maintenance escalation only. Do not analyze EHS/personnel hazard exposure; route PPE, blocked walkway, "
            "fall, pinch, geofence, or unsafe-person exposure to the hazard agent."
        ),
        "hazard": (
            "Hazard exposure route: evaluate area, PPE, body position, restricted-zone, fall, pinch, and immediate "
            "make-safe controls. Do not perform machine RCA or predictive-maintenance diagnosis."
        ),
        "iqc": "IQC route: evaluate product quality evidence and containment only.",
        "energy": (
            "Energy management route: evaluate utility load, idle running, peak demand, forecast, and bounded "
            "optimization only. Do not write PLC controls, stop production, or claim verified savings without "
            "meter baseline and production approval."
        ),
        "wi": "Work-instruction route: answer released operating guidance and escalation boundaries only.",
        "changeover": "Changeover route: evaluate SKU conversion, checklist, line-clearance, and first-piece verification only.",
    }
    return AgentRouteSelection(
        mode=resolved,
        route=resolved,
        source="analysis_mode",
        boundary=boundaries.get(resolved, "Use the selected agent route only."),
    )


def build_route_boundary_prompt_context(mode: str) -> str:
    route = select_agent_route(mode)
    if route.route == "maintenance":
        return (
            "Agent route:\n"
            "- route=maintenance; evaluate equipment condition only.\n"
            "- EHS/personnel exposure belongs to hazard agent."
        )
    return (
        "Agent route:\n"
        f"- route={route.route}; source={route.source}.\n"
        f"- boundary={route.boundary}\n"
        "Stay inside this route only."
    )


def build_mode_contract_prompt(prompt: str, mode: str) -> str:
    return get_mode_runtime(mode).build_contract_prompt(prompt)


def build_mode_repair_prompt(previous_answer: str, mode: str) -> str:
    return get_mode_runtime(mode).build_repair_prompt(previous_answer)


def check_mode_contract(answer: str, mode: str, *, min_words: int) -> ContractCheck:
    return get_mode_runtime(mode).check_contract(answer, min_words)


def mode_response_fields(
    structured: StructuredAnswer | IQCStructuredAnswer | WIStructuredAnswer | ChangeoverStructuredAnswer | MaintenanceStructuredAnswer | EnergyStructuredAnswer,
    mode: str,
) -> dict[str, object]:
    runtime = get_mode_runtime(mode)
    if runtime.mode == "maintenance":
        assert isinstance(structured, MaintenanceStructuredAnswer)
        return {
            "machine": structured.machine,
            "symptom": structured.symptom,
            "maintenance_risk": structured.maintenance_risk,
            "evidence_needed": structured.evidence_needed,
            "action": structured.action,
        }
    if runtime.mode == "iqc":
        assert isinstance(structured, IQCStructuredAnswer)
        return {
            "product": structured.product,
            "quality_risk": structured.quality_risk,
            "disposition": structured.disposition,
            "action": structured.action,
        }
    if runtime.mode == "energy":
        assert isinstance(structured, EnergyStructuredAnswer)
        return {
            "asset": structured.asset,
            "energy_signal": structured.energy_signal,
            "optimization": structured.optimization,
            "verification": structured.verification,
            "action": structured.action,
        }
    if runtime.mode == "wi":
        assert isinstance(structured, WIStructuredAnswer)
        return {
            "machine": structured.machine,
            "work_instruction": structured.work_instruction,
            "risk_control": structured.risk_control,
            "action": structured.action,
        }
    if runtime.mode == "changeover":
        assert isinstance(structured, ChangeoverStructuredAnswer)
        return {
            "machine": structured.machine,
            "sku": structured.sku,
            "changeover_step": structured.changeover_step,
            "verification": structured.verification,
            "action": structured.action,
        }
    assert isinstance(structured, StructuredAnswer)
    return {
        "scene": structured.scene,
        "risk": structured.risk,
        "action": structured.action,
    }


def decide_action(mode: str, fields: dict[str, object]) -> ActionDecision:
    return decide_action_with_context_guard(mode, fields).decision


def decide_action_with_context_guard(mode: str, fields: dict[str, object]) -> ContextGuardResult:
    resolved = resolve_agent_mode(mode)
    if resolved == "iqc":
        decision = _decide_iqc(fields)
    elif resolved == "energy":
        decision = _decide_energy(fields)
    elif resolved == "maintenance":
        decision = _decide_maintenance(fields)
    elif resolved == "wi":
        decision = _decide_wi(fields)
    elif resolved == "changeover":
        decision = _decide_changeover(fields)
    else:
        decision = _decide_hazard(fields)
    return _evaluate_context_guard(resolved, fields, decision)


def build_agent_loop_metadata(
    *,
    mode: str,
    repaired: bool,
    validation_attempts: int,
    initial_violations: list[str],
    final_violations: list[str],
    decision: ActionDecision,
    action_card: ActionCard | None = None,
    context_guard: ContextGuardResult | None = None,
    tool_plan: dict[str, object] | None = None,
    knowledge_base: dict[str, object] | None = None,
    maintenance_evaluation: dict[str, object] | None = None,
    quality_evaluation: dict[str, object] | None = None,
    source_evaluation: dict[str, object] | None = None,
    maintenance_evaluation_guard_applied: bool = False,
    iqc_quality_guard_applied: bool = False,
    source_guard_applied: bool = False,
    follow_up_plan: dict[str, object] | None = None,
) -> dict[str, object]:
    resolved_mode = resolve_agent_mode(mode)
    guard_status = context_guard.status if context_guard is not None else "clear"
    blocked_fields = list(context_guard.blocked_fields) if context_guard is not None else []
    guard_reasons = list(context_guard.reasons) if context_guard is not None else []
    tool_status = str(tool_plan.get("status", "not_recorded")) if tool_plan is not None else "not_recorded"
    selected_tools = list(tool_plan.get("selected_tools", [])) if tool_plan is not None else []
    used_tool_calls = int(tool_plan.get("used_tool_calls", 0)) if tool_plan is not None else 0
    follow_up_status = str(follow_up_plan.get("status", "not_recorded")) if follow_up_plan is not None else "not_recorded"
    follow_up_requests = follow_up_plan.get("requests", []) if follow_up_plan is not None else []
    follow_up_request_count = len(follow_up_requests) if isinstance(follow_up_requests, list) else 0
    follow_up_stage = (
        {
            "name": "build_follow_up_plan",
            "status": "completed",
            "follow_up_status": follow_up_status,
            "request_count": follow_up_request_count,
        }
        if follow_up_plan is not None
        else {"name": "build_follow_up_plan", "status": "skipped"}
    )
    action_card_stage = (
        {"name": "build_action_card", "status": "completed", "priority": action_card.priority}
        if action_card is not None
        else {"name": "build_action_card", "status": "skipped"}
    )
    kb_hits = knowledge_base.get("hits", []) if knowledge_base is not None else []
    kb_hit_count = len(kb_hits) if isinstance(kb_hits, list) else 0
    kb_source_ids = (
        [f"{hit.get('revision', 'unknown')}#{hit.get('section_id', 'section')}" for hit in kb_hits if isinstance(hit, dict)]
        if isinstance(kb_hits, list)
        else []
    )
    kb_stage = (
        {
            "name": _knowledge_base_stage_name(resolved_mode),
            "status": "completed" if knowledge_base.get("status") == "matched" else "skipped",
            "kb_status": str(knowledge_base.get("status", "not_recorded")),
            "hit_count": kb_hit_count,
        }
        if knowledge_base is not None
        else None
    )
    eval_breaches = maintenance_evaluation.get("breaches", []) if maintenance_evaluation is not None else []
    eval_breach_count = len(eval_breaches) if isinstance(eval_breaches, list) else 0
    eval_stage = (
        {
            "name": "evaluate_maintenance_thresholds",
            "status": "completed",
            "evaluation_status": str(maintenance_evaluation.get("status", "not_recorded")),
            "risk_level": str(maintenance_evaluation.get("risk_level", "not_recorded")),
            "breach_count": eval_breach_count,
        }
        if maintenance_evaluation is not None
        else None
    )
    quality_findings = quality_evaluation.get("findings", []) if quality_evaluation is not None else []
    quality_finding_count = len(quality_findings) if isinstance(quality_findings, list) else 0
    quality_eval_stage = (
        {
            "name": "evaluate_iqc_quality_rules",
            "status": "completed",
            "evaluation_status": str(quality_evaluation.get("status", "not_recorded")),
            "risk_level": str(quality_evaluation.get("risk_level", "not_recorded")),
            "finding_count": quality_finding_count,
        }
        if quality_evaluation is not None
        else None
    )
    source_eval_stage = (
        {
            "name": "evaluate_released_source",
            "status": "completed",
            "evaluation_status": str(source_evaluation.get("status", "not_recorded")),
            "source_status": str(source_evaluation.get("source_status", "not_recorded")),
            "recommended_channel": str(source_evaluation.get("recommended_channel", "")),
        }
        if source_evaluation is not None
        else None
    )
    stages = [
        {"name": "normalize_agent", "status": "completed"},
        {"name": "select_agent_route", "status": "completed", "route": resolved_mode},
        {"name": "collect_evidence", "status": "completed"},
    ]
    if kb_stage is not None:
        stages.append(kb_stage)
    if eval_stage is not None:
        stages.append(eval_stage)
    stages.extend(
        [
            {
                "name": "bounded_react_tools",
                "status": "completed" if tool_plan is not None else "skipped",
                "tool_status": tool_status,
                "selected_tools": selected_tools,
                "used_tool_calls": used_tool_calls,
            },
            {"name": "build_contract_prompt", "status": "completed"},
            {"name": "model_infer", "status": "completed", "attempts": validation_attempts},
            {
                "name": "validate_contract",
                "status": "completed",
                "attempts": validation_attempts,
                "final_violations": final_violations,
            },
            {
                "name": "repair_contract",
                "status": "completed" if repaired else "skipped",
                "initial_violations": initial_violations,
            },
            {"name": "identify_context", "status": "completed", "blocked_fields": blocked_fields},
            {"name": "structure_action", "status": "completed", "channel": decision.channel},
            {
                "name": "uncertainty_guard",
                "status": "completed" if guard_status != "clear" else "skipped",
                "guard_status": guard_status,
                "blocked_fields": blocked_fields,
            },
            quality_eval_stage
            if quality_eval_stage is not None
            else {"name": "evaluate_iqc_quality_rules", "status": "skipped"},
            source_eval_stage
            if source_eval_stage is not None
            else {"name": "evaluate_released_source", "status": "skipped"},
            {
                "name": "iqc_quality_guard",
                "status": "completed" if iqc_quality_guard_applied else "skipped",
                "evaluation_status": (
                    str(quality_evaluation.get("status", "not_recorded"))
                    if quality_evaluation is not None
                    else "not_recorded"
                ),
                "risk_level": (
                    str(quality_evaluation.get("risk_level", "not_recorded"))
                    if quality_evaluation is not None
                    else "not_recorded"
                ),
                "final_channel": decision.channel,
            },
            {
                "name": "released_source_guard",
                "status": "completed" if source_guard_applied else "skipped",
                "evaluation_status": (
                    str(source_evaluation.get("status", "not_recorded"))
                    if source_evaluation is not None
                    else "not_recorded"
                ),
                "source_status": (
                    str(source_evaluation.get("source_status", "not_recorded"))
                    if source_evaluation is not None
                    else "not_recorded"
                ),
                "final_channel": decision.channel,
            },
            {
                "name": "maintenance_evaluation_guard",
                "status": "completed" if maintenance_evaluation_guard_applied else "skipped",
                "evaluation_status": (
                    str(maintenance_evaluation.get("status", "not_recorded"))
                    if maintenance_evaluation is not None
                    else "not_recorded"
                ),
                "risk_level": (
                    str(maintenance_evaluation.get("risk_level", "not_recorded"))
                    if maintenance_evaluation is not None
                    else "not_recorded"
                ),
                "final_channel": decision.channel,
            },
            action_card_stage,
            follow_up_stage,
        ]
    )
    return {
        "version": AGENT_LOOP_VERSION,
        "mode": resolved_mode,
        "stages": stages,
        "validation_attempts": validation_attempts,
        "contract_repaired": repaired,
        "decision": decision.as_dict(),
        "context_guard": {
            "status": guard_status,
            "blocked_fields": blocked_fields,
            "reasons": guard_reasons,
        },
        "route_selection": select_agent_route(mode).as_dict(),
        "tool_plan": {
            "status": tool_status,
            "selected_tools": selected_tools,
            "used_tool_calls": used_tool_calls,
        },
        "knowledge_base": {
            "status": str(knowledge_base.get("status", "not_recorded")) if knowledge_base is not None else "not_recorded",
            "hit_count": kb_hit_count,
            "source_ids": kb_source_ids,
        },
        "maintenance_evaluation": {
            "status": (
                str(maintenance_evaluation.get("status", "not_recorded"))
                if maintenance_evaluation is not None
                else "not_recorded"
            ),
            "risk_level": (
                str(maintenance_evaluation.get("risk_level", "not_recorded"))
                if maintenance_evaluation is not None
                else "not_recorded"
            ),
            "breach_count": eval_breach_count,
            "recommended_channel": (
                str(maintenance_evaluation.get("recommended_channel", ""))
                if maintenance_evaluation is not None
                else ""
            ),
        },
        "quality_evaluation": {
            "status": (
                str(quality_evaluation.get("status", "not_recorded"))
                if quality_evaluation is not None
                else "not_recorded"
            ),
            "risk_level": (
                str(quality_evaluation.get("risk_level", "not_recorded"))
                if quality_evaluation is not None
                else "not_recorded"
            ),
            "finding_count": quality_finding_count,
            "detector_status": (
                str(quality_evaluation.get("detector_status", ""))
                if quality_evaluation is not None
                else ""
            ),
            "recommended_channel": (
                str(quality_evaluation.get("recommended_channel", ""))
                if quality_evaluation is not None
                else ""
            ),
        },
        "source_evaluation": {
            "status": (
                str(source_evaluation.get("status", "not_recorded"))
                if source_evaluation is not None
                else "not_recorded"
            ),
            "source_status": (
                str(source_evaluation.get("source_status", "not_recorded"))
                if source_evaluation is not None
                else "not_recorded"
            ),
            "recommended_channel": (
                str(source_evaluation.get("recommended_channel", ""))
                if source_evaluation is not None
                else ""
            ),
        },
        "follow_up_plan": {
            "status": follow_up_status,
            "request_count": follow_up_request_count,
            "next_action": str(follow_up_plan.get("next_action", "")) if follow_up_plan is not None else "",
        },
    }


def _knowledge_base_stage_name(mode: str) -> str:
    if mode == "maintenance":
        return "retrieve_maintenance_kb"
    if mode == "iqc":
        return "retrieve_iqc_quality_plan"
    if mode == "wi":
        return "retrieve_released_wi_source"
    if mode == "changeover":
        return "retrieve_changeover_checklist"
    return "retrieve_knowledge_base"


def build_action_card(mode: str, fields: dict[str, object], decision: ActionDecision) -> ActionCard:
    resolved = resolve_agent_mode(mode)
    priority = _priority_for(decision.channel)
    integration_target = _integration_target_for(resolved, decision.channel)
    evidence_fields = tuple(key for key, value in fields.items() if key != "action" and _field_text(fields, key))
    return ActionCard(
        version=ACTION_CARD_VERSION,
        mode=resolved,
        channel=decision.channel,
        title=_action_title(resolved, decision.channel),
        priority=priority,
        owner=decision.owner,
        requires_human=decision.requires_human,
        operator_message=_operator_message(resolved, fields, decision),
        integration_target=integration_target,
        required_confirmations=_required_confirmations(resolved, decision.channel),
        evidence_fields=evidence_fields,
    )


def build_integration_event(
    *,
    request_id: str,
    device: dict[str, object],
    mode: str,
    fields: dict[str, object],
    action_card: ActionCard,
    follow_up_plan: dict[str, object] | None = None,
    knowledge_base: dict[str, object] | None = None,
    detector_evidence: dict[str, object] | None = None,
    maintenance_evaluation: dict[str, object] | None = None,
    quality_evaluation: dict[str, object] | None = None,
    source_evaluation: dict[str, object] | None = None,
) -> IntegrationEvent:
    target = action_card.integration_target
    event_type = _event_type_for(target, action_card.channel)
    routing_key = _routing_key_for(target, action_card.owner, action_card.channel)
    status = _integration_status(action_card)
    payload = {
        "request_id": request_id,
        "analysis_mode": resolve_agent_mode(mode),
        "device": device,
        "action_card": action_card.as_dict(),
        "evidence": {key: fields[key] for key in action_card.evidence_fields if key in fields},
        "action": _field_text(fields, "action"),
    }
    if follow_up_plan is not None:
        payload["follow_up_plan"] = follow_up_plan
    if knowledge_base is not None:
        payload["knowledge_base"] = knowledge_base
    if detector_evidence is not None:
        payload["detector_evidence"] = detector_evidence
    if maintenance_evaluation is not None:
        payload["maintenance_evaluation"] = maintenance_evaluation
    if quality_evaluation is not None:
        payload["quality_evaluation"] = quality_evaluation
    if source_evaluation is not None:
        payload["source_evaluation"] = source_evaluation
    return IntegrationEvent(
        version=INTEGRATION_EVENT_VERSION,
        event_type=event_type,
        target=target,
        routing_key=routing_key,
        status=status,
        idempotency_key=f"{request_id}:{target}:{action_card.channel}",
        requires_human=action_card.requires_human,
        payload=payload,
    )


def _decide_hazard(fields: dict[str, object]) -> ActionDecision:
    action = _field_text(fields, "action")
    if _starts(action, "Stop"):
        return ActionDecision("stop_and_make_safe", "operator", True, "hazard action starts with Stop")
    if _starts(action, "Report"):
        return ActionDecision("ehs_report", "ehs", True, "hazard action starts with Report")
    if _starts(action, "Wear"):
        return ActionDecision("ppe_control", "operator", False, "hazard action starts with Wear")
    if _starts(action, "Inspect"):
        return ActionDecision("inspect_area", "operator", False, "hazard action starts with Inspect")
    return ActionDecision("continue_with_controls", "operator", False, "hazard action stays within Keep controls")


def _decide_iqc(fields: dict[str, object]) -> ActionDecision:
    disposition = _field_text(fields, "disposition").lower()
    decisions = {
        "pass": ActionDecision("continue_production", "operator", False, "IQC disposition is pass"),
        "needs_review": ActionDecision("quality_review", "quality_engineer", True, "IQC disposition needs review"),
        "expand_inspection": ActionDecision(
            "expand_inspection", "quality_engineer", True, "IQC disposition expands sampling or containment"
        ),
        "quality_hold": ActionDecision("quality_hold", "quality_engineer", True, "IQC disposition requires quality hold"),
        "stop_production": ActionDecision(
            "stop_production", "shift_lead", True, "IQC disposition requires production stop decision"
        ),
        "rework": ActionDecision("rework_hold", "quality_engineer", True, "IQC disposition routes suspect units to rework"),
        "scrap": ActionDecision("scrap_review", "quality_engineer", True, "IQC disposition requires scrap authority"),
        "capa_request": ActionDecision("capa_request", "quality_engineer", True, "IQC disposition requests CAPA review"),
    }
    return decisions.get(
        disposition,
        ActionDecision("quality_review", "quality_engineer", True, "IQC disposition is unknown or unsupported"),
    )


def _decide_energy(fields: dict[str, object]) -> ActionDecision:
    action = _field_text(fields, "action")
    if _starts(action, "Reduce"):
        return ActionDecision(
            "energy_reduce_load",
            "energy_manager",
            True,
            "energy action starts with Reduce and needs production/energy confirmation",
        )
    if _starts(action, "Shift", "Schedule"):
        return ActionDecision(
            "energy_schedule_optimization",
            "production_planner",
            True,
            "energy action shifts or schedules load and needs production confirmation",
        )
    if _starts(action, "Report"):
        return ActionDecision("energy_report", "energy_manager", True, "energy action starts with Report")
    if _starts(action, "Hold"):
        return ActionDecision("energy_hold", "production_lead", True, "energy action starts with Hold")
    if _starts(action, "Inspect"):
        return ActionDecision("energy_inspection", "operator", False, "energy action starts with Inspect")
    return ActionDecision("energy_monitoring", "operator", False, "energy action stays within Keep monitoring")


def _decide_maintenance(fields: dict[str, object]) -> ActionDecision:
    action = _field_text(fields, "action")
    if _starts(action, "Stop"):
        return ActionDecision("maintenance_stop", "maintenance_engineer", True, "maintenance action starts with Stop")
    if _starts(action, "Escalate"):
        return ActionDecision(
            "maintenance_escalation", "maintenance_engineer", True, "maintenance action starts with Escalate"
        )
    if _starts(action, "Schedule"):
        return ActionDecision(
            "schedule_maintenance", "maintenance_planner", True, "maintenance action starts with Schedule"
        )
    if _starts(action, "Report"):
        return ActionDecision("maintenance_report", "maintenance_engineer", True, "maintenance action starts with Report")
    if _contains(action, "escalate", "senior maintenance engineer", "urgent assessment"):
        return ActionDecision(
            "maintenance_escalation",
            "maintenance_engineer",
            True,
            "maintenance action contains escalation language",
        )
    if _starts(action, "Monitor"):
        return _apply_maintenance_severity_rule(
            fields,
            ActionDecision("condition_monitoring", "operator", False, "maintenance action starts with Monitor"),
        )
    if _starts(action, "Inspect"):
        return _apply_maintenance_severity_rule(
            fields,
            ActionDecision("condition_inspection", "operator", False, "maintenance action starts with Inspect"),
        )
    return _apply_maintenance_severity_rule(
        fields,
        ActionDecision("continue_with_monitoring", "operator", False, "maintenance action stays within Keep controls"),
    )


def _decide_wi(fields: dict[str, object]) -> ActionDecision:
    action = _field_text(fields, "action")
    if _starts(action, "Stop"):
        return ActionDecision("wi_stop", "operator", True, "WI action starts with Stop")
    if _starts(action, "Ask", "Report", "Escalate"):
        return ActionDecision("wi_human_support", "line_lead", True, "WI action requests human support")
    return ActionDecision("guided_operation", "operator", False, "WI action remains within guided operation")


def _decide_changeover(fields: dict[str, object]) -> ActionDecision:
    action = _field_text(fields, "action")
    if _starts(action, "Stop", "Hold"):
        return ActionDecision("changeover_hold", "line_lead", True, "changeover action starts with Stop or Hold")
    if _starts(action, "Report", "Escalate"):
        return ActionDecision("changeover_escalation", "line_lead", True, "changeover action requests escalation")
    if _starts(action, "Verify", "Confirm"):
        return ActionDecision("changeover_verification", "operator_quality", True, "changeover action requires verification")
    return ActionDecision("controlled_changeover_step", "operator", False, "changeover action stays within controlled setup")


def _apply_maintenance_severity_rule(fields: dict[str, object], decision: ActionDecision) -> ActionDecision:
    if decision.requires_human:
        return decision

    severity_text = " ".join(
        _field_text(fields, key) for key in ("machine", "symptom", "maintenance_risk", "action")
    ).lower()
    critical_markers = (
        "red alarm",
        "smoke",
        "burning",
        "fire",
        "overtemperature trip",
        "imminent mechanical failure",
        "catastrophic component damage",
        "catastrophic equipment downtime",
        "senior maintenance engineer",
        "urgent assessment",
        "e-stop",
        "emergency stop",
        "severe leak",
    )
    if any(marker in severity_text for marker in critical_markers):
        return ActionDecision(
            "maintenance_escalation",
            "maintenance_engineer",
            True,
            f"{decision.reason}; severity rule found critical maintenance indicator",
        )

    alarm_markers = ("yellow plc alarm", "amber plc alarm", "yellow alarm", "amber alarm", "active alarm")
    condition_markers = (
        "vib rms",
        "vibration rms",
        "trend rising",
        "high vibration",
        "overheat",
        "overheating",
        "temperature",
        "temp ",
        "oil stain",
        "oil leak",
        "leaked oil",
        "lubrication starvation",
        "belt wear",
        "frayed",
    )
    has_alarm = any(marker in severity_text for marker in alarm_markers)
    has_condition = any(marker in severity_text for marker in condition_markers)
    if has_alarm and has_condition:
        return ActionDecision(
            "maintenance_report",
            "maintenance_engineer",
            True,
            f"{decision.reason}; severity rule found alarm plus maintenance condition evidence",
        )
    if has_alarm:
        return ActionDecision(
            "maintenance_report",
            "maintenance_engineer",
            True,
            f"{decision.reason}; severity rule found active warning alarm",
        )
    return decision


def _evaluate_context_guard(mode: str, fields: dict[str, object], decision: ActionDecision) -> ContextGuardResult:
    blocked_fields = _blocked_context_fields(mode, fields)
    if not blocked_fields:
        return ContextGuardResult(
            status="clear",
            blocked_fields=(),
            reasons=(),
            original_decision=decision,
            decision=decision,
        )

    reason_text = _guard_reason(mode, blocked_fields)
    if decision.requires_human:
        guarded = ActionDecision(
            decision.channel,
            decision.owner,
            True,
            f"{decision.reason}; context guard: {reason_text}",
        )
    else:
        guarded = _identification_required_decision(mode, reason_text)
    return ContextGuardResult(
        status="human_confirm_required",
        blocked_fields=blocked_fields,
        reasons=(reason_text,),
        original_decision=decision,
        decision=guarded,
    )


def _blocked_context_fields(mode: str, fields: dict[str, object]) -> tuple[str, ...]:
    checks = {
        "hazard": ("scene", "risk"),
        "maintenance": ("machine",),
        "iqc": ("product", "quality_risk"),
        "energy": ("asset", "energy_signal"),
        "wi": ("machine", "work_instruction"),
        "changeover": ("machine", "sku", "changeover_step"),
    }
    watched_fields = checks.get(mode, ())
    return tuple(field for field in watched_fields if _is_unknownish(_field_text(fields, field)))


def _guard_reason(mode: str, blocked_fields: tuple[str, ...]) -> str:
    fields = ", ".join(blocked_fields)
    if mode == "iqc":
        return f"{fields} must be identified before any IQC release or containment disposition is trusted"
    if mode == "maintenance":
        return f"{fields} must be identified before this maintenance recommendation can be treated as machine-specific"
    if mode == "energy":
        return f"{fields} must be identified before this energy recommendation can be treated as production-ready"
    if mode == "wi":
        return f"{fields} must be identified before operator guidance can be followed"
    if mode == "changeover":
        return f"{fields} must be identified before changeover can continue or restart"
    return f"{fields} must be identified before hazard exposure can be downgraded"


def _identification_required_decision(mode: str, reason: str) -> ActionDecision:
    if mode == "iqc":
        return ActionDecision("quality_review", "quality_engineer", True, f"context guard: {reason}")
    if mode == "maintenance":
        return ActionDecision(
            "maintenance_identification_required",
            "maintenance_engineer",
            True,
            f"context guard: {reason}",
        )
    if mode == "energy":
        return ActionDecision("energy_review", "energy_manager", True, f"context guard: {reason}")
    if mode == "wi":
        return ActionDecision("wi_identification_required", "line_lead", True, f"context guard: {reason}")
    if mode == "changeover":
        return ActionDecision(
            "changeover_identification_required",
            "operator_quality",
            True,
            f"context guard: {reason}",
        )
    return ActionDecision("hazard_identification_required", "operator", True, f"context guard: {reason}")


def _field_text(fields: dict[str, object], key: str) -> str:
    return str(fields.get(key) or "").strip()


def _starts(value: str, *starters: str) -> bool:
    lowered = value.lower()
    return any(lowered.startswith(starter.lower()) for starter in starters)


def _contains(value: str, *needles: str) -> bool:
    lowered = value.lower()
    return any(needle.lower() in lowered for needle in needles)


def _is_unknownish(value: str) -> bool:
    normalized = " ".join(value.lower().replace("-", " ").replace("_", " ").split())
    if not normalized:
        return True
    if normalized in {"unknown", "none", "n/a", "na", "not available", "unavailable"}:
        return True
    markers = (
        "unknown",
        "unidentified",
        "not identified",
        "not available",
        "not visible",
        "not readable",
        "not fully readable",
        "unreadable",
        "unavailable",
        "unclear",
        "cannot determine",
        "can't determine",
        "insufficient",
        "not enough",
    )
    return any(marker in normalized for marker in markers)


def _priority_for(channel: str) -> str:
    if channel in {
        "stop_and_make_safe",
        "maintenance_stop",
        "stop_production",
        "changeover_hold",
        "wi_stop",
    }:
        return "critical"
    if channel in {
        "ehs_report",
        "quality_hold",
        "maintenance_escalation",
        "changeover_escalation",
        "capa_request",
        "energy_reduce_load",
        "energy_hold",
        }:
        return "high"
    if channel in {
        "expand_inspection",
        "quality_review",
        "schedule_maintenance",
        "maintenance_report",
        "changeover_verification",
        "changeover_identification_required",
        "hazard_identification_required",
        "maintenance_identification_required",
        "rework_hold",
        "scrap_review",
        "wi_human_support",
        "wi_identification_required",
        "wi_source_required",
        "changeover_source_required",
        "energy_schedule_optimization",
        "energy_report",
        "energy_review",
        }:
        return "medium"
    return "low"


def _integration_target_for(mode: str, channel: str) -> str:
    if mode == "iqc":
        if channel == "continue_production":
            return "none"
        return "qms_quality_event"
    if mode == "maintenance":
        if channel in {
            "condition_inspection",
            "condition_monitoring",
            "continue_with_monitoring",
            "maintenance_identification_required",
        }:
            return "cmms_observation"
        return "maintenance_work_order"
    if mode == "energy":
        if channel in {"energy_inspection", "energy_monitoring"}:
            return "energy_observation"
        return "energy_management_event"
    if mode == "changeover":
        return "changeover_checklist"
    if mode == "wi":
        return "wi_reference"
    if channel in {"ehs_report", "stop_and_make_safe"}:
        return "ehs_case"
    return "safety_observation"


def _required_confirmations(mode: str, channel: str) -> tuple[str, ...]:
    if mode == "iqc":
        base = ("product identity", "lot or batch", "quality authority")
        if channel == "continue_production":
            return ("product identity", "sampling plan")
        if channel == "stop_production":
            return (*base, "shift lead approval")
        return base
    if mode == "maintenance":
        base = ("machine identity", "manual or signal evidence")
        if channel in {"maintenance_stop", "maintenance_escalation"}:
            return (*base, "maintenance engineer approval")
        if channel == "schedule_maintenance":
            return (*base, "maintenance window")
        return base
    if mode == "energy":
        base = ("asset identity", "meter baseline", "production schedule")
        if channel in {"energy_reduce_load", "energy_schedule_optimization", "energy_hold"}:
            return (*base, "energy manager approval", "production lead approval")
        return base
    if mode == "changeover":
        if channel == "changeover_source_required":
            return ("machine identity", "target SKU", "released checklist", "operator quality confirmation")
        return ("machine identity", "target SKU", "line clearance", "first-piece verification")
    if mode == "wi":
        if channel in {"wi_stop", "wi_human_support", "wi_identification_required", "wi_source_required"}:
            return ("machine identity", "current WI revision", "line lead confirmation")
        return ("machine identity", "current WI revision")
    if channel == "hazard_identification_required":
        return ("area identity", "exposure controlled", "supervisor confirmation")
    if channel in {"stop_and_make_safe", "ehs_report"}:
        return ("area identity", "exposure controlled", "supervisor or EHS confirmation")
    return ("area identity", "operator confirmation")


def _action_title(mode: str, channel: str) -> str:
    titles = {
        "continue_production": "Continue production under IQC controls",
        "quality_review": "Send product to quality review",
        "expand_inspection": "Expand inspection and contain suspect units",
        "quality_hold": "Place product on quality hold",
        "stop_production": "Stop production for quality containment",
        "rework_hold": "Hold product for rework disposition",
        "scrap_review": "Hold product for scrap authority review",
        "capa_request": "Open CAPA review request",
        "energy_reduce_load": "Review energy load reduction",
        "energy_schedule_optimization": "Review energy schedule optimization",
        "energy_report": "Report energy anomaly",
        "energy_hold": "Hold energy control action",
        "energy_review": "Confirm energy asset and baseline",
        "energy_inspection": "Inspect energy signal",
        "energy_monitoring": "Continue energy monitoring",
        "maintenance_stop": "Stop machine for maintenance risk",
        "maintenance_escalation": "Escalate machine condition to maintenance",
        "schedule_maintenance": "Schedule maintenance inspection",
        "maintenance_report": "Report machine condition to maintenance",
        "maintenance_identification_required": "Confirm machine before maintenance action",
        "condition_monitoring": "Monitor machine condition",
        "condition_inspection": "Inspect machine condition",
        "continue_with_monitoring": "Continue with maintenance monitoring",
        "changeover_hold": "Hold changeover until confirmed",
        "changeover_escalation": "Escalate changeover issue",
        "changeover_identification_required": "Confirm machine and SKU before changeover",
        "changeover_source_required": "Confirm released changeover source",
        "changeover_verification": "Verify changeover before restart",
        "controlled_changeover_step": "Continue controlled changeover step",
        "wi_stop": "Stop and confirm work instruction",
        "wi_human_support": "Ask line lead for WI support",
        "wi_identification_required": "Confirm machine and WI source",
        "wi_source_required": "Confirm released WI source",
        "guided_operation": "Continue guided operation",
        "stop_and_make_safe": "Stop and make area safe",
        "ehs_report": "Report hazard exposure",
        "hazard_identification_required": "Confirm area and hazard evidence",
        "ppe_control": "Apply PPE control",
        "inspect_area": "Inspect area before continuing",
        "continue_with_controls": "Continue with hazard controls",
    }
    return titles.get(channel, f"Handle {mode} action")


def _operator_message(mode: str, fields: dict[str, object], decision: ActionDecision) -> str:
    action = _field_text(fields, "action")
    if mode == "iqc":
        context = _field_text(fields, "disposition") or decision.channel
        if "context guard:" in decision.reason:
            return f"{action} Do not release product until product identity and quality evidence are confirmed by {decision.owner}."
        return f"{action} Route as {context}; do not release final disposition without {decision.owner} confirmation."
    if mode == "maintenance":
        if decision.channel == "maintenance_identification_required":
            return f"Confirm machine identity and missing evidence before applying maintenance guidance. Original action: {action}"
        evidence = _field_text(fields, "evidence_needed")
        if evidence:
            return f"{action} Evidence needed: {evidence}"
        return action
    if mode == "energy":
        if decision.channel == "energy_review":
            return f"Confirm asset identity, meter baseline, and production schedule before applying energy guidance. Original action: {action}"
        verification = _field_text(fields, "verification")
        if verification:
            return f"{action} Verification required: {verification}"
        return action
    if mode == "changeover":
        if decision.channel in {"changeover_identification_required", "changeover_source_required"}:
            return f"Confirm machine identity, target SKU evidence, and checklist source before continuing changeover. Original action: {action}"
        verification = _field_text(fields, "verification")
        if verification:
            return f"{action} Verification before restart: {verification}"
        return action
    if mode == "wi":
        if decision.channel in {"wi_identification_required", "wi_source_required"}:
            return f"Confirm machine identity and current WI revision before following guidance. Original action: {action}"
        control = _field_text(fields, "risk_control")
        if control:
            return f"{action} Respect control: {control}"
        return action
    if decision.channel == "hazard_identification_required":
        return f"Confirm area identity and visible hazard evidence before downgrading exposure. Original action: {action}"
    return action


def _event_type_for(target: str, channel: str) -> str:
    if target == "none":
        return "none"
    prefixes = {
        "qms_quality_event": "qms",
        "maintenance_work_order": "cmms",
        "cmms_observation": "cmms",
        "energy_management_event": "ems",
        "energy_observation": "ems",
        "changeover_checklist": "mes",
        "wi_reference": "wi",
        "ehs_case": "ehs",
        "safety_observation": "ehs",
    }
    prefix = prefixes.get(target, "wear_edge")
    return f"{prefix}.{channel}.requested"


def _routing_key_for(target: str, owner: str, channel: str) -> str:
    if target == "none":
        return "none"
    return f"{target}.{owner}.{channel}"


def _integration_status(action_card: ActionCard) -> str:
    if action_card.integration_target == "none":
        return "no_external_action"
    if action_card.requires_human:
        return "pending_human_confirmation"
    return "ready_for_dispatch"
