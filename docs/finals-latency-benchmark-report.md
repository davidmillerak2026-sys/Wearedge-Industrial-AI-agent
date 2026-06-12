# Finals Latency Benchmark Report

Generated: 2026-06-12T04:17:14+00:00

## Boundary

Default in_process mode is a deterministic local replay of the Workflow Canvas decision engine. Use --base-url against a deployed Jetson/IPC/local-server gateway before claiming deployed endpoint latency.

## Summary

- Evidence tier: in_process
- Mode: in_process
- Endpoint: `jetson.competition.build_competition_decision`
- Dataset cases: 15
- Iterations: 20
- Samples: 300
- Target latency: <= 500 ms
- Target met: True

## Latency Stats

| Metric | Min | P50 | P95 | Avg | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wall-clock replay latency | 1 ms | 1 ms | 1 ms | 1.0 ms | 1 ms |
| Decision-reported latency | 1 ms | 1 ms | 1 ms | 1.0 ms | 1 ms |

## Sample Coverage

| Case | Samples | Max Wall Latency |
| --- | ---: | ---: |
| final_energy_01_peak_load_shift | 20 | 1 ms |
| final_energy_02_idle_compressor | 20 | 1 ms |
| final_energy_03_auxiliary_load | 20 | 1 ms |
| final_flexible_01_order_change | 20 | 1 ms |
| final_flexible_02_short_run_sku | 20 | 1 ms |
| final_flexible_03_line_clearance | 20 | 1 ms |
| final_maint_01_vibration_escalation | 20 | 1 ms |
| final_maint_02_bearing_heat | 20 | 1 ms |
| final_maint_03_pump_anomaly | 20 | 1 ms |
| final_quality_01_lot_containment | 20 | 1 ms |
| final_quality_02_first_piece_reject | 20 | 1 ms |
| final_quality_03_camera_confidence | 20 | 1 ms |
| final_wfc_01_dashboard_reuse | 20 | 1 ms |
| final_wfc_02_human_gate_mapping | 20 | 1 ms |
| final_wfc_03_resource_binding_two_lines | 20 | 1 ms |

## Next Evidence Upgrade

- Run the same script with `--base-url http://<edge-host>:<port>` against the deployed FastAPI gateway.
- Capture Jetson / IPC / local industrial PC resource logs beside this report before final-round defense.
- Keep this report separate from model image-inference latency; it measures the Workflow Canvas collaborative decision path.
