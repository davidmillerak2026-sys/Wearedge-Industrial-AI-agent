from __future__ import annotations

from dataclasses import dataclass
from typing import Any


IQC_DETECTOR_EVIDENCE_VERSION = "wear-edge-iqc-detector-evidence.v1"


@dataclass(frozen=True)
class IqcDetectorDetection:
    defect_class: str
    confidence: float | None
    bbox: tuple[float, ...] | None
    label: str
    detection_id: str
    source: str

    def as_dict(self) -> dict[str, object]:
        return {
            "defect_class": self.defect_class,
            "confidence": self.confidence,
            "bbox": list(self.bbox) if self.bbox is not None else None,
            "label": self.label,
            "detection_id": self.detection_id,
            "source": self.source,
        }


@dataclass(frozen=True)
class IqcDetectorEvidence:
    version: str
    status: str
    source: str
    product_id: str | None
    detections: tuple[IqcDetectorDetection, ...]
    invalid_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "version": self.version,
            "status": self.status,
            "source": self.source,
            "product_id": self.product_id,
            "detections": [detection.as_dict() for detection in self.detections],
            "detection_count": len(self.detections),
        }
        if self.invalid_reason:
            data["invalid_reason"] = self.invalid_reason
        return data


def normalize_iqc_detector_evidence(raw: dict[str, object] | None) -> IqcDetectorEvidence | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return _invalid("m400", "detector_evidence_json must be a JSON object")

    source = str(raw.get("source") or "visual_defect_detector").strip() or "visual_defect_detector"
    product_id = str(raw.get("product_id") or "").strip() or None
    has_detection_output = "detections" in raw or "defects" in raw
    raw_detections = raw.get("detections") if "detections" in raw else raw.get("defects")
    if raw_detections is None:
        if has_detection_output:
            return _invalid(source, "detections must be a JSON array")
        return _invalid(source, "detector evidence must include detections")
    if not isinstance(raw_detections, list):
        return _invalid(source, "detections must be a JSON array")

    detections: list[IqcDetectorDetection] = []
    for index, item in enumerate(raw_detections, start=1):
        detection = _normalize_detection(item, source=source, index=index)
        if detection is not None:
            detections.append(detection)

    if raw_detections and not detections:
        return _invalid(source, "detections did not include a usable defect_class or label")
    return IqcDetectorEvidence(
        version=IQC_DETECTOR_EVIDENCE_VERSION,
        status="available" if detections else "clear",
        source=source,
        product_id=product_id,
        detections=tuple(detections),
    )


def build_iqc_detector_prompt_context(evidence: IqcDetectorEvidence | None) -> str:
    if evidence is None or evidence.status == "invalid":
        return ""
    lines = [
        "Visual defect detector evidence:",
        f"- status={evidence.status}; source={evidence.source}; product_id={evidence.product_id or 'unknown'}.",
    ]
    if evidence.detections:
        detection_text = "; ".join(
            (
                f"{item.defect_class} conf={item.confidence if item.confidence is not None else 'unknown'} "
                f"bbox={list(item.bbox) if item.bbox is not None else 'none'}"
            )
            for item in evidence.detections
        )
        lines.append(f"- detections: {detection_text}.")
    else:
        lines.append("- detections: none above detector output threshold.")
    lines.append("Rule: treat detector boxes as evidence, but keep QMS disposition deterministic and traceable.")
    return "\n".join(lines)


def _normalize_detection(
    item: object,
    *,
    source: str,
    index: int,
) -> IqcDetectorDetection | None:
    if not isinstance(item, dict):
        return None
    defect_class = str(
        item.get("defect_class")
        or item.get("class")
        or item.get("class_name")
        or item.get("label")
        or ""
    ).strip()
    if not defect_class:
        return None
    label = str(item.get("label") or defect_class).strip()
    detection_id = str(item.get("detection_id") or item.get("id") or f"det-{index:03d}").strip()
    return IqcDetectorDetection(
        defect_class=defect_class.lower().replace(" ", "_"),
        confidence=_number(item.get("confidence") or item.get("score")),
        bbox=_bbox(item.get("bbox") or item.get("box")),
        label=label,
        detection_id=detection_id,
        source=source,
    )


def _invalid(source: str, reason: str) -> IqcDetectorEvidence:
    return IqcDetectorEvidence(
        version=IQC_DETECTOR_EVIDENCE_VERSION,
        status="invalid",
        source=source,
        product_id=None,
        detections=(),
        invalid_reason=reason,
    )


def _bbox(value: object) -> tuple[float, ...] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    parsed = tuple(_number(item) for item in value)
    if any(item is None for item in parsed):
        return None
    return tuple(float(item) for item in parsed if item is not None)


def _number(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(str(value))
    except (TypeError, ValueError):
        return None
