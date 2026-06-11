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
| [`smoke_workflow_canvas_decision.py`](smoke_workflow_canvas_decision.py) | Smoke test the Workflow Canvas decision payload in-process or against a running gateway. |
| [`build_submission_evidence.py`](build_submission_evidence.py) | Generate JSON and Markdown evidence snapshots for the submission package. |
| [`verify_submission_package.py`](verify_submission_package.py) | Check Phase A-E repository deliverables, generated evidence, registration fields, and deadline markers. |
| [`verify_live_evidence.py`](verify_live_evidence.py) | Initialize and check ignored Xcelerator, Gongyi Mofang, edge runtime, video, legal, and submission evidence assets. |
| [`capture_dashboard_mock.py`](capture_dashboard_mock.py) | Capture the Dashboard mock to a local ignored screenshot under `submission-assets/screenshots/`. |
| [`capture_submission_screenshots.py`](capture_submission_screenshots.py) | Batch-render README, reports, payloads, CLI outputs, and the Dashboard mock into local ignored screenshots. |
| [`generate_enterprise_demo_video.py`](generate_enterprise_demo_video.py) | Generate the 3-5 minute enterprise-group demo MP4 and final narration under ignored `submission-assets/live-evidence/video/`. |
| [`network_diagnostics.sh`](network_diagnostics.sh) | Capture router, DNS, GitHub, Hugging Face, and mirror connectivity diagnostics. |
| [`run_maintenance_session_poc.sh`](run_maintenance_session_poc.sh) | Exercise multi-evidence lao-shi-fu maintenance session flow. |

## Script Rule

Scripts should be repeatable and safe to run on a clean Jetson clone. Keep generated packages, logs, and temporary outputs outside Git.
