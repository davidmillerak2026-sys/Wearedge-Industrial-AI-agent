# Tests

The test suite protects the engineering claims in the README and docs.

## Coverage Areas

| Area | Representative Tests |
| --- | --- |
| Output contracts | `test_output_contract.py` |
| Agent routing and action cards | `test_agent_loop.py`, `test_agently_orchestrator.py` |
| M400 payload and device context | `test_jetson_payload.py`, `test_device_context.py` |
| Audit logging | `test_audit_log.py` |
| Maintenance knowledge and sessions | `test_maintenance_kb.py`, `test_maintenance_session.py`, `test_maintenance_session_api.py` |
| IQC quality rules | `test_iqc_quality_plan.py`, `test_iqc_quality_eval.py`, `test_iqc_detector.py` |
| Released-source guards | `test_released_source.py` |
| Five-agent PoC validation | `test_agent_poc_validation.py` |

## Run

```bash
python -m pytest
```

The tests use local fixtures and deterministic stubs where possible. Real Jetson model latency and M400 device behavior are recorded under `docs/poc-results/` instead of being required for every local test run.
