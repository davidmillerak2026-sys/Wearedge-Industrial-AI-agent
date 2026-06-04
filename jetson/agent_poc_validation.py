from __future__ import annotations

from dataclasses import dataclass

from .agently_orchestrator import run_m400_agently_workflow


@dataclass(frozen=True)
class FakeModelResponse:
    answer: str
    latency_ms: int


@dataclass(frozen=True)
class AgentPOCScenario:
    mode: str
    title: str
    prompt: str
    answer: str
    expected_fields: tuple[str, ...]
    expected_channel: str
    expected_owner: str
    expected_target: str
    expected_priority: str
    expected_requires_human: bool
    image_bytes: int
    needs_ocr: bool = False
    high_detail: bool = False
    expected_tool_status: str = "missing_tool_connections"
    expected_selected_tools: tuple[str, ...] = ()
    expected_context_guard_status: str | None = "clear"
    expected_blocked_fields: tuple[str, ...] = ()
    expected_follow_up_status: str | None = None


@dataclass(frozen=True)
class AgentPOCResult:
    mode: str
    title: str
    passed: bool
    failures: tuple[str, ...]
    action_channel: str
    owner: str
    integration_target: str
    priority: str
    requires_human: bool
    tool_status: str
    selected_tools: tuple[str, ...]
    context_guard_status: str
    blocked_fields: tuple[str, ...]
    follow_up_status: str
    follow_up_request_count: int
    runtime_event_count: int
    runtime_last_event: str
    request_id: str

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "title": self.title,
            "passed": self.passed,
            "failures": list(self.failures),
            "action_channel": self.action_channel,
            "owner": self.owner,
            "integration_target": self.integration_target,
            "priority": self.priority,
            "requires_human": self.requires_human,
            "tool_status": self.tool_status,
            "selected_tools": list(self.selected_tools),
            "context_guard_status": self.context_guard_status,
            "blocked_fields": list(self.blocked_fields),
            "follow_up_status": self.follow_up_status,
            "follow_up_request_count": self.follow_up_request_count,
            "runtime_event_count": self.runtime_event_count,
            "runtime_last_event": self.runtime_last_event,
            "request_id": self.request_id,
        }


POC_SCENARIOS: tuple[AgentPOCScenario, ...] = (
    AgentPOCScenario(
        mode="maintenance",
        title="lao-shi-fu predictive maintenance",
        prompt=(
            "M400 sees a packaging line drive station with residue near the gearbox. "
            "Assess predictive-maintenance risk without inventing hidden readings."
        ),
        answer=(
            "- Machine: Packaging line drive station with gearbox guard, motor housing, coupling cover, and residue near the base area.\n"
            "- Symptom: Residue appears around the gearbox base and nearby floor, suggesting a visible leak indicator without confirmed pressure readings.\n"
            "- Maintenance Risk: Possible lubricant loss or seal degradation could increase heat, vibration, contamination, and unplanned downtime risk over time.\n"
            "- Evidence Needed: Check gearbox manual inspection points, lubricant level trend, vibration history, operator notes, and recent alarm log before assigning cause.\n"
            "- Action: Schedule a maintenance inspection during the next controlled window after verifying leak source, vibration trend, and manual alarm history."
        ),
        expected_fields=("machine", "symptom", "maintenance_risk", "evidence_needed", "action"),
        expected_channel="schedule_maintenance",
        expected_owner="maintenance_planner",
        expected_target="maintenance_work_order",
        expected_priority="medium",
        expected_requires_human=True,
        image_bytes=1_200_000,
        high_detail=True,
    ),
    AgentPOCScenario(
        mode="iqc",
        title="online quality inspection",
        prompt=(
            "M400 captures an in-process machined housing after station output. "
            "Assess visible quality risk and containment action."
        ),
        answer=(
            "- Product: Machined aluminum housing shows visible edge burrs, uneven sealing surface marks, and possible handling contamination after station output.\n"
            "- Quality Risk: Burrs and contamination near the sealing face could create assembly leakage, downstream rework, and customer escape risk.\n"
            "- Disposition: quality_hold\n"
            "- Action: Hold suspect housings from the same station lot and shift while quality reviews containment evidence before release."
        ),
        expected_fields=("product", "quality_risk", "disposition", "action"),
        expected_channel="quality_hold",
        expected_owner="quality_engineer",
        expected_target="qms_quality_event",
        expected_priority="high",
        expected_requires_human=True,
        image_bytes=1_600_000,
        needs_ocr=True,
        high_detail=True,
    ),
    AgentPOCScenario(
        mode="changeover",
        title="changeover guidance",
        prompt=(
            "M400 sees a filling station during SKU conversion. "
            "Guide the operator through the next controlled changeover step."
        ),
        answer=(
            "- Machine: Filling line station one with guide rails, change part tray, control panel, and label reference visible near operator.\n"
            "- SKU: Target SKU is not fully readable, but visible label reference and change parts indicate a controlled conversion.\n"
            "- Changeover Step: Confirm line clearance, match visible change parts to the approved checklist, and avoid changing hidden recipe parameters.\n"
            "- Verification: Check machine identity, target SKU evidence, guide alignment, label match, and first-piece verification before restart authorization.\n"
            "- Action: Confirm the target SKU evidence and checklist step with operator quality before restarting the converted station."
        ),
        expected_fields=("machine", "sku", "changeover_step", "verification", "action"),
        expected_channel="changeover_verification",
        expected_owner="operator_quality",
        expected_target="changeover_checklist",
        expected_priority="medium",
        expected_requires_human=True,
        image_bytes=1_400_000,
        needs_ocr=True,
        high_detail=True,
        expected_context_guard_status="human_confirm_required",
        expected_blocked_fields=("sku",),
    ),
    AgentPOCScenario(
        mode="wi",
        title="general work instruction",
        prompt=(
            "M400 sees a cartoner station and the operator asks for safe operating points. "
            "Answer with bounded work-instruction guidance."
        ),
        answer=(
            "- Machine: Cartoner station two appears visible with operator panel, infeed guide, guard door, and product transfer area in view.\n"
            "- Work Instruction: Verify visible guide alignment, confirm the current work instruction revision, and keep hands outside guarded transfer areas.\n"
            "- Risk Control: Safety guard status, product orientation, tooling clearance, and escalation rules must be respected before touching machine settings.\n"
            "- Action: Follow the current work instruction revision while confirming guide alignment and keeping hands outside the guarded transfer area."
        ),
        expected_fields=("machine", "work_instruction", "risk_control", "action"),
        expected_channel="guided_operation",
        expected_owner="operator",
        expected_target="wi_reference",
        expected_priority="low",
        expected_requires_human=False,
        image_bytes=900_000,
        high_detail=True,
    ),
    AgentPOCScenario(
        mode="hazard",
        title="hazard exposure",
        prompt=(
            "M400 sees an operator near a blocked walkway and moving equipment. "
            "Identify immediate hazard exposure and safe next action."
        ),
        answer=(
            "- Scene: Operator is standing beside moving equipment with loose packaging, blocked walkway space, and restricted access path near controls.\n"
            "- Risk: Trip obstruction and proximity to moving equipment could expose the operator to fall, pinch, or restart hazards.\n"
            "- Action: Stop and make the area safe by clearing packaging, controlling access, and confirming supervisor awareness before continuing work."
        ),
        expected_fields=("scene", "risk", "action"),
        expected_channel="stop_and_make_safe",
        expected_owner="operator",
        expected_target="ehs_case",
        expected_priority="critical",
        expected_requires_human=True,
        image_bytes=850_000,
    ),
)


MAINTENANCE_TOOLS = ("asset_registry", "telemetry_history", "manual_kb")
IQC_TOOLS = ("visual_defect_detector", "quality_plan", "lot_context")
CHANGEOVER_TOOLS = ("sku_recipe", "changeover_checklist", "first_piece_plan")
WI_TOOLS = ("wi_repository", "machine_identity")
HAZARD_TOOLS = ("ppe_detector", "zone_geofence", "ehs_rules")


def _maintenance_case(
    *,
    title: str,
    action: str,
    expected_channel: str,
    expected_owner: str,
    expected_target: str,
    expected_priority: str,
    expected_requires_human: bool,
    machine: str = "Packaging line drive station with gearbox guard, motor housing, coupling cover, and residue near the base area.",
    expected_context_guard_status: str = "clear",
    expected_blocked_fields: tuple[str, ...] = (),
) -> AgentPOCScenario:
    return AgentPOCScenario(
        mode="maintenance",
        title=title,
        prompt="Golden maintenance scenario for bounded predictive-maintenance routing.",
        answer=(
            f"- Machine: {machine}\n"
            "- Symptom: Visible residue, vibration marks, and dust collection around the gearbox base suggest an abnormal condition requiring safe inspection.\n"
            "- Maintenance Risk: Possible lubricant loss, seal wear, heat buildup, or vibration growth could increase downtime risk if ignored.\n"
            "- Evidence Needed: Check asset identity, released manual inspection points, vibration trend, operator notes, and recent alarm history before assigning cause.\n"
            f"- Action: {action}"
        ),
        expected_fields=("machine", "symptom", "maintenance_risk", "evidence_needed", "action"),
        expected_channel=expected_channel,
        expected_owner=expected_owner,
        expected_target=expected_target,
        expected_priority=expected_priority,
        expected_requires_human=expected_requires_human,
        image_bytes=1_100_000,
        high_detail=True,
        expected_selected_tools=MAINTENANCE_TOOLS,
        expected_context_guard_status=expected_context_guard_status,
        expected_blocked_fields=expected_blocked_fields,
    )


def _iqc_case(
    *,
    title: str,
    disposition: str,
    action: str,
    expected_channel: str,
    expected_owner: str,
    expected_target: str,
    expected_priority: str,
    expected_requires_human: bool,
    product: str = "Machined aluminum housing from line three shows visible sealing face, edges, and handling contact areas after station output.",
    quality_risk: str = "Visible burrs, sealing surface marks, or handling contamination could create assembly leakage and downstream customer escape risk.",
    expected_context_guard_status: str = "clear",
    expected_blocked_fields: tuple[str, ...] = (),
) -> AgentPOCScenario:
    return AgentPOCScenario(
        mode="iqc",
        title=title,
        prompt="Golden IQC scenario that must respect detector-first evidence boundaries.",
        answer=(
            f"- Product: {product}\n"
            f"- Quality Risk: {quality_risk}\n"
            f"- Disposition: {disposition}\n"
            f"- Action: {action}"
        ),
        expected_fields=("product", "quality_risk", "disposition", "action"),
        expected_channel=expected_channel,
        expected_owner=expected_owner,
        expected_target=expected_target,
        expected_priority=expected_priority,
        expected_requires_human=expected_requires_human,
        image_bytes=1_600_000,
        needs_ocr=True,
        high_detail=True,
        expected_selected_tools=IQC_TOOLS,
        expected_context_guard_status=expected_context_guard_status,
        expected_blocked_fields=expected_blocked_fields,
    )


def _changeover_case(
    *,
    title: str,
    action: str,
    expected_channel: str,
    expected_owner: str,
    expected_priority: str,
    expected_requires_human: bool,
    machine: str = "Filling line station one with guide rails, change part tray, control panel, and label reference visible near operator.",
    sku: str = "Target SKU SKU-C500 is visible on the traveler beside the released C500 conversion checklist and change part tray.",
    changeover_step: str = "Match visible change parts to the released checklist, confirm line clearance, and avoid hidden recipe parameter changes.",
    expected_context_guard_status: str = "clear",
    expected_blocked_fields: tuple[str, ...] = (),
) -> AgentPOCScenario:
    return AgentPOCScenario(
        mode="changeover",
        title=title,
        prompt="Golden changeover scenario that checks machine, SKU, and checklist-source boundaries.",
        answer=(
            f"- Machine: {machine}\n"
            f"- SKU: {sku}\n"
            f"- Changeover Step: {changeover_step}\n"
            "- Verification: Check machine identity, target SKU evidence, guide alignment, label match, and first-piece verification before restart authorization.\n"
            f"- Action: {action}"
        ),
        expected_fields=("machine", "sku", "changeover_step", "verification", "action"),
        expected_channel=expected_channel,
        expected_owner=expected_owner,
        expected_target="changeover_checklist",
        expected_priority=expected_priority,
        expected_requires_human=expected_requires_human,
        image_bytes=1_400_000,
        needs_ocr=True,
        high_detail=True,
        expected_selected_tools=CHANGEOVER_TOOLS,
        expected_context_guard_status=expected_context_guard_status,
        expected_blocked_fields=expected_blocked_fields,
    )


def _wi_case(
    *,
    title: str,
    action: str,
    expected_channel: str,
    expected_owner: str,
    expected_priority: str,
    expected_requires_human: bool,
    machine: str = "Cartoner station two appears visible with operator panel, infeed guide, guard door, and product transfer area.",
    work_instruction: str = "Released WI revision WI-CT-200 says verify guide alignment, confirm product orientation, and keep hands outside guarded transfer areas.",
    expected_context_guard_status: str = "clear",
    expected_blocked_fields: tuple[str, ...] = (),
) -> AgentPOCScenario:
    return AgentPOCScenario(
        mode="wi",
        title=title,
        prompt="Golden WI scenario that checks released source and safe operator guidance boundaries.",
        answer=(
            f"- Machine: {machine}\n"
            f"- Work Instruction: {work_instruction}\n"
            "- Risk Control: Safety guard status, product orientation, tooling clearance, and escalation rules must be respected before touching settings.\n"
            f"- Action: {action}"
        ),
        expected_fields=("machine", "work_instruction", "risk_control", "action"),
        expected_channel=expected_channel,
        expected_owner=expected_owner,
        expected_target="wi_reference",
        expected_priority=expected_priority,
        expected_requires_human=expected_requires_human,
        image_bytes=950_000,
        high_detail=True,
        expected_selected_tools=WI_TOOLS,
        expected_context_guard_status=expected_context_guard_status,
        expected_blocked_fields=expected_blocked_fields,
    )


def _hazard_case(
    *,
    title: str,
    action: str,
    expected_channel: str,
    expected_owner: str,
    expected_target: str,
    expected_priority: str,
    expected_requires_human: bool,
    scene: str = "Operator is working beside moving equipment with loose packaging, blocked walkway space, and restricted access path near controls.",
    risk: str = "Trip obstruction and proximity to moving equipment could expose the operator to fall, pinch, or restart hazards.",
    expected_context_guard_status: str = "clear",
    expected_blocked_fields: tuple[str, ...] = (),
) -> AgentPOCScenario:
    return AgentPOCScenario(
        mode="hazard",
        title=title,
        prompt="Golden hazard scenario for deterministic exposure escalation and downgrade blocking.",
        answer=(
            f"- Scene: {scene}\n"
            f"- Risk: {risk}\n"
            f"- Action: {action}"
        ),
        expected_fields=("scene", "risk", "action"),
        expected_channel=expected_channel,
        expected_owner=expected_owner,
        expected_target=expected_target,
        expected_priority=expected_priority,
        expected_requires_human=expected_requires_human,
        image_bytes=850_000,
        expected_selected_tools=HAZARD_TOOLS,
        expected_context_guard_status=expected_context_guard_status,
        expected_blocked_fields=expected_blocked_fields,
    )


GOLDEN_SCENARIOS: tuple[AgentPOCScenario, ...] = (
    POC_SCENARIOS[0],
    _maintenance_case(
        title="maintenance monitor visible condition",
        action="Monitor the condition during normal operation while recording visible residue changes and asking maintenance to review next available trend.",
        expected_channel="maintenance_identification_required",
        expected_owner="maintenance_engineer",
        expected_target="cmms_observation",
        expected_priority="medium",
        expected_requires_human=True,
    ),
    _maintenance_case(
        title="maintenance unknown machine blocks low-control inspection",
        machine="Unknown machine in the current M400 frame with no readable asset tag or station identifier.",
        action="Inspect the area safely and confirm machine identity before applying any machine-specific maintenance recommendation or increasing operating speed.",
        expected_channel="maintenance_identification_required",
        expected_owner="maintenance_engineer",
        expected_target="cmms_observation",
        expected_priority="medium",
        expected_requires_human=True,
        expected_context_guard_status="human_confirm_required",
        expected_blocked_fields=("machine",),
    ),
    _maintenance_case(
        title="maintenance stop severe visible condition",
        action="Stop the machine under local procedure and escalate visible smoke odor or leaking fluid evidence to maintenance engineering immediately.",
        expected_channel="maintenance_stop",
        expected_owner="maintenance_engineer",
        expected_target="maintenance_work_order",
        expected_priority="critical",
        expected_requires_human=True,
    ),
    _maintenance_case(
        title="maintenance report observation package",
        action="Report the abnormal vibration observation to maintenance and attach M400 images, operator notes, and recent alarm context for review.",
        expected_channel="maintenance_report",
        expected_owner="maintenance_engineer",
        expected_target="maintenance_work_order",
        expected_priority="medium",
        expected_requires_human=True,
    ),
    POC_SCENARIOS[1],
    _iqc_case(
        title="iqc detector-first pass blocked without detector evidence",
        disposition="pass",
        quality_risk="Insufficient detector evidence is available to confirm absence of small burrs, contamination, mix-up, or cosmetic escape risk.",
        action="Continue production under current inspection controls while recording operator check result and keeping normal sampling frequency.",
        expected_channel="quality_review",
        expected_owner="quality_engineer",
        expected_target="qms_quality_event",
        expected_priority="medium",
        expected_requires_human=True,
        expected_context_guard_status="human_confirm_required",
        expected_blocked_fields=("quality_risk",),
    ),
    _iqc_case(
        title="iqc expand inspection adjacent units",
        disposition="expand_inspection",
        quality_risk="Visible edge burr evidence could create assembly fit issues and should trigger adjacent-unit inspection before release.",
        action="Expand inspection to adjacent units from the same station lot and shift while holding suspect housings for quality engineer review.",
        expected_channel="expand_inspection",
        expected_owner="quality_engineer",
        expected_target="qms_quality_event",
        expected_priority="medium",
        expected_requires_human=True,
    ),
    _iqc_case(
        title="iqc stop production severe quality risk",
        disposition="stop_production",
        action="Stop production and notify shift lead while quality contains suspect units, records evidence, and reviews station escape risk.",
        expected_channel="stop_production",
        expected_owner="shift_lead",
        expected_target="qms_quality_event",
        expected_priority="critical",
        expected_requires_human=True,
    ),
    _iqc_case(
        title="iqc clean pass with detector clear evidence",
        disposition="pass",
        quality_risk="Detector clear confidence 0.91 and no visible quality risk is observed on the sealing face, edges, or handling contact areas in this frame.",
        action="Continue production under current inspection controls while recording visible product identity and sampling result for traceability.",
        expected_channel="continue_production",
        expected_owner="operator",
        expected_target="none",
        expected_priority="low",
        expected_requires_human=False,
    ),
    POC_SCENARIOS[2],
    _changeover_case(
        title="changeover controlled setup with source present",
        action="Set the visible guide rail width only after line clearance and label match are confirmed by the operator.",
        expected_channel="controlled_changeover_step",
        expected_owner="operator",
        expected_priority="low",
        expected_requires_human=False,
    ),
    _changeover_case(
        title="changeover rag source missing blocks controlled step",
        sku="Target SKU SKU-X999 is visible on the traveler but no released conversion checklist can be matched.",
        changeover_step="Checklist source not available for this SKU, so the visible guide rail adjustment cannot be treated as released work.",
        action="Set no further parameters until operator quality confirms machine identity, target SKU evidence, and released checklist source.",
        expected_channel="changeover_identification_required",
        expected_owner="operator_quality",
        expected_priority="medium",
        expected_requires_human=True,
        expected_context_guard_status="human_confirm_required",
        expected_blocked_fields=("changeover_step",),
    ),
    _changeover_case(
        title="changeover hold before restart",
        action="Hold restart until line clearance, target SKU evidence, label match, and first-piece verification are accepted by operator quality.",
        expected_channel="changeover_hold",
        expected_owner="line_lead",
        expected_priority="critical",
        expected_requires_human=True,
    ),
    _changeover_case(
        title="changeover escalate mismatch",
        action="Escalate the mismatch to line lead before changing recipe, tooling, label settings, or restarting the converted station.",
        expected_channel="changeover_escalation",
        expected_owner="line_lead",
        expected_priority="high",
        expected_requires_human=True,
    ),
    POC_SCENARIOS[3],
    _wi_case(
        title="wi rag source missing blocks guided operation",
        work_instruction="Current WI revision is not available from the connected RAG source, so guidance cannot be trusted as released.",
        action="Follow no operating changes until line lead confirms machine identity and the released work instruction revision.",
        expected_channel="wi_identification_required",
        expected_owner="line_lead",
        expected_priority="medium",
        expected_requires_human=True,
        expected_context_guard_status="human_confirm_required",
        expected_blocked_fields=("work_instruction",),
    ),
    _wi_case(
        title="wi ask human for abnormal state",
        action="Ask line lead to confirm the abnormal panel message before changing speed, clearing faults, or touching guarded areas.",
        expected_channel="wi_human_support",
        expected_owner="line_lead",
        expected_priority="medium",
        expected_requires_human=True,
    ),
    _wi_case(
        title="wi stop unsafe operation",
        action="Stop operation and keep hands outside guarded transfer areas until the guard status and machine state are confirmed.",
        expected_channel="wi_stop",
        expected_owner="operator",
        expected_priority="critical",
        expected_requires_human=True,
    ),
    _wi_case(
        title="wi confirm released setup point",
        action="Confirm guide alignment and product orientation against the released instruction before feeding product through the station.",
        expected_channel="guided_operation",
        expected_owner="operator",
        expected_priority="low",
        expected_requires_human=False,
    ),
    POC_SCENARIOS[4],
    _hazard_case(
        title="hazard inspect area before continuing",
        action="Inspect the walkway and control area before continuing, then remove packaging and confirm access remains clear.",
        expected_channel="inspect_area",
        expected_owner="operator",
        expected_target="safety_observation",
        expected_priority="low",
        expected_requires_human=False,
    ),
    _hazard_case(
        title="hazard wear ppe control",
        action="Wear required PPE and confirm the face shield, gloves, and hearing protection are suitable before entering the station.",
        expected_channel="ppe_control",
        expected_owner="operator",
        expected_target="safety_observation",
        expected_priority="low",
        expected_requires_human=False,
    ),
    _hazard_case(
        title="hazard report exposure",
        action="Report the blocked walkway and moving equipment exposure to EHS and supervisor before allowing routine work to resume.",
        expected_channel="ehs_report",
        expected_owner="ehs",
        expected_target="ehs_case",
        expected_priority="high",
        expected_requires_human=True,
    ),
    _hazard_case(
        title="hazard unknown scene blocks downgrade",
        scene="Unknown scene context from the current M400 frame with no reliable area, equipment, or walkway identity.",
        risk="Cannot determine whether moving equipment, blocked access, or restricted-zone exposure is controlled from this image alone.",
        action="Keep current controls in place while continuing only after supervisor confirms the area identity and exposure status.",
        expected_channel="hazard_identification_required",
        expected_owner="operator",
        expected_target="safety_observation",
        expected_priority="medium",
        expected_requires_human=True,
        expected_context_guard_status="human_confirm_required",
        expected_blocked_fields=("scene", "risk"),
    ),
)


def run_agent_poc_validations() -> tuple[AgentPOCResult, ...]:
    return tuple(_run_one_poc(scenario) for scenario in POC_SCENARIOS)


def run_agent_golden_validations() -> tuple[AgentPOCResult, ...]:
    return tuple(_run_one_poc(scenario) for scenario in GOLDEN_SCENARIOS)


def format_agent_poc_markdown(results: tuple[AgentPOCResult, ...]) -> str:
    lines = [
        "| Agent | Result | Channel | Owner | Target | Last event |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(
            "| "
            f"{result.mode} | {status} | {result.action_channel} | {result.owner} | "
            f"{result.integration_target} | {result.runtime_last_event} |"
        )
    return "\n".join(lines)


def _run_one_poc(scenario: AgentPOCScenario) -> AgentPOCResult:
    request_id = _request_id_for(scenario)
    workflow = run_m400_agently_workflow(
        prompt=scenario.prompt,
        mode=scenario.mode,
        image_bytes=scenario.image_bytes,
        request_id=request_id,
        device={
            "device_id": "m400-poc-01",
            "location_hint": "poc-cell",
            "capture_mode": "poc-fixed-frame",
        },
        contract_min_words=16,
        contract_repair_enabled=True,
        current_image_min_tokens=560,
        current_image_max_tokens=560,
        audio_runtime="llama.cpp",
        model_variant="E2B",
        audio_seconds=0,
        needs_ocr=scenario.needs_ocr,
        high_detail=scenario.high_detail,
        infer_model=lambda prompt: FakeModelResponse(answer=scenario.answer, latency_ms=25),
    )

    failures: list[str] = []
    if not workflow.contract.ok:
        failures.extend(workflow.contract.violations)
    missing_fields = [field for field in scenario.expected_fields if not workflow.fields.get(field)]
    if missing_fields:
        failures.append(f"missing expected fields: {', '.join(missing_fields)}")

    action_card = workflow.action_card
    if action_card is None:
        failures.append("missing action_card")
        action_channel = ""
        owner = ""
        target = ""
        priority = ""
        requires_human = False
    else:
        action_channel = action_card.channel
        owner = action_card.owner
        target = action_card.integration_target
        priority = action_card.priority
        requires_human = action_card.requires_human
        if action_card.channel != scenario.expected_channel:
            failures.append(f"channel expected {scenario.expected_channel}, got {action_card.channel}")
        if action_card.owner != scenario.expected_owner:
            failures.append(f"owner expected {scenario.expected_owner}, got {action_card.owner}")
        if action_card.integration_target != scenario.expected_target:
            failures.append(f"target expected {scenario.expected_target}, got {action_card.integration_target}")
        if action_card.priority != scenario.expected_priority:
            failures.append(f"priority expected {scenario.expected_priority}, got {action_card.priority}")
        if action_card.requires_human != scenario.expected_requires_human:
            failures.append(
                f"requires_human expected {scenario.expected_requires_human}, got {action_card.requires_human}"
            )

    integration_event = workflow.integration_event
    if integration_event is None:
        failures.append("missing integration_event")
    else:
        if integration_event.target != scenario.expected_target:
            failures.append(f"integration target expected {scenario.expected_target}, got {integration_event.target}")
        if not integration_event.idempotency_key.startswith(f"{request_id}:{scenario.expected_target}:"):
            failures.append("integration idempotency key does not include request_id and target")

    tool_plan = workflow.tool_plan
    tool_status = str(tool_plan.get("status") or "")
    selected_tools = tuple(str(tool) for tool in tool_plan.get("selected_tools", []))
    if scenario.expected_tool_status and tool_status != scenario.expected_tool_status:
        failures.append(f"tool_status expected {scenario.expected_tool_status}, got {tool_status}")
    if scenario.expected_selected_tools and selected_tools != scenario.expected_selected_tools:
        failures.append(
            f"selected_tools expected {', '.join(scenario.expected_selected_tools)}, got {', '.join(selected_tools)}"
        )

    context_guard = {}
    if isinstance(workflow.agent_loop, dict):
        guard = workflow.agent_loop.get("context_guard")
        if isinstance(guard, dict):
            context_guard = guard
    context_guard_status = str(context_guard.get("status") or "")
    blocked_fields = tuple(str(field) for field in context_guard.get("blocked_fields", []))
    if scenario.expected_context_guard_status is not None and context_guard_status != scenario.expected_context_guard_status:
        failures.append(
            f"context_guard expected {scenario.expected_context_guard_status}, got {context_guard_status}"
        )
    if scenario.expected_blocked_fields and set(blocked_fields) != set(scenario.expected_blocked_fields):
        failures.append(
            f"blocked_fields expected {', '.join(scenario.expected_blocked_fields)}, got {', '.join(blocked_fields)}"
        )

    follow_up_plan = workflow.follow_up_plan if isinstance(workflow.follow_up_plan, dict) else {}
    follow_up_status = str(follow_up_plan.get("status") or "")
    follow_up_requests = follow_up_plan.get("requests", [])
    follow_up_request_count = len(follow_up_requests) if isinstance(follow_up_requests, list) else 0
    expected_follow_up_status = scenario.expected_follow_up_status
    if expected_follow_up_status is None:
        expected_follow_up_status = "operator_evidence_required" if scenario.mode == "maintenance" else "not_required"
    if follow_up_status != expected_follow_up_status:
        failures.append(f"follow_up_status expected {expected_follow_up_status}, got {follow_up_status}")
    if scenario.mode == "maintenance" and follow_up_request_count == 0:
        failures.append("maintenance follow_up_plan did not include operator evidence requests")

    runtime_events = workflow.runtime_stream.get("events", [])
    runtime_last_event = ""
    if isinstance(runtime_events, list) and runtime_events:
        last_event = runtime_events[-1]
        if isinstance(last_event, dict):
            runtime_last_event = str(last_event.get("event") or "")
    if workflow.runtime_stream.get("closed") is not True:
        failures.append("runtime_stream did not close")
    if runtime_last_event != "workflow.closed":
        failures.append(f"runtime last event expected workflow.closed, got {runtime_last_event}")

    return AgentPOCResult(
        mode=scenario.mode,
        title=scenario.title,
        passed=not failures,
        failures=tuple(failures),
        action_channel=action_channel,
        owner=owner,
        integration_target=target,
        priority=priority,
        requires_human=requires_human,
        tool_status=tool_status,
        selected_tools=selected_tools,
        context_guard_status=context_guard_status,
        blocked_fields=blocked_fields,
        follow_up_status=follow_up_status,
        follow_up_request_count=follow_up_request_count,
        runtime_event_count=len(runtime_events) if isinstance(runtime_events, list) else 0,
        runtime_last_event=runtime_last_event,
        request_id=request_id,
    )


def _request_id_for(scenario: AgentPOCScenario) -> str:
    slug = "".join(character if character.isalnum() else "-" for character in scenario.title.lower())
    slug = "-".join(part for part in slug.split("-") if part)
    return f"poc-{scenario.mode}-{slug[:40]}"
