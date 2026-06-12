from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_official_attachment_pack.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_official_attachment_pack", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_official_attachment_pack_writes_html_zip_and_manifest(tmp_path: Path) -> None:
    module = _load_module()

    manifest = module.build_official_attachment_pack(output_dir=tmp_path)

    zip_path = Path(manifest["zip_path"])
    manifest_path = Path(manifest["manifest_path"])
    assert manifest["ok"] is True
    assert zip_path.is_file()
    assert manifest_path.is_file()
    assert manifest["zip_sha256"] == module.file_sha256(zip_path)
    assert len(manifest["attachments"]) == len(module.ATTACHMENTS)
    assert any(item["slug"] == "business-plan" for item in manifest["attachments"])
    assert all(Path(item["html_path"]).is_file() for item in manifest["attachments"])

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        assert "OFFICIAL_ATTACHMENT_PACK_MANIFEST.json" in names
        assert "html/01-business-plan.html" in names
        assert "html/02-technical-solution.html" in names
        packed_manifest = json.loads(archive.read("OFFICIAL_ATTACHMENT_PACK_MANIFEST.json").decode("utf-8"))

    assert packed_manifest["zip_sha256"] is None
    assert "repo-controlled" in "\n".join(manifest["privacy_boundary"])


def test_build_official_attachment_pack_dry_run_writes_nothing(tmp_path: Path) -> None:
    module = _load_module()

    manifest = module.build_official_attachment_pack(output_dir=tmp_path, dry_run=True)

    assert manifest["ok"] is True
    assert manifest["dry_run"] is True
    assert manifest["zip_sha256"] is None
    assert list(tmp_path.iterdir()) == []


def test_official_attachment_pack_secret_scan_uses_repo_relative_path(tmp_path: Path) -> None:
    module = _load_module()
    secret = tmp_path / "docs" / "secret.md"
    secret.parent.mkdir(parents=True)
    secret.write_text("password = should-not-ship\n", encoding="utf-8")

    findings = module.detect_secret_findings([secret], repo_root=tmp_path)

    assert findings
    assert findings[0].startswith("docs/secret.md:")
