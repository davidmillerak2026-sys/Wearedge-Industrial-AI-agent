from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "docs" / "submission" / "submission-package-manifest.md"
VERIFICATION_DATE = "2026-06-11"


@dataclass(frozen=True)
class Artifact:
    path: str
    title: str
    note: str = ""


PHASE_ARTIFACTS: dict[str, list[Artifact]] = {
    "Phase A - Offline evaluation": [
        Artifact("evals/competition_offline_dataset.jsonl", "Offline dataset"),
        Artifact("evals/finals_validation_dataset.jsonl", "Final-round validation dataset"),
        Artifact("scripts/run_competition_eval.py", "Competition evaluator"),
        Artifact("scripts/run_finals_validation.py", "Final-round validation evaluator"),
        Artifact("docs/competition-offline-eval-report.md", "Offline evaluation report"),
        Artifact("docs/finals-validation-report.md", "Final-round validation report"),
        Artifact("tests/test_competition_eval.py", "Evaluator pytest coverage"),
        Artifact("tests/test_run_finals_validation.py", "Final-round evaluator pytest coverage"),
    ],
    "Phase B - Gongyi Mofang PoC package": [
        Artifact("docs/gongyi-mofang-workflow-canvas-memory-202604.md", "Gongyi Mofang Workflow Canvas memory"),
        Artifact("docs/edge-agent-runtime-for-xcelerator.md", "Edge Agent Runtime notes"),
        Artifact("docs/submission/edge-runtime-evidence-runbook.md", "Edge runtime evidence runbook"),
        Artifact("wfc-blocks/wearedge-agent-service/info.json", "WFC Wearedge resource block metadata"),
        Artifact(
            "wfc-blocks/wearedge-agent-service/function-blocks/CallWearedgeDecisionApi.py",
            "WFC Python function block prototype",
        ),
        Artifact("scripts/smoke_edge_runtime_profile.py", "Edge runtime profile smoke script"),
        Artifact("scripts/benchmark_edge_stdlib_gateway.py", "Edge stdlib HTTP gateway benchmark"),
        Artifact("scripts/collect_edge_runtime_evidence.py", "Edge runtime live-evidence collector"),
        Artifact("scripts/smoke_solution_profile.py", "Industrial-agent solution profile smoke script"),
        Artifact("docs/workflow-canvas-poc-runbook.md", "Workflow Canvas runbook"),
        Artifact("docs/workflow-canvas-api-schema.md", "Workflow Canvas API schema"),
        Artifact("workflows/wearedge_wfc_poc_payload.json", "Workflow Canvas sample payload"),
        Artifact("workflows/wfc_call_wearedge_decision_fb_main.py", "WFC fb_main.py live-edit reference"),
        Artifact("scripts/smoke_workflow_canvas_decision.py", "Workflow Canvas smoke script"),
        Artifact("scripts/package_wfc_resource_block.py", "WFC resource block package builder"),
        Artifact("scripts/wfc_private_api_probe.py", "WFC read-only private API probe"),
        Artifact("docs/xcelerator-apiworld-onboarding.md", "Xcelerator API World onboarding notes"),
        Artifact("openapi/wearedge-xcelerator-apiworld.openapi.json", "Xcelerator OpenAPI import spec"),
    ],
    "Phase C - Demo evidence": [
        Artifact("docs/submission/demo-shot-list.md", "Demo shot list"),
        Artifact("docs/submission/demo-script.md", "Demo script"),
        Artifact("docs/submission/screenshots-checklist.md", "Screenshots checklist"),
        Artifact("docs/submission/live-platform-evidence-runbook.md", "Live platform evidence runbook"),
        Artifact("docs/submission/video-production-plan.md", "Demo video production plan"),
        Artifact("docs/submission/poc-evidence-index.md", "PoC evidence index"),
        Artifact("docs/submission/dashboard-mock.html", "Dashboard mock"),
        Artifact("docs/submission/capture-runbook.md", "Capture runbook"),
        Artifact("docs/submission/evidence/README.md", "Generated evidence summary"),
        Artifact("scripts/capture_submission_screenshots.py", "Batch screenshot capture script"),
        Artifact("scripts/verify_live_evidence.py", "Live evidence verifier"),
        Artifact("scripts/generate_enterprise_demo_video.py", "Enterprise demo video generator"),
    ],
    "Phase D - Business and technical package": [
        Artifact("docs/siemens-industrial-agent-track-memory-20260521.md", "Siemens industrial agent track memory"),
        Artifact("docs/industrial-agent-solution-profile.md", "Industrial-agent solution profile"),
        Artifact("docs/submission/enterprise-winning-strategy.md", "Enterprise group winning strategy"),
        Artifact("docs/submission/finals-foundation-roadmap.md", "Final-round foundation roadmap"),
        Artifact("docs/submission/finals-hmi-console.html", "Final-round HMI decision console"),
        Artifact("docs/submission/judging-scorecard-evidence-map.md", "Judging scorecard evidence map"),
        Artifact("docs/submission/defense-qna-playbook.md", "Defense Q&A playbook"),
        Artifact("docs/submission/business-plan.md", "Business plan draft"),
        Artifact("docs/submission/technical-solution.md", "Technical solution draft"),
        Artifact("docs/submission/ip-and-compliance-statement.md", "IP and compliance statement"),
        Artifact("docs/submission/company-info-and-compliance-intake.md", "Company info and compliance intake"),
        Artifact("docs/submission/team-and-company-info-template.md", "Team and company template"),
        Artifact("scripts/verify_finals_foundation.py", "Final-round foundation verifier"),
    ],
    "Phase E - Registration fields": [
        Artifact("docs/submission/registration-fields.md", "Registration fields"),
        Artifact("docs/submission/final-checklist.md", "Final checklist"),
        Artifact("scripts/build_final_submission_bundle.py", "Repo-controlled final submission bundle builder"),
        Artifact("scripts/prepare_final_human_action_pack.py", "Final human action template generator"),
        Artifact("scripts/generate_final_readiness_report.py", "Final readiness report generator"),
        Artifact("scripts/run_final_readiness_pipeline.py", "One-command final readiness pipeline"),
        Artifact("scripts/generate_final_action_board.py", "Final action board generator"),
        Artifact("docs/submission/final-human-action-runbook.md", "Final human action runbook"),
        Artifact("docs/submission/final-readiness-report.md", "Final readiness report"),
        Artifact("docs/submission/final-action-board.md", "Final action board"),
    ],
}

REGISTRATION_REQUIRED_MARKERS = (
    "## 短版字段",
    "## 中版字段",
    "## 长版字段",
    "## 拟开发智能体",
    "## 目标客户群",
    "## 产品优势",
    "## 商业模式",
    "## 知识产权说明",
    "## 人工待填字段",
)

REPORT_REQUIRED_MARKERS = (
    "不是客户真实产线数据",
    "| Maintenance F1 |",
    "| Energy forecast accuracy |",
    "| Schedule efficiency gain |",
)

WFC_REQUIRED_TOP_LEVEL_FIELDS = (
    "ok",
    "workflow_canvas",
    "collaborative_decision",
    "competition_metrics",
)

EDGE_PROFILE_REQUIRED_TOP_LEVEL_FIELDS = (
    "ok",
    "edge_node",
    "edge_capabilities",
    "platform_integration",
    "safety_boundary",
)

SOLUTION_PROFILE_REQUIRED_TOP_LEVEL_FIELDS = (
    "ok",
    "industrial_problem",
    "model_runtime",
    "agent_system",
    "decision_mechanism",
    "platform_integration",
    "validation_evidence",
)

EXTERNAL_PENDING_ITEMS = (
    "按 docs/submission/company-info-and-compliance-intake.md 补齐企业名称、统一社会信用代码、联系人、电话、邮箱等真实主体信息",
    "用真实 WFC Dashboard / log-manager ok=true / HumanApprovalGate 截图替换当前 fallback 标记的 04/05/06 Gongyi Mofang 证据",
    "将临时 PoC HTTPS 地址替换为稳定可复现地址，并在 Xcelerator / WFC 材料中同步更新",
    "企业负责人最终签署的知识产权、无产权纠纷、无不良记录承诺",
    "报名系统字段填报截图，隐藏证件号等敏感字段后存入 submission-assets/live-evidence/submission/",
    "报名系统正式提交成功状态截图",
)


def verify_package(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    phases = [_verify_phase(repo_root, name, artifacts) for name, artifacts in PHASE_ARTIFACTS.items()]
    evidence = _verify_evidence(repo_root)
    registration = _verify_registration_fields(repo_root)
    report = _verify_offline_report(repo_root)
    timeline = _verify_timeline(repo_root)

    repo_failures = [
        failure
        for section in (phases, [evidence, registration, report, timeline])
        for item in section
        for failure in item.get("failures", [])
    ]

    return {
        "verification_date": VERIFICATION_DATE,
        "repo_ready": not repo_failures,
        "repo_failures": repo_failures,
        "phases": phases,
        "evidence": evidence,
        "registration_fields": registration,
        "offline_report": report,
        "timeline": timeline,
        "external_pending_items": list(EXTERNAL_PENDING_ITEMS),
        "recommended_next_action": (
            "Replace fallback WFC evidence and fill human-owned registration fields."
            if not repo_failures
            else "Fix repository-controlled failures before capture/submission."
        ),
    }


def render_manifest(result: dict[str, Any]) -> str:
    lines = [
        "# Submission Package Manifest",
        "",
        f"更新日期：{result['verification_date']}",
        "",
        "此文件由 `scripts/verify_submission_package.py --write-manifest` 生成，用于提交前总控检查。",
        "",
        "## Repository Readiness",
        "",
        f"- Repository-controlled package ready: {result['repo_ready']}",
        f"- Recommended next action: {result['recommended_next_action']}",
        "",
        "## Phase Status",
        "",
        "| Phase | Status | Artifacts |",
        "| --- | --- | ---: |",
    ]
    for phase in result["phases"]:
        lines.append(f"| {phase['name']} | {phase['status']} | {phase['present_count']} / {phase['artifact_count']} |")

    lines.extend(
        [
            "",
            "## Validation Status",
            "",
            "| Check | Status | Notes |",
            "| --- | --- | --- |",
            _status_row("Generated evidence", result["evidence"]),
            _status_row("Registration fields", result["registration_fields"]),
            _status_row("Offline report boundary", result["offline_report"]),
            _status_row("Submission timeline", result["timeline"]),
            "",
            "## External Pending Items",
            "",
        ]
    )
    for item in result["external_pending_items"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## External Evidence Command",
            "",
            "```powershell",
            "python scripts/run_final_readiness_pipeline.py --json",
            "python scripts/verify_live_evidence.py --stage platform --allow-missing --write-manifest",
            "python scripts/verify_live_evidence.py --stage final --allow-missing --write-manifest",
            "```",
        ]
    )

    lines.extend(
        [
            "",
            "## Repository Failures",
            "",
        ]
    )
    if result["repo_failures"]:
        for failure in result["repo_failures"]:
            lines.append(f"- {failure}")
    else:
        lines.append("- None.")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the Wearedge competition submission package.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable verification output.")
    parser.add_argument(
        "--write-manifest",
        nargs="?",
        const=str(DEFAULT_MANIFEST),
        default=None,
        help="Write a Markdown manifest. Defaults to docs/submission/submission-package-manifest.md.",
    )
    args = parser.parse_args(argv)

    result = verify_package()
    if args.write_manifest:
        manifest_path = Path(args.write_manifest)
        if not manifest_path.is_absolute():
            manifest_path = REPO_ROOT / manifest_path
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(render_manifest(result), encoding="utf-8")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"repo_ready={result['repo_ready']}")
        print(f"phase_count={len(result['phases'])}")
        print(f"repo_failure_count={len(result['repo_failures'])}")
        print(f"external_pending_count={len(result['external_pending_items'])}")
        if args.write_manifest:
            print(f"manifest={Path(args.write_manifest)}")

    return 0 if result["repo_ready"] else 1


def _verify_phase(repo_root: Path, name: str, artifacts: list[Artifact]) -> dict[str, Any]:
    items = []
    failures = []
    for artifact in artifacts:
        path = repo_root / artifact.path
        present = path.exists() and (path.is_dir() or path.stat().st_size > 0)
        if not present:
            failures.append(f"{name}: missing or empty {artifact.path}")
        items.append(
            {
                "path": artifact.path,
                "title": artifact.title,
                "present": present,
                "note": artifact.note,
            }
        )
    return {
        "name": name,
        "status": "ready" if not failures else "missing",
        "artifact_count": len(artifacts),
        "present_count": sum(1 for item in items if item["present"]),
        "artifacts": items,
        "failures": failures,
    }


def _verify_evidence(repo_root: Path) -> dict[str, Any]:
    failures: list[str] = []
    summary = _load_json(repo_root / "docs" / "submission" / "evidence" / "competition-eval-summary.json", failures)
    decision = _load_json(repo_root / "docs" / "submission" / "evidence" / "workflow-canvas-decision.json", failures)
    edge_profile = _load_json(repo_root / "docs" / "submission" / "evidence" / "edge-runtime-profile.json", failures)
    gateway_latency = _load_json(
        repo_root / "docs" / "submission" / "evidence" / "finals-jetson-gateway-latency-benchmark.json",
        [],
    ) or _load_json(
        repo_root / "docs" / "submission" / "evidence" / "finals-local-gateway-latency-benchmark.json",
        failures,
    )
    solution_profile = _load_json(repo_root / "docs" / "submission" / "evidence" / "solution-profile.json", failures)

    if summary:
        if summary.get("all_cases_passed") is not True:
            failures.append("generated evidence: offline cases are not all passed")
        if summary.get("all_target_checks_passed") is not True:
            failures.append("generated evidence: competition target checks are not all passed")

    if decision:
        for field in WFC_REQUIRED_TOP_LEVEL_FIELDS:
            if field not in decision:
                failures.append(f"generated evidence: missing WFC field {field}")
        workflow = _object(decision.get("workflow_canvas"))
        function_blocks = workflow.get("function_blocks")
        if not isinstance(function_blocks, list) or not function_blocks:
            failures.append("generated evidence: workflow_canvas.function_blocks is empty")

    if edge_profile:
        for field in EDGE_PROFILE_REQUIRED_TOP_LEVEL_FIELDS:
            if field not in edge_profile:
                failures.append(f"generated evidence: missing edge runtime field {field}")
        capabilities = _object(edge_profile.get("edge_capabilities"))
        safety = _object(edge_profile.get("safety_boundary"))
        if capabilities.get("workflow_canvas_ready") is not True:
            failures.append("generated evidence: edge runtime is not Workflow Canvas ready")
        if safety.get("model_direct_ot_control") is not False:
            failures.append("generated evidence: edge safety boundary allows direct OT control")

    if gateway_latency:
        if gateway_latency.get("mode") != "http":
            failures.append("generated evidence: gateway benchmark did not use HTTP mode")
        if gateway_latency.get("target_met") is not True:
            failures.append("generated evidence: gateway benchmark did not meet latency target")
        resource_profile = _object(gateway_latency.get("resource_profile"))
        if int(resource_profile.get("sample_count", 0)) <= 0:
            failures.append("generated evidence: gateway benchmark missing resource samples")

    if solution_profile:
        for field in SOLUTION_PROFILE_REQUIRED_TOP_LEVEL_FIELDS:
            if field not in solution_profile:
                failures.append(f"generated evidence: missing solution profile field {field}")
        decision_mechanism = _object(solution_profile.get("decision_mechanism"))
        model_runtime = _object(solution_profile.get("model_runtime"))
        if decision_mechanism.get("model_dependency") != "not required for /v1/workflow-canvas/decision":
            failures.append("generated evidence: solution profile does not separate model from decision engine")
        if not model_runtime.get("primary_model"):
            failures.append("generated evidence: solution profile missing primary model")

    return {
        "status": "ready" if not failures else "review",
        "notes": "offline evidence, WFC smoke snapshot, edge runtime profile, HTTP resource benchmark, and solution profile are present",
        "failures": failures,
    }


def _verify_registration_fields(repo_root: Path) -> dict[str, Any]:
    failures: list[str] = []
    text = _read_text(repo_root / "docs" / "submission" / "registration-fields.md", failures)
    for marker in REGISTRATION_REQUIRED_MARKERS:
        if marker not in text:
            failures.append(f"registration-fields.md missing section: {marker}")
    return {
        "status": "ready" if not failures else "review",
        "notes": "short/mid/long field copy and human-owned fields are separated",
        "failures": failures,
    }


def _verify_offline_report(repo_root: Path) -> dict[str, Any]:
    failures: list[str] = []
    text = _read_text(repo_root / "docs" / "competition-offline-eval-report.md", failures)
    for marker in REPORT_REQUIRED_MARKERS:
        if marker not in text:
            failures.append(f"offline report missing marker: {marker}")
    return {
        "status": "ready" if not failures else "review",
        "notes": "report includes metric table and simulated/offline boundary",
        "failures": failures,
    }


def _verify_timeline(repo_root: Path) -> dict[str, Any]:
    failures: list[str] = []
    text = _read_text(repo_root / "docs" / "submission" / "final-checklist.md", failures)
    for marker in ("2026-07-08", "2026-07-10", "官方报名截止"):
        if marker not in text:
            failures.append(f"final-checklist.md missing timeline marker: {marker}")
    return {
        "status": "ready" if not failures else "review",
        "notes": "internal submit date and official deadline are tracked",
        "failures": failures,
    }


def _status_row(label: str, section: dict[str, Any]) -> str:
    return f"| {label} | {section['status']} | {section['notes']} |"


def _read_text(path: Path, failures: list[str]) -> str:
    if not path.exists():
        failures.append(f"missing file: {path.relative_to(REPO_ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def _load_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.exists():
        failures.append(f"missing file: {path.relative_to(REPO_ROOT)}")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {path.relative_to(REPO_ROOT)}: {exc}")
        return {}
    return data if isinstance(data, dict) else {}


def _object(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


if __name__ == "__main__":
    raise SystemExit(main())
