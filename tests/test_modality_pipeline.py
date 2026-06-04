from __future__ import annotations

from jetson.modality_pipeline import build_modality_plan, choose_visual_token_budget, plan_audio_fusion


def test_visual_token_budget_keeps_hazard_lightweight() -> None:
    budget = choose_visual_token_budget(analysis_mode="hazard", image_bytes=800_000)

    assert budget.min_tokens == 70
    assert budget.max_tokens == 70
    assert budget.as_llama_env()["LLAMA_IMAGE_MAX_TOKENS"] == "70"


def test_visual_token_budget_raises_for_quality_and_ocr() -> None:
    quality = choose_visual_token_budget(analysis_mode="iqc", image_bytes=900_000)
    ocr = choose_visual_token_budget(analysis_mode="wi", image_bytes=900_000, needs_ocr=True)

    assert quality.max_tokens == 280
    assert ocr.max_tokens == 560


def test_audio_fusion_keeps_e2b_llama_cpp_disabled() -> None:
    plan = plan_audio_fusion(runtime="llama.cpp", model_variant="E2B", audio_seconds=12)

    assert not plan.enabled
    assert plan.route == "vllm_or_nim"


def test_audio_fusion_allows_vllm_small_model_audio() -> None:
    plan = plan_audio_fusion(runtime="vLLM", model_variant="E4B", audio_seconds=12)

    assert plan.enabled
    assert plan.route == "native_multimodal_request"


def test_modality_plan_marks_runtime_budget_match() -> None:
    plan = build_modality_plan(
        analysis_mode="hazard",
        image_bytes=800_000,
        current_image_min_tokens=70,
        current_image_max_tokens=70,
        audio_runtime="llama.cpp",
        model_variant="E2B",
    )

    assert plan["visual_token_budget"]["status"] == "matched"
    assert plan["visual_token_budget"]["recommended"]["max_tokens"] == 70
    assert plan["audio_fusion"]["route"] == "vllm_or_nim"


def test_modality_plan_flags_server_restart_when_iqc_needs_more_tokens() -> None:
    plan = build_modality_plan(
        analysis_mode="iqc",
        image_bytes=900_000,
        current_image_min_tokens=70,
        current_image_max_tokens=70,
        audio_runtime="vllm",
        model_variant="E4B",
        audio_seconds=12,
    )

    assert plan["visual_token_budget"]["status"] == "requires_server_restart"
    assert plan["visual_token_budget"]["recommended"]["max_tokens"] == 280
    assert plan["audio_fusion"]["enabled"] is True
