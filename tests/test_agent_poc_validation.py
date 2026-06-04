from __future__ import annotations

from collections import Counter

from jetson.agent_poc_validation import GOLDEN_SCENARIOS, POC_SCENARIOS, run_agent_golden_validations, run_agent_poc_validations


def test_all_five_agent_poc_scenarios_are_present() -> None:
    assert [scenario.mode for scenario in POC_SCENARIOS] == [
        "maintenance",
        "iqc",
        "changeover",
        "wi",
        "hazard",
    ]


def test_all_five_agent_poc_scenarios_pass() -> None:
    results = run_agent_poc_validations()

    assert all(result.passed for result in results)
    assert {result.runtime_last_event for result in results} == {"workflow.closed"}
    assert {result.integration_target for result in results} == {
        "maintenance_work_order",
        "qms_quality_event",
        "changeover_checklist",
        "wi_reference",
        "ehs_case",
    }


def test_golden_scenarios_cover_five_cases_per_agent() -> None:
    counts = Counter(scenario.mode for scenario in GOLDEN_SCENARIOS)

    assert counts == {
        "maintenance": 5,
        "iqc": 5,
        "changeover": 5,
        "wi": 5,
        "hazard": 5,
    }


def test_golden_scenarios_cover_detector_and_rag_source_gaps() -> None:
    by_title = {scenario.title: scenario for scenario in GOLDEN_SCENARIOS}

    iqc = by_title["iqc detector-first pass blocked without detector evidence"]
    changeover = by_title["changeover rag source missing blocks controlled step"]
    wi = by_title["wi rag source missing blocks guided operation"]

    assert iqc.expected_channel == "quality_review"
    assert iqc.expected_selected_tools[0] == "visual_defect_detector"
    assert iqc.expected_blocked_fields == ("quality_risk",)
    assert changeover.expected_selected_tools == ("sku_recipe", "changeover_checklist", "first_piece_plan")
    assert changeover.expected_blocked_fields == ("changeover_step",)
    assert wi.expected_selected_tools == ("wi_repository", "machine_identity")
    assert wi.expected_blocked_fields == ("work_instruction",)


def test_all_golden_scenarios_pass() -> None:
    results = run_agent_golden_validations()

    assert all(result.passed for result in results), [result.as_dict() for result in results if not result.passed]
    assert {result.runtime_last_event for result in results} == {"workflow.closed"}
    assert {result.tool_status for result in results} == {"missing_tool_connections"}
