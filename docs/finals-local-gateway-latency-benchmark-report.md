# Finals Latency Benchmark Report

Generated: 2026-06-12T02:07:28+00:00

## Boundary

This benchmark starts the Wearedge FastAPI gateway on the current workstation and measures real HTTP POST calls to /v1/workflow-canvas/decision. It is stronger than in-process replay, but it is still not Jetson/IPC hardware evidence until rerun on the final edge node with resource logs.

## Summary

- Evidence tier: local_fastapi_http_gateway
- Mode: http
- Endpoint: `http://127.0.0.1:51343/v1/workflow-canvas/decision`
- Dataset cases: 15
- Iterations: 20
- Samples: 300
- Target latency: <= 500 ms
- Target met: True

## Gateway

- App: `jetson.app:app`
- Base URL: `http://127.0.0.1:51343`
- Healthz OK: True
- Workflow endpoint: `/v1/workflow-canvas/decision`

## Latency Stats

| Metric | Min | P50 | P95 | Avg | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wall-clock replay latency | 1 ms | 12 ms | 24 ms | 9.9 ms | 28 ms |
| Decision-reported latency | 1 ms | 1 ms | 1 ms | 1.0 ms | 1 ms |

## Sample Coverage

| Case | Samples | Max Wall Latency |
| --- | ---: | ---: |
| final_energy_01_peak_load_shift | 20 | 23 ms |
| final_energy_02_idle_compressor | 20 | 27 ms |
| final_energy_03_auxiliary_load | 20 | 24 ms |
| final_flexible_01_order_change | 20 | 23 ms |
| final_flexible_02_short_run_sku | 20 | 22 ms |
| final_flexible_03_line_clearance | 20 | 16 ms |
| final_maint_01_vibration_escalation | 20 | 22 ms |
| final_maint_02_bearing_heat | 20 | 24 ms |
| final_maint_03_pump_anomaly | 20 | 26 ms |
| final_quality_01_lot_containment | 20 | 24 ms |
| final_quality_02_first_piece_reject | 20 | 28 ms |
| final_quality_03_camera_confidence | 20 | 25 ms |
| final_wfc_01_dashboard_reuse | 20 | 26 ms |
| final_wfc_02_human_gate_mapping | 20 | 23 ms |
| final_wfc_03_resource_binding_two_lines | 20 | 25 ms |

## Next Evidence Upgrade

- Run the same script with `--base-url http://<edge-host>:<port>` against the deployed FastAPI gateway.
- Capture Jetson / IPC / local industrial PC resource logs beside this report before final-round defense.
- Keep this report separate from model image-inference latency; it measures the Workflow Canvas collaborative decision path.
