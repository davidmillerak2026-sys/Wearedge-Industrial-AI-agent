# WearEdge Five-Agent POC Validation

This note defines the repeatable software POC for the five WearEdge M400 agents. It validates the deterministic agent loop before real M400 / Jetson / plant trials.

## Scope

The POC runs fixed scenario answers through the same Agently-style workflow used by `/v1/infer`:

```text
M400 scenario prompt
  -> normalize_agent / select_agent_route
  -> collect_evidence
  -> bounded_react_tools
  -> mode-specific output contract
  -> model answer validation
  -> identify_context / uncertainty_guard
  -> deterministic action mapping
  -> action_card
  -> integration_event
  -> agently_trace
  -> runtime_stream
```

It does not prove camera quality, model vision accuracy, network latency, or QMS/CMMS/MES/EHS integration availability. Those remain real-site validation tasks. This POC proves the five agent loops can accept valid structured outputs and deterministically produce the expected action envelope.

The route boundary is part of the POC: `maintenance` remains predictive-maintenance / machine-condition only, while personnel exposure, PPE, blocked walkways, fall/pinch risk, and restricted-zone hazards belong to the `hazard` route selected at the start of the loop.

## Command

```powershell
python scripts/validate_agent_pocs.py
```

For machine-readable output:

```powershell
python scripts/validate_agent_pocs.py --json
```

For the expanded 25-case golden matrix:

```powershell
python scripts/validate_agent_pocs.py --golden
```

## Current POC Matrix

| Agent | POC situation | Expected channel | Owner | Integration target | Human gate |
| --- | --- | --- | --- | --- | --- |
| `maintenance` | M400 sees residue near a packaging line gearbox | `schedule_maintenance` | `maintenance_planner` | `maintenance_work_order` | yes |
| `iqc` | M400 sees burrs and contamination on machined housing | `quality_hold` | `quality_engineer` | `qms_quality_event` | yes |
| `changeover` | M400 sees a filling station during SKU conversion | `changeover_verification` | `operator_quality` | `changeover_checklist` | yes |
| `wi` | M400 sees a cartoner station and operator asks for operating points | `guided_operation` | `operator` | `wi_reference` | no |
| `hazard` | M400 sees blocked walkway and moving equipment exposure | `stop_and_make_safe` | `operator` | `ehs_case` | yes |

## Golden Scenario Matrix

The expanded matrix keeps 5 cases per agent and exercises the industrial guardrails that are easy to miss in a single happy-path POC:

| Agent | Golden coverage |
| --- | --- |
| `maintenance` | schedule, monitor, unknown machine guard, stop, report |
| `iqc` | quality hold, detector-first pass blocked, expand inspection, stop production, clean pass |
| `changeover` | verification, controlled setup, RAG/checklist source missing guard, hold, escalate |
| `wi` | guided operation, RAG/WI source missing guard, ask human support, stop, confirm setup point |
| `hazard` | stop, inspect, PPE control, EHS report, unknown scene/risk downgrade blocked |

Key added checks:

- IQC `pass` is blocked into `quality_review` when detector evidence is insufficient.
- Changeover `controlled_changeover_step` is blocked when released checklist source is not available.
- WI `guided_operation` is blocked when the released WI revision cannot be retrieved.
- Hazard downgrade is blocked when scene or risk context is unknown.
- Every golden case checks `tool_plan.status`, selected tools, action card routing, integration event, and `runtime_stream.closed`.

## Latest Local Result

```text
WearEdge five-agent POC validation: 5/5 passed

| Agent | Result | Channel | Owner | Target | Last event |
| --- | --- | --- | --- | --- | --- |
| maintenance | PASS | schedule_maintenance | maintenance_planner | maintenance_work_order | workflow.closed |
| iqc | PASS | quality_hold | quality_engineer | qms_quality_event | workflow.closed |
| changeover | PASS | changeover_verification | operator_quality | changeover_checklist | workflow.closed |
| wi | PASS | guided_operation | operator | wi_reference | workflow.closed |
| hazard | PASS | stop_and_make_safe | operator | ehs_case | workflow.closed |
```

Expanded golden result:

```text
WearEdge golden scenario validation: 25/25 passed
```

## Latest Jetson Maintenance Result

On 2026-05-13, the maintenance agent was validated on Jetson with a generated M400-style packaging-line drive-station image containing asset ID, station sign, vibration RMS display, temperature gauges, HMI load/current/speed, oil staining, belt wear, and a yellow PLC alarm.

Detailed multi-turn record with preserved M400-style photos, code path, and agent-loop trace: [lao-shi-fu-maintenance-poc.md](lao-shi-fu-maintenance-poc.md).

Runtime setup:

```text
LLAMA_IMAGE_MIN_TOKENS=560
LLAMA_IMAGE_MAX_TOKENS=560
analysis_mode=maintenance
request_id=0099ca4bdef542f29e1349de83ed1271
```

Result:

| Field | Value |
| --- | --- |
| `machine` | `Packaging Line Drive Station PKG-L3-GBX-03` |
| `symptom` | VIB RMS `7.8 mm/s`, motor/gearbox temperatures around `78C/82C`, yellow PLC alarm |
| `action_card.channel` | `maintenance_report` |
| `priority` | `medium` |
| `owner` | `maintenance_engineer` |
| `integration_target` | `maintenance_work_order` |
| `integration_event.status` | `pending_human_confirmation` |
| `runtime_stream.closed` | `true` |

This confirms the latest engineering loop can read machine identity and condition-monitoring values when the visual token budget is raised, and the deterministic severity rule can upgrade a low-control `Inspect` action into `maintenance_report` when yellow alarm plus maintenance condition evidence is present.

## Acceptance Criteria

Each POC case must satisfy all of these checks:

- `contract.ok == true`
- every mode-specific required field is present
- `action_card.channel`, `owner`, `priority`, `requires_human`, and `integration_target` match the scenario expectation
- `integration_event.target` matches the action card target
- `integration_event.idempotency_key` includes `request_id`, target, and channel
- `runtime_stream.closed == true`
- the final runtime event is `workflow.closed`
- golden scenarios additionally verify detector/RAG source guard behavior and selected evidence tools

## Next Site POC

After the software POC passes, the next validation should use real M400 images against the Jetson gateway:

1. Capture one representative frame per agent mode.
2. Run `/v1/infer` with `analysis_mode` set to the target agent.
3. Compare the returned `action_card` and `integration_event` against the matrix above.
4. Confirm the operator can understand the `operator_message` on the M400 screen.
5. Save the `request_id` and audit event for review.

## Maintenance Evidence Follow-Up Loop

Predictive maintenance should not end with a single image. When the first M400 frame identifies a machine risk but the evidence tools are missing, the agent should guide the operator through a bounded evidence collection loop:

```text
initial M400 frame
  -> maintenance action card
  -> follow_up_plan requests
  -> evidence gaps identified
  -> operator prompted to collect missing evidence
  -> extra image / voice / typed observation uploaded
  -> Jetson re-runs same request family
  -> final maintenance_report / escalation / monitoring recommendation
```

Recommended follow-up prompts for the operator:

1. Photograph the machine asset plate and station sign if identity is uncertain.
2. Photograph the lubrication record or nearby maintenance checklist.
3. Photograph the recent maintenance record sheet or posted PM tag.
4. Photograph HMI alarm details, vibration display, current/load/speed, and temperature gauges.
5. Ask the operator to report sensory observations: unusual noise, smell, heat, vibration, shaking, or oil leakage.

This is now represented as `follow_up_plan` in the Jetson response. For maintenance, the plan can return `status=operator_evidence_required`, `next_action=collect_operator_evidence`, and capture requests such as `maintenance_condition_screen_photo`, `maintenance_temperature_gauge_photo`, `maintenance_lubrication_record_photo`, `maintenance_recent_work_record_photo`, and `maintenance_operator_sensory_check`.

The final decision should combine visible evidence, captured records, and operator observation. Without telemetry history, alarm history, manual thresholds, or maintenance records, the agent should avoid RUL claims and instead return a bounded maintenance report or evidence request.
