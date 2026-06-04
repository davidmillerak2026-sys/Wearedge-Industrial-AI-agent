from __future__ import annotations

from jetson.evidence_plan import EVIDENCE_PLAN_VERSION, build_evidence_plan, build_evidence_prompt_context


def test_evidence_plan_declares_current_edge_sources_and_missing_iqc_tools() -> None:
    plan = build_evidence_plan(
        mode="quality",
        device={"device_id": "m400-demo-01", "location_hint": "line-3"},
        image_bytes=1_200_000,
        needs_ocr=True,
        high_detail=True,
    )

    as_dict = plan.as_dict()

    assert as_dict["version"] == EVIDENCE_PLAN_VERSION
    assert as_dict["mode"] == "iqc"
    assert [item["name"] for item in as_dict["current_sources"]] == [
        "m400_image",
        "device_context",
        "ocr_attention",
        "high_detail_visual",
    ]
    assert "visual_defect_detector" in as_dict["missing_tools"]
    assert "quality_plan" not in as_dict["missing_tools"]
    quality_plan = next(item for item in as_dict["planned_tools"] if item["name"] == "quality_plan")
    assert quality_plan["status"] == "available"
    assert quality_plan["kind"] == "rag_tool"
    assert "release decisions" in as_dict["policy"]


def test_evidence_plan_marks_supplied_iqc_detector_as_available() -> None:
    plan = build_evidence_plan(
        mode="iqc",
        device={"device_id": "m400-demo-01", "location_hint": "line-3"},
        image_bytes=1_200_000,
        needs_ocr=True,
        high_detail=True,
        available_tools=("visual_defect_detector",),
    )

    as_dict = plan.as_dict()
    detector = next(item for item in as_dict["planned_tools"] if item["name"] == "visual_defect_detector")

    assert detector["status"] == "available"
    assert "visual_defect_detector" not in as_dict["missing_tools"]


def test_evidence_prompt_context_blocks_unlisted_external_claims() -> None:
    plan = build_evidence_plan(
        mode="maintenance",
        device={"device_id": "m400-demo-01"},
        image_bytes=900_000,
        needs_ocr=False,
        high_detail=False,
    )

    prompt_context = build_evidence_prompt_context(plan)

    assert "current=m400_image, device_context" in prompt_context
    assert "telemetry_history" in prompt_context
    assert "Do not claim unavailable external evidence" in prompt_context
