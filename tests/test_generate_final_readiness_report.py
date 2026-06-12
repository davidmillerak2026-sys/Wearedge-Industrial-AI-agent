from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_final_readiness_report.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_final_readiness_report", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_readiness_report_shows_missing_external_items(tmp_path: Path) -> None:
    module = _load_module()
    assets = tmp_path / "live-evidence"

    result = module.build_final_readiness(
        assets_dir=assets,
        bundle_path=tmp_path / "missing-bundle.zip",
        bundle_manifest_path=tmp_path / "missing-bundle-manifest.json",
        human_action_manifest_path=tmp_path / "missing-human-manifest.json",
    )
    report = module.render_readiness_report(result)

    assert result["repo"]["ready"] is True
    assert result["overall_ready_for_official_submission"] is False
    assert "legal/company-info-filled.md" in report
    assert "Run python scripts/run_final_readiness_pipeline.py --json" in report


def test_final_readiness_detects_bundle_and_human_manifest(tmp_path: Path) -> None:
    module = _load_module()
    assets = tmp_path / "live-evidence"
    bundle = tmp_path / "bundle.zip"
    bundle.write_bytes(b"fake bundle")
    bundle_manifest = tmp_path / "bundle.bundle-manifest.json"
    bundle_manifest.write_text(
        json.dumps({"file_count": 5, "bundle_sha256": module.file_sha256(bundle)}),
        encoding="utf-8",
    )
    human_manifest = tmp_path / "final-human-action-pack-manifest.json"
    human_manifest.write_text(
        json.dumps({"written_count": 7, "final_targets_not_created": ["legal/company-info-filled.md"]}),
        encoding="utf-8",
    )

    result = module.build_final_readiness(
        assets_dir=assets,
        bundle_path=bundle,
        bundle_manifest_path=bundle_manifest,
        human_action_manifest_path=human_manifest,
    )

    assert result["status"]["bundle_present"] is True
    assert result["status"]["human_templates_present"] is True
    assert result["bundle"]["manifest_file_count"] == 5
    assert result["human_action_pack"]["written_count"] == 7
    assert result["human_action_pack"]["template_count"] == 7
    assert result["finals_foundation"]["latency_replay"]["ready"] is True


def test_render_readiness_report_includes_commands_and_boundary(tmp_path: Path) -> None:
    module = _load_module()

    result = module.build_final_readiness(
        assets_dir=tmp_path / "assets",
        bundle_path=tmp_path / "missing.zip",
        bundle_manifest_path=tmp_path / "missing.json",
        human_action_manifest_path=tmp_path / "human.json",
    )
    report = module.render_readiness_report(result)

    assert "Verification Commands" in report
    assert "Finals foundation ready" in report
    assert "Finals Foundation" in report
    assert "Workflow Canvas evidence tier" in report
    assert "local_fastapi_http_gateway" in report
    assert "Workflow Canvas replay mode" in report
    assert "Workflow Canvas resource samples" in report
    assert "Workflow Canvas gateway RSS max" in report
    assert "run_final_readiness_pipeline.py --json" in report
    assert "verify_finals_foundation.py --json" in report
    assert "benchmark_workflow_canvas_latency.py" in report
    assert "benchmark_local_gateway_latency.py" in report
    assert "generate_final_readiness_report.py --write" in report
    assert "does not make external/human-owned files complete" in report
