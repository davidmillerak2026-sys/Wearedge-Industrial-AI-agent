from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_finals_foundation.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_finals_foundation", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_finals_foundation_verifier_tracks_direction_and_performance_baseline() -> None:
    module = _load_module()

    result = module.verify_finals_foundation()

    assert result["foundation_ready"] is True
    assert result["finals_ready"] is False
    assert result["direction_coverage"]["selected_direction_count"] == 5
    assert result["direction_coverage"]["all_cases_meet_min_required_directions"] is True
    assert result["performance"]["decision_accuracy_target_met"] is True
    assert result["performance"]["latency_target_met"] is True
    assert result["performance"]["finals_validation_ready"] is True
    assert result["performance"]["finals_case_count"] == 15
    assert result["latency_replay"]["ready"] is True
    assert result["latency_replay"]["target_met"] is True
    assert result["latency_replay"]["mode"] == "http"
    assert result["latency_replay"]["evidence_tier"] == "final_edge_stdlib_http_gateway"
    assert result["latency_replay"]["sample_count"] > 0
    assert result["latency_replay"]["resource_sample_count"] > 0
    assert result["latency_replay"]["process_rss_mb_max"] > 0
    assert result["hmi"]["natural_language_api_foundation"] is True
    assert result["hmi"]["natural_language_console_foundation"] is True
    assert result["hmi"]["decision_visualization_foundation"] is True
    assert result["hmi"]["production_hmi_foundation"] is True
    assert result["hmi"]["capabilities"]["missing_capabilities"] == []
    assert result["hmi"]["capabilities"]["capabilities"]["natural_language_query"] is True
    assert result["hmi"]["capabilities"]["capabilities"]["evidence_references"] is True
    assert result["hmi"]["capabilities"]["capabilities"]["audit_trail"] is True
    assert result["platform_evidence"]["fallback_warning_count"] == 2
    assert result["priority_gaps"]


def test_finals_foundation_report_states_boundary() -> None:
    module = _load_module()
    result = module.verify_finals_foundation()

    report = module.render_markdown(result)

    assert "Foundation ready: True" in report
    assert "Finals ready: False" in report
    assert "Decision accuracy" in report
    assert "Latency" in report
    assert "Latency Replay Evidence" in report
    assert "Evidence tier: final_edge_stdlib_http_gateway" in report
    assert "Replay mode: http" in report
    assert "Resource samples:" in report
    assert "Production HMI foundation: True" in report
    assert "HMI missing capabilities: None" in report
    assert "Finals validation cases: 15 / 15" in report
    assert "Foundation-ready does not mean finals-ready" in report
