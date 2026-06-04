from __future__ import annotations

from jetson.iqc_quality_plan import (
    IQC_QUALITY_PLAN_VERSION,
    build_iqc_quality_plan_prompt_context,
    retrieve_iqc_quality_plan_context,
)


def test_iqc_quality_plan_retrieves_product_specific_rules() -> None:
    result = retrieve_iqc_quality_plan_context(
        query_text=(
            "M400 sees AL-HOUSING-L3 machined aluminum housing with burrs, sealing face marks, "
            "and possible contamination near the station output."
        )
    )

    as_dict = result.as_dict()
    section_ids = {hit["section_id"] for hit in as_dict["hits"]}
    prompt_context = build_iqc_quality_plan_prompt_context(result)

    assert as_dict["version"] == IQC_QUALITY_PLAN_VERSION
    assert as_dict["status"] == "matched"
    assert as_dict["query_product_id"] == "AL-HOUSING-L3"
    assert as_dict["detector"]["required_for_pass"] is True
    assert as_dict["detector"]["minimum_confidence"] == 0.62
    assert "ALH-BURR-01" in section_ids
    assert "ALH-SEAL-02" in section_ids
    assert "IQC quality-plan context" in prompt_context
    assert "required_for_pass=true" in prompt_context
    assert "quality authority" in prompt_context


def test_iqc_quality_plan_no_match_blocks_quality_plan_claims() -> None:
    result = retrieve_iqc_quality_plan_context(query_text="unknown product with a possible visual defect")
    prompt_context = build_iqc_quality_plan_prompt_context(result)

    assert result.status == "no_match"
    assert result.hits == ()
    assert result.as_dict()["defect_rules"] == []
    assert "Do not claim released tolerance" in prompt_context
