from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAINTENANCE_KB_VERSION = "wear-edge-maintenance-kb.v1"
DEFAULT_KB_DIR = Path(__file__).resolve().parents[1] / "data" / "maintenance_kb"
ASSET_ID_RE = re.compile(r"\b[A-Z]{2,6}-[A-Z0-9]+-[A-Z0-9]+-\d{2}\b", re.IGNORECASE)
WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?")
MAX_CONTENT_CHARS = 130


@dataclass(frozen=True)
class MaintenanceKbHit:
    asset_id: str
    source_id: str
    source_title: str
    revision: str
    section_id: str
    section_title: str
    content: str
    score: int
    matched_terms: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "asset_id": self.asset_id,
            "source_id": self.source_id,
            "source_title": self.source_title,
            "revision": self.revision,
            "section_id": self.section_id,
            "section_title": self.section_title,
            "content": self.content,
            "score": self.score,
            "matched_terms": list(self.matched_terms),
        }


@dataclass(frozen=True)
class MaintenanceKbResult:
    version: str
    status: str
    query_asset_id: str | None
    kb_dir: str
    hits: tuple[MaintenanceKbHit, ...]
    thresholds: dict[str, Any] | None = None
    missing_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "status": self.status,
            "query_asset_id": self.query_asset_id,
            "kb_dir": self.kb_dir,
            "hits": [hit.as_dict() for hit in self.hits],
            "thresholds": dict(self.thresholds or {}),
            "missing_reason": self.missing_reason,
        }


def retrieve_maintenance_kb_context(
    *,
    query_text: str,
    kb_dir: Path | None = None,
    max_hits: int = 3,
) -> MaintenanceKbResult:
    resolved_dir = kb_dir or DEFAULT_KB_DIR
    documents = _load_documents(resolved_dir)
    if not documents:
        return MaintenanceKbResult(
            version=MAINTENANCE_KB_VERSION,
            status="not_configured",
            query_asset_id=_extract_asset_id(query_text),
            kb_dir=str(resolved_dir),
            hits=(),
            missing_reason="no maintenance KB documents found",
        )

    asset_id = _extract_asset_id(query_text)
    if not asset_id:
        return MaintenanceKbResult(
            version=MAINTENANCE_KB_VERSION,
            status="no_match",
            query_asset_id=None,
            kb_dir=str(resolved_dir),
            hits=(),
            thresholds={},
            missing_reason="asset identity is required before applying machine-specific maintenance KB thresholds",
        )
    query_terms = _terms(query_text)
    hits: list[MaintenanceKbHit] = []
    thresholds_by_asset: dict[str, dict[str, Any]] = {}
    for document in documents:
        doc_asset = str(document.get("asset_id") or "")
        thresholds = document.get("thresholds")
        if doc_asset and isinstance(thresholds, dict):
            thresholds_by_asset[doc_asset.lower()] = thresholds
        if doc_asset.lower() != asset_id.lower():
            continue
        doc_score = 6
        for section in document.get("sections", []):
            if not isinstance(section, dict):
                continue
            keywords = tuple(str(item).lower() for item in section.get("keywords", []) if str(item).strip())
            matched = tuple(keyword for keyword in keywords if keyword in query_terms or keyword in query_text.lower())
            score = doc_score + len(matched) * 2
            if score <= 0:
                continue
            hits.append(
                MaintenanceKbHit(
                    asset_id=doc_asset,
                    source_id=f"{doc_asset}:{document.get('revision', 'unknown')}",
                    source_title=str(document.get("title") or "Maintenance knowledge base"),
                    revision=str(document.get("revision") or "unknown"),
                    section_id=str(section.get("id") or "section"),
                    section_title=str(section.get("title") or "Untitled section"),
                    content=_truncate(str(section.get("content") or "")),
                    score=score,
                    matched_terms=matched,
                )
            )

    ranked = tuple(sorted(hits, key=lambda hit: (-hit.score, hit.section_id))[:max_hits])
    matched_thresholds = (
        _clean_thresholds(thresholds_by_asset.get(ranked[0].asset_id.lower(), {})) if ranked else {}
    )
    return MaintenanceKbResult(
        version=MAINTENANCE_KB_VERSION,
        status="matched" if ranked else "no_match",
        query_asset_id=asset_id,
        kb_dir=str(resolved_dir),
        hits=ranked,
        thresholds=matched_thresholds,
        missing_reason=None if ranked else "no KB section matched the maintenance context",
    )


def build_maintenance_kb_prompt_context(result: MaintenanceKbResult | None) -> str:
    if result is None:
        return ""
    if result.status != "matched":
        return (
            "Maintenance KB context:\n"
            f"- Retrieval status: {result.status}.\n"
            f"- Missing reason: {result.missing_reason or 'no matched source'}.\n"
            "- Do not claim manual thresholds or KB-backed failure modes unless retrieval returns matched sections."
        )
    lines = [
        "Maintenance KB context:",
        f"- status={result.status}; asset={result.query_asset_id or 'unknown'}.",
    ]
    if result.thresholds:
        lines.append(f"- thresholds: {_format_thresholds(result.thresholds)}.")
    for hit in result.hits:
        lines.append(
            f"- source {hit.revision}#{hit.section_id} ({hit.section_title}): {hit.content}"
        )
    lines.extend(
        [
            "KB rule: reference evidence only; no final root cause, RUL, restart permission, or maintenance release.",
        ]
    )
    return "\n".join(lines)


def _load_documents(kb_dir: Path) -> tuple[dict[str, Any], ...]:
    if not kb_dir.exists():
        return ()
    documents: list[dict[str, Any]] = []
    for path in sorted(kb_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            documents.append(data)
    return tuple(documents)


def _extract_asset_id(text: str) -> str | None:
    match = ASSET_ID_RE.search(text.upper())
    return match.group(0).upper() if match else None


def _terms(text: str) -> set[str]:
    return {match.group(0).lower() for match in WORD_RE.finditer(text)}


def _truncate(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= MAX_CONTENT_CHARS:
        return cleaned
    return f"{cleaned[:MAX_CONTENT_CHARS - 3]}..."


def _clean_thresholds(value: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, threshold_value in value.items():
        key_text = str(key).strip()
        if not key_text:
            continue
        if isinstance(threshold_value, (str, int, float, bool)):
            cleaned[key_text] = threshold_value
        elif isinstance(threshold_value, list):
            cleaned[key_text] = [str(item) for item in threshold_value if str(item).strip()]
    return cleaned


def _format_thresholds(thresholds: dict[str, Any]) -> str:
    labels = {
        "vibration_rms_high_mm_s": "vib",
        "gearbox_temperature_high_c": "gbx_temp",
        "bearing_temperature_high_c": "bearing_temp",
        "yellow_alarm_codes": "alarm_code",
        "yellow_alarm_colors": "alarm_color",
        "lubrication_max_interval_days": "lube_interval_days",
    }
    operators = {
        "vibration_rms_high_mm_s": ">",
        "gearbox_temperature_high_c": ">=",
        "bearing_temperature_high_c": ">=",
    }
    parts: list[str] = []
    for key in sorted(thresholds):
        value = thresholds[key]
        label = labels.get(key, key)
        if isinstance(value, list):
            value_text = ",".join(str(item) for item in value)
        else:
            value_text = str(value)
        operator = operators.get(key, "=")
        parts.append(f"{label}{operator}{value_text}")
    return "; ".join(parts)
