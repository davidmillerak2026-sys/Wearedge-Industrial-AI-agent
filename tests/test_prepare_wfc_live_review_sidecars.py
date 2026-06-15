from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "prepare_wfc_live_review_sidecars.py"
PROMOTE_SCRIPT_PATH = REPO_ROOT / "scripts" / "promote_wfc_live_evidence.py"
PNG_BYTES = b"\x89PNG\r\n\x1a\nlive-wfc-dashboard"


def _load_module():
    promote_spec = importlib.util.spec_from_file_location("promote_wfc_live_evidence", PROMOTE_SCRIPT_PATH)
    assert promote_spec is not None
    assert promote_spec.loader is not None
    promote_module = importlib.util.module_from_spec(promote_spec)
    sys.modules[promote_spec.name] = promote_module
    promote_spec.loader.exec_module(promote_module)

    spec = importlib.util.spec_from_file_location("prepare_wfc_live_review_sidecars", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_prepare_review_sidecars_writes_review_for_existing_png(tmp_path: Path) -> None:
    module = _load_module()
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    screenshot = source_dir / "04-dashboard-decision-view.png"
    screenshot.write_bytes(PNG_BYTES)

    selected = module.resolve_targets(["dashboard"])
    result = module.prepare_review_sidecars(
        source_dir=source_dir,
        selected_targets=selected,
        source_url="https://wfc.bd-iiot.com/project/cmq6lbb9x00bx1l6pxll7voae",
        captured_at_utc="2026-06-15T08:00:00Z",
        reviewer_role="WFC operator",
        operator_note="unit test",
    )

    assert result["ok"] is True
    review = json.loads((source_dir / "04-dashboard-decision-view.review.json").read_text(encoding="utf-8"))
    assert review["live_wfc_source"] is True
    assert review["source_url"].startswith("https://wfc.bd-iiot.com/")
    assert set(review["observed_signals"]) >= {
        "metric_cards",
        "decision_path",
        "approval_items",
        "workflow_state",
    }


def test_prepare_review_sidecars_rejects_missing_screenshot(tmp_path: Path) -> None:
    module = _load_module()
    selected = module.resolve_targets(["human-approval"])

    try:
        module.prepare_review_sidecars(
            source_dir=tmp_path / "source",
            selected_targets=selected,
            source_url="https://wfc.bd-iiot.com/project/cmq6lbb9x00bx1l6pxll7voae",
        )
    except FileNotFoundError as exc:
        assert "missing live WFC screenshot" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected missing screenshot to be rejected")


def test_prepare_review_sidecars_template_only_is_not_promotable(tmp_path: Path) -> None:
    module = _load_module()
    selected = module.resolve_targets(["06"])
    result = module.prepare_review_sidecars(
        source_dir=tmp_path / "source",
        selected_targets=selected,
        source_url="https://wfc.bd-iiot.com/project/cmq6lbb9x00bx1l6pxll7voae",
        captured_at_utc="2026-06-15T08:00:00Z",
        template_only=True,
    )

    template_path = tmp_path / "source" / "06-human-approval-gate.review.template.json"
    template = json.loads(template_path.read_text(encoding="utf-8"))
    assert result["template_only"] is True
    assert template["live_wfc_source"] is False
    assert not (tmp_path / "source" / "06-human-approval-gate.review.json").exists()


def test_prepare_review_sidecars_rejects_non_wfc_source_url(tmp_path: Path) -> None:
    module = _load_module()
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "06-human-approval-gate.png").write_bytes(PNG_BYTES)
    selected = module.resolve_targets(["06"])

    try:
        module.prepare_review_sidecars(
            source_dir=source_dir,
            selected_targets=selected,
            source_url="https://example.com/not-wfc",
            captured_at_utc="2026-06-15T08:00:00Z",
        )
    except ValueError as exc:
        assert "source_url" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected non-WFC source URL to be rejected")
