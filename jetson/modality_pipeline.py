from __future__ import annotations

from dataclasses import dataclass


VISUAL_TOKEN_BUDGETS = (70, 140, 280, 560, 1120)
MAX_GEMMA4_AUDIO_SECONDS = 30


@dataclass(frozen=True)
class VisualTokenBudget:
    min_tokens: int
    max_tokens: int
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "min_tokens": self.min_tokens,
            "max_tokens": self.max_tokens,
            "reason": self.reason,
        }

    def as_llama_env(self) -> dict[str, str]:
        return {
            "LLAMA_IMAGE_MIN_TOKENS": str(self.min_tokens),
            "LLAMA_IMAGE_MAX_TOKENS": str(self.max_tokens),
        }


@dataclass(frozen=True)
class AudioFusionPlan:
    enabled: bool
    runtime: str
    model_variant: str
    max_audio_seconds: int
    route: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "runtime": self.runtime,
            "model_variant": self.model_variant,
            "max_audio_seconds": self.max_audio_seconds,
            "route": self.route,
            "reason": self.reason,
        }


def build_modality_plan(
    *,
    analysis_mode: str,
    image_bytes: int,
    current_image_min_tokens: int,
    current_image_max_tokens: int,
    audio_runtime: str,
    model_variant: str,
    audio_seconds: int = 0,
    needs_ocr: bool = False,
    high_detail: bool = False,
) -> dict[str, object]:
    visual_budget = choose_visual_token_budget(
        analysis_mode=analysis_mode,
        image_bytes=image_bytes,
        needs_ocr=needs_ocr,
        high_detail=high_detail,
    )
    audio_fusion = plan_audio_fusion(
        runtime=audio_runtime,
        model_variant=model_variant,
        audio_seconds=audio_seconds,
    )
    visual_status = (
        "matched"
        if visual_budget.min_tokens == current_image_min_tokens and visual_budget.max_tokens == current_image_max_tokens
        else "requires_server_restart"
    )
    return {
        "visual_token_budget": {
            "recommended": visual_budget.as_dict(),
            "current_runtime": {
                "min_tokens": current_image_min_tokens,
                "max_tokens": current_image_max_tokens,
            },
            "status": visual_status,
            "llama_env": visual_budget.as_llama_env(),
        },
        "audio_fusion": audio_fusion.as_dict(),
    }


def choose_visual_token_budget(
    *,
    analysis_mode: str,
    image_bytes: int,
    needs_ocr: bool = False,
    high_detail: bool = False,
) -> VisualTokenBudget:
    """Visual Token Dynamic Allocation module.

    The runtime launcher consumes the returned budget through
    LLAMA_IMAGE_MIN_TOKENS and LLAMA_IMAGE_MAX_TOKENS.
    """
    mode = analysis_mode.strip().lower().replace("-", "_")
    budget = _base_visual_budget(mode)
    reason = f"{mode or 'hazard'} baseline"

    if image_bytes >= 3 * 1024 * 1024:
        budget = max(budget, 140)
        reason = "large frame keeps more visual evidence"
    if high_detail:
        budget = max(budget, 280)
        reason = "high-detail inspection"
    if needs_ocr:
        budget = max(budget, 560)
        reason = "OCR or small-text reading"

    return VisualTokenBudget(min_tokens=budget, max_tokens=budget, reason=reason)


def plan_audio_fusion(
    *,
    runtime: str,
    model_variant: str,
    audio_seconds: int,
) -> AudioFusionPlan:
    """Audio Fusion module.

    Current WearEdge PoC keeps llama.cpp on image+text. Native audio should
    route through vLLM/NIM when the selected Gemma 4 variant and device allow it.
    """
    runtime_key = runtime.strip().lower()
    variant = model_variant.strip().upper()
    supports_audio = variant in {"E2B", "E4B"}

    if not supports_audio:
        return AudioFusionPlan(
            enabled=False,
            runtime=runtime_key,
            model_variant=variant,
            max_audio_seconds=MAX_GEMMA4_AUDIO_SECONDS,
            route="disabled",
            reason="selected Gemma 4 variant does not expose the small-model audio path",
        )
    if audio_seconds > MAX_GEMMA4_AUDIO_SECONDS:
        return AudioFusionPlan(
            enabled=False,
            runtime=runtime_key,
            model_variant=variant,
            max_audio_seconds=MAX_GEMMA4_AUDIO_SECONDS,
            route="reject_or_chunk",
            reason="audio clip exceeds Gemma 4 small-model single-clip limit",
        )
    if runtime_key == "llama.cpp" and variant == "E2B":
        return AudioFusionPlan(
            enabled=False,
            runtime=runtime_key,
            model_variant=variant,
            max_audio_seconds=MAX_GEMMA4_AUDIO_SECONDS,
            route="vllm_or_nim",
            reason="E2B audio is intentionally kept out of the current llama.cpp Orin Nano path",
        )
    return AudioFusionPlan(
        enabled=runtime_key in {"vllm", "nim"},
        runtime=runtime_key,
        model_variant=variant,
        max_audio_seconds=MAX_GEMMA4_AUDIO_SECONDS,
        route="native_multimodal_request",
        reason="route audio with image/text through the Gemma 4 small-model multimodal stack",
    )


def _base_visual_budget(mode: str) -> int:
    budgets = {
        "hazard": 70,
        "maintenance": 140,
        "iqc": 280,
        "wi": 280,
        "changeover": 280,
    }
    return budgets.get(mode, 70)
