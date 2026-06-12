from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_final_readiness_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_final_readiness_pipeline", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_readiness_pipeline_refreshes_local_manifests_without_final_targets(tmp_path: Path) -> None:
    module = _load_module()
    assets = tmp_path / "live-evidence"

    result = module.run_pipeline(
        assets_dir=assets,
        submission_manifest_path=tmp_path / "submission-package-manifest.md",
        live_evidence_manifest_path=tmp_path / "live-evidence-manifest.md",
        readiness_report_path=tmp_path / "final-readiness-report.md",
        finals_validation_report_path=tmp_path / "finals-validation-report.md",
        latency_benchmark_report_path=tmp_path / "finals-latency-benchmark-report.md",
        latency_benchmark_json_path=tmp_path / "finals-latency-benchmark.json",
        bundle_output_dir=tmp_path / "bundle",
        wfc_package_output_dir=tmp_path / "wfc-resource-package",
    )

    assert result["ok"] is True
    assert result["repo_ready"] is True
    assert result["finals_foundation_ready"] is True
    assert result["finals_ready"] is False
    assert result["finals_priority_gap_count"] > 0
    assert result["latency_benchmark_mode"] == "in_process"
    assert result["latency_benchmark_target_met"] is True
    assert result["latency_benchmark_sample_count"] > 0
    assert result["selected_latency_evidence_tier"] == "final_edge_fastapi_http_gateway"
    assert result["selected_latency_evidence_mode"] == "http"
    assert result["selected_latency_evidence_sample_count"] > 0
    assert result["selected_latency_resource_sample_count"] > 0
    assert result["selected_latency_process_rss_mb_max"] > 0
    assert result["final_ready"] is False
    assert result["final_missing_count"] >= 6
    assert Path(result["bundle_path"]).is_file()
    assert Path(result["wfc_package_path"]).is_file()
    assert Path(result["edge_runtime_evidence_manifest_path"]).is_file()
    assert result["edge_runtime_evidence_ok"] is True
    assert result["edge_runtime_evidence_sample_count"] > 0
    assert (tmp_path / "submission-package-manifest.md").is_file()
    assert (tmp_path / "live-evidence-manifest.md").is_file()
    assert (tmp_path / "final-readiness-report.md").is_file()
    assert (tmp_path / "finals-validation-report.md").is_file()
    assert (tmp_path / "finals-latency-benchmark-report.md").is_file()
    assert (tmp_path / "finals-latency-benchmark.json").is_file()
    assert (assets / "edge-runtime" / "06-http-resource-benchmark.json").is_file()
    assert (assets / "edge-runtime" / "07-edge-runtime-evidence-manifest.md").is_file()
    assert (assets / "final-human-action-pack-manifest.json").is_file()
    assert not (assets / "legal" / "company-info-filled.md").exists()
    assert not (assets / "submission" / "01-registration-form-filled.png").exists()


def test_final_readiness_pipeline_strict_mode_blocks_when_external_files_missing(tmp_path: Path) -> None:
    module = _load_module()

    result = module.run_pipeline(
        assets_dir=tmp_path / "live-evidence",
        submission_manifest_path=tmp_path / "submission-package-manifest.md",
        live_evidence_manifest_path=tmp_path / "live-evidence-manifest.md",
        readiness_report_path=tmp_path / "final-readiness-report.md",
        finals_validation_report_path=tmp_path / "finals-validation-report.md",
        latency_benchmark_report_path=tmp_path / "finals-latency-benchmark-report.md",
        latency_benchmark_json_path=tmp_path / "finals-latency-benchmark.json",
        bundle_output_dir=tmp_path / "bundle",
        wfc_package_output_dir=tmp_path / "wfc-resource-package",
        strict_final=True,
    )

    assert result["ok"] is False
    assert result["blocking_reason"] == "Final external/human-owned evidence is incomplete."
    assert "Fill/capture the final live-evidence files" in "\n".join(result["recommended_next_actions"])


def test_render_summary_includes_primary_status_fields(tmp_path: Path) -> None:
    module = _load_module()
    result = module.run_pipeline(
        assets_dir=tmp_path / "live-evidence",
        submission_manifest_path=tmp_path / "submission-package-manifest.md",
        live_evidence_manifest_path=tmp_path / "live-evidence-manifest.md",
        readiness_report_path=tmp_path / "final-readiness-report.md",
        finals_validation_report_path=tmp_path / "finals-validation-report.md",
        latency_benchmark_report_path=tmp_path / "finals-latency-benchmark-report.md",
        latency_benchmark_json_path=tmp_path / "finals-latency-benchmark.json",
        bundle_output_dir=tmp_path / "bundle",
        wfc_package_output_dir=tmp_path / "wfc-resource-package",
    )

    summary = module.render_summary(result)

    assert "repo_ready=True" in summary
    assert "finals_foundation_ready=True" in summary
    assert "finals_validation_report=" in summary
    assert "latency_benchmark_report=" in summary
    assert "latency_benchmark_target_met=True" in summary
    assert "edge_runtime_evidence_ok=True" in summary
    assert "selected_latency_evidence_tier=final_edge_fastapi_http_gateway" in summary
    assert "selected_latency_evidence_mode=http" in summary
    assert "selected_latency_resource_sample_count=" in summary
    assert "selected_latency_process_rss_mb_max=" in summary
    assert "final_missing_count=" in summary
    assert "readiness_report=" in summary
