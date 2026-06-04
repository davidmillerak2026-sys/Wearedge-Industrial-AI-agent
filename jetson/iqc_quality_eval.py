from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


IQC_EVALUATION_VERSION = "wear-edge-iqc-quality-eval.v1"
BLOCKED_IQC_CLAIMS = (
    "final product release",
    "customer disposition",
    "scrap authority",
    "quality hold release",
)
CONFIDENCE_RE = re.compile(r"\b(?:confidence|conf)\s*[:=]?\s*(0(?:\.\d+)?|1(?:\.0+)?)\b", re.IGNORECASE)


@dataclass(frozen=True)
class IqcQualityFinding:
    defect_class: str
    severity: str
    reaction_plan: str
    rule_id: str
    evidence_source: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "defect_class": self.defect_class,
            "severity": self.severity,
            "reaction_plan": self.reaction_plan,
            "rule_id": self.rule_id,
            "evidence_source": self.evidence_source,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class IqcQualityEvaluation:
    version: str
    status: str
    risk_level: str
    query_product_id: str | None
    plan_source_ids: tuple[str, ...]
    detector_status: str
    findings: tuple[IqcQualityFinding, ...]
    missing_inputs: tuple[str, ...]
    recommended_channel: str
    requires_human: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "status": self.status,
            "risk_level": self.risk_level,
            "query_product_id": self.query_product_id,
            "plan_source_ids": list(self.plan_source_ids),
            "detector_status": self.detector_status,
            "findings": [finding.as_dict() for finding in self.findings],
            "missing_inputs": list(self.missing_inputs),
            "recommended_channel": self.recommended_channel,
            "requires_human": self.requires_human,
            "blocked_claims": list(BLOCKED_IQC_CLAIMS),
        }


def evaluate_iqc_quality_condition(
    *,
    fields: dict[str, object],
    knowledge_base: dict[str, object] | None,
    tool_plan: dict[str, object] | None = None,
    detector_evidence: dict[str, object] | None = None,
) -> IqcQualityEvaluation:
    kb = knowledge_base if isinstance(knowledge_base, dict) else {}
    plan_matched = str(kb.get("status") or "") == "matched"
    detector = kb.get("detector") if isinstance(kb.get("detector"), dict) else {}
    required_for_pass = bool(detector.get("required_for_pass"))
    min_confidence = _number(detector.get("minimum_confidence")) or 0.0
    detector_status = _detector_status(
        fields,
        min_confidence=min_confidence,
        tool_plan=tool_plan,
        detector_evidence=detector_evidence,
    )
    missing_inputs: list[str] = []
    if not plan_matched:
        missing_inputs.append("matched IQC quality plan")
    if required_for_pass and detector_status in {"missing", "missing_tool_connection", "below_confidence", "invalid"}:
        missing_inputs.append("visual defect detector evidence")

    findings = _merge_findings(
        _findings_from_detector(detector_evidence, kb, min_confidence=min_confidence),
        _findings_from_rules(fields, kb),
    )
    disposition = _field_text(fields, "disposition").lower()
    risk_level = _risk_level_for(findings=findings, disposition=disposition)
    status = _status_for(
        plan_matched=plan_matched,
        detector_status=detector_status,
        required_for_pass=required_for_pass,
        findings=findings,
        disposition=disposition,
        missing_inputs=missing_inputs,
    )
    recommended_channel = _recommended_channel_for(
        status=status,
        risk_level=risk_level,
        disposition=disposition,
        findings=findings,
    )
    return IqcQualityEvaluation(
        version=IQC_EVALUATION_VERSION,
        status=status,
        risk_level=risk_level,
        query_product_id=str(kb.get("query_product_id") or "") or None,
        plan_source_ids=_source_ids(kb),
        detector_status=detector_status,
        findings=tuple(findings),
        missing_inputs=tuple(dict.fromkeys(missing_inputs)),
        recommended_channel=recommended_channel,
        requires_human=recommended_channel != "continue_production",
    )


def build_iqc_quality_prompt_context(result: IqcQualityEvaluation | None) -> str:
    if result is None:
        return ""
    data = result.as_dict()
    lines = [
        "Deterministic IQC quality evaluation:",
        (
            f"- status={data['status']}; risk={data['risk_level']}; "
            f"detector={data['detector_status']}; channel={data['recommended_channel']}."
        ),
    ]
    if result.findings:
        finding_text = "; ".join(
            (
                f"{finding.defect_class}/{finding.severity} -> {finding.reaction_plan} "
                f"({finding.rule_id}, {finding.evidence_source})"
            )
            for finding in result.findings
        )
        lines.append(f"- findings: {finding_text}.")
    if result.missing_inputs:
        lines.append(f"- missing: {', '.join(result.missing_inputs)}.")
    lines.append("Rule: detector and quality-plan evidence gate pass/release; QMS authority owns final disposition.")
    return "\n".join(lines)


def _findings_from_rules(fields: dict[str, object], kb: dict[str, object]) -> list[IqcQualityFinding]:
    rules = kb.get("defect_rules") if isinstance(kb.get("defect_rules"), list) else []
    text = _quality_observation_text(fields)
    if _is_insufficient_detector_pass_text(text):
        return []
    if _is_explicit_clean_pass_text(text):
        return []
    findings: list[IqcQualityFinding] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        keywords = tuple(str(item).lower() for item in rule.get("keywords", []) if str(item).strip())
        matched = tuple(keyword for keyword in keywords if keyword in text)
        defect_class = str(rule.get("defect_class") or "")
        if not matched and defect_class and defect_class.replace("_", " ") not in text:
            continue
        findings.append(
            IqcQualityFinding(
                defect_class=defect_class or "unknown_defect",
                severity=str(rule.get("severity") or "unknown"),
                reaction_plan=str(rule.get("reaction_plan") or "needs_review"),
                rule_id=str(rule.get("id") or "quality_rule"),
                evidence_source="vlm_structured_fields",
                reason=f"matched quality-plan term(s): {', '.join(matched or (defect_class,))}",
            )
        )
    return findings


def _findings_from_detector(
    detector_evidence: dict[str, object] | None,
    kb: dict[str, object],
    *,
    min_confidence: float,
) -> list[IqcQualityFinding]:
    if not isinstance(detector_evidence, dict) or detector_evidence.get("status") != "available":
        return []
    rules = kb.get("defect_rules") if isinstance(kb.get("defect_rules"), list) else []
    rules_by_class = {
        str(rule.get("defect_class") or "").lower(): rule
        for rule in rules
        if isinstance(rule, dict) and str(rule.get("defect_class") or "").strip()
    }
    detections = detector_evidence.get("detections") if isinstance(detector_evidence.get("detections"), list) else []
    findings: list[IqcQualityFinding] = []
    for detection in detections:
        if not isinstance(detection, dict):
            continue
        defect_class = str(detection.get("defect_class") or detection.get("label") or "").lower()
        if not defect_class:
            continue
        confidence = _number(detection.get("confidence"))
        if confidence is None or confidence < min_confidence:
            continue
        rule = rules_by_class.get(defect_class)
        detection_id = str(detection.get("detection_id") or defect_class)
        if rule is None:
            findings.append(
                IqcQualityFinding(
                    defect_class=defect_class,
                    severity="unknown",
                    reaction_plan="quality_review",
                    rule_id="unmapped_detector_class",
                    evidence_source=f"visual_defect_detector:{detection_id}",
                    reason=f"detector class {defect_class} confidence {confidence:.2f} has no mapped quality rule",
                )
            )
            continue
        findings.append(
            IqcQualityFinding(
                defect_class=defect_class,
                severity=str(rule.get("severity") or "unknown"),
                reaction_plan=str(rule.get("reaction_plan") or "quality_review"),
                rule_id=str(rule.get("id") or "quality_rule"),
                evidence_source=f"visual_defect_detector:{detection_id}",
                reason=f"detector class {defect_class} confidence {confidence:.2f} >= {min_confidence:.2f}",
            )
        )
    return findings


def _merge_findings(
    primary: list[IqcQualityFinding],
    secondary: list[IqcQualityFinding],
) -> list[IqcQualityFinding]:
    merged: list[IqcQualityFinding] = []
    seen: set[tuple[str, str]] = set()
    for finding in [*primary, *secondary]:
        key = (finding.rule_id, finding.defect_class)
        if key in seen:
            continue
        seen.add(key)
        merged.append(finding)
    return merged


def _is_explicit_clean_pass_text(text: str) -> bool:
    clean_markers = (
        "no visible quality risk",
        "no visible defect",
        "detector clear",
        "detector no defect",
        "detector passed",
    )
    defect_markers = (
        "burr",
        "scratch",
        "contamination",
        "foreign material",
        "wrong label",
        "label mismatch",
        "missing feature",
        "missing hole",
        "mixed sku",
        "mix-up",
    )
    return any(marker in text for marker in clean_markers) and not any(marker in text for marker in defect_markers)


def _is_insufficient_detector_pass_text(text: str) -> bool:
    insufficient_markers = (
        "insufficient detector evidence",
        "detector evidence is unavailable",
        "detector evidence unavailable",
        "not enough detector evidence",
    )
    return " pass " in f" {text} " and any(marker in text for marker in insufficient_markers)


def _detector_status(
    fields: dict[str, object],
    *,
    min_confidence: float,
    tool_plan: dict[str, object] | None,
    detector_evidence: dict[str, object] | None,
) -> str:
    if isinstance(detector_evidence, dict):
        status = str(detector_evidence.get("status") or "")
        if status == "invalid":
            return "invalid"
        detections = detector_evidence.get("detections") if isinstance(detector_evidence.get("detections"), list) else []
        if status == "clear" or not detections:
            return "provided_clear"
        usable_confidences = [
            confidence
            for confidence in (_number(item.get("confidence")) for item in detections if isinstance(item, dict))
            if confidence is not None and confidence >= min_confidence
        ]
        return "provided" if usable_confidences else "below_confidence"

    text = _joined_field_text(fields)
    if "detector clear" in text or "detector no defect" in text or "detector passed" in text:
        return "provided_clear"
    if "detector" in text or "bbox" in text or "confidence" in text:
        confidence = _detector_confidence(text)
        if confidence is not None and confidence < min_confidence:
            return "below_confidence"
        return "provided"
    skipped = tool_plan.get("skipped_tools", []) if isinstance(tool_plan, dict) else []
    if any(isinstance(item, dict) and item.get("name") == "visual_defect_detector" for item in skipped):
        return "missing_tool_connection"
    return "missing"


def _status_for(
    *,
    plan_matched: bool,
    detector_status: str,
    required_for_pass: bool,
    findings: list[IqcQualityFinding],
    disposition: str,
    missing_inputs: list[str],
) -> str:
    if not plan_matched:
        return "insufficient_evidence"
    if findings:
        if detector_status in {"provided", "provided_clear"}:
            return "detector_or_plan_risk_detected"
        return "visible_risk_needs_detector_review"
    if disposition == "pass":
        if required_for_pass and detector_status not in {"provided", "provided_clear"}:
            return "insufficient_detector_evidence"
        return "within_plan_observation"
    if missing_inputs:
        return "insufficient_evidence"
    return "quality_review_required"


def _risk_level_for(*, findings: list[IqcQualityFinding], disposition: str) -> str:
    severities = {finding.severity.lower() for finding in findings}
    if "critical" in severities or disposition == "stop_production":
        return "high"
    if severities.intersection({"major", "high"}) or disposition in {"quality_hold", "scrap", "capa_request"}:
        return "medium"
    if disposition in {"expand_inspection", "rework", "needs_review"}:
        return "medium"
    return "low"


def _recommended_channel_for(
    *,
    status: str,
    risk_level: str,
    disposition: str,
    findings: list[IqcQualityFinding],
) -> str:
    if status in {"insufficient_evidence", "insufficient_detector_evidence", "quality_review_required"}:
        return "quality_review"
    if findings:
        reactions = [finding.reaction_plan for finding in findings]
        if "stop_production" in reactions or risk_level == "high":
            return "stop_production"
        if "quality_hold" in reactions:
            return "quality_hold"
        if "expand_inspection" in reactions:
            return "expand_inspection"
        return "quality_review"
    if disposition in {
        "needs_review",
        "expand_inspection",
        "quality_hold",
        "stop_production",
        "rework",
        "scrap",
        "capa_request",
    }:
        return {
            "needs_review": "quality_review",
            "rework": "rework_hold",
            "scrap": "scrap_review",
        }.get(disposition, disposition)
    return "continue_production"


def _source_ids(kb: dict[str, object]) -> tuple[str, ...]:
    hits = kb.get("hits") if isinstance(kb.get("hits"), list) else []
    source_ids: list[str] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        revision = str(hit.get("revision") or "unknown")
        section_id = str(hit.get("section_id") or "rule")
        source_ids.append(f"{revision}#{section_id}")
    return tuple(dict.fromkeys(source_ids))


def _joined_field_text(fields: dict[str, object]) -> str:
    return " ".join(str(value) for _, value in sorted(fields.items()) if value is not None).lower()


def _quality_observation_text(fields: dict[str, object]) -> str:
    keys = ("quality_risk", "disposition", "action")
    return " ".join(str(fields.get(key) or "") for key in keys).lower()


def _field_text(fields: dict[str, object], key: str) -> str:
    return str(fields.get(key) or "").strip()


def _detector_confidence(text: str) -> float | None:
    match = CONFIDENCE_RE.search(text)
    if not match:
        return None
    return _number(match.group(1))


def _number(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None
