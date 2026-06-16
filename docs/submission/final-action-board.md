# Final Action Board

Updated: 2026-06-16T11:37:09+00:00

## Current Gate

- Repository ready: True
- Finals foundation ready: True
- Finals ready: False
- Final external evidence ready: False
- Final missing files: 6
- Fallback warnings: 0
- Edge latency evidence tier: final_edge_fastapi_http_gateway
- Edge HTTP samples: 4500
- Edge HTTP p95/max latency: 6 / 33 ms

## Do Next

1. Finish the high-value WFC writeback proof: if WFC can provide readable JSON export, run binding analysis; otherwise manually connect `输出1 -> 更新数据表.1`, then capture `gongyi-mofang/197-wfc-data-table-values-after-python-writeback-20260616.png`.
2. Keep the Cloud Run stable endpoint evidence current with `python scripts/verify_stable_wearedge_endpoint.py --base-url https://wearedge-agent-service-863888677331.asia-east1.run.app --write-evidence` before final upload.
3. Finish Xcelerator API selector/path binding: backend has been filled with Cloud Run `https://wearedge-agent-service-863888677331.asia-east1.run.app`, but the tenant proxy currently returns code `-107`; use `python scripts/verify_xcelerator_proxy.py --write-evidence` after each platform change until proxy returns Wearedge `ok=true`.
4. Complete the six enterprise-owned legal/contact/submission evidence files.
5. Run `python scripts/verify_final_external_assets.py --write-report` after signed PDFs, final screenshots, video, and live WFC evidence are in place.
6. Run `python scripts/run_final_readiness_pipeline.py --json` and `python scripts/verify_live_evidence.py --stage final --write-manifest` before final upload.

## WFC Live Replacement

| Status | Target | Owner | Action | Acceptance |
| --- | --- | --- | --- | --- |
| present | `gongyi-mofang/04-dashboard-decision-view.png` | WFC operator | Create or preview the real WFC Dashboard/ui-builder view. | Shows Wearedge metric cards, decision path, approval items, and workflow state from live WFC context. |
| present | `gongyi-mofang/05-run-log-ok-true.png` | WFC operator | Keep the reviewed live WFC run-log screenshot for the required gate; after pasting the updated live-edit package, recapture the run log. | Shows WFC-native CallWearedgeDecisionApi.output JSON beginning with ok=true; preferred recapture also shows wfc_writeback.method=wfc_output1_to_update_data_table. |
| present | `gongyi-mofang/06-human-approval-gate.png` | WFC operator | Show HumanApprovalGate or approval-state panel for a high-risk recommendation. | Shows pending/approved/rejected human confirmation; model is not directly controlling OT. |

## High-Value Strengthening

These items improve finals-readiness and credibility, but they do not change the six human-owned final blockers.

| Status | Target | Owner | Action | Acceptance |
| --- | --- | --- | --- | --- |
| present | `gongyi-mofang/196-wfc-dynamic-writeback-output-ok-20260616.png` | WFC operator | After pasting the updated WFC Function Block code, capture the live output JSON. | Shows ok=true plus wfc_writeback.method=wfc_output1_to_update_data_table and fields_ready values. |
| optional_pending | `gongyi-mofang/197-wfc-data-table-values-after-python-writeback-20260616.png` | WFC operator | If WFC can export readable JSON, run binding analysis; otherwise manually connect output1 to UpdateDataTable, then capture the native WFC data table after DEBUG. | Shows selected_direction, approval_status, recommended_action, and latency_ms values matching the Python output fields_ready object. |
| present | `gongyi-mofang/workflow-export/199-wfc-workflow-export-20260616.wfcw` | WFC operator | Keep the live WFC workflow and deployment-data exports archived under ignored evidence. | Shows project assets can be exported/archived; .wfcw/.wfcd are proprietary binary exports and do not replace JSON binding analysis or live data-table proof. |
| present | `stable-endpoint/stable-endpoint-evidence.md` | Platform operator | Cloud Run stable endpoint is deployed; rerun the stable endpoint verifier before final upload. | Shows healthz, runtime-profile, and workflow-canvas decision checks passing on a non-temporary HTTPS host. |
| present | `xcelerator/45-xcelerator-api-backend-cloud-run-filled-20260616.png` | Platform operator | Keep the Xcelerator API service backend replacement screenshot and continue selector/path binding. | Shows Cloud Run URL in the live Xcelerator draft; proxy selector still needs verification until it returns Wearedge ok=true. |

## Human-Owned Final Files

| Status | Target | Owner | Action | Acceptance |
| --- | --- | --- | --- | --- |
| missing | `legal/company-info-filled.md` | Enterprise owner | Copy from company-info-filled.template.md and fill final company/contact/team fields. | Enterprise name, unified social credit code, contacts, roles, eligibility, and no-adverse-record confirmation are filled. |
| missing | `legal/ip-and-no-dispute-signed.pdf` | Enterprise owner | Sign/stamp the IP and no-dispute statement template and export PDF. | Signed or stamped PDF confirms lawful IP ownership/no ownership dispute and open-source/model boundary. |
| missing | `legal/no-adverse-record-signed.pdf` | Enterprise owner | Sign/stamp the no-adverse-record statement and export PDF. | Signed or stamped PDF confirms enterprise eligibility and truthful simulated/offline evidence labeling. |
| missing | `legal/submission-contact-confirmation.md` | Final submitter | Fill primary/backup contact and account-owner confirmations. | Primary and backup contacts are complete; Xcelerator/WFC/final submitter ownership is confirmed. |
| missing | `submission/01-registration-form-filled.png` | Final submitter | Capture filled registration form before final submit. | Shows project name and filled fields while hiding certificate numbers and private contact details for reuse. |
| missing | `submission/02-submission-success.png` | Final submitter | Capture official submitted/success status after final submit. | Shows submitted/success status, project name or submission id if visible, with private fields hidden for reuse. |

## Command Sequence

```powershell
python scripts/prepare_final_human_action_pack.py --json
python scripts/verify_final_external_assets.py --write-report
python scripts/run_final_readiness_pipeline.py --json
python scripts/verify_live_evidence.py --stage final --write-manifest
python scripts/verify_submission_package.py --write-manifest
```

## Boundary

- Do not commit files under `submission-assets/live-evidence/`.
- Current WFC replacement targets should have no fallback metadata; preserve reviewed live evidence sidecars and recapture from WFC when the updated Function Block is promoted into the platform.
- WFC dynamic data-table writeback is still a high-value strengthening item; stable HTTPS endpoint evidence is now captured via Cloud Run, and Xcelerator backend replacement is partially evidenced. Xcelerator live debug screenshots remain pending because the tenant proxy currently returns selector error code `-107`.
- For the next manual capture session, use `docs/submission/live-enhancement-capture-runbook-20260616.md`.
- For final promotion, keep a `.review.json` sidecar beside each staged WFC screenshot and use `--require-review-sidecars`.
- Do not describe local smoke tests, generated dashboards, or fallback images as live WFC `ok=true` execution.
- Signed legal files, company identifiers, private contacts, and final registration screenshots remain human-owned external evidence.
