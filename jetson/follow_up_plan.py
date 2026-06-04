from __future__ import annotations

import re
from dataclasses import dataclass

from .agent_profiles import normalize_agent_mode


FOLLOW_UP_PLAN_VERSION = "wear-edge-follow-up-plan.v1"
CONDITION_VALUE_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mm/s|rpm|amp|amps|a|%|deg|c|celsius|°c|°)\b")


@dataclass(frozen=True)
class FollowUpRequest:
    id: str
    capture_type: str
    priority: str
    prompt: str
    reason: str
    expected_fields: tuple[str, ...]
    maps_to_tools: tuple[str, ...]
    blocks_final_judgment: bool = True

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "capture_type": self.capture_type,
            "priority": self.priority,
            "prompt": self.prompt,
            "reason": self.reason,
            "expected_fields": list(self.expected_fields),
            "maps_to_tools": list(self.maps_to_tools),
            "blocks_final_judgment": self.blocks_final_judgment,
        }


@dataclass(frozen=True)
class FollowUpPlan:
    version: str
    mode: str
    status: str
    summary: str
    next_action: str
    requests: tuple[FollowUpRequest, ...]
    completion_rule: str
    blocked_claims: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "mode": self.mode,
            "status": self.status,
            "summary": self.summary,
            "next_action": self.next_action,
            "requests": [request.as_dict() for request in self.requests],
            "completion_rule": self.completion_rule,
            "blocked_claims": list(self.blocked_claims),
        }


def build_follow_up_plan(
    *,
    mode: str,
    fields: dict[str, object],
    evidence_plan: dict[str, object],
    tool_plan: dict[str, object],
    decision_channel: str,
    accepted_evidence_ids: tuple[str, ...] | list[str] | None = None,
) -> FollowUpPlan:
    resolved = normalize_agent_mode(mode)
    if resolved != "maintenance":
        return _not_required_plan(resolved)

    missing_tools = _missing_tools(evidence_plan=evidence_plan, tool_plan=tool_plan)
    field_text = _joined_field_text(fields)
    visual_requests: list[FollowUpRequest] = []

    if _is_unknownish(_field_text(fields, "machine")) or (
        "asset_registry" in missing_tools and not _has_asset_identity(field_text)
    ):
        visual_requests.append(
            FollowUpRequest(
                id="maintenance_asset_identity_photo",
                capture_type="photo",
                priority="required",
                prompt="Photograph the machine asset plate and station sign so the asset id and line/station are readable.",
                reason="Machine-specific maintenance guidance requires a trusted asset identity.",
                expected_fields=("asset_id", "station_id", "line_id"),
                maps_to_tools=("asset_registry",),
            )
        )

    if not _has_operating_readings(field_text) and (
        "telemetry_history" in missing_tools or _needs_operating_readings(field_text)
    ):
        visual_requests.append(
            FollowUpRequest(
                id="maintenance_condition_screen_photo",
                capture_type="photo",
                priority="required",
                prompt=(
                    "Photograph the HMI or condition monitor showing vibration RMS, current, load, speed, "
                    "and the active alarm code."
                ),
                reason="The first image did not provide stable numeric condition readings for trend comparison.",
                expected_fields=("vibration_rms", "current", "load", "speed", "alarm_code"),
                maps_to_tools=("telemetry_history",),
            )
        )

    if not _has_temperature_readings(field_text) and (
        "telemetry_history" in missing_tools or _needs_temperature_readings(field_text)
    ):
        visual_requests.append(
            FollowUpRequest(
                id="maintenance_temperature_gauge_photo",
                capture_type="photo",
                priority="required",
                prompt="Photograph the motor, bearing, and gearbox temperature gauges with units readable.",
                reason="Temperature values must be captured before assigning heat-related maintenance risk.",
                expected_fields=("motor_temperature", "bearing_temperature", "gearbox_temperature", "temperature_unit"),
                maps_to_tools=("telemetry_history", "manual_kb"),
            )
        )

    if not _has_lubrication_evidence(field_text) and (
        "manual_kb" in missing_tools or _mentions_lubrication(field_text)
    ):
        visual_requests.append(
            FollowUpRequest(
                id="maintenance_lubrication_record_photo",
                capture_type="photo",
                priority="required",
                prompt="Photograph the nearby lubrication record, lubrication point card, or maintenance checklist.",
                reason="Lubrication state is operator evidence until the released manual or KB is connected.",
                expected_fields=("lubrication_date", "lubricant_type", "lubrication_point", "operator_initials"),
                maps_to_tools=("manual_kb", "work_order_history"),
            )
        )

    if not _has_history_evidence(field_text) and (
        "work_order_history" in missing_tools or _mentions_history(field_text)
    ):
        visual_requests.append(
            FollowUpRequest(
                id="maintenance_recent_work_record_photo",
                capture_type="photo",
                priority="required",
                prompt="Photograph the most recent maintenance record, PM tag, repair note, or posted issue log.",
                reason="Recent work history is needed before deciding whether this is recurring, worsening, or already controlled.",
                expected_fields=("last_maintenance_date", "last_repair_action", "open_issue", "technician_note"),
                maps_to_tools=("work_order_history",),
            )
        )

    operator_sensory_request = FollowUpRequest(
        id="maintenance_operator_sensory_check",
        capture_type="voice_or_form",
        priority="required" if decision_channel in {"maintenance_report", "maintenance_escalation"} else "recommended",
        prompt=(
            "Ask the operator one sensory question at a time after visual evidence is sufficient: unusual noise, "
            "smell, heat, shaking, abnormal vibration, oil leakage, and when the condition started."
        ),
        reason="Experienced operator observations are evidence and should be captured after targeted visual evidence.",
        expected_fields=(
            "unusual_noise",
            "unusual_smell",
            "felt_heat",
            "felt_shaking",
            "visible_leak",
            "started_when",
        ),
        maps_to_tools=("work_order_history",),
    )

    remaining_visual_requests = _filter_completed_requests(_dedupe_requests(visual_requests), accepted_evidence_ids)
    remaining_operator_requests = _filter_completed_requests((operator_sensory_request,), accepted_evidence_ids)
    if remaining_visual_requests:
        selected_requests = remaining_visual_requests
        status = "operator_evidence_required"
        next_action = "collect_visual_evidence_gaps"
        summary = (
            "Maintenance judgment remains bounded. The latest M400 image may satisfy multiple visual evidence "
            "points; collect another M400 frame that covers as many of the remaining visual gaps as possible, "
            "then rerun the same request family."
        )
        completion_rule = (
            "After each uploaded image, let Jetson extract all useful evidence points from that image. "
            "Do not bind one photo to one fixed evidence slot; ask for another photo only for remaining gaps."
        )
    elif remaining_operator_requests:
        selected_requests = remaining_operator_requests
        status = "operator_evidence_required"
        next_action = "collect_operator_sensory_evidence"
        summary = (
            "Targeted visual evidence is sufficient for this pass. Capture operator sensory observations "
            "as one-question-at-a-time voice evidence before final maintenance judgment."
        )
        completion_rule = (
            "Ask the operator one sensory question at a time, attach the structured voice evidence to the same "
            "request_family_id, then rerun the maintenance workflow for the final action card."
        )
    else:
        selected_requests = ()
        status = "ready_for_human_confirmation"
        next_action = "review_action_card"
        summary = (
            "Targeted visual evidence and operator sensory evidence are accepted for this pass. Review the "
            "bounded action card and keep blocked claims out of the final judgment."
        )
        completion_rule = "Use the action card and trace for human-confirmed maintenance follow-up."

    return FollowUpPlan(
        version=FOLLOW_UP_PLAN_VERSION,
        mode=resolved,
        status=status,
        summary=summary,
        next_action=next_action,
        requests=selected_requests,
        completion_rule=completion_rule,
        blocked_claims=("final root cause", "remaining useful life", "restart permission", "maintenance release"),
    )


def build_contract_failure_follow_up_plan(mode: str) -> FollowUpPlan:
    resolved = normalize_agent_mode(mode)
    return FollowUpPlan(
        version=FOLLOW_UP_PLAN_VERSION,
        mode=resolved,
        status="contract_failed",
        summary="No operator follow-up plan was created because the model output failed the structured contract.",
        next_action="retry_or_manual_review",
        requests=(),
        completion_rule="Retry with a valid contract answer or route the request to manual review.",
        blocked_claims=("final action", "integration dispatch"),
    )


def _not_required_plan(mode: str) -> FollowUpPlan:
    return FollowUpPlan(
        version=FOLLOW_UP_PLAN_VERSION,
        mode=mode,
        status="not_required",
        summary="No maintenance evidence follow-up is required for this agent mode.",
        next_action="review_action_card",
        requests=(),
        completion_rule="Use the action card and mode-specific evidence plan.",
        blocked_claims=(),
    )


def _missing_tools(*, evidence_plan: dict[str, object], tool_plan: dict[str, object]) -> tuple[str, ...]:
    names: list[str] = []
    for value in evidence_plan.get("missing_tools", []):
        names.append(str(value))
    for item in tool_plan.get("skipped_tools", []):
        if isinstance(item, dict):
            names.append(str(item.get("name") or ""))
    for value in tool_plan.get("deferred_tools", []):
        names.append(str(value))
    return tuple(dict.fromkeys(name for name in names if name))


def _dedupe_requests(requests: list[FollowUpRequest]) -> tuple[FollowUpRequest, ...]:
    by_id: dict[str, FollowUpRequest] = {}
    for request in requests:
        by_id.setdefault(request.id, request)
    return tuple(by_id.values())


def _filter_completed_requests(
    requests: tuple[FollowUpRequest, ...],
    accepted_evidence_ids: tuple[str, ...] | list[str] | None,
) -> tuple[FollowUpRequest, ...]:
    accepted = {str(evidence_id) for evidence_id in accepted_evidence_ids or ()}
    if not accepted:
        return requests
    return tuple(request for request in requests if request.id not in accepted)


def _joined_field_text(fields: dict[str, object]) -> str:
    return " ".join(_field_text(fields, key) for key in sorted(fields)).lower()


def _field_text(fields: dict[str, object], key: str) -> str:
    return str(fields.get(key) or "").strip()


def _needs_operating_readings(text: str) -> bool:
    reading_markers = ("vibration", "rms", "current", "load", "speed", "alarm", "hmi", "plc")
    return any(marker in text for marker in reading_markers) and CONDITION_VALUE_RE.search(text) is None


def _has_asset_identity(text: str) -> bool:
    if _is_unknownish(text):
        return False
    asset_markers = ("asset", "station", "line", "machine", "drive", "gearbox", "motor", "m400", "pkg", "cartoner")
    has_marker = any(marker in text for marker in asset_markers)
    has_identifier_shape = bool(re.search(r"\b[a-z]{1,8}[-_]?\d{1,4}(?:[-_][a-z0-9]{1,8})*\b", text))
    return has_marker and has_identifier_shape


def _has_operating_readings(text: str) -> bool:
    reading_markers = ("vibration", "rms", "current", "load", "speed", "alarm", "hmi", "plc", "rpm", "amp")
    return any(marker in text for marker in reading_markers) and CONDITION_VALUE_RE.search(text) is not None


def _needs_temperature_readings(text: str) -> bool:
    heat_markers = ("heat", "hot", "temperature", "temp", "bearing", "gearbox", "motor")
    return any(marker in text for marker in heat_markers) and CONDITION_VALUE_RE.search(text) is None


def _has_temperature_readings(text: str) -> bool:
    heat_markers = ("heat", "hot", "temperature", "temp", "bearing", "gearbox", "motor")
    temp_value_re = re.compile(r"\b\d+(?:\.\d+)?\s*(?:deg|c|celsius|°c|°)\b")
    return any(marker in text for marker in heat_markers) and temp_value_re.search(text) is not None


def _mentions_lubrication(text: str) -> bool:
    return any(marker in text for marker in ("lubric", "oil", "grease", "gearbox", "bearing"))


def _has_lubrication_evidence(text: str) -> bool:
    if _mentions_gap(text, ("lubric", "oil", "grease")):
        return False
    has_lube_marker = any(marker in text for marker in ("lubric", "oil", "grease"))
    has_record_marker = any(marker in text for marker in ("record", "date", "type", "point", "initial", "card"))
    has_date_shape = bool(re.search(r"\b(?:20\d{2}[-/年]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", text))
    return has_lube_marker and (has_record_marker or has_date_shape)


def _mentions_history(text: str) -> bool:
    return any(marker in text for marker in ("history", "recent", "record", "repair", "pm", "work order", "alarm log"))


def _has_history_evidence(text: str) -> bool:
    if _mentions_gap(text, ("history", "recent", "record", "repair", "pm", "work order")):
        return False
    history_markers = ("history", "recent", "record", "repair", "pm", "work order", "alarm log")
    detail_markers = ("date", "note", "closed", "open", "technician", "completed", "tag")
    has_date_shape = bool(re.search(r"\b(?:20\d{2}[-/年]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", text))
    return any(marker in text for marker in history_markers) and (any(marker in text for marker in detail_markers) or has_date_shape)


def _mentions_gap(text: str, subjects: tuple[str, ...]) -> bool:
    gap_markers = ("missing", "need", "needed", "request", "required", "lacking", "absence", "not visible", "not readable")
    if not any(subject in text for subject in subjects):
        return False
    return any(marker in text for marker in gap_markers)


def _is_unknownish(value: str) -> bool:
    normalized = " ".join(value.lower().replace("-", " ").replace("_", " ").split())
    if not normalized:
        return True
    markers = (
        "unknown",
        "unidentified",
        "not identified",
        "not available",
        "not visible",
        "not readable",
        "unreadable",
        "unclear",
        "cannot determine",
        "insufficient",
    )
    return any(marker in normalized for marker in markers)
