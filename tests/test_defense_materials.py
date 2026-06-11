from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_judging_scorecard_maps_all_weighted_dimensions() -> None:
    text = (REPO_ROOT / "docs" / "submission" / "judging-scorecard-evidence-map.md").read_text(
        encoding="utf-8"
    )

    for marker in ("Innovation", "Technical level", "Application prospect", "Team ability", "Feasibility"):
        assert marker in text
    for weight in ("30%", "20%", "10%"):
        assert weight in text
    assert "fallback" in text
    assert "HumanApprovalGate" in text
    assert "verify_live_evidence.py" in text


def test_defense_qna_covers_core_risks_and_model_boundary() -> None:
    text = (REPO_ROOT / "docs" / "submission" / "defense-qna-playbook.md").read_text(
        encoding="utf-8"
    )

    for marker in (
        "What exact industrial problem",
        "What model do you use",
        "What mechanism actually makes decisions",
        "How do you avoid unsafe OT control",
        "Are your metrics real production results",
    ):
        assert marker in text
    assert "Gemma 4 E2B" in text
    assert "deterministic KPI" in text
    assert "not directly writes PLC" in text or "never directly writes PLC" in text
