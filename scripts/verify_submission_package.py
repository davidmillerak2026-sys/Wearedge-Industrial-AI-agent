from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "docs" / "submission" / "submission-package-manifest.md"
VERIFICATION_DATE = "2026-06-04"


@dataclass(frozen=True)
class Artifact:
    path: str
    title: str
    note: str = ""


PHASE_ARTIFACTS: dict[str, list[Artifact]] = {
    "Phase A - Offline evaluation": [
        Artifact("evals/competition_offline_dataset.jsonl", "Offline dataset"),
        Artifact("scripts/run_competition_eval.py", "Competition evaluator"),
        Artifact("docs/competition-offline-eval-report.md", "Offline evaluation report"),
        Artifact("tests/test_competition_eval.py", "Evaluator pytest coverage"),
    ],
    "Phase B - Gongyi Mofang PoC package": [
        Artifact("docs/workflow-canvas-poc-runbook.md", "Workflow Canvas runbook"),
        Artifact("docs/workflow-canvas-api-schema.md", "Workflow Canvas API schema"),
        Artifact("workflows/wearedge_wfc_poc_payload.json", "Workflow Canvas sample payload"),
        Artifact("scripts/smoke_workflow_canvas_decision.py", "Workflow Canvas smoke script"),
        Artifact("docs/xcelerator-apiworld-onboarding.md", "Xcelerator API World onboarding notes"),
        Artifact("openapi/wearedge-xcelerator-apiworld.openapi.json", "Xcelerator OpenAPI import spec"),
    ],
    "Phase C - Demo evidence": [
        Artifact("docs/submission/demo-shot-list.md", "Demo shot list"),
        Artifact("docs/submission/demo-script.md", "Demo script"),
        Artifact("docs/submission/screenshots-checklist.md", "Screenshots checklist"),
        Artifact("docs/submission/poc-evidence-index.md", "PoC evidence index"),
        Artifact("docs/submission/dashboard-mock.html", "Dashboard mock"),
        Artifact("docs/submission/capture-runbook.md", "Capture runbook"),
        Artifact("docs/submission/evidence/README.md", "Generated evidence summary"),
        Artifact("scripts/capture_submission_screenshots.py", "Batch screenshot capture script"),
    ],
    "Phase D - Business and technical package": [
        Artifact("docs/submission/business-plan.md", "Business plan draft"),
        Artifact("docs/submission/technical-solution.md", "Technical solution draft"),
        Artifact("docs/submission/ip-and-compliance-statement.md", "IP and compliance statement"),
        Artifact("docs/submission/team-and-company-info-template.md", "Team and company template"),
    ],
    "Phase E - Registration fields": [
        Artifact("docs/submission/registration-fields.md", "Registration fields"),
        Artifact("docs/submission/final-checklist.md", "Final checklist"),
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

EXTERNAL_PENDING_ITEMS = (
    "企业名称、统一社会信用代码、联系人、电话、邮箱等真实主体信息",
    "企业负责人最终签署的知识产权、无产权纠纷、无不良记录承诺",
    "真实工易魔方 / Xcelerator 平台截图，待平台环境开通后补齐",
    "3-5 分钟演示视频文件或可访问链接",
    "报名系统正式提交状态截图",
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
            "Capture screenshots/video and fill human-owned registration fields."
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

    return {
        "status": "ready" if not failures else "review",
        "notes": "offline evidence and WFC smoke snapshot are present",
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
