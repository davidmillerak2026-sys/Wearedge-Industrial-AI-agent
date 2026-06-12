# Wearedge Finals Validation Report

Generated: 2026-06-12

## Boundary

This report is an expanded offline/simulated validation artifact for final-round preparation. It does not replace live Xcelerator or Gongyi Mofang workflow execution evidence.

## Executive Summary

- Finals validation ready: True
- Case count: 15 / 15
- Case pass rate: 100.0%
- Decision accuracy estimate: 95.0% min
- Latency: 1 ms max
- All cases have >=3 directions: True
- All five directions selected: True
- All five primary directions represented: True

## Final-Round KPI Checks

| KPI | Current | Target | Status |
| --- | ---: | ---: | --- |
| Decision accuracy | 95.0% min | >= 90.0% | PASS |
| Response latency | 1 ms max | <= 500 ms | PASS |
| Agent directions per case | 3 min | >= 3 | PASS |
| Dataset size | 15 cases | >= 15 cases | PASS |

## Primary Direction Coverage

| Primary direction | Case count |
| --- | ---: |
| energy | 3 |
| flexible_production | 3 |
| maintenance | 3 |
| quality | 3 |
| workflow_canvas | 3 |

## Case Results

| Case | Primary | Directions | Accuracy | Latency | Result |
| --- | --- | ---: | ---: | ---: | --- |
| final_maint_01_vibration_escalation | maintenance | 4 | 96.5% | 1 ms | PASS |
| final_maint_02_bearing_heat | maintenance | 4 | 96.5% | 1 ms | PASS |
| final_maint_03_pump_anomaly | maintenance | 3 | 95.0% | 1 ms | PASS |
| final_quality_01_lot_containment | quality | 3 | 95.0% | 1 ms | PASS |
| final_quality_02_first_piece_reject | quality | 4 | 96.5% | 1 ms | PASS |
| final_quality_03_camera_confidence | quality | 4 | 96.5% | 1 ms | PASS |
| final_energy_01_peak_load_shift | energy | 4 | 96.5% | 1 ms | PASS |
| final_energy_02_idle_compressor | energy | 3 | 95.0% | 1 ms | PASS |
| final_energy_03_auxiliary_load | energy | 5 | 97.0% | 1 ms | PASS |
| final_flexible_01_order_change | flexible_production | 4 | 96.5% | 1 ms | PASS |
| final_flexible_02_short_run_sku | flexible_production | 4 | 96.5% | 1 ms | PASS |
| final_flexible_03_line_clearance | flexible_production | 4 | 96.5% | 1 ms | PASS |
| final_wfc_01_dashboard_reuse | workflow_canvas | 4 | 96.5% | 1 ms | PASS |
| final_wfc_02_human_gate_mapping | workflow_canvas | 3 | 95.0% | 1 ms | PASS |
| final_wfc_03_resource_binding_two_lines | workflow_canvas | 3 | 95.0% | 1 ms | PASS |

## Next Evidence Upgrade

- Replace WFC fallback Dashboard/run-log/HumanApprovalGate assets with live platform execution screenshots.
- Add deployed API endpoint latency logs and edge-hardware replay logs.
- Keep simulated/offline and live platform evidence explicitly separated in defense material.
