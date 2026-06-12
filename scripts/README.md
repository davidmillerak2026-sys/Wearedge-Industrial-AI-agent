# Scripts

Operational scripts for Jetson setup, model service startup, smoke tests, and PoC validation.

| Script | Purpose |
| --- | --- |
| [`setup_jetson.sh`](setup_jetson.sh) | Install baseline Jetson packages and Python environment. |
| [`build_llama_cpp.sh`](build_llama_cpp.sh) | Build llama.cpp for Jetson CUDA inference. |
| [`download_models.sh`](download_models.sh) | Download model files when network access is available. |
| [`run_llama_server.sh`](run_llama_server.sh) | Start llama.cpp server with the configured text model and mmproj. |
| [`run_fastapi.sh`](run_fastapi.sh) | Start the WearEdge FastAPI gateway. |
| [`smoke_test.sh`](smoke_test.sh) | Verify gateway health, llama text path, image upload, output contract, audit, and agent runs. |
| [`validate_agent_pocs.py`](validate_agent_pocs.py) | Run golden five-agent validation scenarios. |
| [`run_competition_eval.py`](run_competition_eval.py) | Run offline competition-target evaluation and generate the Markdown report. |
| [`run_finals_validation.py`](run_finals_validation.py) | Run the expanded final-round offline validation set and generate direction coverage, KPI, and primary-direction balance evidence. |
| [`benchmark_workflow_canvas_latency.py`](benchmark_workflow_canvas_latency.py) | Replay the final-round Workflow Canvas collaborative decision path and generate latency report/JSON evidence; use `--base-url` for deployed gateway benchmarking. |
| [`benchmark_local_gateway_latency.py`](benchmark_local_gateway_latency.py) | Start the local Wearedge FastAPI gateway, benchmark real HTTP calls to `/v1/workflow-canvas/decision`, sample gateway CPU/RSS/system memory, and write local-gateway latency/resource evidence. |
| [`benchmark_edge_stdlib_gateway.py`](benchmark_edge_stdlib_gateway.py) | Start a dependency-light Python stdlib HTTP gateway for Jetson/IPC evidence when FastAPI/Uvicorn are unavailable; it reuses the same Workflow Canvas decision engine and marks the evidence boundary. |
| [`collect_edge_runtime_evidence.py`](collect_edge_runtime_evidence.py) | Copy or rerun the HTTP gateway latency/resource benchmark into ignored live evidence files under `submission-assets/live-evidence/edge-runtime/`. |
| [`collect_jetson_edge_evidence.py`](collect_jetson_edge_evidence.py) | Deploy the competition runtime to a Jetson over SSH, run the final-edge HTTP/resource benchmark, collect `tegrastats`, and pull evidence back without storing SSH secrets; falls back to the stdlib gateway when FastAPI dependencies are absent. |
| [`verify_finals_foundation.py`](verify_finals_foundation.py) | Verify the final-round foundation: direction coverage, >=90% decision accuracy, <=500ms latency, WFC/Xcelerator execution skeleton, and HMI baseline without claiming finals completion. |
| [`smoke_workflow_canvas_decision.py`](smoke_workflow_canvas_decision.py) | Smoke test the Workflow Canvas decision payload in-process or against a running gateway. |
| [`package_wfc_resource_block.py`](package_wfc_resource_block.py) | Build a deterministic Gongyi Mofang WFC resource block zip and manifest under ignored `submission-assets/live-evidence/`. |
| [`build_final_submission_bundle.py`](build_final_submission_bundle.py) | Build the repo-controlled final submission bundle zip and manifest while excluding live screenshots, signed legal files, and registration screenshots by default. |
| [`prepare_final_human_action_pack.py`](prepare_final_human_action_pack.py) | Generate ignored templates for final enterprise-owned legal/contact files, registration screenshots, and live WFC replacement checklists without satisfying verifier targets. |
| [`promote_wfc_live_evidence.py`](promote_wfc_live_evidence.py) | Promote reviewed live Gongyi Mofang Dashboard/run-log/HumanApprovalGate screenshots from an ignored staging folder, remove fallback markers, and write a replacement manifest. |
| [`verify_final_external_assets.py`](verify_final_external_assets.py) | Validate ignored final human/platform assets without printing private values: signed PDFs, contact Markdown, registration screenshots, final video, and live WFC replacements. |
| [`generate_final_readiness_report.py`](generate_final_readiness_report.py) | Generate a one-page final readiness report that combines repository readiness, live evidence status, submission bundle presence, human templates, and remaining gaps. |
| [`generate_final_action_board.py`](generate_final_action_board.py) | Generate the current final action board: WFC fallback replacements, six human-owned final files, and validation commands. |
| [`run_final_readiness_pipeline.py`](run_final_readiness_pipeline.py) | Refresh the final human templates, WFC resource package, repo-controlled submission bundle, manifests, and final readiness report in one safe local command. |
| [`build_submission_evidence.py`](build_submission_evidence.py) | Generate JSON and Markdown evidence snapshots for the submission package. |
| [`verify_submission_package.py`](verify_submission_package.py) | Check Phase A-E repository deliverables, generated evidence, registration fields, and deadline markers. |
| [`verify_live_evidence.py`](verify_live_evidence.py) | Initialize and check ignored Xcelerator, Gongyi Mofang, edge runtime, video, legal, and submission evidence assets. |
| [`wfc_private_api_probe.py`](wfc_private_api_probe.py) | Read-only Gongyi Mofang private API probe for project-file, workflow JSON, data-table, Dashboard Explorer, and log-manager diagnosis; requires credentials through local environment variables and redacts them from output. |
| [`capture_dashboard_mock.py`](capture_dashboard_mock.py) | Capture the Dashboard mock to a local ignored screenshot under `submission-assets/screenshots/`. |
| [`capture_submission_screenshots.py`](capture_submission_screenshots.py) | Batch-render README, reports, payloads, CLI outputs, and the Dashboard mock into local ignored screenshots. |
| [`generate_enterprise_demo_video.py`](generate_enterprise_demo_video.py) | Generate the 3-5 minute enterprise-group demo MP4 and final narration under ignored `submission-assets/live-evidence/video/`. |
| [`network_diagnostics.sh`](network_diagnostics.sh) | Capture router, DNS, GitHub, Hugging Face, and mirror connectivity diagnostics. |
| [`run_maintenance_session_poc.sh`](run_maintenance_session_poc.sh) | Exercise multi-evidence lao-shi-fu maintenance session flow. |

## Script Rule

Scripts should be repeatable and safe to run on a clean Jetson clone. Keep generated packages, logs, and temporary outputs outside Git.
