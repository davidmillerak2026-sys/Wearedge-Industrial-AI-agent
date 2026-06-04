from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class LLMClient(Protocol):
    provider: str

    def generate(self, prompt: str) -> str:
        ...


@dataclass
class ExtractiveLLM:
    provider: str = "extractive"

    def generate(self, prompt: str) -> str:
        context_marker = "Retrieved evidence:"
        question_marker = "Question:"
        response_language = _response_language(prompt)
        question = _between(prompt, question_marker, context_marker).strip()
        context = prompt.split(context_marker, 1)[-1].strip()
        evidence = "\n\n".join(extract_evidence_snippets(context, limit=3))
        if "RAG_ANSWER_CONTRACT_V1" in prompt:
            return _contract_response(
                question=question,
                context=context,
                evidence=evidence,
                response_language=response_language,
            )
        if _prefers_chinese(response_language):
            if not evidence:
                evidence = "未检索到强相关证据。"
            return (
                f"回答:\n"
                f"请基于以下检索证据处理：{question or '现场问题'}\n"
                f"最终动作应以已发布的 SOP/QMS 权限为准。\n\n"
                f"证据:\n{evidence}\n\n"
                f"残余风险:\n如果证据没有包含已发布的阈值、公差或审批权限，请先升级给责任工程师再行动。"
            )

        if not evidence:
            evidence = "No strong retrieved evidence was available."
        return (
            f"Answer:\n"
            f"Use the retrieved evidence below for: {question or 'the operator question'}. "
            f"Follow released SOP/QMS authority for the final action.\n\n"
            f"Evidence:\n{evidence}\n\n"
            f"Residual risk:\nIf the evidence does not include a released threshold, tolerance, or approval authority, escalate to the responsible engineer before acting."
        )


@dataclass
class OllamaLLM:
    model: str
    base_url: str = "http://localhost:11434"
    provider: str = "ollama"
    timeout_seconds: int = 120

    def generate(self, prompt: str) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        response = post_json(f"{self.base_url.rstrip('/')}/api/generate", payload, timeout=self.timeout_seconds)
        return str(response.get("response", "")).strip()


@dataclass
class OpenAICompatibleLLM:
    model: str
    base_url: str
    api_key: str
    provider: str = "openai-compatible"
    timeout_seconds: int = 120

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a careful industrial RAG assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        response = post_json(url, payload, headers=headers, timeout=self.timeout_seconds)
        choices = response.get("choices", [])
        if not choices:
            return ""
        return str(choices[0]["message"]["content"]).strip()


def create_llm(provider: str, *, model: str | None = None) -> LLMClient:
    normalized = provider.lower().strip()
    if normalized == "extractive":
        return ExtractiveLLM()
    if normalized == "ollama":
        return OllamaLLM(
            model=model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    if normalized in {"openai-compatible", "openai_compatible"}:
        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY", "")
        if not base_url:
            raise ValueError("OPENAI_COMPATIBLE_BASE_URL is required for openai-compatible provider.")
        return OpenAICompatibleLLM(model=model or "local-model", base_url=base_url, api_key=api_key)
    raise ValueError(f"Unknown provider: {provider}")


def post_json(
    url: str,
    payload: dict,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    request_headers.update(headers or {})
    request = urllib.request.Request(url, data=data, headers=request_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM provider request failed: {exc}") from exc


def _between(text: str, start_marker: str, end_marker: str) -> str:
    if start_marker not in text:
        return ""
    after_start = text.split(start_marker, 1)[1]
    if end_marker in after_start:
        return after_start.split(end_marker, 1)[0]
    return after_start


def _response_language(prompt: str) -> str:
    marker = "Response language:"
    if marker not in prompt:
        return "English"
    return prompt.split(marker, 1)[1].splitlines()[0].strip() or "English"


def _prefers_chinese(language: str) -> bool:
    normalized = language.lower()
    return any(token in normalized for token in ("chinese", "zh", "中文", "简体", "繁体"))


def extract_evidence_snippets(context: str, *, limit: int) -> list[str]:
    snippets: list[str] = []
    for section in context.split("---"):
        stripped = section.strip()
        if not stripped.startswith("[S"):
            continue
        header = stripped.splitlines()[0].strip()
        text = stripped.split("Text:", 1)[-1].strip() if "Text:" in stripped else stripped
        compact = " ".join(text.split())
        snippets.append(f"{header}\n{compact[:700]}")
        if len(snippets) >= limit:
            break
    return snippets


def _contract_response(
    *,
    question: str,
    context: str,
    evidence: str,
    response_language: str,
) -> str:
    citations = _citation_ids(context)
    if _prefers_chinese(response_language):
        payload = {
            "direct_answer": f"请基于检索证据处理：{question or '现场问题'}，最终动作以已发布 SOP/QMS 权限为准。",
            "measured_facts": [evidence] if evidence else [],
            "inference": ["检索证据可作为现场判断的依据，但不能替代已发布规则或责任工程师审批。"],
            "missing_evidence": ["若证据未包含阈值、公差、审批权限或设备上下文，需要先补齐。"],
            "residual_risk": "如果证据链不完整，直接行动可能影响安全、质量或设备可用性。",
            "safe_next_step": "先按已发布 SOP/QMS 执行安全处置，并将缺失证据升级给责任工程师确认。",
            "citations": citations,
            "requires_human_approval": True,
        }
        return json.dumps(payload, ensure_ascii=False)

    payload = {
        "direct_answer": f"Use the retrieved evidence for: {question or 'the operator question'}, and keep final action under released SOP/QMS authority.",
        "measured_facts": [evidence] if evidence else [],
        "inference": ["The retrieved evidence can support operator guidance, but it does not replace released rules or responsible engineering approval."],
        "missing_evidence": ["Confirm released thresholds, tolerances, approval authority, and device context when they are not present in evidence."],
        "residual_risk": "If the evidence chain is incomplete, direct action could affect safety, quality, or equipment uptime.",
        "safe_next_step": "Follow the released SOP/QMS-safe path and escalate missing evidence to the responsible engineer.",
        "citations": citations,
        "requires_human_approval": True,
    }
    return json.dumps(payload)


def _citation_ids(context: str) -> list[str]:
    seen: list[str] = []
    for match in re.finditer(r"^\[(S\d+)\]", context, flags=re.MULTILINE):
        label = match.group(1)
        if label not in seen:
            seen.append(label)
    return seen
