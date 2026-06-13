# Finals Latency Benchmark Report

Generated: 2026-05-22T03:49:25+00:00

## Collection Context

- Workstation collected at: 2026-06-13T12:13:40+00:00
- SSH host: `192.168.55.1`
- Remote competition directory: `/home/ryn/Wearedge-Industrial-AI-agent-competition`
- Timestamp note: benchmark `generated_at` and `tegrastats` timestamps come from the Jetson system clock.

## Boundary

This benchmark starts a dependency-light Python stdlib HTTP gateway on the final Jetson/IPC/plant edge node and measures real HTTP POST calls to /v1/workflow-canvas/decision. It uses the same jetson.competition.build_competition_decision entry point as the FastAPI gateway, but it is a fallback evidence path for environments where FastAPI/Uvicorn are not installed. It measures the collaborative decision path, not high-detail image/VLM inference.

## Summary

- Evidence tier: final_edge_stdlib_http_gateway
- Mode: http
- Endpoint: `http://127.0.0.1:33989/v1/workflow-canvas/decision`
- Dataset cases: 15
- Iterations: 20
- Samples: 300
- Target latency: <= 500 ms
- Target met: True

## Gateway

- App: `scripts.benchmark_edge_stdlib_gateway:StdlibWorkflowCanvasGateway`
- Base URL: `http://127.0.0.1:33989`
- Healthz OK: True
- Deployment mode: `jetson_edge_stdlib_http_gateway_benchmark`
- Workflow endpoint: `/v1/workflow-canvas/decision`
- Dependency profile: `python_stdlib_no_fastapi_uvicorn`

## Resource Profile

- Available: True
- Sample count: 7
- Sample interval: 0.1 s
- Platform: Linux 5.15.148-tegra aarch64
- CPU logical/physical: 6 / None
- Total memory: 7619.93 MB

| Resource | P50 | P95 | Avg | Max |
| --- | ---: | ---: | ---: | ---: |
| Gateway process CPU | 96.77% | 108.2% | 83.22% | 108.2% |
| Gateway RSS | 21.29 MB | 21.36 MB | 21.25 MB | 21.36 MB |
| System memory | 60.82% | 60.82% | 60.81% | 60.82% |

Resource samples describe the benchmark gateway process on the node that runs this script. On Jetson, keep this profile together with tegrastats for final-round defense.

## Latency Stats

| Metric | Min | P50 | P95 | Avg | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wall-clock replay latency | 1 ms | 2 ms | 2 ms | 1.62 ms | 3 ms |
| Decision-reported latency | 1 ms | 1 ms | 1 ms | 1.0 ms | 1 ms |

## Sample Coverage

| Case | Samples | Max Wall Latency |
| --- | ---: | ---: |
| final_energy_01_peak_load_shift | 20 | 2 ms |
| final_energy_02_idle_compressor | 20 | 3 ms |
| final_energy_03_auxiliary_load | 20 | 3 ms |
| final_flexible_01_order_change | 20 | 3 ms |
| final_flexible_02_short_run_sku | 20 | 3 ms |
| final_flexible_03_line_clearance | 20 | 2 ms |
| final_maint_01_vibration_escalation | 20 | 3 ms |
| final_maint_02_bearing_heat | 20 | 3 ms |
| final_maint_03_pump_anomaly | 20 | 2 ms |
| final_quality_01_lot_containment | 20 | 2 ms |
| final_quality_02_first_piece_reject | 20 | 2 ms |
| final_quality_03_camera_confidence | 20 | 2 ms |
| final_wfc_01_dashboard_reuse | 20 | 2 ms |
| final_wfc_02_human_gate_mapping | 20 | 2 ms |
| final_wfc_03_resource_binding_two_lines | 20 | 2 ms |

## Next Evidence Upgrade

- Keep the generated JSON/report together with Jetson `tegrastats` logs as final-edge HTTP decision-path evidence.
- If FastAPI/Uvicorn become available on the edge node, rerun `scripts/collect_jetson_edge_evidence.py --allow-remote-pip-install` to upgrade this fallback evidence to FastAPI gateway evidence.
- Keep the stdlib fallback boundary visible; it proves edge execution of the same deterministic decision engine, not the full production gateway stack.
- Keep this report separate from model image-inference latency; it measures the Workflow Canvas collaborative decision path.
