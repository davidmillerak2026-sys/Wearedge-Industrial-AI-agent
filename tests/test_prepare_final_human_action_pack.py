from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "prepare_final_human_action_pack.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("prepare_final_human_action_pack", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_prepare_templates_writes_templates_without_final_targets(tmp_path: Path) -> None:
    module = _load_module()

    result = module.prepare_templates(tmp_path)

    assert result["ok"] is True
    assert result["written_count"] == len(module.TEMPLATES)
    assert (tmp_path / "legal" / "company-info-filled.template.md").is_file()
    assert (tmp_path / "legal" / "ip-and-no-dispute-statement.template.md").is_file()
    assert (tmp_path / "submission" / "registration-form-capture-checklist.template.md").is_file()
    assert (tmp_path / "final-human-action-pack-manifest.json").is_file()
    assert not (tmp_path / "legal" / "company-info-filled.md").exists()
    assert not (tmp_path / "legal" / "ip-and-no-dispute-signed.pdf").exists()
    assert not (tmp_path / "submission" / "01-registration-form-filled.png").exists()


def test_prepare_templates_skips_existing_without_overwrite(tmp_path: Path) -> None:
    module = _load_module()
    existing = tmp_path / "legal" / "company-info-filled.template.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("keep me", encoding="utf-8")

    result = module.prepare_templates(tmp_path, overwrite=False, write_manifest=False)

    assert result["skipped_count"] == 1
    assert existing.read_text(encoding="utf-8") == "keep me"


def test_prepare_templates_can_overwrite_existing(tmp_path: Path) -> None:
    module = _load_module()
    existing = tmp_path / "legal" / "company-info-filled.template.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("old", encoding="utf-8")

    result = module.prepare_templates(tmp_path, overwrite=True, write_manifest=False)

    assert result["skipped_count"] == 0
    assert "submission-assets/live-evidence/legal/company-info-filled.md" in existing.read_text(encoding="utf-8")
