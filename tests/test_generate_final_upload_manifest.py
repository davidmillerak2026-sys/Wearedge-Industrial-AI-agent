from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_final_upload_manifest.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_final_upload_manifest", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_dummy_outputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    bundle = tmp_path / "bundle.zip"
    bundle.write_bytes(b"PK\x03\x04repo bundle")
    bundle_manifest = tmp_path / "bundle.bundle-manifest.json"
    bundle_manifest.write_text(
        json.dumps({"bundle_sha256": "abc123", "file_count": 7}),
        encoding="utf-8",
    )
    wfc_package = tmp_path / "wearedge-agent-service-0.1.0.zip"
    wfc_package.write_bytes(b"PK\x03\x04wfc")
    official_pack = tmp_path / "wearedge-official-attachment-pack.zip"
    official_pack.write_bytes(b"PK\x03\x04official")
    return bundle, bundle_manifest, wfc_package, official_pack


def test_final_upload_manifest_builds_queue_without_private_values(tmp_path: Path) -> None:
    module = _load_module()
    bundle, bundle_manifest, wfc_package, official_pack = _write_dummy_outputs(tmp_path)

    manifest = module.build_final_upload_manifest(
        assets_dir=tmp_path / "live-evidence",
        submission_bundle=bundle,
        submission_bundle_manifest=bundle_manifest,
        wfc_package=wfc_package,
        official_attachment_pack=official_pack,
    )

    assert manifest["repo_ready"] is True
    assert manifest["official_submission_ready"] is False
    assert manifest["bundle"]["present"] is True
    assert manifest["bundle"]["sha256"] == "abc123"
    assert manifest["bundle"]["file_count"] == 7
    assert manifest["wfc_package"]["present"] is True
    assert manifest["official_attachment_pack"]["present"] is True
    assert any(item["title"] == "Business plan" for item in manifest["items"])
    assert any(item["title"] == "Repo-controlled submission bundle" for item in manifest["items"])
    assert any(item["title"] == "Official attachment pack" for item in manifest["items"])
    assert any(item["status"] in {"blocked", "missing"} for item in manifest["items"])
    assert any(blocker["path"] == "legal/company-info-filled.md" for blocker in manifest["blocking_items"])
    assert "enterprise identifiers" in "\n".join(manifest["privacy_boundary"])

    sources = [item["source"] for item in manifest["items"]]
    assert "submission-assets/live-evidence/submission-bundle/wearedge-industrial-ai-agent-repo-controlled-submission-bundle.zip" in sources
    assert "submission-assets/live-evidence/official-attachment-pack/wearedge-official-attachment-pack.zip" in sources
    assert "submission-assets/live-evidence/gongyi-mofang/wfc-resource-package/wearedge-agent-service-0.1.0.zip" in sources


def test_render_upload_manifest_includes_gate_queue_and_checks(tmp_path: Path) -> None:
    module = _load_module()
    bundle, bundle_manifest, wfc_package, official_pack = _write_dummy_outputs(tmp_path)
    manifest = module.build_final_upload_manifest(
        assets_dir=tmp_path / "live-evidence",
        submission_bundle=bundle,
        submission_bundle_manifest=bundle_manifest,
        wfc_package=wfc_package,
        official_attachment_pack=official_pack,
    )

    text = module.render_upload_manifest(manifest)

    assert "# Final Upload Manifest" in text
    assert "Official submission ready: False" in text
    assert "| Priority | Status | Attachment | Source | Audience | Action |" in text
    assert "`legal/company-info-filled.md`" in text
    assert "python scripts/generate_final_upload_manifest.py --write" in text


def test_final_upload_manifest_cli_writes_markdown(tmp_path: Path) -> None:
    module = _load_module()
    bundle, bundle_manifest, wfc_package, official_pack = _write_dummy_outputs(tmp_path)
    output = tmp_path / "final-upload-manifest.md"

    exit_code = module.main(
        [
            "--assets-dir",
            str(tmp_path / "live-evidence"),
            "--submission-bundle",
            str(bundle),
            "--submission-bundle-manifest",
            str(bundle_manifest),
            "--wfc-package",
            str(wfc_package),
            "--official-attachment-pack",
            str(official_pack),
            "--output",
            str(output),
            "--write",
        ]
    )

    assert exit_code == 0
    assert output.is_file()
    assert "Repo-controlled submission bundle" in output.read_text(encoding="utf-8")
    assert "Official attachment pack" in output.read_text(encoding="utf-8")
