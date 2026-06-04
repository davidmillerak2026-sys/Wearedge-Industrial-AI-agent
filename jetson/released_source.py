from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent_profiles import normalize_agent_mode


RELEASED_SOURCE_VERSION = "wear-edge-released-source.v1"
RELEASED_SOURCE_EVALUATION_VERSION = "wear-edge-released-source-eval.v1"
DEFAULT_SOURCE_DIR = Path(__file__).resolve().parents[1] / "data" / "released_sources"
WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?")
MAX_CONTENT_CHARS = 140


@dataclass(frozen=True)
class ReleasedSourceHit:
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
class ReleasedSourceResult:
    version: str
    mode: str
    status: str
    source_dir: str
    source_type: str
    source_id: str | None
    revision: str | None
    machine_id: str | None
    sku_id: str | None
    hits: tuple[ReleasedSourceHit, ...]
    authority: dict[str, Any] | None = None
    required_confirmations: tuple[str, ...] = ()
    missing_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "mode": self.mode,
            "status": self.status,
            "source_dir": self.source_dir,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "revision": self.revision,
            "machine_id": self.machine_id,
            "sku_id": self.sku_id,
            "hits": [hit.as_dict() for hit in self.hits],
            "authority": dict(self.authority or {}),
            "required_confirmations": list(self.required_confirmations),
            "missing_reason": self.missing_reason,
        }


@dataclass(frozen=True)
class ReleasedSourceEvaluation:
    version: str
    mode: str
    status: str
    source_status: str
    source_ids: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    recommended_channel: str
    requires_human: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "mode": self.mode,
            "status": self.status,
            "source_status": self.source_status,
            "source_ids": list(self.source_ids),
            "missing_inputs": list(self.missing_inputs),
            "recommended_channel": self.recommended_channel,
            "requires_human": self.requires_human,
            "blocked_claims": _blocked_claims_for(self.mode),
        }


def retrieve_released_source_context(
    *,
    mode: str,
    query_text: str,
    source_dir: Path | None = None,
    max_hits: int = 3,
) -> ReleasedSourceResult:
    resolved = normalize_agent_mode(mode)
    if resolved not in {"wi", "changeover"}:
        return _not_applicable(resolved, source_dir or DEFAULT_SOURCE_DIR)
    resolved_dir = source_dir or DEFAULT_SOURCE_DIR
    documents = _load_documents(resolved_dir, mode=resolved)
    if not documents:
        return ReleasedSourceResult(
            version=RELEASED_SOURCE_VERSION,
            mode=resolved,
            status="not_configured",
            source_dir=str(resolved_dir),
            source_type=_source_type_for(resolved),
            source_id=None,
            revision=None,
            machine_id=None,
            sku_id=None,
            hits=(),
            missing_reason=f"no released {resolved} source documents found",
        )

    query = query_text.lower()
    query_terms = _terms(query_text)
    best_document = _select_document(documents, mode=resolved, query=query, query_terms=query_terms)
    if best_document is None:
        return ReleasedSourceResult(
            version=RELEASED_SOURCE_VERSION,
            mode=resolved,
            status="no_match",
            source_dir=str(resolved_dir),
            source_type=_source_type_for(resolved),
            source_id=None,
            revision=None,
            machine_id=None,
            sku_id=None,
            hits=(),
            required_confirmations=_required_confirmations_for(resolved),
            missing_reason=_missing_reason_for(resolved),
        )

    hits = _rank_section_hits(best_document, query=query, query_terms=query_terms, max_hits=max_hits)
    return ReleasedSourceResult(
        version=RELEASED_SOURCE_VERSION,
        mode=resolved,
        status="matched",
        source_dir=str(resolved_dir),
        source_type=_source_type_for(resolved),
        source_id=str(best_document.get("source_id") or ""),
        revision=str(best_document.get("revision") or "unknown"),
        machine_id=str(best_document.get("machine_id") or "") or None,
        sku_id=str(best_document.get("sku_id") or "") or None,
        hits=hits,
        authority=_clean_dict(best_document.get("authority")),
        required_confirmations=tuple(
            str(item) for item in best_document.get("required_confirmations", []) if str(item).strip()
        )
        or _required_confirmations_for(resolved),
    )


def build_released_source_prompt_context(result: ReleasedSourceResult | None) -> str:
    if result is None:
        return ""
    label = "Released WI source" if result.mode == "wi" else "Released changeover source"
    if result.status != "matched":
        return (
            f"{label} context:\n"
            f"- Retrieval status: {result.status}.\n"
            f"- Missing reason: {result.missing_reason or 'no matched released source'}.\n"
            "- Do not claim released operating steps, restart readiness, recipe authority, or WI revision without a matched source."
        )
    lines = [
        f"{label} context:",
        (
            f"- status={result.status}; source={result.source_id or 'unknown'}; "
            f"revision={result.revision or 'unknown'}; machine={result.machine_id or 'unknown'}; "
            f"sku={result.sku_id or 'not_applicable'}."
        ),
    ]
    if result.authority:
        authority = "; ".join(f"{key}={value}" for key, value in sorted(result.authority.items()))
        lines.append(f"- authority: {authority}.")
    for hit in result.hits:
        lines.append(f"- source {hit.revision}#{hit.section_id} ({hit.section_title}): {hit.content}")
    lines.append("Source rule: cite released source context, but keep completion/restart authority human-confirmed.")
    return "\n".join(lines)


def evaluate_released_source_condition(
    *,
    mode: str,
    fields: dict[str, object],
    knowledge_base: dict[str, object] | None,
) -> ReleasedSourceEvaluation | None:
    resolved = normalize_agent_mode(mode)
    if resolved not in {"wi", "changeover"}:
        return None
    kb = knowledge_base if isinstance(knowledge_base, dict) else {}
    source_status = str(kb.get("status") or "missing")
    matched = source_status == "matched"
    missing_inputs: list[str] = []
    if not matched:
        missing_inputs.append("released work instruction source" if resolved == "wi" else "released changeover checklist")
    if resolved == "changeover" and matched and not str(kb.get("sku_id") or "").strip():
        missing_inputs.append("target SKU source")
    if _has_restart_or_completion_claim(resolved, fields) and missing_inputs:
        status = "blocked_completion_claim"
    elif missing_inputs:
        status = "missing_released_source"
    else:
        status = "released_source_matched"
    recommended_channel = (
        "wi_source_required"
        if resolved == "wi" and missing_inputs
        else "changeover_source_required"
        if resolved == "changeover" and missing_inputs
        else "guided_operation"
        if resolved == "wi"
        else "controlled_changeover_step"
    )
    return ReleasedSourceEvaluation(
        version=RELEASED_SOURCE_EVALUATION_VERSION,
        mode=resolved,
        status=status,
        source_status=source_status,
        source_ids=_source_ids(kb),
        missing_inputs=tuple(dict.fromkeys(missing_inputs)),
        recommended_channel=recommended_channel,
        requires_human=bool(missing_inputs),
    )


def build_released_source_evaluation_prompt_context(result: ReleasedSourceEvaluation | None) -> str:
    if result is None:
        return ""
    data = result.as_dict()
    lines = [
        "Deterministic released-source evaluation:",
        (
            f"- status={data['status']}; source_status={data['source_status']}; "
            f"channel={data['recommended_channel']}."
        ),
    ]
    if result.source_ids:
        lines.append(f"- sources: {', '.join(result.source_ids)}.")
    if result.missing_inputs:
        lines.append(f"- missing: {', '.join(result.missing_inputs)}.")
    lines.append("Rule: released source is required before trusted WI guidance or changeover continuation.")
    return "\n".join(lines)


def _not_applicable(mode: str, source_dir: Path) -> ReleasedSourceResult:
    return ReleasedSourceResult(
        version=RELEASED_SOURCE_VERSION,
        mode=mode,
        status="not_applicable",
        source_dir=str(source_dir),
        source_type="not_applicable",
        source_id=None,
        revision=None,
        machine_id=None,
        sku_id=None,
        hits=(),
    )


def _load_documents(source_dir: Path, *, mode: str) -> tuple[dict[str, Any], ...]:
    if not source_dir.exists():
        return ()
    documents: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("released") is not False and str(data.get("mode") or "") == mode:
            documents.append(data)
    return tuple(documents)


def _select_document(
    documents: tuple[dict[str, Any], ...],
    *,
    mode: str,
    query: str,
    query_terms: set[str],
) -> dict[str, Any] | None:
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for document in documents:
        score = 0
        machine_score = _alias_score(document.get("machine_id"), document.get("machine_aliases"), query, query_terms)
        sku_score = _alias_score(document.get("sku_id"), document.get("sku_aliases"), query, query_terms)
        if mode == "wi":
            if machine_score <= 0:
                continue
            score += machine_score + 20
        if mode == "changeover":
            if sku_score <= 0:
                continue
            score += sku_score + max(machine_score, 0) + 20
        for section in document.get("sections", []):
            if isinstance(section, dict):
                keywords = tuple(str(item).lower() for item in section.get("keywords", []) if str(item).strip())
                score += sum(2 for keyword in keywords if keyword in query or keyword in query_terms)
        if score > 0:
            scored.append((score, str(document.get("source_id") or ""), document))
    if not scored:
        return None
    return sorted(scored, key=lambda item: (-item[0], item[1]))[0][2]


def _rank_section_hits(
    document: dict[str, Any],
    *,
    query: str,
    query_terms: set[str],
    max_hits: int,
) -> tuple[ReleasedSourceHit, ...]:
    source_id = str(document.get("source_id") or "released_source")
    revision = str(document.get("revision") or "unknown")
    source_title = str(document.get("title") or _source_type_for(str(document.get("mode") or "")))
    hits: list[ReleasedSourceHit] = []
    for section in document.get("sections", []):
        if not isinstance(section, dict):
            continue
        keywords = tuple(str(item).lower() for item in section.get("keywords", []) if str(item).strip())
        matched = tuple(keyword for keyword in keywords if keyword in query or keyword in query_terms)
        hits.append(
            ReleasedSourceHit(
                source_id=source_id,
                source_title=source_title,
                revision=revision,
                section_id=str(section.get("id") or "section"),
                section_title=str(section.get("title") or "Untitled section"),
                content=_truncate(str(section.get("content") or "")),
                score=6 + len(matched) * 3,
                matched_terms=matched,
            )
        )
    return tuple(sorted(hits, key=lambda hit: (-hit.score, hit.section_id))[:max_hits])


def _alias_score(
    identifier: object,
    aliases: object,
    query: str,
    query_terms: set[str],
) -> int:
    candidates = [str(identifier or "").lower()]
    if isinstance(aliases, list):
        candidates.extend(str(item).lower() for item in aliases if str(item).strip())
    score = 0
    for candidate in candidates:
        if not candidate:
            continue
        if candidate in query:
            score = max(score, 18)
        elif candidate.replace("-", " ") in query:
            score = max(score, 14)
        elif candidate in query_terms:
            score = max(score, 10)
    return score


def _source_ids(kb: dict[str, object]) -> tuple[str, ...]:
    hits = kb.get("hits") if isinstance(kb.get("hits"), list) else []
    source_ids: list[str] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        revision = str(hit.get("revision") or "unknown")
        section_id = str(hit.get("section_id") or "section")
        source_ids.append(f"{revision}#{section_id}")
    return tuple(dict.fromkeys(source_ids))


def _has_restart_or_completion_claim(mode: str, fields: dict[str, object]) -> bool:
    text = " ".join(str(value) for value in fields.values() if value).lower()
    if mode == "changeover":
        return any(marker in text for marker in ("restart", "start up", "startup", "complete", "release"))
    return any(marker in text for marker in ("operate", "follow", "adjust", "set parameter", "continue"))


def _blocked_claims_for(mode: str) -> tuple[str, ...]:
    if mode == "changeover":
        return (
            "restart authorization",
            "changeover completion",
            "recipe release",
            "first-piece release",
        )
    return (
        "trusted operating instruction",
        "parameter change authority",
        "guard bypass",
        "WI revision release",
    )


def _source_type_for(mode: str) -> str:
    return "released_work_instruction" if mode == "wi" else "released_changeover_checklist"


def _missing_reason_for(mode: str) -> str:
    if mode == "wi":
        return "machine identity or released WI alias is required before trusted operation guidance"
    return "target SKU and released changeover checklist alias are required before changeover continuation"


def _required_confirmations_for(mode: str) -> tuple[str, ...]:
    if mode == "wi":
        return ("machine identity", "current WI revision", "line lead confirmation")
    return ("machine identity", "target SKU", "released checklist", "first-piece verification")


def _terms(text: str) -> set[str]:
    return {match.group(0).lower() for match in WORD_RE.finditer(text)}


def _truncate(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= MAX_CONTENT_CHARS:
        return cleaned
    return f"{cleaned[:MAX_CONTENT_CHARS - 3]}..."


def _clean_dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
