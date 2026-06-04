from __future__ import annotations

from jetson.iqc_quality_eval import (
    IQC_EVALUATION_VERSION,
    build_iqc_quality_prompt_context,
    evaluate_iqc_quality_condition,
)
from jetson.iqc_quality_plan import retrieve_iqc_quality_plan_context


def _quality_plan() -> dict[str, object]:
    return retrieve_iqc_quality_plan_context(
        query_text="AL-HOUSING-L3 machined aluminum housing line three station output"
    ).as_dict()


def _detector_evidence() -> dict[str, object]:
    return {
        "version": "wear-edge-iqc-detector-evidence.v1",
        "status": "available",
        "source": "simulated_m400_detector",
        "product_id": "AL-HOUSING-L3",
        "detections": [
            {
                "defect_class": "edge_burr",
                "confidence": 0.73,
                "bbox": [180, 450, 330, 535],
                "detection_id": "det-edge-burr",
                "source": "simulated_m400_detector",
            },
            {
                "defect_class": "sealing_face_scratch",
                "confidence": 0.84,
                "bbox": [610, 335, 775, 435],
                "detection_id": "det-seal-scratch",
                "source": "simulated_m400_detector",
            },
        ],
        "detection_count": 2,
    }


def test_iqc_quality_eval_blocks_pass_without_detector_evidence() -> None:
    result = evaluate_iqc_quality_condition(
        fields={
            "product": "AL-HOUSING-L3 machined aluminum housing from line three.",
            "quality_risk": "No visible quality risk is observed on the sealing face or edges.",
            "disposition": "pass",
            "action": "Continue production under current inspection controls.",
        },
        knowledge_base=_quality_plan(),
        tool_plan={"skipped_tools": [{"name": "visual_defect_detector"}]},
    )

    as_dict = result.as_dict()
    prompt_context = build_iqc_quality_prompt_context(result)

    assert as_dict["version"] == IQC_EVALUATION_VERSION
    assert as_dict["status"] == "insufficient_detector_evidence"
    assert as_dict["recommended_channel"] == "quality_review"
    assert as_dict["requires_human"] is True
    assert "visual defect detector evidence" in as_dict["missing_inputs"]
    assert "Deterministic IQC quality evaluation" in prompt_context


def test_iqc_quality_eval_allows_pass_with_detector_clear_evidence() -> None:
    result = evaluate_iqc_quality_condition(
        fields={
            "product": "AL-HOUSING-L3 machined aluminum housing from line three.",
            "quality_risk": "No visible quality risk is observed.",
            "disposition": "pass",
            "action": "Continue production under current inspection controls.",
        },
        knowledge_base=_quality_plan(),
        tool_plan={"skipped_tools": []},
        detector_evidence={
            "version": "wear-edge-iqc-detector-evidence.v1",
            "status": "clear",
            "source": "simulated_m400_detector",
            "product_id": "AL-HOUSING-L3",
            "detections": [],
            "detection_count": 0,
        },
    )

    assert result.status == "within_plan_observation"
    assert result.risk_level == "low"
    assert result.recommended_channel == "continue_production"
    assert result.requires_human is False


def test_iqc_quality_eval_prefers_detector_findings_for_containment() -> None:
    result = evaluate_iqc_quality_condition(
        fields={
            "product": "AL-HOUSING-L3 machined aluminum housing from line three.",
            "quality_risk": "Detector reports edge burr and sealing face scratch on the inspected unit.",
            "disposition": "needs_review",
            "action": "Hold suspect units while quality reviews detector evidence.",
        },
        knowledge_base=_quality_plan(),
        tool_plan={"skipped_tools": []},
        detector_evidence=_detector_evidence(),
    )

    findings = {finding.defect_class: finding for finding in result.findings}

    assert result.status == "detector_or_plan_risk_detected"
    assert result.detector_status == "provided"
    assert result.recommended_channel == "quality_hold"
    assert "visual defect detector evidence" not in result.missing_inputs
    assert findings["edge_burr"].evidence_source == "visual_defect_detector:det-edge-burr"
    assert findings["sealing_face_scratch"].evidence_source == "visual_defect_detector:det-seal-scratch"


def test_iqc_quality_eval_maps_defect_rules_to_containment() -> None:
    result = evaluate_iqc_quality_condition(
        fields={
            "product": "AL-HOUSING-L3 machined aluminum housing from line three.",
            "quality_risk": "Visible sealing face scratch and handling contamination could create leakage escape risk.",
            "disposition": "needs_review",
            "action": "Inspect suspect units and ask quality to confirm containment.",
        },
        knowledge_base=_quality_plan(),
        tool_plan={"skipped_tools": [{"name": "visual_defect_detector"}]},
    )

    findings = {finding.defect_class: finding for finding in result.findings}

    assert result.status == "visible_risk_needs_detector_review"
    assert result.risk_level == "medium"
    assert result.recommended_channel == "quality_hold"
    assert "sealing_face_scratch" in findings
    assert "contamination" in findings
