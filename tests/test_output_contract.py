from __future__ import annotations

from jetson.output_contract import (
    build_changeover_contract_prompt,
    build_contract_prompt,
    build_energy_contract_prompt,
    build_iqc_contract_prompt,
    build_iqc_repair_prompt,
    build_maintenance_contract_prompt,
    build_repair_prompt,
    build_wi_contract_prompt,
    check_changeover_output_contract,
    check_energy_output_contract,
    check_iqc_output_contract,
    check_maintenance_output_contract,
    check_output_contract,
    check_wi_output_contract,
)


def test_contract_accepts_three_labeled_long_fields() -> None:
    answer = (
        "- Scene: Dusty industrial storage room with stacked cartons loose cables broken pallets and scattered debris near the entrance.\n"
        "- Risk: Trip hazard from loose materials on the walking path could cause falls during urgent inspection work.\n"
        "- Action: Stop entry and inspect the floor carefully while wearing proper PPE before moving any stored materials."
    )

    check = check_output_contract(answer, min_words=16)

    assert check.ok
    assert check.structured is not None
    assert check.structured.scene.startswith("Dusty industrial storage room")
    assert check.structured.action.startswith("Stop entry")


def test_contract_rejects_short_or_unsafe_action() -> None:
    answer = (
        "- Scene: Dusty attic space.\n"
        "- Risk: Falling debris hazard.\n"
        "- Action: Move boxes quickly."
    )

    check = check_output_contract(answer, min_words=16)

    assert not check.ok
    assert any("scene must contain" in violation for violation in check.violations)
    assert any("action must start" in violation for violation in check.violations)


def test_contract_prompt_normalizes_under_12_rule() -> None:
    prompt = """Return exactly this format and nothing else:
- Scene: <one short phrase>
- Risk: <one short hazard>
- Action: <one safe next action>

Rules:
Scene must describe the place.
Risk must name a hazard.
Action must start with Stop, Inspect, Wear, Keep, or Report.
Each line must be under 12 words.
Do not add any introduction."""

    contract_prompt = build_contract_prompt(prompt)

    assert "Each line must be more than 15 words." in contract_prompt
    assert "under 12 words" not in contract_prompt


def test_repair_prompt_carries_previous_answer() -> None:
    repair_prompt = build_repair_prompt("- Scene: Warehouse.\n- Risk: Trip.\n- Action: Stop.")

    assert "Previous answer:" in repair_prompt
    assert "- Scene: Warehouse." in repair_prompt
    assert "Each line must be more than 15 words." in repair_prompt


def test_iqc_contract_accepts_quality_disposition() -> None:
    answer = (
        "- Product: Machined aluminum housing shows visible edge burrs uneven surface marks and possible handling contamination near the sealing face.\n"
        "- Quality Risk: Burrs or contamination on the sealing face could create assembly leakage escapes and downstream rework risk.\n"
        "- Disposition: expand_inspection\n"
        "- Action: Expand inspection to adjacent units from the same station lot and shift while holding suspect housings for quality engineer review."
    )

    check = check_iqc_output_contract(answer, min_words=16)

    assert check.ok
    assert check.structured is not None
    assert check.structured.disposition == "expand_inspection"
    assert check.structured.action.startswith("Expand inspection")


def test_iqc_contract_rejects_invalid_disposition_or_action_mapping() -> None:
    answer = (
        "- Product: Machined aluminum housing shows visible edge burrs uneven surface marks and possible handling contamination near the sealing face.\n"
        "- Quality Risk: Burrs or contamination on the sealing face could create assembly leakage escapes and downstream rework risk.\n"
        "- Disposition: stop_production\n"
        "- Action: Inspect only one part and continue the process without containment while waiting for later review."
    )

    check = check_iqc_output_contract(answer, min_words=16)

    assert not check.ok
    assert any("disposition=stop_production" in violation for violation in check.violations)


def test_iqc_contract_prompt_and_repair_prompt() -> None:
    contract_prompt = build_iqc_contract_prompt("Assess this in-process part for quality risk.")
    repair_prompt = build_iqc_repair_prompt("- Product: Part.\n- Quality Risk: Unknown.")

    assert "- Disposition:" in contract_prompt
    assert "expand_inspection" in contract_prompt
    assert "Previous answer:" in repair_prompt
    assert "Disposition must be one exact allowed value" in repair_prompt


def test_wi_contract_accepts_machine_operation_guidance() -> None:
    answer = (
        "- Machine: Horizontal CNC machining center at station three with visible control panel and clamping fixture.\n"
        "- Work Instruction: Follow the posted work instruction for loading orientation clamp confirmation cycle start and first visible part condition before operating.\n"
        "- Risk Control: Keep guards closed confirm fixture seating check coolant flow and escalate any alarm or abnormal vibration before continuing production.\n"
        "- Action: Confirm the machine identity and posted work instruction revision before asking for any parameter or restart guidance."
    )

    check = check_wi_output_contract(answer, min_words=16)

    assert check.ok
    assert check.structured is not None
    assert check.structured.machine.startswith("Horizontal CNC")


def test_changeover_contract_accepts_sku_guidance() -> None:
    answer = (
        "- Machine: Packaging cell labeler with visible HMI recipe screen and adjustable guide rail section.\n"
        "- SKU: Target SKU appears to be label family A123 on the visible traveler but needs operator confirmation.\n"
        "- Changeover Step: Confirm the target SKU against the traveler then set guides label roll and recipe only to released setup instructions.\n"
        "- Verification: Verify first-piece label position barcode readability date code and line clearance before releasing startup parts downstream.\n"
        "- Action: Confirm the target SKU and hold startup until first-piece verification is accepted by the authorized quality role."
    )

    check = check_changeover_output_contract(answer, min_words=16)

    assert check.ok
    assert check.structured is not None
    assert check.structured.sku.startswith("Target SKU")


def test_wi_and_changeover_prompts_expose_required_fields() -> None:
    wi_prompt = build_wi_contract_prompt("How do I operate this machine safely?")
    changeover_prompt = build_changeover_contract_prompt("Guide this SKU changeover.")

    assert "- Work Instruction:" in wi_prompt
    assert "- Risk Control:" in wi_prompt
    assert "- Changeover Step:" in changeover_prompt
    assert "- Verification:" in changeover_prompt


def test_maintenance_contract_accepts_predictive_maintenance_guidance() -> None:
    answer = (
        "- Machine: Conveyor drive station with visible motor gearbox guard and nearby lubrication point.\n"
        "- Symptom: Visible oil staining and dust accumulation around the gearbox base suggest an abnormal condition requiring inspection.\n"
        "- Maintenance Risk: Leakage or poor lubrication could increase wear heat vibration and unplanned downtime if not checked promptly.\n"
        "- Evidence Needed: Inspect the lubrication point review gearbox temperature vibration history and confirm the released maintenance manual threshold.\n"
        "- Action: Inspect the gearbox area safely and report the condition to maintenance before increasing production speed today."
    )

    check = check_maintenance_output_contract(answer, min_words=16)

    assert check.ok
    assert check.structured is not None
    assert check.structured.machine.startswith("Conveyor drive")


def test_maintenance_prompt_exposes_required_fields() -> None:
    prompt = build_maintenance_contract_prompt("Check this machine for predictive maintenance risk.")

    assert "- Symptom:" in prompt
    assert "- Maintenance Risk:" in prompt
    assert "- Evidence Needed:" in prompt


def test_energy_contract_accepts_bounded_energy_guidance() -> None:
    answer = (
        "- Asset: Packaging line three cartoner and conveyor cell with visible production schedule context and energy meter reference.\n"
        "- Energy Signal: Meter table shows sustained twelve kilowatt idle load during a documented break window with no verified product movement.\n"
        "- Optimization: Peak-load reduction may be possible by shifting auxiliary running time while preserving production plan quality checks and restart readiness.\n"
        "- Verification: Confirm meter baseline demand tariff production schedule and line lead approval before any load reduction or schedule change.\n"
        "- Action: Reduce auxiliary load only after baseline meter evidence and production approval confirm the idle window is safe."
    )

    check = check_energy_output_contract(answer, min_words=16)

    assert check.ok
    assert check.structured is not None
    assert check.structured.asset.startswith("Packaging line three")


def test_energy_prompt_exposes_required_fields() -> None:
    prompt = build_energy_contract_prompt("Assess this line for energy optimization.")

    assert "- Energy Signal:" in prompt
    assert "- Optimization:" in prompt
    assert "- Verification:" in prompt
