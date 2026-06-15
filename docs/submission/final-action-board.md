# Final Action Board

Updated: 2026-06-15T07:17:02+00:00

## Current Gate

- Repository ready: True
- Finals foundation ready: True
- Finals ready: False
- Final external evidence ready: False
- Final missing files: 6
- Fallback warnings: 0
- Edge latency evidence tier: final_edge_fastapi_http_gateway
- Edge HTTP samples: 300
- Edge HTTP p95/max latency: 6 / 8 ms

## Do Next

1. Keep the current WFC live evidence set; recapture only if workflow code, dashboard fields, or approval UI changes.
2. Complete the six enterprise-owned legal/contact/submission evidence files.
3. Run `python scripts/verify_final_external_assets.py --write-report` after signed PDFs, final screenshots, video, and live WFC evidence are in place.
4. Run `python scripts/run_final_readiness_pipeline.py --json` and `python scripts/verify_live_evidence.py --stage final --write-manifest` before final upload.

## WFC Live Replacement

| Status | Target | Owner | Action | Acceptance |
| --- | --- | --- | --- | --- |
| present | `gongyi-mofang/04-dashboard-decision-view.png` | WFC operator | Create or preview the real WFC Dashboard/ui-builder view. | Shows Wearedge metric cards, decision path, approval items, and workflow state from live WFC context. |
| present | `gongyi-mofang/05-run-log-ok-true.png` | WFC operator | Keep the reviewed live WFC run-log screenshot; recapture only if workflow code changes. | Shows WFC-native CallWearedgeDecisionApi.output JSON beginning with ok=true; data-table writeback is tracked separately. |
| present | `gongyi-mofang/06-human-approval-gate.png` | WFC operator | Show HumanApprovalGate or approval-state panel for a high-risk recommendation. | Shows pending/approved/rejected human confirmation; model is not directly controlling OT. |

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
- Current WFC replacement targets should have no fallback metadata; preserve reviewed live evidence sidecars and recapture from WFC only when the workflow changes.
- For final promotion, keep a `.review.json` sidecar beside each staged WFC screenshot and use `--require-review-sidecars`.
- Do not describe local smoke tests, generated dashboards, or fallback images as live WFC `ok=true` execution.
- Signed legal files, company identifiers, private contacts, and final registration screenshots remain human-owned external evidence.
