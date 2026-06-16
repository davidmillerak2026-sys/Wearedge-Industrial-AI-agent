# PoC Evidence Index

更新日期：2026-06-16

## 当前可提交证据

| Evidence | Path | Status |
| --- | --- | --- |
| Siemens co-creation one-pager | `docs/siemens-xcelerator-co-creation-onepager.md` | ready |
| Siemens industrial agent track memory | `docs/siemens-industrial-agent-track-memory-20260521.md` | ready |
| Gongyi Mofang Workflow Canvas memory | `docs/gongyi-mofang-workflow-canvas-memory-202604.md` | ready |
| Edge Agent Runtime for Xcelerator | `docs/edge-agent-runtime-for-xcelerator.md` | ready |
| Edge runtime evidence runbook | `docs/submission/edge-runtime-evidence-runbook.md` | ready |
| Enterprise group winning strategy | `docs/submission/enterprise-winning-strategy.md` | ready |
| Siemens track official review | `docs/submission/siemens-track-official-review-20260616.md` | ready |
| Finals foundation roadmap | `docs/submission/finals-foundation-roadmap.md` | ready |
| Judging scorecard evidence map | `docs/submission/judging-scorecard-evidence-map.md` | ready |
| Defense Q&A playbook | `docs/submission/defense-qna-playbook.md` | ready |
| Xcelerator API World onboarding notes | `docs/xcelerator-apiworld-onboarding.md` | ready |
| Xcelerator OpenAPI import spec | `openapi/wearedge-xcelerator-apiworld.openapi.json` | ready |
| WFC resource block prototype | `wfc-blocks/wearedge-agent-service/` | ready |
| WFC resource block package builder | `scripts/package_wfc_resource_block.py` | ready |
| WFC workflow binding analyzer | `scripts/analyze_wfc_workflow_bindings.py` | ready |
| WFC live edit package builder | `scripts/prepare_wfc_live_edit_package.py` | ready |
| WFC dynamic writeback closure plan | `docs/submission/wfc-writeback-and-stable-endpoint-closure.md` | ready |
| Stable endpoint verifier | `scripts/verify_stable_wearedge_endpoint.py` | ready |
| Xcelerator proxy verifier | `scripts/verify_xcelerator_proxy.py` | ready |
| Stable endpoint deployment pack | `deploy/stable-endpoint/` | ready |
| Google Cloud Run deployment pack | `Dockerfile.cloudrun`, `deploy/cloud-run/` | ready |
| Cloud Run stable endpoint evidence summary | `docs/submission/cloud-run-stable-endpoint-evidence-20260616.md` | generated |
| Xcelerator proxy verification record | `docs/submission/xcelerator-proxy-verification-20260616.md` | generated |
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
| Jetson edge FastAPI gateway latency/resource report | `docs/finals-jetson-gateway-latency-benchmark-report.md` | generated |
| Jetson edge FastAPI gateway latency/resource JSON | `docs/submission/evidence/finals-jetson-gateway-latency-benchmark.json` | generated |
| Edge stdlib gateway benchmark script | `scripts/benchmark_edge_stdlib_gateway.py` | ready |
| Jetson edge evidence collector | `scripts/collect_jetson_edge_evidence.py` | ready |
| Edge runtime evidence collector | `scripts/collect_edge_runtime_evidence.py` | ready |
| Finals foundation verifier | `scripts/verify_finals_foundation.py` | ready |
| Workflow Canvas smoke script | `scripts/smoke_workflow_canvas_decision.py` | ready |
| Submission evidence snapshots | `docs/submission/evidence/` | ready |
| Live platform evidence runbook | `docs/submission/live-platform-evidence-runbook.md` | ready |
| Live enhancement manual capture runbook | `docs/submission/live-enhancement-capture-runbook-20260616.md` | ready |
| Xcelerator live evidence status | `docs/submission/platform-live-evidence-status-20260609.md` | ready |
| Live evidence verifier | `scripts/verify_live_evidence.py` | ready |
| Final external assets quality verifier | `scripts/verify_final_external_assets.py` | ready |
| Repo-controlled submission bundle builder | `scripts/build_final_submission_bundle.py` | ready |
| Final human action runbook | `docs/submission/final-human-action-runbook.md` | ready |
| Final human template generator | `scripts/prepare_final_human_action_pack.py` | ready |
| Final readiness report | `docs/submission/final-readiness-report.md` | generated |
| Final action board | `docs/submission/final-action-board.md` | generated |
| Final readiness pipeline | `scripts/run_final_readiness_pipeline.py` | ready |
| Demo video production plan | `docs/submission/video-production-plan.md` | ready |
| Company info and compliance intake | `docs/submission/company-info-and-compliance-intake.md` | ready |
| First-round submission attachment index | `docs/submission/first-round-submission-attachment-index.md` | ready |
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
- Edge stdlib gateway evidence is checked by `scripts/benchmark_edge_stdlib_gateway.py`; it exists for Jetson/IPC nodes without FastAPI/Uvicorn, uses the same `jetson.competition.build_competition_decision()` entry point, and must be described as fallback HTTP decision-path evidence.
- Jetson live edge evidence is collected by `scripts/collect_jetson_edge_evidence.py`; the latest 2026-06-15 FastAPI rerun used SSH host `wearedge-pro.local` and isolated remote directory `/home/ryn/Wearedge-Industrial-AI-agent-fastapi-competition`, produced 300 iterations / 4500 HTTP decision samples on the Jetson FastAPI gateway, and met the <=500 ms target with wall-clock P95 6 ms and max 33 ms. The public report/JSON are stored under `docs/`; the raw `tegrastats` and collection files remain ignored under `submission-assets/live-evidence/edge-runtime/`.
- Ignored live edge-runtime evidence is collected by `scripts/collect_edge_runtime_evidence.py`; it writes `edge-runtime/06-http-resource-benchmark.*` and `edge-runtime/07-edge-runtime-evidence-manifest.md` under `submission-assets/live-evidence/`.
- Finals foundation is checked by `scripts/verify_finals_foundation.py --json`; it verifies direction coverage, decision accuracy, latency, platform skeleton, and HMI baseline while explicitly keeping finals completion separate from foundation readiness.
- Current Xcelerator integration has live draft evidence: Wearedge app group, app draft, API service draft, current application home, current API detail, current 4-endpoint API list, and 2026-06-16 Cloud Run backend replacement screenshots are captured under `submission-assets/live-evidence/xcelerator/`.
- Current WFC integration has real Gongyi Mofang project evidence: authenticated project page, `Wearedge WFC PoC` project, Python function block, data-table fields, live `fb_main.py` source search showing Wearedge `_summary` fields, DEBUG entry, `Workflow is ready` log-manager evidence, 2026-06-12 WFC/SPIDR -> Wearedge gateway `POST /v1/workflow-canvas/decision` `200 OK` auxiliary live-call evidence, 2026-06-12 native WFC run-state screenshots showing `CallWearedgeDecisionApi` with output `状态码 Good`, 2026-06-13 live WFC native run log `CallWearedgeDecisionApi.output` with JSON beginning `"ok": true` promoted to `05-run-log-ok-true.png`, live `更新数据表.1` binding screenshots showing `selected_direction`, `priority`, `recommended_action`, and `approval_status` mapped into the WFC global data-table update block, 2026-06-13 WFC native `更新数据表.1` static input evidence where `selected_direction=maintenance`, `priority=P1`, `recommended_action=Inspect bearing vibration...`, and `approval_status=pending_human_approval` are visible and locked during DEBUG, and 2026-06-16 live WFC DEBUG evidence where新版 `CallWearedgeDecisionApi.output` shows `ok=true`, `状态码 Good`, and `wfc_writeback.method=wfc_output1_to_update_data_table` after a real `POST /v1/workflow-canvas/decision` through the temporary HTTPS PoC endpoint.
- `scripts/analyze_wfc_workflow_bindings.py` is now the offline gate for exported WFC `workflow.json`: it reports whether `CallWearedgeDecisionApi` has a confirmed `输出1` data connection into `更新数据表.1`, without calling or modifying the platform.
- WFC resource package zip is generated locally under ignored `submission-assets/live-evidence/gongyi-mofang/wfc-resource-package/` by `scripts/package_wfc_resource_block.py`; it is a reusable prototype attachment, not proof of live platform execution.
- Repo-controlled final submission bundle is generated locally under ignored `submission-assets/live-evidence/submission-bundle/` by `scripts/build_final_submission_bundle.py`; it excludes live screenshots, signed legal files, company identifiers, and final registration screenshots by default.
- Final human-owned templates are generated locally under ignored `submission-assets/live-evidence/` by `scripts/prepare_final_human_action_pack.py`; they use `.template.*` names and do not satisfy final verifier targets until signed/filled/captured files are created.
- Final readiness pipeline is run by `scripts/run_final_readiness_pipeline.py --json`; it refreshes final human templates, the WFC resource package, the repo-controlled submission bundle, manifests, and `docs/submission/final-readiness-report.md`.
- Final action board is generated by `scripts/generate_final_action_board.py --write`; it turns the current verifier output into the remaining WFC replacement tasks, six human-owned final files, and validation command sequence.
- Final external asset quality is checked by `scripts/verify_final_external_assets.py --write-report`; it validates formats, empty/template fields, WFC fallback markers, and video presence without printing private company/contact values.
- Dashboard, run-log, and HumanApprovalGate evidence under `submission-assets/live-evidence/gongyi-mofang/04*`, `05*`, and `06*` are now treated as live WFC evidence with fallback warnings cleared. `05-run-log-ok-true.png` is a reviewed live WFC native run-log screenshot showing `CallWearedgeDecisionApi.output` with `"ok": true`.
- Dynamic Python-output-to-`更新数据表.1` writeback has one live output proof: 2026-06-16 WFC DEBUG output shows `ok=true`, `状态码 Good`, `wfc_writeback.method=wfc_output1_to_update_data_table`, and `fields_ready`; the remaining strengthening gap is a clear data-port line, exported workflow binding, or native data-table value proof showing `更新数据表.1` values changed from Python output. 2026-06-16 live debugging also showed direct Python callback writeback can hang the WFC DEBUG run, so the official WFC007 route remains `CallWearedgeDecisionApi 输出1 -> 更新数据表.1 输入`.
- Stable API endpoint evidence is now available through Google Cloud Run. `scripts/verify_stable_wearedge_endpoint.py` validates `/v1/healthz` as a Cloud Run-compatible fallback for `/healthz`, plus `/v1/edge/runtime-profile` and `/v1/workflow-canvas/decision`; the current Cloud Run URL is `https://wearedge-agent-service-863888677331.asia-east1.run.app` and verifier output is `ready=True`. Xcelerator backend replacement has been captured in live screenshots, but `scripts/verify_xcelerator_proxy.py` currently records platform code `-107` (`Can not find selector`), so remaining platform strengthening is selector/API path binding plus live Xcelerator debug/test screenshots.
- Stable endpoint deployment paths are documented in `deploy/stable-endpoint/`: enterprise HTTPS gateway, Cloudflare Named Tunnel with a bound domain, and Xcelerator API World Proxy. A localhost preflight may prove API contract only; it is not final endpoint evidence.
- The official competition page review is captured in `docs/submission/siemens-track-official-review-20260616.md`; it confirms Wearedge is aligned to the Siemens track and lists current omissions against the official page.
- Current edge runtime profile is API-ready and can be captured locally through `GET /v1/edge/runtime-profile`.
- Gongyi Mofang source documents have been reviewed and distilled into a project memory card, but screenshots must still be produced from the live WFC account.
- High-risk actions are routed through human confirmation, not direct OT control.
- Live Gongyi screenshots, signed company materials, and video should be stored under `submission-assets/live-evidence/` and checked with `python scripts/verify_live_evidence.py --stage final`.
