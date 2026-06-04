from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock

from .agent_profiles import normalize_agent_mode


MAINTENANCE_SESSION_VERSION = "wear-edge-maintenance-session.v1"
MAINTENANCE_EVIDENCE_VERSION = "wear-edge-maintenance-evidence.v1"
SESSION_TRACE_VERSION = "wear-edge-maintenance-session-trace.v1"
MAX_SUMMARY_CHARS = 700
MAX_FIELD_CHARS = 180
MAX_PROMPT_CONTEXT_ITEMS = 12
ALLOWED_EVIDENCE_STATUSES = {
    "accepted",
    "missing",
    "unclear",
    "conflicts_with_previous",
    "requires_human_confirm",
}
MAINTENANCE_EVIDENCE_TYPES = {
    "maintenance_initial_frame",
    "maintenance_followup_frame",
    "maintenance_asset_identity_photo",
    "maintenance_condition_screen_photo",
    "maintenance_temperature_gauge_photo",
    "maintenance_lubrication_record_photo",
    "maintenance_recent_work_record_photo",
    "maintenance_operator_sensory_check",
}
MAINTENANCE_VISUAL_EVIDENCE_IDS = (
    "maintenance_asset_identity_photo",
    "maintenance_condition_screen_photo",
    "maintenance_temperature_gauge_photo",
    "maintenance_lubrication_record_photo",
    "maintenance_recent_work_record_photo",
)
_SPACE_RE = re.compile(r"\s+")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True)
class MaintenanceEvidence:
    evidence_id: str
    evidence_type: str
    capture_type: str
    status: str
    summary: str
    source: str
    received_at: str
    fields: dict[str, str] = field(default_factory=dict)
    image_bytes: int | None = None
    image_content_type: str | None = None
    request_id: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "version": MAINTENANCE_EVIDENCE_VERSION,
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "capture_type": self.capture_type,
            "status": self.status,
            "summary": self.summary,
            "source": self.source,
            "received_at": self.received_at,
            "fields": dict(self.fields),
            "image_bytes": self.image_bytes,
            "image_content_type": self.image_content_type,
            "request_id": self.request_id,
        }


@dataclass(frozen=True)
class MaintenanceSessionEvent:
    sequence: int
    event: str
    at: str
    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "event": self.event,
            "at": self.at,
            "payload": dict(self.payload),
        }


@dataclass
class MaintenanceSession:
    session_id: str
    created_at: str
    updated_at: str
    device: dict[str, object]
    location_hint: str | None = None
    operator_id: str | None = None
    initial_prompt: str | None = None
    status: str = "open"
    evidence: list[MaintenanceEvidence] = field(default_factory=list)
    requested_evidence_ids: list[str] = field(default_factory=list)
    satisfied_evidence_ids: list[str] = field(default_factory=list)
    last_inference: dict[str, object] | None = None
    events: list[MaintenanceSessionEvent] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "version": MAINTENANCE_SESSION_VERSION,
            "session_id": self.session_id,
            "mode": "maintenance",
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "device": dict(self.device),
            "location_hint": self.location_hint,
            "operator_id": self.operator_id,
            "initial_prompt": self.initial_prompt,
            "evidence": [item.as_dict() for item in self.evidence],
            "evidence_state": self.evidence_state(),
            "requested_evidence_ids": list(self.requested_evidence_ids),
            "satisfied_evidence_ids": list(self.satisfied_evidence_ids),
            "missing_requested_evidence_ids": list(self.missing_requested_evidence_ids()),
            "last_inference": self.last_inference,
        }

    def trace(self) -> dict[str, object]:
        return {
            "version": SESSION_TRACE_VERSION,
            "session_id": self.session_id,
            "status": self.status,
            "events": [event.as_dict() for event in self.events],
        }

    def evidence_state(self) -> dict[str, object]:
        by_status = {status: 0 for status in sorted(ALLOWED_EVIDENCE_STATUSES)}
        by_type: dict[str, str] = {}
        for item in self.evidence:
            by_status[item.status] = by_status.get(item.status, 0) + 1
            by_type[item.evidence_type] = item.status
        accepted_ids = list(
            dict.fromkeys(
                [item.evidence_type for item in self.evidence if item.status == "accepted"]
                + list(self.satisfied_evidence_ids)
            )
        )
        return {
            "count": len(self.evidence),
            "by_status": by_status,
            "by_type": by_type,
            "accepted_evidence_ids": accepted_ids,
            "blocked_statuses": [
                item.evidence_type
                for item in self.evidence
                if item.status in {"unclear", "conflicts_with_previous", "requires_human_confirm"}
            ],
        }

    def missing_requested_evidence_ids(self) -> tuple[str, ...]:
        accepted = {item.evidence_type for item in self.evidence if item.status == "accepted"}
        accepted.update(self.satisfied_evidence_ids)
        return tuple(evidence_id for evidence_id in self.requested_evidence_ids if evidence_id not in accepted)

    def prompt_context(self) -> str:
        accepted = [item for item in self.evidence if item.status == "accepted"]
        blocked = [
            item
            for item in self.evidence
            if item.status in {"unclear", "conflicts_with_previous", "requires_human_confirm"}
        ]
        missing = self.missing_requested_evidence_ids()
        lines = [
            "Maintenance session evidence context:",
            f"- Session ID: {self.session_id}",
            f"- Device: {self.device.get('device_id', 'unknown')}",
        ]
        if self.location_hint:
            lines.append(f"- Location: {self.location_hint}")
        if accepted:
            lines.append("- Accepted evidence:")
            for item in accepted[-MAX_PROMPT_CONTEXT_ITEMS:]:
                lines.append(f"  - {item.evidence_type}: {_prompt_summary(item.summary)}")
        else:
            lines.append("- Accepted evidence: none yet.")
        if blocked:
            lines.append("- Evidence requiring confirmation:")
            for item in blocked[-MAX_PROMPT_CONTEXT_ITEMS:]:
                lines.append(f"  - {item.evidence_type} [{item.status}]: {_prompt_summary(item.summary)}")
        if missing:
            lines.append("- Missing requested evidence:")
            for evidence_id in missing:
                lines.append(f"  - {evidence_id}")
        lines.extend(
            [
                "Session rules:",
                "- Same machine investigation unless evidence conflicts; no RCA/RUL/restart/release without trusted evidence.",
                "- If evidence is missing or unclear, ask targeted M400 follow-up.",
            ]
        )
        return "\n".join(lines)


class MaintenanceSessionStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[str, MaintenanceSession] = {}

    def create_session(
        self,
        *,
        device: dict[str, object],
        location_hint: str | None = None,
        operator_id: str | None = None,
        initial_prompt: str | None = None,
    ) -> MaintenanceSession:
        now = _now()
        session = MaintenanceSession(
            session_id=uuid.uuid4().hex,
            created_at=now,
            updated_at=now,
            device=dict(device),
            location_hint=_clean_optional(location_hint),
            operator_id=_clean_optional(operator_id),
            initial_prompt=_clean_optional(initial_prompt, max_chars=MAX_SUMMARY_CHARS),
        )
        _append_event(session, "maintenance_session.created", {"device": session.device})
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> MaintenanceSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def add_evidence(
        self,
        session_id: str,
        *,
        evidence_type: str,
        capture_type: str,
        status: str | None,
        summary: str | None,
        source: str = "m400",
        fields: dict[str, object] | None = None,
        image_bytes: int | None = None,
        image_content_type: str | None = None,
        request_id: str | None = None,
    ) -> MaintenanceEvidence:
        session = self.require_session(session_id)
        resolved_status = _resolve_status(status=status, summary=summary, image_bytes=image_bytes)
        evidence = MaintenanceEvidence(
            evidence_id=uuid.uuid4().hex,
            evidence_type=_clean_evidence_type(evidence_type),
            capture_type=_clean_required(capture_type, default="photo"),
            status=resolved_status,
            summary=_clean_optional(summary, max_chars=MAX_SUMMARY_CHARS) or "No operator summary was provided.",
            source=_clean_required(source, default="m400"),
            received_at=_now(),
            fields=_clean_fields(fields or {}),
            image_bytes=image_bytes,
            image_content_type=image_content_type,
            request_id=_clean_optional(request_id),
        )
        with self._lock:
            session.evidence.append(evidence)
            session.updated_at = evidence.received_at
            _append_event(
                session,
                "maintenance_session.evidence_added",
                {
                    "evidence_id": evidence.evidence_id,
                    "evidence_type": evidence.evidence_type,
                    "status": evidence.status,
                },
            )
        return evidence

    def record_inference(self, session_id: str, response_body: dict[str, object]) -> MaintenanceSession:
        session = self.require_session(session_id)
        follow_up_plan = response_body.get("follow_up_plan")
        requested = _follow_up_request_ids(follow_up_plan if isinstance(follow_up_plan, dict) else {})
        satisfied = _satisfied_evidence_ids(follow_up_plan if isinstance(follow_up_plan, dict) else {})
        inference_summary = {
            "request_id": response_body.get("request_id"),
            "channel": _nested_value(response_body, "action_card", "channel"),
            "priority": _nested_value(response_body, "action_card", "priority"),
            "owner": _nested_value(response_body, "action_card", "owner"),
            "follow_up_status": _nested_value(response_body, "follow_up_plan", "status"),
            "runtime_closed": _nested_value(response_body, "runtime_stream", "closed"),
        }
        with self._lock:
            session.last_inference = inference_summary
            session.requested_evidence_ids = requested
            session.satisfied_evidence_ids = list(dict.fromkeys(session.satisfied_evidence_ids + satisfied))
            session.updated_at = _now()
            _append_event(
                session,
                "maintenance_session.inference_completed",
                {
                    **inference_summary,
                    "requested_evidence_ids": list(requested),
                    "satisfied_evidence_ids": list(session.satisfied_evidence_ids),
                },
            )
        return session

    def require_session(self, session_id: str) -> MaintenanceSession:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(session_id)
        return session


def build_session_prompt_context(session: MaintenanceSession) -> str:
    return session.prompt_context()


def build_workflow_session_context(session: MaintenanceSession) -> dict[str, object]:
    return {
        "version": MAINTENANCE_SESSION_VERSION,
        "session_id": session.session_id,
        "mode": "maintenance",
        "prompt_context": session.prompt_context(),
        "evidence_state": session.evidence_state(),
        "accepted_evidence": _accepted_evidence_for_workflow(session),
        "missing_requested_evidence_ids": list(session.missing_requested_evidence_ids()),
    }


def _accepted_evidence_for_workflow(session: MaintenanceSession) -> list[dict[str, object]]:
    accepted = [item for item in session.evidence if item.status == "accepted"]
    return [
        {
            "evidence_id": item.evidence_id,
            "evidence_type": item.evidence_type,
            "capture_type": item.capture_type,
            "summary": item.summary,
            "fields": dict(item.fields),
            "received_at": item.received_at,
            "source": item.source,
        }
        for item in accepted[-MAX_PROMPT_CONTEXT_ITEMS:]
    ]


def _follow_up_request_ids(follow_up_plan: dict[str, object]) -> list[str]:
    request_ids: list[str] = []
    for item in follow_up_plan.get("requests", []):
        if isinstance(item, dict):
            request_id = str(item.get("id") or "").strip()
            if request_id:
                request_ids.append(request_id)
    return list(dict.fromkeys(request_ids))


def _satisfied_evidence_ids(follow_up_plan: dict[str, object]) -> list[str]:
    remaining = set(_follow_up_request_ids(follow_up_plan))
    satisfied: list[str] = [
        evidence_id for evidence_id in MAINTENANCE_VISUAL_EVIDENCE_IDS if evidence_id not in remaining
    ]
    if "maintenance_operator_sensory_check" not in remaining and not remaining:
        satisfied.append("maintenance_operator_sensory_check")
    return list(dict.fromkeys(satisfied))


def _prompt_summary(value: str) -> str:
    cleaned = _clean_optional(value, max_chars=160) or ""
    return cleaned


def _resolve_status(*, status: str | None, summary: str | None, image_bytes: int | None) -> str:
    if status:
        cleaned = _clean_required(status, default="accepted")
        if cleaned not in ALLOWED_EVIDENCE_STATUSES:
            raise ValueError(f"unsupported evidence status: {status}")
        return cleaned
    if summary or image_bytes:
        return "accepted"
    return "missing"


def _clean_evidence_type(value: str) -> str:
    cleaned = _clean_required(value, default="")
    if not cleaned:
        raise ValueError("evidence_type is required")
    if cleaned not in MAINTENANCE_EVIDENCE_TYPES:
        raise ValueError(f"unsupported maintenance evidence_type: {value}")
    return cleaned


def _clean_fields(fields: dict[str, object]) -> dict[str, str]:
    return {
        _clean_required(str(key), default="field"): _clean_optional(str(value), max_chars=MAX_FIELD_CHARS) or ""
        for key, value in fields.items()
        if str(key).strip()
    }


def _clean_optional(value: str | None, *, max_chars: int = MAX_FIELD_CHARS) -> str | None:
    if value is None:
        return None
    cleaned = _CONTROL_RE.sub(" ", str(value))
    cleaned = _SPACE_RE.sub(" ", cleaned).strip()
    if not cleaned:
        return None
    return cleaned[:max_chars]


def _clean_required(value: str | None, *, default: str) -> str:
    return _clean_optional(value, max_chars=MAX_FIELD_CHARS) or default


def _nested_value(data: dict[str, object], key: str, nested_key: str) -> object:
    value = data.get(key)
    if isinstance(value, dict):
        return value.get(nested_key)
    return None


def _append_event(session: MaintenanceSession, event: str, payload: dict[str, object]) -> None:
    session.events.append(
        MaintenanceSessionEvent(
            sequence=len(session.events) + 1,
            event=event,
            at=_now(),
            payload=payload,
        )
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_maintenance_mode(mode: str) -> str:
    resolved = normalize_agent_mode(mode)
    if resolved != "maintenance":
        raise ValueError("maintenance sessions only support analysis_mode=maintenance")
    return resolved


maintenance_session_store = MaintenanceSessionStore()
