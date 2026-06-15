from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_submission_package.py"


def _load_verify_module():
    spec = importlib.util.spec_from_file_location("verify_submission_package", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_submission_package_repo_controlled_items_are_ready() -> None:
    module = _load_verify_module()

    result = module.verify_package(REPO_ROOT)

    assert result["repo_ready"] is True
    assert result["repo_failures"] == []
    assert len(result["phases"]) == 5
    assert result["registration_fields"]["status"] == "ready"
    assert result["evidence"]["status"] == "ready"
    phase_e = next(phase for phase in result["phases"] if phase["name"] == "Phase E - Registration fields")
    assert phase_e["present_count"] == phase_e["artifact_count"]
    assert any(
        artifact["path"] == "docs/submission/first-round-submission-attachment-index.md"
        for artifact in phase_e["artifacts"]
    )
    assert any(
        artifact["path"] == "scripts/verify_final_external_assets.py"
        for artifact in phase_e["artifacts"]
    )


def test_submission_manifest_marks_external_pending_without_repo_failure() -> None:
    module = _load_verify_module()
    result = module.verify_package(REPO_ROOT)

    manifest = module.render_manifest(result)

    assert "Repository-controlled package ready: True" in manifest
    assert "保持当前 WFC Dashboard / run-log / HumanApprovalGate live 证据" in manifest
    assert "python scripts/run_final_readiness_pipeline.py --json" in manifest
    assert "python scripts/verify_live_evidence.py --stage final" in manifest
    assert "Repository Failures" in manifest
    assert "- None." in manifest
