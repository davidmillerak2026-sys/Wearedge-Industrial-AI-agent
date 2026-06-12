from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "promote_wfc_live_evidence.py"
PNG_BYTES = b"\x89PNG\r\n\x1a\nlive-wfc-evidence"


def _load_module():
    spec = importlib.util.spec_from_file_location("promote_wfc_live_evidence", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_sources(source_dir: Path) -> None:
    source_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "04-dashboard-decision-view.png",
        "05-run-log-ok-true.png",
        "06-human-approval-gate.png",
    ):
        (source_dir / name).write_bytes(PNG_BYTES + name.encode("utf-8"))


def test_promote_wfc_live_evidence_replaces_fallback_sidecars(tmp_path: Path) -> None:
    module = _load_module()
    module.REPO_ROOT = tmp_path
    source_dir = tmp_path / "source"
    assets_dir = tmp_path / "gongyi-mofang"
    _write_sources(source_dir)
    assets_dir.mkdir(parents=True)
    for sidecar in (
        "04-dashboard-decision-view.fallback.json",
        "05-run-log-ok-true.fallback.json",
        "05-run-log-ok-true.fallback.html",
        "06-human-approval-gate.fallback.json",
    ):
        (assets_dir / sidecar).write_text("fallback", encoding="utf-8")

    manifest = module.promote_wfc_live_evidence(
        source_dir=source_dir,
        assets_dir=assets_dir,
        confirm_live_source=True,
        operator_note="unit test live source",
    )

    assert manifest["ok"] is True
    assert len(manifest["promoted"]) == 3
    assert not (assets_dir / "05-run-log-ok-true.fallback.json").exists()
    assert not (assets_dir / "05-run-log-ok-true.fallback.html").exists()
    assert (assets_dir / "04-dashboard-decision-view.png").read_bytes().startswith(PNG_BYTES)
    manifest_path = assets_dir / module.MANIFEST_NAME
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved["operator_confirmation"] == "live WFC screenshots were reviewed before promotion"
    assert saved["next_check"] == "python scripts/verify_live_evidence.py --stage platform --write-manifest"


def test_promote_wfc_live_evidence_requires_confirmation(tmp_path: Path) -> None:
    module = _load_module()
    module.REPO_ROOT = tmp_path
    source_dir = tmp_path / "source"
    _write_sources(source_dir)

    try:
        module.promote_wfc_live_evidence(
            source_dir=source_dir,
            assets_dir=tmp_path / "assets",
            confirm_live_source=False,
        )
    except ValueError as exc:
        assert "--confirm-live-source" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected confirmation to be required")


def test_promote_wfc_live_evidence_rejects_non_png_source(tmp_path: Path) -> None:
    module = _load_module()
    module.REPO_ROOT = tmp_path
    source_dir = tmp_path / "source"
    _write_sources(source_dir)
    (source_dir / "05-run-log-ok-true.png").write_text("not a png", encoding="utf-8")

    try:
        module.promote_wfc_live_evidence(
            source_dir=source_dir,
            assets_dir=tmp_path / "assets",
            confirm_live_source=True,
        )
    except ValueError as exc:
        assert "must be a PNG" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected non-PNG source to be rejected")


def test_promote_wfc_live_evidence_source_must_be_staging_folder(tmp_path: Path) -> None:
    module = _load_module()
    module.REPO_ROOT = tmp_path
    _write_sources(tmp_path)

    try:
        module.promote_wfc_live_evidence(
            source_dir=tmp_path,
            assets_dir=tmp_path,
            confirm_live_source=True,
        )
    except ValueError as exc:
        assert "staging folder" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected active evidence folder as source to be rejected")
