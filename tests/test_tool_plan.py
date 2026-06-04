from __future__ import annotations

from jetson.evidence_plan import build_evidence_plan
from jetson.tool_plan import TOOL_PLAN_VERSION, build_bounded_tool_plan, build_tool_action_logs, build_tool_prompt_context


def test_bounded_tool_plan_selects_iqc_tools_with_fixed_budget() -> None:
    evidence_plan = build_evidence_plan(
        mode="iqc",
        device={"device_id": "m400-demo-01"},
        image_bytes=1_500_000,
        needs_ocr=True,
        high_detail=True,
    )

    tool_plan = build_bounded_tool_plan(evidence_plan, max_tool_calls=2)
    as_dict = tool_plan.as_dict()

    assert as_dict["version"] == TOOL_PLAN_VERSION
    assert as_dict["mode"] == "iqc"
    assert as_dict["max_iterations"] == 1
    assert as_dict["max_tool_calls"] == 2
    assert as_dict["used_tool_calls"] == 1
    assert as_dict["status"] == "missing_tool_connections"
    assert as_dict["selected_tools"] == ["visual_defect_detector", "quality_plan"]
    assert [item["name"] for item in as_dict["skipped_tools"]] == ["visual_defect_detector"]
    assert as_dict["deferred_tools"] == ["lot_context"]


def test_bounded_tool_plan_counts_supplied_iqc_detector_evidence() -> None:
    evidence_plan = build_evidence_plan(
        mode="iqc",
        device={"device_id": "m400-demo-01"},
        image_bytes=1_500_000,
        needs_ocr=True,
        high_detail=True,
        available_tools=("visual_defect_detector",),
    )

    tool_plan = build_bounded_tool_plan(evidence_plan, max_tool_calls=2)
    as_dict = tool_plan.as_dict()

    assert as_dict["used_tool_calls"] == 2
    assert as_dict["status"] == "ready"
    assert as_dict["selected_tools"] == ["visual_defect_detector", "quality_plan"]
    assert as_dict["skipped_tools"] == []


def test_tool_action_logs_are_skipped_until_tools_are_connected() -> None:
    evidence_plan = build_evidence_plan(
        mode="hazard",
        device={"device_id": "m400-demo-01"},
        image_bytes=700_000,
        needs_ocr=False,
        high_detail=False,
    )
    tool_plan = build_bounded_tool_plan(evidence_plan)

    action_logs = build_tool_action_logs(tool_plan)

    assert [log["tool"] for log in action_logs] == ["ppe_detector", "zone_geofence", "ehs_rules"]
    assert {log["stage"] for log in action_logs} == {"bounded_react_tools"}
    assert {log["status"] for log in action_logs} == {"skipped"}


def test_tool_prompt_context_forbids_claiming_skipped_evidence() -> None:
    evidence_plan = build_evidence_plan(
        mode="maintenance",
        device={"device_id": "m400-demo-01"},
        image_bytes=900_000,
        needs_ocr=False,
        high_detail=False,
    )
    tool_plan = build_bounded_tool_plan(evidence_plan)

    prompt_context = build_tool_prompt_context(tool_plan)

    assert "budget=1 iteration/3 calls" in prompt_context
    assert tool_plan.used_tool_calls == 1
    assert "skipped=asset_registry, telemetry_history" in prompt_context
    assert "used=1" in prompt_context
    assert "Do not present skipped/deferred tools as evidence" in prompt_context
