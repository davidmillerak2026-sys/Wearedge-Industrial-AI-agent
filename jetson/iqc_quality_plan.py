from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IQC_QUALITY_PLAN_VERSION = "wear-edge-iqc-quality-plan.v1"
DEFAULT_PLAN_DIR = Path(__file__).resolve().parents[1] / "data" / "iqc_quality_plans"
PRODUCT_ID_RE = re.compile(r"\b[A-Z]{2,6}-[A-Z0-9]+-[A-Z0-9]+\b", re.IGNORECASE)
WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?")
MAX_CONTENT_CHARS = 130


@dataclass(frozen=True)
class IqcQualityPlanHit:
    plan_id: str
    product_id: str
    source_id: str
    source_title: str
    revision: str
    section_id: str
    defect_class: str
    severity: str
    reaction_plan: str
    content: str
    score: int
    matched_terms: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "product_id": self.product_id,
            "source_id": self.source_id,
            "source_title": self.source_title,
            "revision": self.revision,
            "section_id": self.section_id,
            "defect_class": self.defect_class,
            "severity": self.severity,
            "reaction_plan": self.reaction_plan,
            "content": self.content,
            "score": self.score,
            "matched_terms": list(self.matched_terms),
        }


@dataclass(frozen=True)
class IqcQualityPlanResult:
    version: str
    status: str
    query_product_id: str | None
    plan_dir: str
    hits: tuple[IqcQualityPlanHit, ...]
    detector: dict[str, Any] | None = None
    sampling_rule: dict[str, Any] | None = None
    defect_rules: tuple[dict[str, Any], ...] = ()
    missing_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "status": self.status,
            "query_product_id": self.query_product_id,
            "plan_dir": self.plan_dir,
            "hits": [hit.as_dict() for hit in self.hits],
            "detector": dict(self.detector or {}),
            "sampling_rule": dict(self.sampling_rule or {}),
            "defect_rules": [dict(rule) for rule in self.defect_rules],
            "missing_reason": self.missing_reason,
        }


def retrieve_iqc_quality_plan_context(
    *,
    query_text: str,
    plan_dir: Path | None = None,
    max_hits: int = 4,
) -> IqcQualityPlanResult:
    resolved_dir = plan_dir or DEFAULT_PLAN_DIR
    documents = _load_documents(resolved_dir)
    query_product_id = _extract_product_id(query_text)
    if not documents:
        return IqcQualityPlanResult(
            version=IQC_QUALITY_PLAN_VERSION,
            status="not_configured",
            query_product_id=query_product_id,
            plan_dir=str(resolved_dir),
            hits=(),
            missing_reason="no IQC quality-plan documents found",
        )

    query = query_text.lower()
    query_terms = _terms(query_text)
    best_document = _select_document(documents, query_product_id=query_product_id, query=query, query_terms=query_terms)
    if best_document is None:
        return IqcQualityPlanResult(
            version=IQC_QUALITY_PLAN_VERSION,
            status="no_match",
            query_product_id=query_product_id,
            plan_dir=str(resolved_dir),
            hits=(),
            detector={},
            sampling_rule={},
            defect_rules=(),
            missing_reason="product identity or released quality-plan alias is required before applying IQC disposition rules",
        )

    hits = _rank_rule_hits(best_document, query=query, query_terms=query_terms, max_hits=max_hits)
    return IqcQualityPlanResult(
        version=IQC_QUALITY_PLAN_VERSION,
        status="matched",
        query_product_id=str(best_document.get("product_id") or query_product_id or ""),
        plan_dir=str(resolved_dir),
        hits=hits,
        detector=_clean_dict(best_document.get("detector")),
        sampling_rule=_clean_dict(best_document.get("sampling_rule")),
        defect_rules=_clean_rules(best_document.get("defect_rules")),
        missing_reason=None,
    )


def build_iqc_quality_plan_prompt_context(result: IqcQualityPlanResult | None) -> str:
    if result is None:
        return ""
    if result.status != "matched":
        return (
            "IQC quality-plan context:\n"
            f"- Retrieval status: {result.status}.\n"
            f"- Missing reason: {result.missing_reason or 'no matched source'}.\n"
            "- Do not claim released tolerance, sampling, pass, or disposition authority without a matched quality plan."
        )
    lines = [
        "IQC quality-plan context:",
        f"- status={result.status}; product={result.query_product_id or 'unknown'}.",
    ]
    detector_required = bool((result.detector or {}).get("required_for_pass"))
    min_confidence = (result.detector or {}).get("minimum_confidence")
    if result.sampling_rule:
        lines.append(
            "- sampling: "
            f"{result.sampling_rule.get('frequency', 'unknown frequency')}; "
            f"scope={result.sampling_rule.get('scope', 'unknown scope')}; "
            f"release={result.sampling_rule.get('release_authority', 'quality authority')}."
        )
    lines.append(
        "- detector: "
        f"required_for_pass={str(detector_required).lower()}; "
        f"minimum_confidence={min_confidence if min_confidence is not None else 'not configured'}."
    )
    for hit in result.hits:
        lines.append(
            f"- source {hit.revision}#{hit.section_id} ({hit.defect_class}/{hit.severity} -> "
            f"{hit.reaction_plan}): {hit.content}"
        )
    lines.append("Quality-plan rule: detector evidence and quality authority are required before final release.")
    return "\n".join(lines)


def _load_documents(plan_dir: Path) -> tuple[dict[str, Any], ...]:
    if not plan_dir.exists():
        return ()
    documents: list[dict[str, Any]] = []
    for path in sorted(plan_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("released") is not False:
            documents.append(data)
    return tuple(documents)


def _select_document(
    documents: tuple[dict[str, Any], ...],
    *,
    query_product_id: str | None,
    query: str,
    query_terms: set[str],
) -> dict[str, Any] | None:
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for document in documents:
        product_id = str(document.get("product_id") or "")
        aliases = tuple(str(item).lower() for item in document.get("aliases", []) if str(item).strip())
        score = 0
        if query_product_id and product_id.lower() == query_product_id.lower():
            score += 30
        if product_id.lower() in query:
            score += 24
        for alias in aliases:
            if alias in query:
                score += 12
            elif alias.replace("-", " ") in query:
                score += 8
        for rule in document.get("defect_rules", []):
            if not isinstance(rule, dict):
                continue
            keywords = tuple(str(item).lower() for item in rule.get("keywords", []) if str(item).strip())
            score += sum(2 for keyword in keywords if keyword in query or keyword in query_terms)
        if score > 0:
            scored.append((score, product_id, document))
    if not scored:
        return None
    return sorted(scored, key=lambda item: (-item[0], item[1]))[0][2]


def _rank_rule_hits(
    document: dict[str, Any],
    *,
    query: str,
    query_terms: set[str],
    max_hits: int,
) -> tuple[IqcQualityPlanHit, ...]:
    product_id = str(document.get("product_id") or "")
    revision = str(document.get("revision") or "unknown")
    plan_id = str(document.get("plan_id") or product_id or "quality_plan")
    source_title = str(document.get("product_name") or "IQC quality plan")
    hits: list[IqcQualityPlanHit] = []
    for rule in document.get("defect_rules", []):
        if not isinstance(rule, dict):
            continue
        keywords = tuple(str(item).lower() for item in rule.get("keywords", []) if str(item).strip())
        matched = tuple(keyword for keyword in keywords if keyword in query or keyword in query_terms)
        score = 6 + len(matched) * 3
        hits.append(
            IqcQualityPlanHit(
                plan_id=plan_id,
                product_id=product_id,
                source_id=f"{plan_id}:{revision}",
                source_title=source_title,
                revision=revision,
                section_id=str(rule.get("id") or "rule"),
                defect_class=str(rule.get("defect_class") or "unknown"),
                severity=str(rule.get("severity") or "unknown"),
                reaction_plan=str(rule.get("reaction_plan") or "needs_review"),
                content=_truncate(str(rule.get("content") or "")),
                score=score,
                matched_terms=matched,
            )
        )
    return tuple(sorted(hits, key=lambda hit: (-hit.score, hit.section_id))[:max_hits])


def _extract_product_id(text: str) -> str | None:
    match = PRODUCT_ID_RE.search(text.upper())
    return match.group(0).upper() if match else None


def _terms(text: str) -> set[str]:
    return {match.group(0).lower() for match in WORD_RE.finditer(text)}


def _truncate(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= MAX_CONTENT_CHARS:
        return cleaned
    return f"{cleaned[:MAX_CONTENT_CHARS - 3]}..."


def _clean_dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _clean_rules(value: object) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(dict(item) for item in value if isinstance(item, dict))
