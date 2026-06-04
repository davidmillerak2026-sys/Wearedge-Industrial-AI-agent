from __future__ import annotations

from jetson.iqc_detector import (
    IQC_DETECTOR_EVIDENCE_VERSION,
    build_iqc_detector_prompt_context,
    normalize_iqc_detector_evidence,
)


def test_iqc_detector_normalizes_defect_boxes() -> None:
    evidence = normalize_iqc_detector_evidence(
        {
            "source": "simulated_m400_detector",
            "product_id": "AL-HOUSING-L3",
            "detections": [
                {
                    "class": "sealing_face_scratch",
                    "confidence": 0.84,
                    "bbox": [610, 330, 770, 430],
                }
            ],
        }
    )

    assert evidence is not None
    as_dict = evidence.as_dict()
    prompt_context = build_iqc_detector_prompt_context(evidence)

    assert as_dict["version"] == IQC_DETECTOR_EVIDENCE_VERSION
    assert as_dict["status"] == "available"
    assert as_dict["detection_count"] == 1
    assert as_dict["detections"][0]["defect_class"] == "sealing_face_scratch"
    assert "Visual defect detector evidence" in prompt_context
    assert "sealing_face_scratch" in prompt_context


def test_iqc_detector_marks_empty_detection_output_as_clear() -> None:
    evidence = normalize_iqc_detector_evidence(
        {
            "source": "simulated_m400_detector",
            "product_id": "AL-HOUSING-L3",
            "detections": [],
        }
    )

    assert evidence is not None
    assert evidence.status == "clear"
    assert evidence.as_dict()["detections"] == []


def test_iqc_detector_rejects_non_array_detections() -> None:
    evidence = normalize_iqc_detector_evidence({"detections": {"class": "edge_burr"}})

    assert evidence is not None
    assert evidence.status == "invalid"
    assert "detections must be a JSON array" in str(evidence.invalid_reason)


def test_iqc_detector_requires_explicit_detection_output() -> None:
    evidence = normalize_iqc_detector_evidence({"source": "simulated_m400_detector"})

    assert evidence is not None
    assert evidence.status == "invalid"
    assert "must include detections" in str(evidence.invalid_reason)
