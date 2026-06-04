from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

from .schemas import DocumentChunk, SourceDocument


SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".json", ".csv", ".log"}


def discover_files(paths: Iterable[str | Path]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(candidate)
        elif path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return sorted(files)


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def load_document(path: Path) -> SourceDocument:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        text = _read_csv_as_text(path)
        source_type = "table"
    elif suffix == ".json":
        text = json.dumps(json.loads(read_text_file(path)), ensure_ascii=False, indent=2)
        source_type = "json"
    else:
        text = read_text_file(path)
        source_type = "text"

    source_id = stable_id(str(path.resolve()))
    return SourceDocument(
        source_id=source_id,
        path=str(path),
        title=path.name,
        text=text.strip(),
        metadata={
            "source_type": source_type,
            "extension": suffix,
            "document_id": source_id,
            "revision": "unversioned",
            "approval_status": "unknown",
            "effective_date": "",
            "owner": "",
            "plant": "",
            "line": "",
            "station": "",
            "equipment_id": "",
        },
    )


def load_documents(paths: Iterable[str | Path]) -> list[SourceDocument]:
    return [load_document(path) for path in discover_files(paths)]


def chunk_documents(
    documents: Iterable[SourceDocument],
    *,
    max_chars: int = 1200,
    overlap: int = 180,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        for index, text in enumerate(split_text(document.text, max_chars=max_chars, overlap=overlap)):
            chunk_id = f"{document.source_id}:{index:04d}"
            metadata = dict(document.metadata)
            metadata["chunk_index"] = index
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    source_id=document.source_id,
                    path=document.path,
                    title=document.title,
                    text=text,
                    metadata=metadata,
                )
            )
    return chunks


def split_text(text: str, *, max_chars: int, overlap: int) -> list[str]:
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not normalized:
        return []

    paragraphs = [part.strip() for part in normalized.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_sliding_windows(paragraph, max_chars=max_chars, overlap=overlap))
            continue

        proposed = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(proposed) <= max_chars:
            current = proposed
        else:
            chunks.append(current.strip())
            current = paragraph

    if current:
        chunks.append(current.strip())

    return chunks


def stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def _sliding_windows(text: str, *, max_chars: int, overlap: int) -> list[str]:
    windows: list[str] = []
    start = 0
    step = max(1, max_chars - overlap)
    while start < len(text):
        windows.append(text[start : start + max_chars].strip())
        start += step
    return [window for window in windows if window]


def _read_csv_as_text(path: Path) -> str:
    raw = read_text_file(path)
    rows = list(csv.DictReader(raw.splitlines()))
    if rows:
        lines = []
        for idx, row in enumerate(rows, start=1):
            fields = "; ".join(f"{key}={value}" for key, value in row.items())
            lines.append(f"row {idx}: {fields}")
        return "\n".join(lines)
    return raw

