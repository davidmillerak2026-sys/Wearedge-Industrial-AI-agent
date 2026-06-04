from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class LlamaServerError(RuntimeError):
    """Raised when llama-server rejects or fails a request."""


@dataclass(frozen=True)
class LlamaResponse:
    answer: str
    raw: dict[str, Any]
    latency_ms: int


def build_multimodal_payload(
    *,
    prompt: str,
    image_bytes: bytes,
    image_content_type: str,
    model: str,
    enable_thinking: bool,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{image_content_type};base64,{encoded}"},
                    },
                ],
            }
        ],
        "chat_template_kwargs": {"enable_thinking": enable_thinking},
        "max_tokens": max_tokens,
        "temperature": temperature,
    }


def post_chat_completion(
    *,
    base_url: str,
    payload: dict[str, Any],
    timeout_seconds: int,
) -> LlamaResponse:
    started = time.perf_counter()
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LlamaServerError(f"llama-server returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LlamaServerError(f"llama-server request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LlamaServerError("llama-server returned invalid JSON") from exc

    latency_ms = int((time.perf_counter() - started) * 1000)
    try:
        answer = str(raw["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise LlamaServerError("llama-server response did not include choices[0].message.content") from exc
    return LlamaResponse(answer=answer, raw=raw, latency_ms=latency_ms)
