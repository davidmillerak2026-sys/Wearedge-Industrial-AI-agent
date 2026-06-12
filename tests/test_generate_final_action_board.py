from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_final_action_board.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_final_action_board", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_action_board_tracks_final_missing_and_wfc_fallbacks() -> None:
    module = _load_module()

    board = module.build_action_board()
    report = module.render_action_board(board)

    assert board["repo_ready"] is True
    assert board["foundation_ready"] is True
    assert "legal/company-info-filled.md" in board["final_missing"]
    assert "submission/02-submission-success.png" in board["final_missing"]
    assert any(item["status"] == "fallback" for item in board["wfc_replacement_items"])
    assert "final_edge_stdlib_http_gateway" in report
    expected_latency = (
        f"Edge HTTP p95/max latency: {board['latency_replay']['wall_latency_ms_p95']} / "
        f"{board['latency_replay']['wall_latency_ms_max']} ms"
    )
    assert expected_latency in report
    assert "promote_wfc_live_evidence.py" in report
    assert "verify_final_external_assets.py" in report
    assert "Do not remove `.fallback.json`" in report


def test_action_board_can_render_with_temp_missing_assets(tmp_path: Path) -> None:
    module = _load_module()

    board = module.build_action_board(assets_dir=tmp_path)
    report = module.render_action_board(board)

    assert board["final_ready"] is False
    assert len(board["human_final_items"]) == 6
    assert all(item["status"] == "missing" for item in board["human_final_items"])
    assert "| missing | `gongyi-mofang/04-dashboard-decision-view.png`" in report
    assert "Complete the six enterprise-owned legal/contact/submission evidence files." in report
