from __future__ import annotations

from jetson.maintenance_kb import (
    MAINTENANCE_KB_VERSION,
    build_maintenance_kb_prompt_context,
    retrieve_maintenance_kb_context,
)


def test_maintenance_kb_retrieves_asset_specific_predictive_sections() -> None:
    result = retrieve_maintenance_kb_context(
        query_text=(
            "PKG-L3-GBX-03 has yellow PLC alarm GBX-VIB-HI, vibration RMS 7.2 mm/s, "
            "gearbox temperature 78 C, oil smell, and operator reports abnormal rumble."
        )
    )

    as_dict = result.as_dict()
    section_ids = {hit["section_id"] for hit in as_dict["hits"]}
    prompt_context = build_maintenance_kb_prompt_context(result)

    assert as_dict["version"] == MAINTENANCE_KB_VERSION
    assert as_dict["status"] == "matched"
    assert as_dict["query_asset_id"] == "PKG-L3-GBX-03"
    assert as_dict["thresholds"]["vibration_rms_high_mm_s"] == 6.5
    assert as_dict["thresholds"]["gearbox_temperature_high_c"] == 75
    assert "GBX-VIB-01" in section_ids
    assert "GBX-TEMP-01" in section_ids
    assert "Maintenance KB context" in prompt_context
    assert "thresholds" in prompt_context
    assert "no final root cause" in prompt_context


def test_maintenance_kb_no_match_keeps_manual_claims_blocked() -> None:
    result = retrieve_maintenance_kb_context(query_text="unknown machine with unrelated symptom")
    prompt_context = build_maintenance_kb_prompt_context(result)

    assert result.status == "no_match"
    assert result.hits == ()
    assert result.as_dict()["thresholds"] == {}
    assert "Do not claim manual thresholds" in prompt_context


def test_maintenance_kb_requires_matching_asset_before_thresholds_are_applied() -> None:
    no_asset = retrieve_maintenance_kb_context(query_text="gearbox vibration RMS high with yellow alarm")
    wrong_asset = retrieve_maintenance_kb_context(
        query_text="PKG-L4-GBX-99 gearbox vibration RMS high with yellow alarm"
    )

    assert no_asset.status == "no_match"
    assert no_asset.query_asset_id is None
    assert no_asset.thresholds == {}
    assert no_asset.missing_reason == "asset identity is required before applying machine-specific maintenance KB thresholds"
    assert wrong_asset.status == "no_match"
    assert wrong_asset.query_asset_id == "PKG-L4-GBX-99"
    assert wrong_asset.thresholds == {}
    assert wrong_asset.hits == ()
