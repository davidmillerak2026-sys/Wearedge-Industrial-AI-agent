from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import (
    RagAnswerContract,
    build_degraded_rag_answer,
    build_rag_contract_prompt,
    build_rag_repair_prompt,
    check_rag_answer_contract,
)
from .llm import LLMClient
from .prompts import render_prompt
from .schemas import AgentAnswer, RetrievalHit
from .tools import KnowledgeToolCatalog, citations_from_hits
from .validators import evaluate_action_gate, evaluate_evidence, estimate_confidence


@dataclass(frozen=True)
class WorkflowStage:
    name: str
    ok: bool
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RAGWorkflow:
    def __init__(
        self,
        *,
        tools: KnowledgeToolCatalog,
        llm: LLMClient,
        prompt_template: str,
        response_language: str,
    ) -> None:
        self.tools = tools
        self.llm = llm
        self.prompt_template = prompt_template
        self.response_language = response_language

    def run(
        self,
        question: str,
        *,
        top_k: int = 5,
        metadata_filter: dict[str, str] | None = None,
    ) -> AgentAnswer:
        stages: list[WorkflowStage] = []
        search_result = self.tools.search_knowledge(
            question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        stages.append(
            WorkflowStage(
                name="search_knowledge",
                ok=search_result.ok,
                detail=search_result.error or "search completed",
                metadata=search_result.as_dict(),
            )
        )
        if not search_result.ok:
            return self._degraded_answer(
                question=question,
                hits=[],
                citations=[],
                stages=stages,
                reason=f"knowledge search failed: {search_result.error}",
                repaired=False,
                violations=[],
            )

        hits = list(search_result.data or [])
        citations = citations_from_hits(hits)
        citation_ids = [str(citation["id"]) for citation in citations]
        evidence_gate = evaluate_evidence(hits, citations)
        stages.append(
            WorkflowStage(
                name="evidence_gate",
                ok=evidence_gate.ok,
                detail=evidence_gate.reason,
                metadata=evidence_gate.as_dict(),
            )
        )
        if not evidence_gate.ok:
            return self._degraded_answer(
                question=question,
                hits=hits,
                citations=citations,
                stages=stages,
                reason=evidence_gate.reason,
                repaired=False,
                violations=[],
            )

        context = format_context(hits)
        base_prompt = render_prompt(
            self.prompt_template,
            question=question,
            context=context,
            response_language=self.response_language,
        )
        prompt = build_rag_contract_prompt(base_prompt, allowed_citations=citation_ids)
        try:
            answer = self.llm.generate(prompt).strip()
        except Exception as exc:
            stages.append(
                WorkflowStage(
                    name="model_draft",
                    ok=False,
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )
            return self._degraded_answer(
                question=question,
                hits=hits,
                citations=citations,
                stages=stages,
                reason="model draft failed",
                repaired=False,
                violations=[f"{type(exc).__name__}: {exc}"],
            )

        stages.append(
            WorkflowStage(
                name="model_draft",
                ok=True,
                detail="model returned draft",
                metadata={"provider": self.llm.provider, "answer_chars": len(answer)},
            )
        )
        contract = check_rag_answer_contract(answer, allowed_citations=citation_ids)
        stages.append(
            WorkflowStage(
                name="validate_contract",
                ok=contract.ok,
                detail="contract passed" if contract.ok else "contract failed",
                metadata={"violations": list(contract.violations)},
            )
        )

        repaired = False
        violations = list(contract.violations)
        if not contract.ok:
            repaired = True
            repair_prompt = build_rag_repair_prompt(
                answer,
                violations=contract.violations,
                allowed_citations=citation_ids,
                response_language=self.response_language,
            )
            try:
                repair_answer = self.llm.generate(repair_prompt).strip()
            except Exception as exc:
                stages.append(
                    WorkflowStage(
                        name="repair_once",
                        ok=False,
                        detail=f"{type(exc).__name__}: {exc}",
                    )
                )
                violations.append(f"{type(exc).__name__}: {exc}")
                return self._degraded_answer(
                    question=question,
                    hits=hits,
                    citations=citations,
                    stages=stages,
                    reason="model output failed the RAG answer contract",
                    repaired=True,
                    violations=violations,
                )

            contract = check_rag_answer_contract(repair_answer, allowed_citations=citation_ids)
            answer = repair_answer
            violations = list(contract.violations)
            stages.append(
                WorkflowStage(
                    name="repair_once",
                    ok=contract.ok,
                    detail="repair passed" if contract.ok else "repair failed",
                    metadata={"violations": violations, "answer_chars": len(answer)},
                )
            )

        if contract.ok and contract.structured is not None:
            return self._structured_answer(
                structured=contract.structured,
                hits=hits,
                citations=citations,
                stages=stages,
                repaired=repaired,
                evidence_gate=evidence_gate.as_dict(),
            )

        return self._degraded_answer(
            question=question,
            hits=hits,
            citations=citations,
            stages=stages,
            reason="model output failed the RAG answer contract",
            repaired=repaired,
            violations=violations,
        )

    def _structured_answer(
        self,
        *,
        structured: RagAnswerContract,
        hits: list[RetrievalHit],
        citations: list[dict[str, Any]],
        stages: list[WorkflowStage],
        repaired: bool,
        evidence_gate: dict[str, Any],
    ) -> AgentAnswer:
        action_gate = evaluate_action_gate(structured)
        stages.append(
            WorkflowStage(
                name="action_gate",
                ok=action_gate.ok,
                detail=action_gate.status,
                metadata=action_gate.as_dict(),
            )
        )
        return AgentAnswer(
            answer=structured.as_text(),
            citations=citations,
            retrieved=hits,
            provider=self.llm.provider,
            confidence=estimate_confidence(hits),
            structured=structured.as_dict(),
            contract={
                "ok": True,
                "mode": "structured",
                "repaired": repaired,
                "violations": [],
                "evidence_gate": evidence_gate,
                "action_gate": action_gate.as_dict(),
                "stages": [stage.as_dict() for stage in stages],
            },
        )

    def _degraded_answer(
        self,
        *,
        question: str,
        hits: list[RetrievalHit],
        citations: list[dict[str, Any]],
        stages: list[WorkflowStage],
        reason: str,
        repaired: bool,
        violations: list[str],
    ) -> AgentAnswer:
        citation_ids = [str(citation["id"]) for citation in citations]
        degraded = build_degraded_rag_answer(
            question=question,
            citations=citation_ids,
            response_language=self.response_language,
            reason=reason,
        )
        action_gate = evaluate_action_gate(degraded)
        stages.append(
            WorkflowStage(
                name="action_gate",
                ok=action_gate.ok,
                detail=action_gate.status,
                metadata=action_gate.as_dict(),
            )
        )
        return AgentAnswer(
            answer=degraded.as_text(),
            citations=citations,
            retrieved=hits,
            provider=self.llm.provider,
            confidence=estimate_confidence(hits),
            structured=degraded.as_dict(),
            contract={
                "ok": True,
                "mode": "degraded",
                "repaired": repaired,
                "violations": violations,
                "reason": reason,
                "action_gate": action_gate.as_dict(),
                "stages": [stage.as_dict() for stage in stages],
            },
        )


def format_context(hits: list[RetrievalHit]) -> str:
    if not hits:
        return "No evidence retrieved."
    sections: list[str] = []
    for idx, hit in enumerate(hits, start=1):
        metadata = ", ".join(f"{key}={value}" for key, value in hit.chunk.metadata.items())
        sections.append(
            f"[S{idx}] {hit.chunk.title}\n"
            f"Path: {hit.chunk.path}\n"
            f"Score: {hit.score:.4f}\n"
            f"Metadata: {metadata}\n"
            f"Text: {hit.chunk.text}"
        )
    return "\n\n---\n\n".join(sections)
