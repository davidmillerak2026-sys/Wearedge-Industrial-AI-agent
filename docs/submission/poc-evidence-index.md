# PoC Evidence Index

更新日期：2026-06-12

## 当前可提交证据

| Evidence | Path | Status |
| --- | --- | --- |
| Siemens co-creation one-pager | `docs/siemens-xcelerator-co-creation-onepager.md` | ready |
| Siemens industrial agent track memory | `docs/siemens-industrial-agent-track-memory-20260521.md` | ready |
| Gongyi Mofang Workflow Canvas memory | `docs/gongyi-mofang-workflow-canvas-memory-202604.md` | ready |
| Edge Agent Runtime for Xcelerator | `docs/edge-agent-runtime-for-xcelerator.md` | ready |
| Edge runtime evidence runbook | `docs/submission/edge-runtime-evidence-runbook.md` | ready |
| Enterprise group winning strategy | `docs/submission/enterprise-winning-strategy.md` | ready |
| Finals foundation roadmap | `docs/submission/finals-foundation-roadmap.md` | ready |
| Judging scorecard evidence map | `docs/submission/judging-scorecard-evidence-map.md` | ready |
| Defense Q&A playbook | `docs/submission/defense-qna-playbook.md` | ready |
| Xcelerator API World onboarding notes | `docs/xcelerator-apiworld-onboarding.md` | ready |
| Xcelerator OpenAPI import spec | `openapi/wearedge-xcelerator-apiworld.openapi.json` | ready |
| WFC resource block prototype | `wfc-blocks/wearedge-agent-service/` | ready |
| WFC resource block package builder | `scripts/package_wfc_resource_block.py` | ready |
| Competition requirements and optimization direction | `docs/赛事要求与Wearedge智能体优化方向.md` | ready |
| Workflow Canvas API schema | `docs/workflow-canvas-api-schema.md` | ready |
| Workflow Canvas PoC runbook | `docs/workflow-canvas-poc-runbook.md` | ready |
| Workflow Canvas payload | `workflows/wearedge_wfc_poc_payload.json` | ready |
| Offline evaluation dataset | `evals/competition_offline_dataset.jsonl` | ready |
| Offline evaluation script | `scripts/run_competition_eval.py` | ready |
| Finals validation dataset | `evals/finals_validation_dataset.jsonl` | ready |
| Finals validation report | `docs/finals-validation-report.md` | generated |
| Finals validation script | `scripts/run_finals_validation.py` | ready |
| Finals latency benchmark report | `docs/finals-latency-benchmark-report.md` | generated |
| Finals latency benchmark JSON | `docs/submission/evidence/finals-latency-benchmark.json` | generated |
| Finals latency benchmark script | `scripts/benchmark_workflow_canvas_latency.py` | ready |
| Local FastAPI gateway latency/resource report | `docs/finals-local-gateway-latency-benchmark-report.md` | generated |
| Local FastAPI gateway latency/resource JSON | `docs/submission/evidence/finals-local-gateway-latency-benchmark.json` | generated |
| Local FastAPI gateway benchmark script | `scripts/benchmark_local_gateway_latency.py` | ready |
| Edge stdlib gateway benchmark script | `scripts/benchmark_edge_stdlib_gateway.py` | ready |
| Edge runtime evidence collector | `scripts/collect_edge_runtime_evidence.py` | ready |
| Finals foundation verifier | `scripts/verify_finals_foundation.py` | ready |
| Workflow Canvas smoke script | `scripts/smoke_workflow_canvas_decision.py` | ready |
| Submission evidence snapshots | `docs/submission/evidence/` | ready |
| Live platform evidence runbook | `docs/submission/live-platform-evidence-runbook.md` | ready |
| Xcelerator live evidence status | `docs/submission/platform-live-evidence-status-20260609.md` | ready |
| Live evidence verifier | `scripts/verify_live_evidence.py` | ready |
| Repo-controlled submission bundle builder | `scripts/build_final_submission_bundle.py` | ready |
| Final human action runbook | `docs/submission/final-human-action-runbook.md` | ready |
| Final human template generator | `scripts/prepare_final_human_action_pack.py` | ready |
| Final readiness report | `docs/submission/final-readiness-report.md` | generated |
| Final action board | `docs/submission/final-action-board.md` | generated |
| Final readiness pipeline | `scripts/run_final_readiness_pipeline.py` | ready |
| Demo video production plan | `docs/submission/video-production-plan.md` | ready |
| Company info and compliance intake | `docs/submission/company-info-and-compliance-intake.md` | ready |
| Dashboard mock | `docs/submission/dashboard-mock.html` | ready |
| Finals HMI decision console | `docs/submission/finals-hmi-console.html` | ready |
| Capture runbook | `docs/submission/capture-runbook.md` | ready |
| Technical architecture | `docs/technical_architecture.md` | ready |
| Technical evidence | `docs/technical-evidence.md` | ready |

## Evidence Boundaries

- Current offline evaluation is simulated and repository-local.
- Finals validation is now checked by `scripts/run_finals_validation.py --json`; it uses 15 simulated final-round cases, covers all five directions, and represents each primary direction 3 times.
- Finals latency replay is checked by `scripts/benchmark_workflow_canvas_latency.py`; the default `in_process` mode measures deterministic local replay of the Workflow Canvas collaborative decision path and must be upgraded with `--base-url http://<edge-host>:<port>` before claiming deployed endpoint latency.
- Local FastAPI gateway latency/resource evidence is checked by `scripts/benchmark_local_gateway_latency.py`; it starts the Wearedge gateway locally, measures real HTTP calls to `/v1/workflow-canvas/decision`, and samples gateway CPU/RSS/system memory, but it is still workstation evidence until rerun on Jetson / IPC.
- Edge stdlib gateway evidence is checked by `scripts/benchmark_edge_stdlib_gateway.py`; it exists for Jetson/IPC nodes without FastAPI/Uvicorn, uses the same `jetson.competition.build_competition_decision()` entry point, and must be described as fallback HTTP decision-path evidence rather than full FastAPI production-gateway evidence.
- Ignored live edge-runtime evidence is collected by `scripts/collect_edge_runtime_evidence.py`; it writes `edge-runtime/06-http-resource-benchmark.*` and `edge-runtime/07-edge-runtime-evidence-manifest.md` under `submission-assets/live-evidence/`.
- Finals foundation is checked by `scripts/verify_finals_foundation.py --json`; it verifies direction coverage, decision accuracy, latency, platform skeleton, and HMI baseline while explicitly keeping finals completion separate from foundation readiness.
- Current Xcelerator integration has live draft evidence: Wearedge app group, app draft, API service draft, current application home, current API detail, and current 4-endpoint API list are captured under `submission-assets/live-evidence/xcelerator/`.
- Current WFC integration has real Gongyi Mofang project evidence: authenticated project page, `Wearedge WFC PoC` project, Python function block, data-table fields, `fb_main.py` saved into the live Python block, DEBUG entry, and `Workflow is ready` log-manager evidence.
- WFC resource package zip is generated locally under ignored `submission-assets/live-evidence/gongyi-mofang/wfc-resource-package/` by `scripts/package_wfc_resource_block.py`; it is a reusable prototype attachment, not proof of live platform execution.
- Repo-controlled final submission bundle is generated locally under ignored `submission-assets/live-evidence/submission-bundle/` by `scripts/build_final_submission_bundle.py`; it excludes live screenshots, signed legal files, company identifiers, and final registration screenshots by default.
- Final human-owned templates are generated locally under ignored `submission-assets/live-evidence/` by `scripts/prepare_final_human_action_pack.py`; they use `.template.*` names and do not satisfy final verifier targets until signed/filled/captured files are created.
- Final readiness pipeline is run by `scripts/run_final_readiness_pipeline.py --json`; it refreshes final human templates, the WFC resource package, the repo-controlled submission bundle, manifests, and `docs/submission/final-readiness-report.md`.
- Final action board is generated by `scripts/generate_final_action_board.py --write`; it turns the current verifier output into the remaining WFC 04/05/06 replacement tasks, six human-owned final files, and validation command sequence.
- Dashboard, `ok=true` run log, and HumanApprovalGate now have fallback demo assets under `submission-assets/live-evidence/gongyi-mofang/04-06*`; they are visibly marked or metadata-marked as mock/API-smoke evidence and must not be described as live WFC `ok=true` proof until the platform workflow execution is reproduced end to end.
- Current edge runtime profile is API-ready and can be captured locally through `GET /v1/edge/runtime-profile`.
- Gongyi Mofang source documents have been reviewed and distilled into a project memory card, but screenshots must still be produced from the live WFC account.
- High-risk actions are routed through human confirmation, not direct OT control.
- Live Gongyi screenshots, signed company materials, and video should be stored under `submission-assets/live-evidence/` and checked with `python scripts/verify_live_evidence.py --stage final`.
