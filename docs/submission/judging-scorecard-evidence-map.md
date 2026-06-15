# Judging Scorecard Evidence Map

Updated: 2026-06-11

Purpose: map the enterprise-group judging criteria to Wearedge's exact claims, repository evidence, live evidence, and final proof gaps. Use this as the defense checklist before submission and presentation.

## Scorecard Summary

| Judging dimension | Weight | Wearedge winning claim | Strongest evidence | Current status |
| --- | ---: | --- | --- | --- |
| Innovation | 30% | Edge-side industrial agent runtime, not a cloud chatbot; Xcelerator/Gongyi Mofang orchestrates safe workflow closure. | `docs/edge-agent-runtime-for-xcelerator.md`, `/v1/edge/runtime-profile`, WFC resource package, enterprise demo video. | Strong repo, edge, and platform evidence; final human-owned files remain. |
| Technical level | 30% | Verifiable API, deterministic KPI evaluator, WFC resource/function block, OpenAPI import, tests and smoke scripts. | `openapi/wearedge-xcelerator-apiworld.openapi.json`, `scripts/run_competition_eval.py`, `scripts/smoke_workflow_canvas_decision.py`, `wfc-blocks/wearedge-agent-service/`. | Strong; repo verifier passes. |
| Application prospect | 20% | Multi-SKU manufacturing customers can reduce downtime, defects, energy waste, and changeover coordination cost. | `docs/submission/business-plan.md`, `docs/submission/registration-fields.md`, `docs/competition-offline-eval-report.md`. | Strong narrative; real customer ROI remains PoC-stage. |
| Team ability | 10% | Enterprise-group delivery plan, IT/OT roles, IP/compliance boundary, Siemens co-creation path. | `docs/submission/team-and-company-info-template.md`, `docs/submission/company-info-and-compliance-intake.md`, `docs/submission/final-human-action-runbook.md`. | Requires final enterprise owner information and signed commitments. |
| Feasibility | 10% | Dual-path demo: live platform evidence where available, local API and generated assets as fallback, with honest boundaries. | `docs/submission/live-platform-evidence-runbook.md`, `scripts/verify_live_evidence.py`, `scripts/build_final_submission_bundle.py`, `submission-assets/live-evidence/`. | Platform stage ready; final stage waits on 6 human/external files. |

## Claim-To-Evidence Map

| Claim | Evidence to show | Boundary language |
| --- | --- | --- |
| Wearedge can run on edge compute such as Jetson / IPC / local industrial PC. | `docs/edge-agent-runtime-for-xcelerator.md`, edge runtime screenshots, `/v1/edge/runtime-profile`. | Current evidence proves PoC/runtime readiness; production deployment needs site-specific hardening and customer validation. |
| Wearedge integrates with Xcelerator API World. | Xcelerator app/API draft screenshots, 4-endpoint OpenAPI import, `docs/xcelerator-apiworld-onboarding.md`. | Service remains unpublished/tenant-only unless explicitly approved for publication. |
| Wearedge integrates with Gongyi Mofang WFC. | WFC project screenshots, Python block saved as `CallWearedgeDecisionApi`, data-table fields, WFC resource package zip, live WFC `ok=true` run-log screenshot, live Dashboard, and live HumanApprovalGate evidence. | Dynamic data-table writeback should be described as a strengthening item until final native value-change proof is captured. |
| Decisions are not model-only. | `jetson.competition.build_competition_decision()`, offline eval report, tests, technical solution. | Model explains and structures evidence; deterministic evaluator and HumanApprovalGate control action boundaries. |
| Wearedge covers at least three industrial-agent directions. | Workflow Canvas decision JSON, offline dataset, eval report, registration fields. | Current coverage is offline/simulated PoC until joint platform PoC data is collected. |
| High-risk OT actions remain safe. | `HumanApprovalGate` language in API response, dashboard mock, technical solution, business plan. | Never claim direct PLC/robot/quality release control by the model. |

## Must-Say Phrases

- Wearedge's core differentiation is putting the industrial agent runtime near the production line, then letting Xcelerator / Gongyi Mofang orchestrate workflow, approvals, and writeback.
- The model is an evidence interpreter and recommendation generator; deterministic guards and human approval define the final action boundary.
- Current first-round metrics are simulated/offline engineering validation. Live Xcelerator and Gongyi Mofang evidence proves platform integration path; customer production proof belongs to the joint PoC phase.
- The project is enterprise-deliverable: API, OpenAPI, WFC resource package, edge runtime profile, evaluation scripts, bundle builder, and compliance templates are all repeatable.

## Must-Not-Say Phrases

- Do not describe any future fallback/mock WFC image as live WFC execution.
- Do not say Wearedge has been deployed to a real customer production line unless customer-authorized logs exist.
- Do not say Gemma 4 E2B or any foundation model is self-developed.
- Do not say the model directly controls PLC, robot, stop-line, or quality release decisions.
- Do not expose WFC password, session cookie, Xcelerator AppSecret, AppID screenshots, or company certificate numbers.

## Final Gaps Before Submission

| Gap | Proof file | Owner |
| --- | --- | --- |
| Company and contact values | `submission-assets/live-evidence/legal/company-info-filled.md` | Enterprise owner |
| Signed IP/no-dispute statement | `submission-assets/live-evidence/legal/ip-and-no-dispute-signed.pdf` | Enterprise owner |
| Signed no-adverse-record statement | `submission-assets/live-evidence/legal/no-adverse-record-signed.pdf` | Enterprise owner |
| Submission contact confirmation | `submission-assets/live-evidence/legal/submission-contact-confirmation.md` | Final submitter |
| Filled registration screenshot | `submission-assets/live-evidence/submission/01-registration-form-filled.png` | Final submitter |
| Submission success screenshot | `submission-assets/live-evidence/submission/02-submission-success.png` | Final submitter |

## Final Verification Commands

```powershell
python scripts/verify_submission_package.py --write-manifest
python scripts/verify_live_evidence.py --stage final --allow-missing --write-manifest
python scripts/build_final_submission_bundle.py --json
python scripts/prepare_final_human_action_pack.py --json
```
