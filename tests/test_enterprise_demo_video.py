from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_enterprise_demo_video.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_enterprise_demo_video", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_enterprise_demo_narration_has_submission_boundaries(tmp_path: Path) -> None:
    module = _load_module()

    result = module.script_only(tmp_path)
    script = (tmp_path / module.DEFAULT_SCRIPT).read_text(encoding="utf-8")

    assert result["ok"] is True
    assert 180 <= result["duration_seconds"] <= 300
    assert result["fallback_scenes"] >= 1
    assert "Xcelerator" in script
    assert "工易魔方" in script
    assert "fallback/mock/API-smoke" in script
    assert "不能声称已完成 live WFC `ok=true`" in script
