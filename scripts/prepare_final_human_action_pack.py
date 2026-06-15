from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS_DIR = REPO_ROOT / "submission-assets" / "live-evidence"


@dataclass(frozen=True)
class TemplateFile:
    path: str
    title: str
    final_target: str
    content: str


TEMPLATES: tuple[TemplateFile, ...] = (
    TemplateFile(
        path="legal/company-info-filled.template.md",
        title="Company and contact information template",
        final_target="legal/company-info-filled.md",
        content="""# Company And Contact Information

Do not commit this file to Git. Fill the final copy at:

```text
submission-assets/live-evidence/legal/company-info-filled.md
```

## Enterprise

| Field | Final value |
| --- | --- |
| Enterprise name |  |
| Unified social credit code |  |
| Registered address |  |
| Enterprise type |  |
| SME eligibility confirmed |  |
| No adverse record confirmed |  |

## Project Contact

| Field | Final value |
| --- | --- |
| Project owner |  |
| Mobile |  |
| Email |  |
| Backup contact |  |
| Backup mobile |  |
| Backup email |  |

## Team Roles

| Role | Name | Responsibility | Confirmed |
| --- | --- | --- | --- |
| Project lead |  | Registration, business, defense coordination |  |
| Technical lead |  | Agent architecture, API, evaluation metrics |  |
| IT/OT integration lead |  | Xcelerator, Gongyi Mofang, MES/QMS/EMS/CMMS |  |
| Edge deployment lead |  | Jetson / IPC / local industrial PC evidence |  |
| Business lead |  | Target customers, business model, ROI |  |
| Delivery lead |  | Joint PoC, customer pilot, project plan |  |
""",
    ),
    TemplateFile(
        path="legal/ip-and-no-dispute-statement.template.md",
        title="IP and no-dispute statement template",
        final_target="legal/ip-and-no-dispute-signed.pdf",
        content="""# IP And No-Dispute Statement Template

Final signed or stamped PDF target:

```text
submission-assets/live-evidence/legal/ip-and-no-dispute-signed.pdf
```

Statement draft:

We confirm that the enterprise owns or has lawful rights to submit the Wearedge Industrial AI Agent project. The submitted project materials, source code maintained in the GitHub repository, Workflow Canvas resource prototype, API schema, evaluation scripts, and documentation do not knowingly infringe third-party intellectual property rights.

We confirm that there is no ownership dispute affecting the submitted project. Open-source dependencies and model/runtime components are used according to their applicable licenses. Model weights are not claimed as self-developed foundation models and are not committed to the repository.

Enterprise:

Authorized representative:

Signature or company stamp:

Date:
""",
    ),
    TemplateFile(
        path="legal/no-adverse-record-statement.template.md",
        title="No adverse record statement template",
        final_target="legal/no-adverse-record-signed.pdf",
        content="""# No Adverse Record Statement Template

Final signed or stamped PDF target:

```text
submission-assets/live-evidence/legal/no-adverse-record-signed.pdf
```

Statement draft:

We confirm that the participating enterprise has no adverse record that would make it ineligible for the 11th Maker China Industrial Agent SME Innovation and Entrepreneurship Competition.

We confirm that the submitted materials are truthful, accurate, and verifiable to the best of our knowledge, and that any simulated/offline PoC evidence is clearly marked as such.

Enterprise:

Authorized representative:

Signature or company stamp:

Date:
""",
    ),
    TemplateFile(
        path="legal/submission-contact-confirmation.template.md",
        title="Submission contact confirmation template",
        final_target="legal/submission-contact-confirmation.md",
        content="""# Submission Contact Confirmation

Final target:

```text
submission-assets/live-evidence/legal/submission-contact-confirmation.md
```

| Field | Final value |
| --- | --- |
| Primary contact name |  |
| Primary contact mobile |  |
| Primary contact email |  |
| Backup contact name |  |
| Backup contact mobile |  |
| Backup contact email |  |
| Xcelerator account owner confirmed |  |
| Gongyi Mofang account owner confirmed |  |
| Final submitter confirmed |  |
""",
    ),
    TemplateFile(
        path="submission/registration-form-capture-checklist.template.md",
        title="Registration form capture checklist",
        final_target="submission/01-registration-form-filled.png",
        content="""# Registration Form Capture Checklist

Final screenshot target:

```text
submission-assets/live-evidence/submission/01-registration-form-filled.png
```

Before capture:

- Fill enterprise and contact fields with final approved values.
- Paste the project short/mid/long copy from `docs/submission/registration-fields.md`.
- Upload or attach the repo-controlled submission bundle and required supporting files.
- Hide or crop sensitive certificate numbers before using the screenshot in public materials.
- Confirm the screenshot shows the project name and enough field context to prove pre-submit readiness.
""",
    ),
    TemplateFile(
        path="submission/submission-success-capture-checklist.template.md",
        title="Submission success capture checklist",
        final_target="submission/02-submission-success.png",
        content="""# Submission Success Capture Checklist

Final screenshot target:

```text
submission-assets/live-evidence/submission/02-submission-success.png
```

Capture requirements:

- Show the final submitted / success / accepted status.
- Include the project name or submission id if visible.
- Hide personal phone, full certificate number, and any private token.
- Save immediately after the official submission is complete.
""",
    ),
    TemplateFile(
        path="gongyi-mofang/live-wfc-replacement-checklist.template.md",
        title="Live WFC replacement checklist",
        final_target="gongyi-mofang/04-dashboard-decision-view.png, gongyi-mofang/05-run-log-ok-true.png, gongyi-mofang/06-human-approval-gate.png",
        content="""# Live WFC Replacement Checklist

Targets:

```text
submission-assets/live-evidence/gongyi-mofang/04-dashboard-decision-view.png
submission-assets/live-evidence/gongyi-mofang/05-run-log-ok-true.png
submission-assets/live-evidence/gongyi-mofang/06-human-approval-gate.png
```

Use these to maintain reviewed live WFC evidence. Recapture only if the workflow, Dashboard fields, or approval UI changes.

Required proof:

- Dashboard/ui-builder view showing Wearedge metric cards, decision path, approval items, and workflow state.
- log-manager or run panel showing `wearedge_decision_ok=True`, `ok=true`, latency, function-block output, or successful table writeback.
- HumanApprovalGate or approval-state view showing pending/approved/rejected handling for high-risk actions.
- Do not add `.fallback.json` metadata to these targets unless a screenshot is deliberately replaced by mock/fallback evidence.
""",
    ),
)


def prepare_templates(
    assets_dir: Path = DEFAULT_ASSETS_DIR,
    *,
    overwrite: bool = False,
    write_manifest: bool = True,
) -> dict[str, Any]:
    written: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for template in TEMPLATES:
        path = assets_dir / template.path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            skipped.append(_template_record(template, path))
            continue
        path.write_text(template.content, encoding="utf-8")
        written.append(_template_record(template, path))

    result = {
        "ok": True,
        "assets_dir": str(assets_dir),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "written_count": len(written),
        "skipped_count": len(skipped),
        "written": written,
        "skipped": skipped,
        "final_targets_not_created": sorted({template.final_target for template in TEMPLATES}),
        "safety": [
            "Templates use .template.* names and do not satisfy final verifier targets.",
            "Final signed PDFs, company information, and registration screenshots remain human-owned.",
            "Do not commit generated files under submission-assets/live-evidence/.",
        ],
    }
    if write_manifest:
        manifest_path = assets_dir / "final-human-action-pack-manifest.json"
        manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["manifest_path"] = str(manifest_path)
    return result


def _template_record(template: TemplateFile, path: Path) -> dict[str, str]:
    return {
        "path": str(path),
        "title": template.title,
        "final_target": template.final_target,
    }


def render_summary(result: dict[str, Any]) -> str:
    lines = [
        f"ok={result['ok']}",
        f"assets_dir={result['assets_dir']}",
        f"written_count={result['written_count']}",
        f"skipped_count={result['skipped_count']}",
    ]
    if result.get("manifest_path"):
        lines.append(f"manifest_path={result['manifest_path']}")
    lines.append("final_targets_not_created:")
    lines.extend(f"- {target}" for target in result["final_targets_not_created"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare ignored templates for human-owned final submission files.")
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-manifest", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = prepare_templates(
        args.assets_dir,
        overwrite=args.overwrite,
        write_manifest=not args.no_manifest,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_summary(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
