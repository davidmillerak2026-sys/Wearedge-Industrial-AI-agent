# Final Human Action Runbook

Updated: 2026-06-11

This runbook covers the final files that must be completed by the enterprise owner or final submitter. These files are intentionally not committed to Git because they may contain company identifiers, contact details, signed statements, or registration-system screenshots.

## Generate Templates

```powershell
python scripts/prepare_final_human_action_pack.py --json
python scripts/generate_final_action_board.py --write
```

The command writes templates under ignored `submission-assets/live-evidence/` and does not create the final verifier target files. This avoids accidentally treating unsigned or incomplete files as final evidence.
The action board at `docs/submission/final-action-board.md` is regenerated from the current verifiers and should be treated as the short list of what remains.

## Final Required Files

| Final target | Owner | How to complete |
| --- | --- | --- |
| `submission-assets/live-evidence/legal/company-info-filled.md` | Enterprise owner | Copy from `legal/company-info-filled.template.md`, fill final enterprise name, unified social credit code, contacts, team roles, and eligibility confirmations. |
| `submission-assets/live-evidence/legal/ip-and-no-dispute-signed.pdf` | Enterprise owner | Use `legal/ip-and-no-dispute-statement.template.md`, then sign/stamp and export to PDF. |
| `submission-assets/live-evidence/legal/no-adverse-record-signed.pdf` | Enterprise owner | Use `legal/no-adverse-record-statement.template.md`, then sign/stamp and export to PDF. |
| `submission-assets/live-evidence/legal/submission-contact-confirmation.md` | Final submitter | Copy from `legal/submission-contact-confirmation.template.md` and fill primary/backup contacts. |
| `submission-assets/live-evidence/submission/01-registration-form-filled.png` | Final submitter | Capture the filled registration page before final submit. Hide certificate numbers and private contact fields when reused outside the submission system. |
| `submission-assets/live-evidence/submission/02-submission-success.png` | Final submitter | Capture the official success/submitted status after final submit. |

## WFC Fallback Replacement

Current platform evidence is enough for platform-stage readiness, but final judging language must stay honest while `04/05/06` Gongyi Mofang assets are fallback-marked.

Replace these when live WFC execution is reproduced:

| Target | Required live proof |
| --- | --- |
| `submission-assets/live-evidence/gongyi-mofang/04-dashboard-decision-view.png` | Real WFC Dashboard/ui-builder showing Wearedge metric cards, decision path, approval items, and workflow state. |
| `submission-assets/live-evidence/gongyi-mofang/05-run-log-ok-true.png` | Real log-manager or run panel showing `wearedge_decision_ok=True`, `ok=true`, latency, function-block output, or successful data-table writeback. |
| `submission-assets/live-evidence/gongyi-mofang/06-human-approval-gate.png` | Real HumanApprovalGate or approval-state view showing pending/approved/rejected handling. |

Only remove or supersede `.fallback.json` metadata after real live evidence is captured and documented.

## Verification

Before final submission:

```powershell
python scripts/run_final_readiness_pipeline.py --json
python scripts/verify_live_evidence.py --stage final --write-manifest
python scripts/verify_final_external_assets.py --write-report
python scripts/verify_submission_package.py --write-manifest
python scripts/build_final_submission_bundle.py --json
```

Expected state before the enterprise-owned files are completed:

```text
verify_submission_package: repo_ready=True
verify_live_evidence --stage final: ready=False, missing_count=6
```

Expected state after the enterprise-owned files are completed:

```text
verify_live_evidence --stage final: ready=True, missing_count=0
```

## Redaction Rules

- Do not commit anything under `submission-assets/live-evidence/`.
- Do not store WFC password, session cookie, Xcelerator AppSecret, or API tokens in any file.
- Do not reuse screenshots with full certificate numbers, AppID/AppSecret, tokens, or private contact details in public materials.
- Do not describe fallback/mock WFC evidence as live WFC `ok=true` execution.
