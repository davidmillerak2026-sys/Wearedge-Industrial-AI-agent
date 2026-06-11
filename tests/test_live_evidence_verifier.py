from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_live_evidence.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_live_evidence", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_live_evidence_platform_stage_reports_missing_items(tmp_path: Path) -> None:
    module = _load_module()

    result = module.verify_live_evidence(tmp_path, "platform")

    assert result["ready"] is False
    assert result["missing_count"] == result["expected_count"]
    assert "xcelerator/04-runtime-profile-api-test.png" in result["missing"]
    assert "edge-runtime/05-solution-profile.png" in result["missing"]
    assert "video/wearedge-enterprise-demo-3-5min.mp4" not in result["missing"]


def test_live_evidence_platform_stage_can_be_ready(tmp_path: Path) -> None:
    module = _load_module()
    for item in module.EXPECTED_ITEMS:
        if item.stage == "platform":
            path = tmp_path / item.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"present")

    result = module.verify_live_evidence(tmp_path, "platform")

    assert result["ready"] is True
    assert result["missing"] == []
    assert result["groups"]["gongyi-mofang"]["missing"] == 0


def test_live_evidence_final_stage_includes_legal_and_submission_assets(tmp_path: Path) -> None:
    module = _load_module()

    result = module.verify_live_evidence(tmp_path, "final")
    manifest = module.render_manifest(result)

    assert "legal/ip-and-no-dispute-signed.pdf" in result["missing"]
    assert "submission/02-submission-success.png" in result["missing"]
    assert "video/wearedge-enterprise-demo-3-5min.mp4" in manifest
