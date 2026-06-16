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

STRENGTHENING_TARGETS = (
    "gongyi-mofang/196-wfc-dynamic-writeback-output-ok-20260616.png",
    "gongyi-mofang/197-wfc-data-table-values-after-python-writeback-20260616.png",
    "gongyi-mofang/workflow-export/199-wfc-workflow-export-20260616.wfcw",
    "stable-endpoint/stable-endpoint-evidence.md",
    "xcelerator/45-xcelerator-api-backend-cloud-run-filled-20260616.png",
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
        "action": "Keep the reviewed live WFC run-log screenshot for the required gate; after pasting the updated live-edit package, recapture the run log.",
        "acceptance": "Shows WFC-native CallWearedgeDecisionApi.output JSON beginning with ok=true; preferred recapture also shows wfc_writeback.method=wfc_output1_to_update_data_table.",
    },
    "gongyi-mofang/06-human-approval-gate.png": {
        "owner": "WFC operator",
        "action": "Show HumanApprovalGate or approval-state panel for a high-risk recommendation.",
        "acceptance": "Shows pending/approved/rejected human confirmation; model is not directly controlling OT.",
    },
    "gongyi-mofang/196-wfc-dynamic-writeback-output-ok-20260616.png": {
        "owner": "WFC operator",
        "action": "After pasting the updated WFC Function Block code, capture the live output JSON.",
        "acceptance": "Shows ok=true plus wfc_writeback.method=wfc_output1_to_update_data_table and fields_ready values.",
    },
    "gongyi-mofang/197-wfc-data-table-values-after-python-writeback-20260616.png": {
        "owner": "WFC operator",
        "action": "If WFC can export readable JSON, run binding analysis; otherwise manually connect output1 to UpdateDataTable, then capture the native WFC data table after DEBUG.",
        "acceptance": "Shows selected_direction, approval_status, recommended_action, and latency_ms values matching the Python output fields_ready object.",
    },
    "gongyi-mofang/workflow-export/199-wfc-workflow-export-20260616.wfcw": {
        "owner": "WFC operator",
        "action": "Keep the live WFC workflow and deployment-data exports archived under ignored evidence.",
        "acceptance": "Shows project assets can be exported/archived; .wfcw/.wfcd are proprietary binary exports and do not replace JSON binding analysis or live data-table proof.",
    },
    "stable-endpoint/stable-endpoint-evidence.md": {
        "owner": "Platform operator",
        "action": "Cloud Run stable endpoint is deployed; rerun the stable endpoint verifier before final upload.",
        "acceptance": "Shows healthz, runtime-profile, and workflow-canvas decision checks passing on a non-temporary HTTPS host.",
    },
    "xcelerator/45-xcelerator-api-backend-cloud-run-filled-20260616.png": {
        "owner": "Platform operator",
        "action": "Keep the Xcelerator API service backend replacement screenshot and continue selector/path binding.",
        "acceptance": "Shows Cloud Run URL in the live Xcelerator draft; proxy selector still needs verification until it returns Wearedge ok=true.",
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
    strengthening_items = [_optional_action_row(path, assets_dir) for path in STRENGTHENING_TARGETS]
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
        "strengthening_items": strengthening_items,
        "human_final_items": human_items,
        "next_actions": _next_actions(wfc_items, human_items, strengthening_items),
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


def _optional_action_row(path: str, assets_dir: Path) -> dict[str, Any]:
    detail = ACTION_DETAIL[path]
    full_path = assets_dir / path
    present = _optional_target_ready(path, full_path, assets_dir)
    status = "present" if present else "optional_pending"
    if path == "stable-endpoint/stable-endpoint-evidence.md" and full_path.exists() and not present:
        status = "needs_stable_endpoint"
    return {
        "path": path,
        "status": status,
        "present": present,
        "fallback": False,
        "title": path,
        "owner": detail["owner"],
        "action": detail["action"],
        "acceptance": detail["acceptance"],
    }


def _optional_target_ready(path: str, full_path: Path, assets_dir: Path) -> bool:
    if not full_path.exists() or not full_path.is_file() or full_path.stat().st_size == 0:
        return False
    if path == "gongyi-mofang/workflow-export/199-wfc-workflow-export-20260616.wfcw":
        deployment_export = assets_dir / "gongyi-mofang" / "workflow-export" / "200-wfc-deployment-data-export-20260616.wfcd"
        return deployment_export.exists() and deployment_export.is_file() and deployment_export.stat().st_size > 0
    if path != "stable-endpoint/stable-endpoint-evidence.md":
        return True
    evidence_json = assets_dir / "stable-endpoint" / "stable-endpoint-evidence.json"
    if not evidence_json.exists():
        return False
    try:
        data = json.loads(evidence_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(data.get("ready")) and (data.get("endpoint") or {}).get("evidence_tier") == "stable_https"


def _next_actions(
    wfc_items: list[dict[str, Any]],
    human_items: list[dict[str, Any]],
    strengthening_items: list[dict[str, Any]],
) -> list[str]:
    actions: list[str] = []
    fallback_paths = [item["path"] for item in wfc_items if item["fallback"]]
    missing_wfc_paths = [item["path"] for item in wfc_items if not item["present"]]
    optional_pending = [item["path"] for item in strengthening_items if not item["present"]]
    if fallback_paths:
        actions.append(
            "Replace remaining WFC fallback screenshots with reviewed live WFC screenshots: "
            + ", ".join(fallback_paths)
            + "."
        )
    elif missing_wfc_paths:
        actions.append(
            "Capture missing WFC live evidence screenshots: "
            + ", ".join(missing_wfc_paths)
            + "."
        )
    else:
        actions.append(
            "Finish the high-value WFC writeback proof: if WFC can provide readable JSON export, run binding analysis; otherwise manually connect `输出1 -> 更新数据表.1`, then capture `gongyi-mofang/197-wfc-data-table-values-after-python-writeback-20260616.png`."
        )
    stable_endpoint_item = next(
        (item for item in strengthening_items if item["path"] == "stable-endpoint/stable-endpoint-evidence.md"),
        None,
    )
    if stable_endpoint_item and not stable_endpoint_item["present"]:
        actions.append(
            "Choose a stable endpoint route from `deploy/stable-endpoint/` and run `python scripts/verify_stable_wearedge_endpoint.py --base-url https://<stable-host> --write-evidence`; local/temporary tunnel preflight is not final evidence."
        )
    elif stable_endpoint_item and stable_endpoint_item["present"]:
        actions.append(
            "Keep the Cloud Run stable endpoint evidence current with `python scripts/verify_stable_wearedge_endpoint.py --base-url https://wearedge-agent-service-863888677331.asia-east1.run.app --write-evidence` before final upload."
        )
    remaining_optional = [
        path
        for path in optional_pending
        if path
        not in {
            "gongyi-mofang/197-wfc-data-table-values-after-python-writeback-20260616.png",
            "stable-endpoint/stable-endpoint-evidence.md",
        }
    ]
    if remaining_optional:
        actions.append(
            "Upgrade high-value proof when platform time is available: "
            + ", ".join(remaining_optional)
            + "."
        )
    actions.append(
        "Finish Xcelerator API selector/path binding: backend has been filled with Cloud Run `https://wearedge-agent-service-863888677331.asia-east1.run.app`, but the tenant proxy currently returns code `-107`; use `python scripts/verify_xcelerator_proxy.py --write-evidence` after each platform change until proxy returns Wearedge `ok=true`."
    )
    if any(item["status"] == "missing" for item in human_items):
        actions.append("Complete the six enterprise-owned legal/contact/submission evidence files.")
    if fallback_paths or missing_wfc_paths:
        actions.extend(
            [
                "Run `python scripts/prepare_wfc_live_review_sidecars.py --target dashboard --target human-approval --source-url \"https://wfc.bd-iiot.com/project/cmq6lbb9x00bx1l6pxll7voae\" --operator-note \"reviewed live WFC screenshots\"` after placing real WFC 04/06 PNGs in `submission-assets/live-evidence/gongyi-mofang-live-source/`.",
                "Run `python scripts/promote_wfc_live_evidence.py --confirm-live-source --require-review-sidecars --operator-note \"reviewed live WFC screenshots\"` only after real WFC screenshots and review sidecars are in staging.",
            ]
        )
    actions.extend(
        [
            "Run `python scripts/verify_final_external_assets.py --write-report` after signed PDFs, final screenshots, video, and live WFC evidence are in place.",
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
            "## High-Value Strengthening",
            "",
            "These items improve finals-readiness and credibility, but they do not change the six human-owned final blockers.",
            "",
            "| Status | Target | Owner | Action | Acceptance |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in board["strengthening_items"]:
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

    commands = [
        "python scripts/prepare_final_human_action_pack.py --json",
    ]
    if any(item["status"] != "present" for item in board["wfc_replacement_items"]):
        commands.extend(
            [
                "python scripts/prepare_wfc_live_review_sidecars.py --target dashboard --target human-approval --source-url \"https://wfc.bd-iiot.com/project/cmq6lbb9x00bx1l6pxll7voae\" --operator-note \"reviewed live WFC screenshots\"",
                "python scripts/promote_wfc_live_evidence.py --confirm-live-source --require-review-sidecars --operator-note \"reviewed live WFC screenshots\"",
            ]
        )
    commands.extend(
        [
            "python scripts/verify_final_external_assets.py --write-report",
            "python scripts/run_final_readiness_pipeline.py --json",
            "python scripts/verify_live_evidence.py --stage final --write-manifest",
            "python scripts/verify_submission_package.py --write-manifest",
        ]
    )

    lines.extend(
        [
            "",
            "## Command Sequence",
            "",
            "```powershell",
            *commands,
            "```",
            "",
            "## Boundary",
            "",
            "- Do not commit files under `submission-assets/live-evidence/`.",
            "- Current WFC replacement targets should have no fallback metadata; preserve reviewed live evidence sidecars and recapture from WFC when the updated Function Block is promoted into the platform.",
            "- WFC dynamic data-table writeback is still a high-value strengthening item; stable HTTPS endpoint evidence is now captured via Cloud Run, and Xcelerator backend replacement is partially evidenced. Xcelerator live debug screenshots remain pending because the tenant proxy currently returns selector error code `-107`.",
            "- For the next manual capture session, use `docs/submission/live-enhancement-capture-runbook-20260616.md`.",
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
