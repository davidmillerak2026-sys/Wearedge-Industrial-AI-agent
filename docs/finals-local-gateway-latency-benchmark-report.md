# Finals Latency Benchmark Report

Generated: 2026-06-12T02:20:03+00:00

## Boundary

This benchmark starts the Wearedge FastAPI gateway on the current workstation and measures real HTTP POST calls to /v1/workflow-canvas/decision with process resource sampling. It is stronger than in-process replay, but it is still not Jetson/IPC hardware evidence until rerun on the final edge node.

## Summary

- Evidence tier: local_fastapi_http_gateway
- Mode: http
- Endpoint: `http://127.0.0.1:54336/v1/workflow-canvas/decision`
- Dataset cases: 15
- Iterations: 20
- Samples: 300
- Target latency: <= 500 ms
- Target met: True

## Gateway

- App: `jetson.app:app`
- Base URL: `http://127.0.0.1:54336`
- Healthz OK: True
- Workflow endpoint: `/v1/workflow-canvas/decision`

## Resource Profile

- Available: True
- Sample count: 34
- Sample interval: 0.1 s
- Platform: Windows 10 AMD64
- CPU logical/physical: 22 / 16
- Total memory: 32373.37 MB

| Resource | P50 | P95 | Avg | Max |
| --- | ---: | ---: | ---: | ---: |
| Gateway process CPU | 14.2% | 33.2% | 14.21% | 43.0% |
| Gateway RSS | 59.85 MB | 60.6 MB | 59.86 MB | 60.71 MB |
| System memory | 49.1% | 49.2% | 49.04% | 49.2% |

Resource samples describe the benchmark gateway process on the node that runs this script. For final defense, rerun on Jetson/IPC and keep this profile with tegrastats or OS-level logs.

## Latency Stats

| Metric | Min | P50 | P95 | Avg | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wall-clock replay latency | 1 ms | 14 ms | 24 ms | 11.47 ms | 30 ms |
| Decision-reported latency | 1 ms | 1 ms | 1 ms | 1.0 ms | 1 ms |

## Sample Coverage

| Case | Samples | Max Wall Latency |
| --- | ---: | ---: |
| final_energy_01_peak_load_shift | 20 | 24 ms |
| final_energy_02_idle_compressor | 20 | 26 ms |
| final_energy_03_auxiliary_load | 20 | 27 ms |
| final_flexible_01_order_change | 20 | 24 ms |
| final_flexible_02_short_run_sku | 20 | 29 ms |
| final_flexible_03_line_clearance | 20 | 25 ms |
| final_maint_01_vibration_escalation | 20 | 23 ms |
| final_maint_02_bearing_heat | 20 | 24 ms |
| final_maint_03_pump_anomaly | 20 | 18 ms |
| final_quality_01_lot_containment | 20 | 30 ms |
| final_quality_02_first_piece_reject | 20 | 24 ms |
| final_quality_03_camera_confidence | 20 | 25 ms |
| final_wfc_01_dashboard_reuse | 20 | 25 ms |
| final_wfc_02_human_gate_mapping | 20 | 23 ms |
| final_wfc_03_resource_binding_two_lines | 20 | 22 ms |

## Next Evidence Upgrade

- Rerun `python scripts/benchmark_local_gateway_latency.py` on the Jetson / IPC / final edge gateway.
- Keep the generated report/JSON with Jetson `tegrastats` or OS-level resource logs before final-round defense.
- Keep this report separate from model image-inference latency; it measures the Workflow Canvas collaborative decision path.
