from __future__ import annotations

from jetson.released_source import (
    RELEASED_SOURCE_EVALUATION_VERSION,
    RELEASED_SOURCE_VERSION,
    build_released_source_prompt_context,
    evaluate_released_source_condition,
    retrieve_released_source_context,
)


def test_released_wi_source_retrieves_machine_specific_revision() -> None:
    result = retrieve_released_source_context(
        mode="wi",
        query_text="Cartoner station two has an infeed guide question near the guard door.",
    )
    prompt_context = build_released_source_prompt_context(result)

    as_dict = result.as_dict()

    assert as_dict["version"] == RELEASED_SOURCE_VERSION
    assert as_dict["status"] == "matched"
    assert as_dict["source_id"] == "WI-CARTONER-ST2"
    assert as_dict["machine_id"] == "CARTONER-ST2"
    assert as_dict["hits"]
    assert "Released WI source context" in prompt_context


def test_released_changeover_source_requires_target_sku_match() -> None:
    result = retrieve_released_source_context(
        mode="changeover",
        query_text="Filling line station one labeler changeover for target SKU-C500 and C500 label roll.",
    )

    as_dict = result.as_dict()

    assert as_dict["status"] == "matched"
    assert as_dict["source_id"] == "CO-LABELER-FL1-SKU-C500"
    assert as_dict["machine_id"] == "LABELER-FL1"
    assert as_dict["sku_id"] == "SKU-C500"
    assert any(hit["section_id"] == "CO-C500-FIRST-PIECE" for hit in as_dict["hits"])


def test_released_source_no_match_blocks_trusted_guidance() -> None:
    source = retrieve_released_source_context(
        mode="changeover",
        query_text="Labeler changeover for unreadable target SKU.",
    ).as_dict()
    evaluation = evaluate_released_source_condition(
        mode="changeover",
        fields={
            "machine": "Filling line station one labeler with guide rails visible.",
            "sku": "Target SKU is unreadable.",
            "changeover_step": "Set the guide rails and prepare restart.",
            "verification": "Restart after visual check.",
            "action": "Set guides and restart after operator confirmation.",
        },
        knowledge_base=source,
    )

    assert evaluation is not None
    as_dict = evaluation.as_dict()

    assert as_dict["version"] == RELEASED_SOURCE_EVALUATION_VERSION
    assert as_dict["status"] == "blocked_completion_claim"
    assert as_dict["recommended_channel"] == "changeover_source_required"
    assert as_dict["requires_human"] is True
    assert "released changeover checklist" in as_dict["missing_inputs"]


def test_released_source_matched_allows_wi_guided_operation() -> None:
    source = retrieve_released_source_context(
        mode="wi",
        query_text="Cartoner station 2 operator asks about product guide alignment.",
    ).as_dict()
    evaluation = evaluate_released_source_condition(
        mode="wi",
        fields={
            "machine": "CARTONER-ST2 cartoner station two.",
            "work_instruction": "Follow the released guide alignment instruction for the infeed rails.",
            "risk_control": "Keep guards closed and escalate repeated jams.",
            "action": "Follow the released guide marks while keeping guards closed.",
        },
        knowledge_base=source,
    )

    assert evaluation is not None
    assert evaluation.status == "released_source_matched"
    assert evaluation.recommended_channel == "guided_operation"
    assert evaluation.requires_human is False
