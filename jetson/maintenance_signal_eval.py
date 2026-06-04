from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


MAINTENANCE_EVALUATION_VERSION = "wear-edge-maintenance-condition-eval.v1"
BLOCKED_MAINTENANCE_CLAIMS = (
    "final root cause",
    "remaining useful life",
    "restart permission",
    "maintenance release",
)
NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


@dataclass(frozen=True)
class MaintenanceSignalBreach:
    signal: str
    observed: str
    threshold: str
    comparator: str
    severity: str
    evidence_type: str
    source_field: str
    kb_source_id: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "signal": self.signal,
            "observed": self.observed,
            "threshold": self.threshold,
            "comparator": self.comparator,
            "severity": self.severity,
            "evidence_type": self.evidence_type,
            "source_field": self.source_field,
            "kb_source_id": self.kb_source_id,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MaintenanceConditionEvaluation:
    version: str
    status: str
    risk_level: str
    query_asset_id: str | None
    threshold_source_ids: tuple[str, ...]
    breaches: tuple[MaintenanceSignalBreach, ...]
    observations: tuple[dict[str, object], ...]
    missing_inputs: tuple[str, ...]
    recommended_channel: str
    requires_human: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "status": self.status,
            "risk_level": self.risk_level,
            "query_asset_id": self.query_asset_id,
            "threshold_source_ids": list(self.threshold_source_ids),
            "breaches": [breach.as_dict() for breach in self.breaches],
            "observations": [dict(item) for item in self.observations],
            "missing_inputs": list(self.missing_inputs),
            "recommended_channel": self.recommended_channel,
            "requires_human": self.requires_human,
            "blocked_claims": list(BLOCKED_MAINTENANCE_CLAIMS),
        }


def evaluate_maintenance_condition(
    *,
    session_context: dict[str, object] | None,
    knowledge_base: dict[str, object] | None,
    now: datetime | None = None,
) -> MaintenanceConditionEvaluation:
    kb = knowledge_base if isinstance(knowledge_base, dict) else {}
    thresholds = kb.get("thresholds") if isinstance(kb.get("thresholds"), dict) else {}
    hits = kb.get("hits") if isinstance(kb.get("hits"), list) else []
    threshold_source_ids = _source_ids(hits)
    source_by_hint = _source_by_hint(hits)
    evidence = _accepted_evidence(session_context)
    records = _field_records(evidence)
    has_threshold_inputs = _has_threshold_inputs(records)
    missing_inputs: list[str] = []

    if not evidence:
        missing_inputs.append("accepted maintenance session evidence")
    elif not has_threshold_inputs:
        missing_inputs.append("condition readings, alarm fields, or lubrication date")
    if not thresholds:
        missing_inputs.append("matched maintenance KB thresholds")

    breaches: list[MaintenanceSignalBreach] = []
    observations: list[dict[str, object]] = []

    if thresholds and records:
        _evaluate_numeric_breach(
            breaches,
            records,
            thresholds,
            signal="vibration_rms_mm_s",
            field_names=("vibration_rms_mm_s", "vib_rms_mm_s", "vibration_rms"),
            threshold_key="vibration_rms_high_mm_s",
            unit="mm/s",
            comparator=">",
            severity="high",
            kb_source_id=_source_for_hint(source_by_hint, "GBX-VIB"),
            reason="vibration RMS exceeds the retrieved gearbox high-condition threshold",
        )
        _evaluate_numeric_breach(
            breaches,
            records,
            thresholds,
            signal="gearbox_temperature_c",
            field_names=("gearbox_temperature_c", "gearbox_temp_c", "gearbox_temperature"),
            threshold_key="gearbox_temperature_high_c",
            unit="C",
            comparator=">=",
            severity="high",
            kb_source_id=_source_for_hint(source_by_hint, "GBX-TEMP"),
            reason="gearbox temperature is at or above the retrieved high-condition threshold",
        )
        _evaluate_numeric_breach(
            breaches,
            records,
            thresholds,
            signal="bearing_temperature_c",
            field_names=("bearing_temperature_c", "bearing_temp_c", "bearing_temperature"),
            threshold_key="bearing_temperature_high_c",
            unit="C",
            comparator=">=",
            severity="high",
            kb_source_id=_source_for_hint(source_by_hint, "GBX-TEMP"),
            reason="bearing temperature is at or above the retrieved high-condition threshold",
        )
        _evaluate_alarm_breach(breaches, records, thresholds, _source_for_hint(source_by_hint, "GBX-VIB"))
        _evaluate_lubrication_interval_breach(
            breaches,
            records,
            thresholds,
            kb_source_id=_source_for_hint(source_by_hint, "GBX-LUBE"),
            now=now or datetime.now(timezone.utc),
        )

    _collect_sensory_observations(observations, records)

    status = _status_for(
        evidence=evidence,
        thresholds=thresholds,
        has_threshold_inputs=has_threshold_inputs,
        breaches=breaches,
    )
    risk_level = _risk_level_for(breaches)
    return MaintenanceConditionEvaluation(
        version=MAINTENANCE_EVALUATION_VERSION,
        status=status,
        risk_level=risk_level,
        query_asset_id=str(kb.get("query_asset_id") or "") or None,
        threshold_source_ids=threshold_source_ids,
        breaches=tuple(breaches),
        observations=tuple(observations),
        missing_inputs=tuple(dict.fromkeys(missing_inputs)),
        recommended_channel=_recommended_channel_for(status, risk_level),
        requires_human=status != "within_bounds",
    )


def build_maintenance_condition_prompt_context(result: MaintenanceConditionEvaluation | None) -> str:
    if result is None:
        return ""
    data = result.as_dict()
    lines = [
        "Deterministic maintenance condition evaluation:",
        f"- status={data['status']}; risk={data['risk_level']}; channel={data['recommended_channel']}.",
    ]
    if result.breaches:
        breach_text = "; ".join(
            (
                f"{breach.signal} {breach.observed} {breach.comparator} {breach.threshold} "
                f"({breach.kb_source_id}, {breach.evidence_type}.{breach.source_field})"
            )
            for breach in result.breaches
        )
        lines.append(f"- breaches: {breach_text}.")
    if result.missing_inputs:
        lines.append(f"- missing: {', '.join(result.missing_inputs)}.")
    lines.append("Rule: deterministic KB/session comparison; no RCA, RUL, restart permission, or maintenance release.")
    return "\n".join(lines)


def _accepted_evidence(session_context: dict[str, object] | None) -> tuple[dict[str, object], ...]:
    if not isinstance(session_context, dict):
        return ()
    raw = session_context.get("accepted_evidence")
    if not isinstance(raw, list):
        return ()
    return tuple(item for item in raw if isinstance(item, dict))


def _field_records(evidence: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    records: list[dict[str, object]] = []
    for item in evidence:
        fields = item.get("fields")
        if not isinstance(fields, dict):
            continue
        evidence_type = str(item.get("evidence_type") or "unknown")
        for field, value in fields.items():
            records.append(
                {
                    "field": str(field),
                    "value": value,
                    "evidence_type": evidence_type,
                }
            )
    return tuple(records)


def _evaluate_numeric_breach(
    breaches: list[MaintenanceSignalBreach],
    records: tuple[dict[str, object], ...],
    thresholds: dict[str, object],
    *,
    signal: str,
    field_names: tuple[str, ...],
    threshold_key: str,
    unit: str,
    comparator: str,
    severity: str,
    kb_source_id: str,
    reason: str,
) -> None:
    record = _first_record(records, *field_names)
    observed = _number(record.get("value") if record else None)
    threshold = _number(thresholds.get(threshold_key))
    if record is None or observed is None or threshold is None:
        return
    breached = observed > threshold if comparator == ">" else observed >= threshold
    if not breached:
        return
    breaches.append(
        MaintenanceSignalBreach(
            signal=signal,
            observed=f"{observed:g} {unit}",
            threshold=f"{threshold:g} {unit}",
            comparator=comparator,
            severity=severity,
            evidence_type=str(record["evidence_type"]),
            source_field=str(record["field"]),
            kb_source_id=kb_source_id,
            reason=reason,
        )
    )


def _evaluate_alarm_breach(
    breaches: list[MaintenanceSignalBreach],
    records: tuple[dict[str, object], ...],
    thresholds: dict[str, object],
    kb_source_id: str,
) -> None:
    code_record = _first_record(records, "alarm_code", "plc_alarm_code")
    color_record = _first_record(records, "alarm_color", "plc_alarm_color")
    code = str(code_record.get("value") if code_record else "").strip().upper()
    color = str(color_record.get("value") if color_record else "").strip().lower()
    expected_codes = {str(item).upper() for item in _list_threshold(thresholds, "yellow_alarm_codes")}
    expected_colors = {str(item).lower() for item in _list_threshold(thresholds, "yellow_alarm_colors")}
    if not ((code and code in expected_codes) or (color and color in expected_colors)):
        return
    source_record = code_record or color_record
    assert source_record is not None
    observed = " ".join(part for part in (color, code) if part) or "active alarm"
    breaches.append(
        MaintenanceSignalBreach(
            signal="plc_alarm",
            observed=observed,
            threshold="yellow/amber alarm configured in maintenance KB",
            comparator="matches",
            severity="medium",
            evidence_type=str(source_record["evidence_type"]),
            source_field=str(source_record["field"]),
            kb_source_id=kb_source_id,
            reason="PLC alarm matches the retrieved gearbox warning-alarm rule",
        )
    )


def _evaluate_lubrication_interval_breach(
    breaches: list[MaintenanceSignalBreach],
    records: tuple[dict[str, object], ...],
    thresholds: dict[str, object],
    *,
    kb_source_id: str,
    now: datetime,
) -> None:
    record = _first_record(records, "lubrication_date", "last_lubrication_date", "last_lube_date")
    max_days = _number(thresholds.get("lubrication_max_interval_days"))
    if record is None or max_days is None:
        return
    observed_date = _parse_date(str(record.get("value") or ""))
    if observed_date is None:
        return
    age_days = (now.date() - observed_date.date()).days
    if age_days < int(max_days):
        return
    breaches.append(
        MaintenanceSignalBreach(
            signal="lubrication_interval_days",
            observed=f"{age_days} day(s) since lubrication",
            threshold=f"{int(max_days)} day(s)",
            comparator=">=",
            severity="medium",
            evidence_type=str(record["evidence_type"]),
            source_field=str(record["field"]),
            kb_source_id=kb_source_id,
            reason="lubrication record age meets or exceeds the retrieved maximum check interval",
        )
    )


def _collect_sensory_observations(
    observations: list[dict[str, object]],
    records: tuple[dict[str, object], ...],
) -> None:
    sensory_fields = {
        "unusual_noise": "operator_noise",
        "unusual_smell": "operator_smell",
        "felt_heat": "operator_heat",
        "felt_shaking": "operator_vibration",
        "visible_leak": "operator_visible_leak",
        "started_when": "operator_timing",
    }
    for field_name, signal in sensory_fields.items():
        record = _first_record(records, field_name)
        if record is None:
            continue
        value = str(record.get("value") or "").strip()
        if not value:
            continue
        observations.append(
            {
                "signal": signal,
                "observed": value,
                "evidence_type": str(record["evidence_type"]),
                "source_field": str(record["field"]),
            }
        )


def _status_for(
    *,
    evidence: tuple[dict[str, object], ...],
    thresholds: dict[str, object],
    has_threshold_inputs: bool,
    breaches: list[MaintenanceSignalBreach],
) -> str:
    if not evidence or not thresholds or not has_threshold_inputs:
        return "insufficient_evidence"
    if breaches:
        return "breach_detected"
    return "within_bounds"


def _has_threshold_inputs(records: tuple[dict[str, object], ...]) -> bool:
    watched_fields = {
        "vibration_rms_mm_s",
        "vib_rms_mm_s",
        "vibration_rms",
        "gearbox_temperature_c",
        "gearbox_temp_c",
        "gearbox_temperature",
        "bearing_temperature_c",
        "bearing_temp_c",
        "bearing_temperature",
        "alarm_code",
        "plc_alarm_code",
        "alarm_color",
        "plc_alarm_color",
        "lubrication_date",
        "last_lubrication_date",
        "last_lube_date",
    }
    return any(str(record.get("field") or "").lower() in watched_fields for record in records)


def _risk_level_for(breaches: list[MaintenanceSignalBreach]) -> str:
    high_count = sum(1 for breach in breaches if breach.severity == "high")
    if high_count >= 2:
        return "high"
    if high_count == 1 or breaches:
        return "medium"
    return "low"


def _recommended_channel_for(status: str, risk_level: str) -> str:
    if status == "breach_detected" and risk_level == "high":
        return "maintenance_report"
    if status == "breach_detected":
        return "condition_inspection"
    if status == "within_bounds":
        return "condition_monitoring"
    return "maintenance_identification_required"


def _first_record(records: tuple[dict[str, object], ...], *field_names: str) -> dict[str, object] | None:
    normalized_names = {name.lower() for name in field_names}
    for record in records:
        if str(record.get("field") or "").lower() in normalized_names:
            return record
    return None


def _number(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = NUMBER_RE.search(str(value))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _parse_date(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _list_threshold(thresholds: dict[str, object], key: str) -> tuple[str, ...]:
    value = thresholds.get(key)
    if isinstance(value, list):
        return tuple(str(item) for item in value if str(item).strip())
    if value:
        return (str(value),)
    return ()


def _source_ids(hits: list[object]) -> tuple[str, ...]:
    source_ids: list[str] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        revision = str(hit.get("revision") or "unknown")
        section_id = str(hit.get("section_id") or "section")
        source_ids.append(f"{revision}#{section_id}")
    return tuple(dict.fromkeys(source_ids))


def _source_by_hint(hits: list[object]) -> dict[str, str]:
    sources: dict[str, str] = {}
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        section_id = str(hit.get("section_id") or "")
        source_id = f"{hit.get('revision', 'unknown')}#{section_id or 'section'}"
        for hint in ("GBX-VIB", "GBX-TEMP", "GBX-LUBE", "GBX-HUMAN"):
            if section_id.startswith(hint):
                sources.setdefault(hint, source_id)
    return sources


def _source_for_hint(source_by_hint: dict[str, str], hint: str) -> str:
    return source_by_hint.get(hint, hint)
