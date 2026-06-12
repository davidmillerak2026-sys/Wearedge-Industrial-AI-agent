from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from verify_finals_foundation import verify_finals_foundation
from verify_live_evidence import DEFAULT_ASSETS_DIR, verify_live_evidence
from verify_submission_package import verify_package


DEFAULT_OUTPUT = REPO_ROOT / "docs" / "submission" / "final-action-board.md"

WFC_REPLACEMENT_TARGETS = (
    "gongyi-mofang/04-dashboard-decision-view.png",
    "gongyi-mofang/05-run-log-ok-true.png",
    "gongyi-mofang/06-human-approval-gate.png",
)

HUMAN_FINAL_TARGETS = (
    "legal/company-info-filled.md",
    "legal/ip-and-no-dispute-signed.pdf",
    "legal/no-adverse-record-signed.pdf",
    "legal/submission-contact-confirmation.md",
    "submission/01-registration-form-filled.png",
    "submission/02-submission-success.png",
)

ACTION_DETAIL = {
    "gongyi-mofang/04-dashboard-decision-view.png": {
        "owner": "WFC operator",
        "action": "Create or preview the real WFC Dashboard/ui-builder view.",
        "acceptance": "Shows Wearedge metric cards, decision path, approval items, and workflow state from live WFC context.",
    },
    "gongyi-mofang/05-run-log-ok-true.png": {
        "owner": "WFC operator",
        "action": "Run/debug the workflow and capture log-manager or run panel.",
        "acceptance": "Shows ok=true, wearedge_decision_ok=True, latency, function-block output, or successful table writeback.",
    },
    "gongyi-mofang/06-human-approval-gate.png": {
        "owner": "WFC operator",
        "action": "Show HumanApprovalGate or approval-state panel for a high-risk recommendation.",
        "acceptance": "Shows pending/approved/rejected human confirmation; model is not directly controlling OT.",
    },
    "legal/company-info-filled.md": {
        "owner": "Enterprise owner",
        "action": "Copy from company-info-filled.template.md and fill final company/contact/team fields.",
        "acceptance": "Enterprise name, unified social credit code, contacts, roles, eligibility, and no-adverse-record confirmation are filled.",
    },
    "legal/ip-and-no-dispute-signed.pdf": {
        "owner": "Enterprise owner",
        "action": "Sign/stamp the IP and no-dispute statement template and export PDF.",
        "acceptance": "Signed or stamped PDF confirms lawful IP ownership/no ownership dispute and open-source/model boundary.",
    },
    "legal/no-adverse-record-signed.pdf": {
        "owner": "Enterprise owner",
        "action": "Sign/stamp the no-adverse-record statement and export PDF.",
        "acceptance": "Signed or stamped PDF confirms enterprise eligibility and truthful simulated/offline evidence labeling.",
    },
    "legal/submission-contact-confirmation.md": {
        "owner": "Final submitter",
        "action": "Fill primary/backup contact and account-owner confirmations.",
        "acceptance": "Primary and backup contacts are complete; Xcelerator/WFC/final submitter ownership is confirmed.",
    },
    "submission/01-registration-form-filled.png": {
        "owner": "Final submitter",
        "action": "Capture filled registration form before final submit.",
        "acceptance": "Shows project name and filled fields while hiding certificate numbers and private contact details for reuse.",
    },
    "submission/02-submission-success.png": {
        "owner": "Final submitter",
        "action": "Capture official submitted/success status after final submit.",
        "acceptance": "Shows submitted/success status, project name or submission id if visible, with private fields hidden for reuse.",
    },
}


def build_action_board(*, assets_dir: Path = DEFAULT_ASSETS_DIR, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    assets_dir = _resolve_path(assets_dir, repo_root)
    live = verify_live_evidence(assets_dir, "final")
    foundation = verify_finals_foundation(assets_dir=assets_dir, repo_root=repo_root)
    repo = verify_package(repo_root)
    item_map = {item["path"]: item for item in live["items"]}
    wfc_items = [_action_row(path, item_map) for path in WFC_REPLACEMENT_TARGETS]
    human_items = [_action_row(path, item_map) for path in HUMAN_FINAL_TARGETS]
    return {
        "ok": bool(repo["repo_ready"]) and bool(foundation["foundation_ready"]),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "assets_dir": str(assets_dir),
        "repo_ready": bool(repo["repo_ready"]),
        "foundation_ready": bool(foundation["foundation_ready"]),
        "finals_ready": bool(foundation["finals_ready"]),
        "final_ready": bool(live["ready"]),
        "final_missing": list(live["missing"]),
        "fallback_warnings": list(live["warnings"]),
        "latency_replay": foundation["latency_replay"],
        "priority_gaps": list(foundation["priority_gaps"]),
        "wfc_replacement_items": wfc_items,
        "human_final_items": human_items,
        "next_actions": _next_actions(wfc_items, human_items),
    }


def _action_row(path: str, item_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    item = item_map.get(path, {})
    detail = ACTION_DETAIL[path]
    present = bool(item.get("present"))
    fallback = bool(item.get("fallback"))
    status = "fallback" if fallback else ("present" if present else "missing")
    return {
        "path": path,
        "status": status,
        "present": present,
        "fallback": fallback,
        "title": item.get("title", path),
        "owner": detail["owner"],
        "action": detail["action"],
        "acceptance": detail["acceptance"],
    }


def _next_actions(wfc_items: list[dict[str, Any]], human_items: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []
    if any(item["fallback"] for item in wfc_items):
        actions.append("Replace WFC 04/05/06 fallback screenshots with reviewed live WFC screenshots.")
    if any(item["status"] == "missing" for item in human_items):
        actions.append("Complete the six enterprise-owned legal/contact/submission evidence files.")
    actions.extend(
        [
            "Run `python scripts/promote_wfc_live_evidence.py --confirm-live-source --require-review-sidecars --operator-note \"reviewed live WFC screenshots\"` only after real WFC screenshots and review sidecars are in staging.",
            "Run `python scripts/verify_final_external_assets.py --write-report` after signed PDFs, final screenshots, video, and live WFC replacements are in place.",
            "Run `python scripts/run_final_readiness_pipeline.py --json` and `python scripts/verify_live_evidence.py --stage final --write-manifest` before final upload.",
        ]
    )
    return actions


def render_action_board(board: dict[str, Any]) -> str:
    latency = board["latency_replay"]
    wall = latency.get("wall_latency_ms", {})
    p95_latency = latency.get("wall_latency_ms_p95", wall.get("p95", 0))
    max_latency = latency.get("wall_latency_ms_max", wall.get("max", 0))
    lines = [
        "# Final Action Board",
        "",
        f"Updated: {board['generated_at']}",
        "",
        "## Current Gate",
        "",
        f"- Repository ready: {board['repo_ready']}",
        f"- Finals foundation ready: {board['foundation_ready']}",
        f"- Finals ready: {board['finals_ready']}",
        f"- Final external evidence ready: {board['final_ready']}",
        f"- Final missing files: {len(board['final_missing'])}",
        f"- Fallback warnings: {len(board['fallback_warnings'])}",
        f"- Edge latency evidence tier: {latency.get('evidence_tier', 'unknown')}",
        f"- Edge HTTP samples: {latency.get('sample_count', 0)}",
        f"- Edge HTTP p95/max latency: {p95_latency} / {max_latency} ms",
        "",
        "## Do Next",
        "",
    ]
    lines.extend(f"{idx}. {action}" for idx, action in enumerate(board["next_actions"], start=1))

    lines.extend(
        [
            "",
            "## WFC Live Replacement",
            "",
            "| Status | Target | Owner | Action | Acceptance |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in board["wfc_replacement_items"]:
        lines.append(
            f"| {item['status']} | `{item['path']}` | {item['owner']} | "
            f"{item['action']} | {item['acceptance']} |"
        )

    lines.extend(
        [
            "",
            "## Human-Owned Final Files",
            "",
            "| Status | Target | Owner | Action | Acceptance |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in board["human_final_items"]:
        lines.append(
            f"| {item['status']} | `{item['path']}` | {item['owner']} | "
            f"{item['action']} | {item['acceptance']} |"
        )

    lines.extend(
        [
            "",
            "## Command Sequence",
            "",
            "```powershell",
            "python scripts/prepare_final_human_action_pack.py --json",
            "python scripts/promote_wfc_live_evidence.py --confirm-live-source --require-review-sidecars --operator-note \"reviewed live WFC screenshots\"",
            "python scripts/verify_final_external_assets.py --write-report",
            "python scripts/run_final_readiness_pipeline.py --json",
            "python scripts/verify_live_evidence.py --stage final --write-manifest",
            "python scripts/verify_submission_package.py --write-manifest",
            "```",
            "",
            "## Boundary",
            "",
            "- Do not commit files under `submission-assets/live-evidence/`.",
            "- Do not remove `.fallback.json` metadata until the corresponding screenshot is real WFC live evidence.",
            "- For final promotion, keep a `.review.json` sidecar beside each staged WFC screenshot and use `--require-review-sidecars`.",
            "- Do not describe local smoke tests, generated dashboards, or fallback images as live WFC `ok=true` execution.",
            "- Signed legal files, company identifiers, private contacts, and final registration screenshots remain human-owned external evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def _resolve_path(path: Path, repo_root: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else repo_root / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the final Wearedge action board from current verifiers.")
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    board = build_action_board(assets_dir=args.assets_dir)
    output = _resolve_path(args.output, REPO_ROOT)
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_action_board(board), encoding="utf-8")
        board["output_path"] = str(output)

    print(json.dumps(board, ensure_ascii=False, indent=2) if args.json else render_action_board(board))
    return 0 if board["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
