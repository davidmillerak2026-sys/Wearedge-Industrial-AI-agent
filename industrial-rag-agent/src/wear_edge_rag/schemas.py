from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


Metadata = dict[str, str | int | float | bool | None]


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    path: str
    title: str
    text: str
    metadata: Metadata = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    source_id: str
    path: str
    title: str
    text: str
    metadata: Metadata = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DocumentChunk":
        return cls(
            chunk_id=str(value["chunk_id"]),
            source_id=str(value["source_id"]),
            path=str(value["path"]),
            title=str(value["title"]),
            text=str(value["text"]),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True)
class RetrievalHit:
    chunk: DocumentChunk
    score: float
    rank: int

    def to_citation(self, label: str) -> dict[str, Any]:
        metadata = dict(self.chunk.metadata)
        return {
            "id": label,
            "title": self.chunk.title,
            "path": self.chunk.path,
            "score": round(self.score, 4),
            "document_id": metadata.get("document_id", self.chunk.source_id),
            "revision": metadata.get("revision", "unversioned"),
            "approval_status": metadata.get("approval_status", "unknown"),
            "effective_date": metadata.get("effective_date", ""),
            "owner": metadata.get("owner", ""),
            "metadata": metadata,
        }


@dataclass(frozen=True)
class AgentAnswer:
    answer: str
    citations: list[dict[str, Any]]
    retrieved: list[RetrievalHit]
    provider: str
    confidence: str
    structured: dict[str, Any] | None = None
    contract: dict[str, Any] = field(default_factory=dict)

