from __future__ import annotations

from pathlib import Path


DEFAULT_PROMPT = """You are WearEdge Pro's industrial RAG assistant.

Use only the retrieved evidence. Cite source ids like [S1]. If evidence is missing, say what is missing and give a safe next step.

Response language: {response_language}

Question:
{question}

Retrieved evidence:
{context}
"""


def load_prompt_template(path: str | Path | None) -> str:
    if path is None:
        return DEFAULT_PROMPT
    prompt_path = Path(path)
    if not prompt_path.exists():
        return DEFAULT_PROMPT
    return prompt_path.read_text(encoding="utf-8")


def render_prompt(
    template: str,
    *,
    question: str,
    context: str,
    response_language: str = "English",
) -> str:
    return template.format(
        question=question,
        context=context,
        response_language=response_language,
    )

