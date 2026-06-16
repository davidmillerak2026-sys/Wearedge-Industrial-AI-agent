from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "prepare_wfc_live_edit_package.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("prepare_wfc_live_edit_package", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_prepare_wfc_live_edit_package_writes_paste_ready_files(tmp_path: Path) -> None:
    module = _load_module()
    output_dir = tmp_path / "wfc-live-edit-package"

    manifest = module.build_package(output_dir=output_dir)

    fb_main = output_dir / "fb_main.py"
    sample = output_dir / "wfc-resource-input-sample.json"
    checklist = output_dir / "README-next-live-run.md"
    manifest_path = output_dir / "manifest.json"
    assert fb_main.exists()
    assert "wfc_writeback" in fb_main.read_text(encoding="utf-8")
    assert json.loads(sample.read_text(encoding="utf-8"))["deploymentMode"] == "edge-fastapi-gateway"
    assert "196-wfc-dynamic-writeback-output-ok-20260616.png" in checklist.read_text(encoding="utf-8")
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["files"]["function_block"] == str(fb_main)
    assert manifest["function_block_lines"] < 140
