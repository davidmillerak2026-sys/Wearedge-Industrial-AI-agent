# Gongyi Mofang Official Completion Paths

Updated: 2026-06-13

This note turns the reviewed Gongyi Mofang / Workflow Canvas official manuals and the Xcelerator API World guide into an execution decision for Wearedge. It is intentionally written as an operational memory card so the next platform session does not drift into blind clicking.

## Source Documents Reviewed

| Source | Practical use for Wearedge |
| --- | --- |
| `附件1-工易魔方-让人工智能触手可及 完整版 202604.pdf` | Platform positioning: low-code industrial workflows, IT/OT integration, edge execution, AI/algorithm reuse. |
| `附件3-工易魔方onepage简介.pdf` | Co-creation story: workflow, AI Agent compatibility, deployment modes, secondary development. |
| `第十一届“创客中国-开发工具套件工易魔方推荐.docx` | Competition relevance and recommended Gongyi Mofang tool path. |
| `WFC001_工易魔方工作说明书.docx` | Project, resource configuration, function blocks, debugging, data table, Dashboard workflow. |
| `WFC002_蜘蛛执行器使用手册.docx` | Spider executor on PC/NUC, executor URL and connection evidence. |
| `WFC003_IPC使用手册.docx` | Siemens Edge IPC executor route. |
| `WFC005_如何对资源块及功能块进行二次开发.docx` | Custom resource/function block packaging, `info.json`, resource package installation. |
| `WFC006_资源块安装使用.pdf` | Resource block installation and use. |
| `WFC007_ 如何保存数据，如何在ui-builder上展示图片.docx` | Python JSON output, global data table, ui-builder/Dashboard binding. |
| `WFC010_工易魔方快速入门手册V2.pdf` | Login, project creation, deploy/debug, Spider logs and basic workflow run evidence. |
| Xcelerator API World developer guide | Tenant/app/API-service creation, OpenAPI import, X authentication, subscription/call flow. |

Canonical local memory remains `docs/gongyi-mofang-workflow-canvas-memory-202604.md`.

## Decision

There is no confirmed official CLI for editing a whole Gongyi Mofang Workflow Canvas project from command line.

The official path to our goal is:

```text
Xcelerator API World API service draft
  + Gongyi Mofang Workflow Canvas project
  + Spider/SPIDR or IPC executor
  + Wearedge Agent Service custom resource
  + CallWearedgeDecisionApi Python block
  + global data table update
  + Dashboard/ui-builder preview
  + HumanApprovalGate / approval-state evidence
```

CLI/API work should therefore be used for packaging, probing, backup, smoke tests, and evidence generation. It should not be presented as a substitute for the live WFC run, Dashboard, and log-manager evidence.

## Path A: Official WFC Live Evidence Path

Use this as the main route for the submission screenshots.

| Step | Official-doc basis | Wearedge action | Evidence target |
| --- | --- | --- | --- |
| 1 | WFC001/WFC010 project workflow | Open `Wearedge WFC PoC` and default `工作流.1`. | `00`, `08`, `09`, `11` WFC screenshots. |
| 2 | WFC002/WFC003 Spider/IPC execution | Configure `通用工控机` / SPIDR / IPC executor. | Executor URL, connection state, debug/deploy state. |
| 3 | WFC005/WFC006 custom resources | Finish `Wearedge Agent Service` with `agentHost`, `agentPort`, `apiKeyRef`, `deploymentMode`, `plantId`, `lineId`. | `01-resource-block-wearedge-agent-service.png`. |
| 4 | WFC001 Python/function blocks | Verify `CallWearedgeDecisionApi` Python block input/output and saved `fb_main.py`. | `02-python-function-block-call-api.png`, `102-wfc-python-fb-main-saved.png`. |
| 5 | WFC007 data persistence | Add `更新数据表`, bind Wearedge fields, and prove the target data fields can hold decision values. | `03-global-data-table-decision-fields.png`, binding screenshots, `192-wfc-update-data-table-fields-complete-20260613.png`, `193-wfc-debug-running-fields-locked-20260613.png`. |
| 6 | WFC010 debug/deploy/logs | Run workflow on SPIDR/IPC, capture log-manager output and browser/runtime logs. | `05-run-log-ok-true.png` only after WFC-native `wearedge_decision_ok=True`; interim live evidence is `125-wfc-run-log-workflow-ready-status-good-20260612.png` and `195-wfc-browser-debug-log-20260613.json`. |
| 7 | WFC007 ui-builder/Dashboard | Create/preview Dashboard from live data table or data stream. | `04-dashboard-decision-view.png`. |
| 8 | Safety boundary from runbook | Show approval state for high-risk recommendation. | `06-human-approval-gate.png` or live approval-state panel. |

Important correction: `/dashboard-explorer` is a preview/list page. If it returns `No Dashboard`, it is not the creation entry. The official path is to create or bind a Dashboard/ui-builder view from the workflow/data-table context, then preview it.

## Path B: Official Resource Package Path

Use this to make Wearedge look like a reusable Gongyi Mofang component, not only a one-off canvas demo.

| Step | Action |
| --- | --- |
| 1 | Keep `wfc-blocks/wearedge-agent-service/info.json` aligned with WFC resource naming rules. |
| 2 | Keep `function-blocks/CallWearedgeDecisionApi.py` as the reusable block sample. |
| 3 | Run `python scripts/package_wfc_resource_block.py --json` to produce the local `.zip` package and manifest under ignored `submission-assets/live-evidence/gongyi-mofang/wfc-resource-package/`. |
| 4 | If the WFC/RA environment exposes Swagger, use the manual-noted `:61720/docs` route to upload/install the package. |
| 5 | Capture resource-library or installed-resource screenshots if available. |

This path is official for component packaging and installation. It is not yet confirmed as a complete project editing CLI.

## Path C: Xcelerator API World Path

Use this to prove Wearedge is a platform-facing API service.

| Step | Wearedge status |
| --- | --- |
| Create app group and app draft | Done, unpublished, tenant-only. |
| Create API service draft | Done. |
| Import OpenAPI | Done, 4 endpoints imported. |
| Keep `/v1/workflow-canvas/decision` compatible | Done. |
| Use X authentication for final integration | Supported in code and docs; AppSecret must stay outside Git. |
| Capture API Console call | Pending until stable HTTPS Wearedge service is available. |

This path complements WFC. It proves API/platform readiness but does not replace the WFC workflow run evidence.

## Path D: Safe CLI/API Assistance

CLI should help with repeatability while respecting platform credentials.

Allowed and useful:

- Package local WFC resource block zip.
- Run `scripts/smoke_workflow_canvas_decision.py`.
- Run `scripts/verify_live_evidence.py`.
- Generate local submission evidence, screenshots, and video.
- Run `scripts/wfc_private_api_probe.py --dry-run` to inspect planned read-only WFC project probes.
- Run `scripts/wfc_private_api_probe.py` with a locally supplied `WFC_COOKIE` only when we need authenticated read-only diagnosis; the script never prints credential values.
- Back up non-secret project JSON if the platform exposes readable project files.

Not allowed or not suitable:

- Saving WFC password, session cookies, Xcelerator AppSecret, AppID screenshots, or API keys in Git.
- Claiming private web-app persistence endpoints are official public APIs.
- Replacing `ok=true` live WFC run evidence with a local smoke test without labeling it as fallback.
- Publishing or submitting Xcelerator API services without explicit action-time approval.

## Private Web-App API Notes

Earlier frontend inspection suggests WFC uses internal endpoints such as:

```text
GET  /uploads/{path}
GET  /api/persistence/files/{path}
POST /api/persistence/upload/{path}
POST /api/persistence/diff-update
GET  /api/projects/dashboard-explorer
```

These are useful for read-only diagnosis and possible backup, but they are not official competition evidence by themselves. Any script around them must:

- run read-only by default;
- require credentials through environment variables;
- redact authentication from logs;
- save outputs only under ignored `submission-assets/live-evidence/...`;
- require a separate explicit flag for any write operation.

Dry-run example:

```powershell
python scripts/wfc_private_api_probe.py --project-id cmq6lbb9x00bx1l6pxll7voae --workflow-instance-id ryn.cmq6lbb9x00bx1l6pxll7voae.workflow1 --dry-run --json
```

Authenticated read-only example, only for local diagnosis:

```powershell
$env:WFC_COOKIE="<paste current session cookie locally; do not commit>"
python scripts/wfc_private_api_probe.py --project-id cmq6lbb9x00bx1l6pxll7voae --probe workflow-json --json
Remove-Item Env:WFC_COOKIE
```

## Immediate Next Actions

1. Stop any active WFC debug session before editing.
2. Finish `Wearedge Agent Service` parameters in WFC.
3. Keep `CallWearedgeDecisionApi` block inputs/outputs and saved `fb_main.py` aligned with `workflows/wfc_call_wearedge_decision_fb_main.py`.
4. Replace the current `更新数据表.1` static example values with a confirmed Python `输出1` -> data-table update binding once the WFC data-port gesture is stable.
5. Run the workflow and capture log-manager evidence containing `wearedge_decision_ok` or equivalent `ok=true` output.
6. Build the Dashboard/ui-builder view from workflow data, not from an empty `/dashboard-explorer` page.
7. If GUI remains slow, implement only a read-only private API probe first; do not use private write calls until project JSON paths are backed up and verified.

## Submission Boundary

For judging language:

```text
Official WFC documents support Wearedge as a resource/function-block based Workflow Canvas integration, deployed through Spider/SPIDR or IPC and visualized through global data tables and ui-builder. CLI and private API probes are engineering accelerators only; live platform screenshots and logs remain the primary proof.
```

2026-06-13 live boundary:

```text
The live WFC project now shows `更新数据表.1` carrying four Wearedge decision fields and static example values in DEBUG. Browser runtime logs include `update data table`. This proves the WFC data-table target and execution state, but it is not yet proof that Python `输出1` dynamically wrote those values.
```
