from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .retriever import SparseTfidfIndex
from .schemas import RetrievalHit


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    ok: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if isinstance(self.data, list):
            payload["data_count"] = len(self.data)
            payload.pop("data", None)
        return payload


class KnowledgeToolCatalog:
    def __init__(self, retriever: SparseTfidfIndex) -> None:
        self.retriever = retriever

    def search_knowledge(
        self,
        question: str,
        *,
        top_k: int,
        metadata_filter: dict[str, str] | None = None,
    ) -> ToolResult:
        try:
            hits = self.retriever.search(question, top_k=top_k, metadata_filter=metadata_filter)
        except Exception as exc:  # pragma: no cover - defensive envelope for future tools.
            return ToolResult(
                tool_name="search_knowledge",
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                metadata={"top_k": top_k, "metadata_filter": metadata_filter or {}},
            )
        return ToolResult(
            tool_name="search_knowledge",
            ok=True,
            data=hits,
            metadata={
                "top_k": top_k,
                "metadata_filter": metadata_filter or {},
                "result_count": len(hits),
            },
        )


def citations_from_hits(hits: list[RetrievalHit]) -> list[dict[str, Any]]:
    return [hit.to_citation(f"S{idx}") for idx, hit in enumerate(hits, start=1)]
