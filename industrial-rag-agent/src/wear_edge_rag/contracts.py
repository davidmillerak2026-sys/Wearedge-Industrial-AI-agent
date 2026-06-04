from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


CONTRACT_MARKER = "RAG_ANSWER_CONTRACT_V1"
REQUIRED_KEYS = (
    "direct_answer",
    "measured_facts",
    "inference",
    "missing_evidence",
    "residual_risk",
    "safe_next_step",
    "citations",
    "requires_human_approval",
)
LIST_KEYS = ("measured_facts", "inference", "missing_evidence", "citations")
STRING_KEYS = ("direct_answer", "residual_risk", "safe_next_step")


@dataclass(frozen=True)
class RagAnswerContract:
    direct_answer: str
    measured_facts: list[str] = field(default_factory=list)
    inference: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    residual_risk: str = ""
    safe_next_step: str = ""
    citations: list[str] = field(default_factory=list)
    requires_human_approval: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        sections = [
            f"Direct answer:\n{self.direct_answer}",
            _format_list("Measured facts", self.measured_facts),
            _format_list("Inference", self.inference),
            _format_list("Missing evidence", self.missing_evidence),
            f"Residual risk:\n{self.residual_risk}",
            f"Safe next step:\n{self.safe_next_step}",
            f"Citations:\n{', '.join(self.citations) if self.citations else 'None'}",
            f"Requires human approval: {str(self.requires_human_approval).lower()}",
        ]
        return "\n\n".join(sections)


@dataclass(frozen=True)
class ContractCheck:
    ok: bool
    structured: RagAnswerContract | None
    violations: list[str]


def build_rag_contract_prompt(base_prompt: str, *, allowed_citations: list[str]) -> str:
    citation_text = ", ".join(allowed_citations) if allowed_citations else "none"
    return (
        f"{base_prompt.strip()}\n\n"
        f"{CONTRACT_MARKER}\n"
        "Return exactly one JSON object and no markdown.\n"
        "Required keys in this exact shape:\n"
        "{\n"
        '  "direct_answer": "short operator-facing answer",\n'
        '  "measured_facts": ["facts directly present in retrieved evidence"],\n'
        '  "inference": ["bounded reasoning from the evidence"],\n'
        '  "missing_evidence": ["thresholds, tolerances, authority, or context not found"],\n'
        '  "residual_risk": "remaining safety, quality, or uptime risk",\n'
        '  "safe_next_step": "one safe next action that respects released SOP/QMS authority",\n'
        '  "citations": ["source ids used"],\n'
        '  "requires_human_approval": true\n'
        "}\n"
        f"Allowed citation ids: {citation_text}.\n"
        "Use only allowed citation ids. If released evidence is incomplete, say what is missing. "
        "Do not invent thresholds, tolerances, part numbers, release authority, or SOP steps."
    )


def build_rag_repair_prompt(
    previous_answer: str,
    *,
    violations: list[str],
    allowed_citations: list[str],
    response_language: str,
) -> str:
    citation_text = ", ".join(allowed_citations) if allowed_citations else "none"
    return (
        f"{CONTRACT_MARKER}\n"
        "The previous answer failed the required output contract. Rewrite it as exactly one JSON object.\n"
        f"Response language: {response_language}\n"
        f"Allowed citation ids: {citation_text}.\n"
        f"Violations: {'; '.join(violations)}\n\n"
        "Required keys:\n"
        f"{', '.join(REQUIRED_KEYS)}\n\n"
        "Rules: list fields must be arrays of strings, string fields must be non-empty, "
        "requires_human_approval must be a boolean, and citations must use only allowed ids.\n\n"
        "Previous answer:\n"
        f"{previous_answer.strip()}"
    )


def check_rag_answer_contract(answer: str, *, allowed_citations: list[str]) -> ContractCheck:
    payload, parse_error = _parse_json_object(answer)
    if payload is None:
        return ContractCheck(ok=False, structured=None, violations=[parse_error])
    if not isinstance(payload, dict):
        return ContractCheck(ok=False, structured=None, violations=["answer must be a JSON object"])

    violations: list[str] = []
    missing = [key for key in REQUIRED_KEYS if key not in payload]
    if missing:
        violations.append(f"missing required key(s): {', '.join(missing)}")

    for key in STRING_KEYS:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            violations.append(f"{key} must be a non-empty string")

    normalized_lists: dict[str, list[str]] = {}
    for key in LIST_KEYS:
        value = payload.get(key)
        if not isinstance(value, list):
            violations.append(f"{key} must be a list")
            normalized_lists[key] = []
            continue
        normalized = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        normalized_lists[key] = normalized
        if len(normalized) != len(value):
            violations.append(f"{key} must contain only non-empty string values")

    requires_human_approval = payload.get("requires_human_approval")
    if not isinstance(requires_human_approval, bool):
        violations.append("requires_human_approval must be a boolean")
        requires_human_approval = True

    allowed = set(allowed_citations)
    unknown_citations = [item for item in normalized_lists.get("citations", []) if item not in allowed]
    if unknown_citations:
        violations.append(f"unknown citation id(s): {', '.join(unknown_citations)}")
    if allowed and not normalized_lists.get("citations"):
        violations.append("citations must include at least one retrieved source id")

    if violations:
        return ContractCheck(ok=False, structured=None, violations=violations)

    return ContractCheck(
        ok=True,
        structured=RagAnswerContract(
            direct_answer=str(payload["direct_answer"]).strip(),
            measured_facts=normalized_lists["measured_facts"],
            inference=normalized_lists["inference"],
            missing_evidence=normalized_lists["missing_evidence"],
            residual_risk=str(payload["residual_risk"]).strip(),
            safe_next_step=str(payload["safe_next_step"]).strip(),
            citations=normalized_lists["citations"],
            requires_human_approval=requires_human_approval,
        ),
        violations=[],
    )


def build_degraded_rag_answer(
    *,
    question: str,
    citations: list[str],
    response_language: str,
    reason: str,
) -> RagAnswerContract:
    if _prefers_chinese(response_language):
        return RagAnswerContract(
            direct_answer=f"当前不能给出最终操作结论，因为证据链不完整：{reason}",
            measured_facts=[],
            inference=[],
            missing_evidence=[
                "需要已发布 SOP、阈值、公差、审批权限或设备上下文后才能形成可执行建议。"
            ],
            residual_risk="如果在证据不足时继续行动，可能影响安全、质量或设备可用性。",
            safe_next_step=f"先将问题升级给责任工程师，并补齐与该问题相关的受控证据：{question}",
            citations=citations,
            requires_human_approval=True,
        )
    return RagAnswerContract(
        direct_answer=f"No final operating conclusion is available because the evidence chain is incomplete: {reason}",
        measured_facts=[],
        inference=[],
        missing_evidence=[
            "Released SOP, thresholds, tolerances, approval authority, or device context is required before action."
        ],
        residual_risk="Acting without complete evidence could affect safety, quality, or equipment uptime.",
        safe_next_step=f"Escalate to the responsible engineer and collect controlled evidence for: {question}",
        citations=citations,
        requires_human_approval=True,
    )


def _parse_json_object(answer: str) -> tuple[Any | None, str]:
    text = answer.strip()
    if text.startswith("```"):
        text = "\n".join(line for line in text.splitlines() if not line.strip().startswith("```")).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None, "answer did not contain a JSON object"
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate), ""
    except json.JSONDecodeError as exc:
        return None, f"answer JSON could not be parsed: {exc.msg}"


def _format_list(title: str, values: list[str]) -> str:
    if not values:
        return f"{title}:\n- None"
    lines = "\n".join(f"- {value}" for value in values)
    return f"{title}:\n{lines}"


def _prefers_chinese(language: str) -> bool:
    normalized = language.lower()
    return any(token in normalized for token in ("chinese", "zh", "中文", "简体", "繁体"))
