from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import RagAnswerContract
from .schemas import RetrievalHit


@dataclass(frozen=True)
class EvidenceGateResult:
    ok: bool
    reason: str
    warnings: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionGateResult:
    ok: bool
    status: str
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_evidence(hits: list[RetrievalHit], citations: list[dict[str, Any]]) -> EvidenceGateResult:
    if not hits:
        return EvidenceGateResult(
            ok=False,
            reason="no retrieved evidence matched the question",
            missing_evidence=["retrieved knowledge evidence"],
            metadata={"result_count": 0},
        )

    warnings: list[str] = []
    approval_statuses = {str(citation.get("approval_status", "unknown")) for citation in citations}
    if "released" not in approval_statuses:
        warnings.append("no retrieved citation is marked approval_status=released")
    if any(str(citation.get("revision", "unversioned")) == "unversioned" for citation in citations):
        warnings.append("one or more retrieved citations are missing controlled revision metadata")

    return EvidenceGateResult(
        ok=True,
        reason="retrieved evidence available",
        warnings=warnings,
        missing_evidence=[],
        metadata={
            "result_count": len(hits),
            "best_score": round(hits[0].score, 4),
            "approval_statuses": sorted(approval_statuses),
        },
    )


def evaluate_action_gate(answer: RagAnswerContract) -> ActionGateResult:
    if answer.requires_human_approval:
        return ActionGateResult(
            ok=True,
            status="requires_human_approval",
            reason="model output requires human approval before operational state changes",
        )
    return ActionGateResult(
        ok=True,
        status="advisory_only",
        reason="answer is advisory and does not request a production write",
    )


def estimate_confidence(hits: list[RetrievalHit]) -> str:
    if not hits:
        return "low"
    best = hits[0].score
    if best >= 0.35:
        return "high"
    if best >= 0.18:
        return "medium"
    return "low"
