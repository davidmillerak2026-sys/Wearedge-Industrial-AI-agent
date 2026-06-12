# Finals Latency Benchmark Report

Generated: 2026-05-22T04:19:53+00:00

## Collection Context

- Workstation collected at: 2026-06-12T03:09:50+00:00
- SSH host: `wearedge-pro.local`
- Remote competition directory: `/home/ryn/Wearedge-Industrial-AI-agent-competition`
- Timestamp note: benchmark `generated_at` and `tegrastats` timestamps come from the Jetson system clock.

## Boundary

This benchmark starts the Wearedge FastAPI gateway on the final Jetson/IPC/plant edge node and measures real HTTP POST calls to /v1/workflow-canvas/decision with process resource sampling. It measures the collaborative decision path, not high-detail image/VLM inference.

## Summary

- Evidence tier: final_edge_fastapi_http_gateway
- Mode: http
- Endpoint: `http://127.0.0.1:46745/v1/workflow-canvas/decision`
- Dataset cases: 15
- Iterations: 20
- Samples: 300
- Target latency: <= 500 ms
- Target met: True

## Gateway

- App: `jetson.app:app`
- Base URL: `http://127.0.0.1:46745`
- Healthz OK: True
- Workflow endpoint: `jetson_edge_http_gateway_benchmark`

## Resource Profile

- Available: True
- Sample count: 13
- Sample interval: 0.1 s
- Platform: Linux 5.15.148-tegra aarch64
- CPU logical/physical: 6 / None
- Total memory: 7619.93 MB

| Resource | P50 | P95 | Avg | Max |
| --- | ---: | ---: | ---: | ---: |
| Gateway process CPU | 68.85% | 78.69% | 66.59% | 80.0% |
| Gateway RSS | 47.57 MB | 47.57 MB | 47.55 MB | 47.57 MB |
| System memory | 61.0% | 61.0% | 61.0% | 61.0% |

Resource samples describe the benchmark gateway process on the node that runs this script. On Jetson, keep this profile together with tegrastats for final-round defense.

## Latency Stats

| Metric | Min | P50 | P95 | Avg | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wall-clock replay latency | 3 ms | 4 ms | 4 ms | 3.74 ms | 7 ms |
| Decision-reported latency | 1 ms | 1 ms | 1 ms | 1.0 ms | 1 ms |

## Sample Coverage

| Case | Samples | Max Wall Latency |
| --- | ---: | ---: |
| final_energy_01_peak_load_shift | 20 | 4 ms |
| final_energy_02_idle_compressor | 20 | 4 ms |
| final_energy_03_auxiliary_load | 20 | 4 ms |
| final_flexible_01_order_change | 20 | 4 ms |
| final_flexible_02_short_run_sku | 20 | 4 ms |
| final_flexible_03_line_clearance | 20 | 4 ms |
| final_maint_01_vibration_escalation | 20 | 7 ms |
| final_maint_02_bearing_heat | 20 | 4 ms |
| final_maint_03_pump_anomaly | 20 | 4 ms |
| final_quality_01_lot_containment | 20 | 4 ms |
| final_quality_02_first_piece_reject | 20 | 4 ms |
| final_quality_03_camera_confidence | 20 | 4 ms |
| final_wfc_01_dashboard_reuse | 20 | 4 ms |
| final_wfc_02_human_gate_mapping | 20 | 4 ms |
| final_wfc_03_resource_binding_two_lines | 20 | 4 ms |

## Next Evidence Upgrade

- Keep the generated JSON/report together with Jetson `tegrastats` logs as final-edge hardware evidence.
- Rerun the same collector before final defense if the Jetson image, Python environment, or WFC payload changes.
- Keep this report separate from model image-inference latency; it measures the Workflow Canvas collaborative decision path.
