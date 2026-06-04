from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS: dict[str, Any] = {
    "index_dir": ".rag_index",
    "chunk_size": 1200,
    "chunk_overlap": 180,
    "top_k": 5,
    "provider": "extractive",
    "model": None,
    "response_language": "English",
    "prompt_path": "prompts/industrial_rag_answer.md",
}


def load_settings(path: str | Path | None = None) -> dict[str, Any]:
    settings = dict(DEFAULT_SETTINGS)
    if path:
        raw = Path(path).read_text(encoding="utf-8")
        loaded = json.loads(expand_env_placeholders(raw))
        settings.update(loaded)
    return settings


def expand_env_placeholders(text: str) -> str:
    pattern = re.compile(r"\$\{ENV\.([A-Z0-9_]+)\}")

    def replace(match: re.Match[str]) -> str:
        return os.getenv(match.group(1), "")

    return pattern.sub(replace, text)

