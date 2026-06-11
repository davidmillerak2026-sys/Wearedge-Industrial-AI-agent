from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "package_wfc_resource_block.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("package_wfc_resource_block", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_package_resource_block_writes_deterministic_zip_and_manifest(tmp_path: Path) -> None:
    module = _load_module()

    manifest = module.package_resource_block(output_dir=tmp_path)

    package_path = Path(manifest["package_path"])
    manifest_path = Path(manifest["manifest_path"])
    assert manifest["ok"] is True
    assert manifest["resource"]["name"] == "wearedge-agent-service"
    assert package_path.name == "wearedge-agent-service-0.1.0.zip"
    assert package_path.is_file()
    assert manifest_path.is_file()
    assert manifest["package_sha256"] == module.sha256_file(package_path)

    with zipfile.ZipFile(package_path) as archive:
        names = set(archive.namelist())
        assert "info.json" in names
        assert "README.md" in names
        assert "function-blocks/CallWearedgeDecisionApi.py" in names
        assert all(not name.endswith(".pyc") for name in names)
        info = json.loads(archive.read("info.json").decode("utf-8"))

    saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved_manifest["package_sha256"] == manifest["package_sha256"]
    assert info["displayName"] == "Wearedge Agent Service"


def test_package_resource_block_dry_run_does_not_write_zip(tmp_path: Path) -> None:
    module = _load_module()

    manifest = module.package_resource_block(output_dir=tmp_path, dry_run=True)

    assert manifest["ok"] is True
    assert manifest["dry_run"] is True
    assert manifest["package_sha256"] is None
    assert not Path(manifest["package_path"]).exists()
    assert list(tmp_path.iterdir()) == []


def test_package_resource_block_secret_scan_blocks_sensitive_text(tmp_path: Path) -> None:
    module = _load_module()
    block_root = tmp_path / "block"
    (block_root / "function-blocks").mkdir(parents=True)
    (block_root / "info.json").write_text(
        json.dumps(
            {
                "name": "demo",
                "displayName": "Demo",
                "type": "demo.resource",
                "version": "0.1.0",
            }
        ),
        encoding="utf-8",
    )
    (block_root / "README.md").write_text("safe", encoding="utf-8")
    (block_root / "function-blocks" / "CallWearedgeDecisionApi.py").write_text(
        "password='do-not-package'\n",
        encoding="utf-8",
    )

    try:
        module.package_resource_block(block_root=block_root, output_dir=tmp_path / "out")
    except ValueError as exc:
        assert "possible secret" in str(exc)
    else:
        raise AssertionError("secret scan should reject sensitive text")
