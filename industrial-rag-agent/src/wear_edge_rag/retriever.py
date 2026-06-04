from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from .schemas import DocumentChunk, RetrievalHit


INDEX_FILE = "sparse_index.json"


class SparseTfidfIndex:
    def __init__(self, chunks: list[DocumentChunk] | None = None) -> None:
        self.chunks: list[DocumentChunk] = []
        self._idf: dict[str, float] = {}
        self._doc_vectors: list[dict[str, float]] = []
        self._doc_norms: list[float] = []
        if chunks:
            self.build(chunks)

    def build(self, chunks: list[DocumentChunk]) -> "SparseTfidfIndex":
        self.chunks = list(chunks)
        tokenized = [tokenize(chunk.text) for chunk in self.chunks]
        doc_freq: Counter[str] = Counter()
        for tokens in tokenized:
            doc_freq.update(set(tokens))

        doc_count = max(1, len(self.chunks))
        self._idf = {
            token: math.log((doc_count + 1) / (freq + 1)) + 1.0
            for token, freq in doc_freq.items()
        }
        self._doc_vectors = [self._vectorize(tokens) for tokens in tokenized]
        self._doc_norms = [vector_norm(vector) for vector in self._doc_vectors]
        return self

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        metadata_filter: dict[str, str] | None = None,
    ) -> list[RetrievalHit]:
        query_vector = self._vectorize(tokenize(query))
        query_norm = vector_norm(query_vector)
        if query_norm == 0:
            return []

        scored: list[tuple[float, int]] = []
        for idx, chunk in enumerate(self.chunks):
            if metadata_filter and not metadata_matches(chunk, metadata_filter):
                continue
            denom = query_norm * self._doc_norms[idx]
            if denom == 0:
                continue
            score = dot(query_vector, self._doc_vectors[idx]) / denom
            if score > 0:
                scored.append((score, idx))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievalHit(chunk=self.chunks[idx], score=score, rank=rank)
            for rank, (score, idx) in enumerate(scored[:top_k], start=1)
        ]

    def save(self, index_dir: str | Path) -> Path:
        path = Path(index_dir)
        path.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "backend": "sparse_tfidf",
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }
        index_file = path / INDEX_FILE
        index_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return index_file

    @classmethod
    def load(cls, index_dir: str | Path) -> "SparseTfidfIndex":
        index_file = Path(index_dir) / INDEX_FILE
        payload = json.loads(index_file.read_text(encoding="utf-8"))
        chunks = [DocumentChunk.from_dict(item) for item in payload["chunks"]]
        return cls(chunks)

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        vector: dict[str, float] = {}
        for token, count in counts.items():
            idf = self._idf.get(token)
            if idf is None:
                continue
            vector[token] = (1.0 + math.log(count)) * idf
        return vector


def tokenize(text: str) -> list[str]:
    lower = text.lower()
    latin_tokens = re.findall(r"[a-z0-9][a-z0-9_./:-]*", lower)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", lower)
    cjk_bigrams = [a + b for a, b in zip(cjk_chars, cjk_chars[1:])]
    return latin_tokens + cjk_chars + cjk_bigrams


def metadata_matches(chunk: DocumentChunk, metadata_filter: dict[str, str]) -> bool:
    for key, expected in metadata_filter.items():
        actual = chunk.metadata.get(key)
        if actual is None or str(actual) != expected:
            return False
    return True


def dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(weight * right.get(token, 0.0) for token, weight in left.items())


def vector_norm(vector: dict[str, float]) -> float:
    return math.sqrt(sum(value * value for value in vector.values()))

