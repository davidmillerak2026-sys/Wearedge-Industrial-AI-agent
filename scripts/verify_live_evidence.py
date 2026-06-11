from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS_DIR = REPO_ROOT / "submission-assets" / "live-evidence"
DEFAULT_STAGE = "platform"


@dataclass(frozen=True)
class EvidenceItem:
    group: str
    path: str
    title: str
    stage: str
    note: str


EXPECTED_ITEMS: tuple[EvidenceItem, ...] = (
    EvidenceItem(
        "xcelerator",
        "xcelerator/01-tenant-or-workspace.png",
        "Xcelerator tenant or workspace",
        "platform",
        "Hide personal email, tenant ids, and tokens.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/05-app-group-created.png",
        "Wearedge app group",
        "platform",
        "Show the Wearedge app group and Register App entry.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/07-app-detail-created-redacted-top.png",
        "Wearedge app draft",
        "platform",
        "Show the Wearedge app draft without capturing AppID or AppSecret.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/10-openapi-json-import-filled.png",
        "OpenAPI JSON import",
        "platform",
        "Show the Wearedge OpenAPI JSON/YAML import populated from the repository spec.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/11-openapi-parse-preview.png",
        "OpenAPI parse preview",
        "platform",
        "Show /healthz, /v1/edge/runtime-profile, and /v1/workflow-canvas/decision in the preview.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/16-openapi-four-apis-imported.png",
        "OpenAPI four interfaces imported",
        "platform",
        "Show /healthz, /v1/edge/runtime-profile, /v1/industrial-agent/solution-profile, and /v1/workflow-canvas/decision in the API service interface list.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/15-api-service-saved-unpublished-list.png",
        "Wearedge API service saved as unpublished",
        "platform",
        "Show service status unpublished, tenant visibility, and interface count 4.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/38-xcelerator-client-app-home-current.png",
        "Current Xcelerator application home",
        "platform",
        "Show Wearedge app group, app card, and tenant-internal application evidence from the current console session.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/39-xcelerator-api-detail-current-draft.png",
        "Current Xcelerator API detail draft",
        "platform",
        "Show the current API detail page with unpublished status, owning app, tenant visibility, server host, and /v1 path.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/40-xcelerator-api-interface-list-current-four-endpoints.png",
        "Current Xcelerator API interface list",
        "platform",
        "Show the four tenant-internal, not-enabled endpoints in the current API service draft.",
    ),
    EvidenceItem(
        "xcelerator",
        "xcelerator/04-runtime-profile-api-test.png",
        "Runtime profile API test",
        "platform",
        "Show ok=true, workflow_canvas_ready=true, and model_direct_ot_control=false.",
    ),
    EvidenceItem(
        "gongyi-mofang",
        "gongyi-mofang/00-wfc-projects-authenticated.png",
        "Workflow Canvas authenticated projects page",
        "platform",
        "Show the logged-in Gongyi Mofang projects page and New Blank Project entry.",
    ),
    EvidenceItem(
        "gongyi-mofang",
        "gongyi-mofang/01-resource-block-wearedge-agent-service.png",
        "Workflow Canvas resource configuration",
        "platform",
        "Show Generic IPC/SPIDR configuration or Wearedge Agent Service custom-resource parameters; final evidence should include agentHost, agentPort, deploymentMode, plantId, and lineId.",
    ),
    EvidenceItem(
        "gongyi-mofang",
        "gongyi-mofang/02-python-function-block-call-api.png",
        "CallWearedgeDecisionApi function block",
        "platform",
        "Show POST to /v1/workflow-canvas/decision.",
    ),
    EvidenceItem(
        "gongyi-mofang",
        "gongyi-mofang/03-global-data-table-decision-fields.png",
        "Global data table decision fields",
        "platform",
        "Show primary direction, priority, action, evidence, metrics, owner, residual risk, and approval status.",
    ),
    EvidenceItem(
        "gongyi-mofang",
        "gongyi-mofang/04-dashboard-decision-view.png",
        "Workflow Canvas dashboard",
        "platform",
        "Show metric cards, decision path, approval items, and workflow state.",
    ),
    EvidenceItem(
        "gongyi-mofang",
        "gongyi-mofang/05-run-log-ok-true.png",
        "Workflow run log",
        "platform",
        "Show ok=true, latency, function blocks, or successful table writeback.",
    ),
    EvidenceItem(
        "gongyi-mofang",
        "gongyi-mofang/06-human-approval-gate.png",
        "HumanApprovalGate",
        "platform",
        "Show that high-risk OT actions require human confirmation.",
    ),
    EvidenceItem(
        "edge-runtime",
        "edge-runtime/01-healthz.png",
        "Edge service health",
        "platform",
        "Show /healthz or the local FastAPI service running.",
    ),
    EvidenceItem(
        "edge-runtime",
        "edge-runtime/02-runtime-profile.png",
        "Edge runtime profile",
        "platform",
        "Show Jetson/IPC/local server deployment and safety boundary.",
    ),
    EvidenceItem(
        "edge-runtime",
        "edge-runtime/03-workflow-canvas-decision-smoke.png",
        "Workflow Canvas decision smoke",
        "platform",
        "Show scripts/smoke_workflow_canvas_decision.py output.",
    ),
    EvidenceItem(
        "edge-runtime",
        "edge-runtime/04-jetson-ipc-local-node.png",
        "Edge node proof",
        "platform",
        "Show Jetson, IPC, local industrial PC, or plant edge server runtime proof.",
    ),
    EvidenceItem(
        "edge-runtime",
        "edge-runtime/05-solution-profile.png",
        "Industrial-agent solution profile",
        "platform",
        "Show the explicit industrial problem, model role, KPI decision matrix, and HumanApprovalGate boundary.",
    ),
    EvidenceItem(
        "video",
        "video/wearedge-enterprise-demo-3-5min.mp4",
        "Final enterprise demo video",
        "final",
        "Use a 3-5 minute version for the first-round submission.",
    ),
    EvidenceItem(
        "video",
        "video/wearedge-enterprise-demo-script-final.md",
        "Final demo narration",
        "final",
        "Keep the final script aligned with the recorded video.",
    ),
    EvidenceItem(
        "legal",
        "legal/company-info-filled.md",
        "Filled company and contact information",
        "final",
        "Do not commit sensitive final values to Git.",
    ),
    EvidenceItem(
        "legal",
        "legal/ip-and-no-dispute-signed.pdf",
        "Signed IP and no-dispute statement",
        "final",
        "Signed or stamped by the enterprise owner.",
    ),
    EvidenceItem(
        "legal",
        "legal/no-adverse-record-signed.pdf",
        "Signed no-adverse-record statement",
        "final",
        "Signed or stamped by the enterprise owner.",
    ),
    EvidenceItem(
        "legal",
        "legal/submission-contact-confirmation.md",
        "Submission contact confirmation",
        "final",
        "Confirm primary and backup contacts.",
    ),
    EvidenceItem(
        "submission",
        "submission/01-registration-form-filled.png",
        "Filled registration form",
        "final",
        "Hide sensitive certificate numbers before reuse.",
    ),
    EvidenceItem(
        "submission",
        "submission/02-submission-success.png",
        "Submission success status",
        "final",
        "Final proof for the 2026-07-08 internal target.",
    ),
)


STAGE_ORDER = {"platform": 1, "final": 2}


def verify_live_evidence(assets_dir: Path = DEFAULT_ASSETS_DIR, stage: str = DEFAULT_STAGE) -> dict[str, Any]:
    if stage not in STAGE_ORDER:
        raise ValueError(f"unknown stage: {stage}")

    selected = [item for item in EXPECTED_ITEMS if STAGE_ORDER[item.stage] <= STAGE_ORDER[stage]]
    items = []
    missing = []
    warnings = []
    for item in selected:
        path = assets_dir / item.path
        present = path.exists() and path.is_file() and path.stat().st_size > 0
        fallback_meta = path.with_suffix(".fallback.json")
        fallback = present and fallback_meta.exists() and fallback_meta.is_file()
        if not present:
            missing.append(item.path)
        if fallback:
            warnings.append(
                {
                    "path": item.path,
                    "fallback_metadata": str(fallback_meta.relative_to(assets_dir)),
                    "warning": "Fallback evidence is present; do not describe it as live platform proof.",
                }
            )
        items.append(
            {
                "group": item.group,
                "path": item.path,
                "title": item.title,
                "stage": item.stage,
                "present": present,
                "fallback": fallback,
                "note": item.note,
            }
        )

    groups: dict[str, dict[str, Any]] = {}
    for item in items:
        group = groups.setdefault(item["group"], {"present": 0, "missing": 0, "items": []})
        group["items"].append(item)
        if item["present"]:
            group["present"] += 1
        else:
            group["missing"] += 1

    return {
        "assets_dir": str(assets_dir),
        "stage": stage,
        "ready": not missing,
        "expected_count": len(items),
        "present_count": sum(1 for item in items if item["present"]),
        "missing_count": len(missing),
        "missing": missing,
        "warnings": warnings,
        "groups": groups,
        "items": items,
    }


def initialize_layout(assets_dir: Path = DEFAULT_ASSETS_DIR) -> list[str]:
    groups = sorted({item.group for item in EXPECTED_ITEMS})
    created = []
    for group in groups:
        group_dir = assets_dir / group
        group_dir.mkdir(parents=True, exist_ok=True)
        created.append(str(group_dir))

    readme = assets_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "\n".join(
                [
                    "# Wearedge Live Evidence Assets",
                    "",
                    "This directory is ignored by Git. Store platform screenshots, videos, and signed files here.",
                    "Run `python scripts/verify_live_evidence.py --stage final --write-manifest` before submission.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        created.append(str(readme))
    return created


def render_manifest(result: dict[str, Any]) -> str:
    lines = [
        "# Live Evidence Manifest",
        "",
        f"- Assets dir: `{result['assets_dir']}`",
        f"- Stage: `{result['stage']}`",
        f"- Ready: {result['ready']}",
        f"- Present: {result['present_count']} / {result['expected_count']}",
        "",
        "## Group Status",
        "",
        "| Group | Present | Missing |",
        "| --- | ---: | ---: |",
    ]
    for group_name in sorted(result["groups"]):
        group = result["groups"][group_name]
        lines.append(f"| {group_name} | {group['present']} | {group['missing']} |")

    lines.extend(["", "## Missing Items", ""])
    if result["missing"]:
        for item in result["missing"]:
            lines.append(f"- `{item}`")
        if result["stage"] == "final":
            lines.extend(
                [
                    "",
                    "Generate ignored human-action templates before collecting the final enterprise-owned files:",
                    "",
                    "```powershell",
                    "python scripts/prepare_final_human_action_pack.py --json",
                    "```",
                ]
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Warnings", ""])
    if result["warnings"]:
        for warning in result["warnings"]:
            lines.append(
                f"- `{warning['path']}` uses fallback metadata "
                f"`{warning['fallback_metadata']}`. {warning['warning']}"
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Item Detail", "", "| Status | Path | Title | Note |", "| --- | --- | --- | --- |"])
    for item in result["items"]:
        status = "fallback" if item.get("fallback") else ("present" if item["present"] else "missing")
        lines.append(f"| {status} | `{item['path']}` | {item['title']} | {item['note']} |")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify external live platform evidence assets.")
    parser.add_argument("--assets-dir", default=str(DEFAULT_ASSETS_DIR), help="External evidence assets directory.")
    parser.add_argument("--stage", choices=sorted(STAGE_ORDER), default=DEFAULT_STAGE, help="Evidence stage to verify.")
    parser.add_argument("--init", action="store_true", help="Create the ignored evidence directory layout.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--write-manifest",
        nargs="?",
        const=None,
        default=False,
        help="Write a Markdown manifest. Defaults to live-evidence-manifest.md in the assets dir.",
    )
    parser.add_argument("--allow-missing", action="store_true", help="Exit zero even when evidence is still missing.")
    args = parser.parse_args(argv)

    assets_dir = Path(args.assets_dir)
    if not assets_dir.is_absolute():
        assets_dir = REPO_ROOT / assets_dir

    created = initialize_layout(assets_dir) if args.init else []
    result = verify_live_evidence(assets_dir, args.stage)
    result["created"] = created

    if args.write_manifest is not False:
        manifest_path = Path(args.write_manifest) if args.write_manifest else assets_dir / "live-evidence-manifest.md"
        if not manifest_path.is_absolute():
            manifest_path = REPO_ROOT / manifest_path
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(render_manifest(result), encoding="utf-8")
        result["manifest"] = str(manifest_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"stage={result['stage']}")
        print(f"ready={result['ready']}")
        print(f"present_count={result['present_count']}")
        print(f"missing_count={result['missing_count']}")
        if created:
            print(f"created_count={len(created)}")
        if "manifest" in result:
            print(f"manifest={result['manifest']}")

    return 0 if result["ready"] or args.allow_missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
