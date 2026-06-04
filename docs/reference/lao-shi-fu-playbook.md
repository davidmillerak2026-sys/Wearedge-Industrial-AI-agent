# lao-shi-fu System Playbook

This reference summarizes the lao-shi-fu repository pattern for building a "老师傅" industrial maintenance assistant. It is derived from the source repository's README and architecture documents.

## Product Pattern

lao-shi-fu is a predictive-maintenance pattern for industrial operators. The core promise is to compress months of specialist setup into minutes by combining manufacturer manuals, operator calibration, live time-series signals, logbook entries, KPIs, work orders, and failure history.

The emotional center is "the experienced operator who can hear failure coming." The system should preserve that tacit knowledge as structured evidence and operational memory, not just answer questions.

## Canonical Topology

- KB Builder: convert manufacturer PDF plus operator answers into a structured equipment KB.
- MCP server: expose the agent-facing data surface for KPIs, signals, human context, KB, work orders, failure history, and hierarchy.
- Sentinel: run a small periodic loop that detects threshold breaches, debounces repeated alerts, opens a detected work order, and spawns investigation.
- Investigator: perform bounded root-cause analysis using signal trends, anomaly windows, KPIs, logbook context, shift data, KB knowledge, and previous failures.
- Work Order Generator: turn the RCA into recommended actions, required parts, intervention window, and printable summary.
- Q&A: provide fast operator chat and lightweight handoffs to deeper diagnostic functions.
- Event/UI layer: stream events and `render_*` artifacts to the operator interface so the diagnosis is visible while it unfolds.

## Data and Tool Boundaries

Use this separation when adapting lao-shi-fu:

- Repositories own SQL and data integrity.
- Routers own HTTP and WebSocket transport.
- MCP tools own LLM-facing data contracts.
- Agents call tools; agents do not directly query operational databases.
- Frontend type maps are public contracts for WebSocket frames and artifact payloads.

The lao-shi-fu MCP catalogue has read tools for KPI, signals, context, KB, and hierarchy, plus a narrow KB write tool. Important tool behaviors:

- `get_signal_anomalies` should aggregate contiguous breaches into windows, not dump every breached sample.
- `get_signal_trends` should bucket or cap results and return a truncation hint when too large.
- `update_equipment_kb` should use merge-patch semantics and let the repository handle versioning, confidence, calibration log, and integrity checks.
- All time windows should be offset-aware ISO 8601 timestamps.

## KB Builder Rules

Build a KB through three flows:

- PDF extraction: send the manual to a vision-capable model and validate the result against the equipment KB schema.
- Operator onboarding: ask a short calibration sequence and turn answers into narrow JSON merge patches.
- KB Q&A: expose a side-effect-free function for other agents to ask equipment-specific questions.

Important invariants:

- Pre-stub missing monitored threshold keys as pending calibration instead of inventing values.
- Let null thresholds evaluate as non-breaches until calibrated.
- Flip `onboarding_complete` atomically when calibration is done; Sentinel should watch only completed cells.
- Keep KB Q&A side-effect free and return degraded structured answers instead of throwing.

## Sentinel and Investigator Rules

Sentinel should be deterministic and boring:

- Tick on a fixed interval.
- Look back over a small recent window.
- Use one shared threshold evaluator.
- Check tool error flags and skip bad cells for that tick.
- Debounce continuous breaches.
- Open a detected work order and spawn investigation asynchronously.

Investigator should be powerful but bounded:

- Inject recent failure history for the same cell before the run starts.
- Use MCP tools for evidence gathering.
- Use local tools for `submit_rca`, KB handoff, and UI rendering.
- Cap turns and wall-clock time.
- On timeout or crash, write a visible degraded RCA or keep the pipeline recoverable.
- Preserve provider-specific reasoning blocks or session state when using extended thinking or hosted agents.

The durable learning loop is: Sentinel opens work order -> Investigator submits RCA -> RCA writes failure history -> future Investigator runs see the prior failure mode.

## Work Order and Q&A Rules

The Work Order Generator is a short structured-output loop:

- Input: analyzed work order plus RCA.
- Output: recommended actions, priorities, durations, required parts, maintenance window, printable summary.
- It should normally finish in one or two turns and does not need extended thinking.

Q&A is for operator interaction:

- Keep per-connection chat state for the active WebSocket.
- Stream text and tool status frames promptly.
- Use agent-as-tool handoffs for deeper questions, but prefer fast deterministic paths for chat latency.
- Do not expose raw JSON dumps in chat; summarize tool results and render structured artifacts when useful.

## Generative UI Rules

Treat `render_*` tools as local artifact emitters, not data tools. Useful artifacts include signal charts, diagnostic cards, pattern-match callouts, work-order cards, KB progress, KB cards, alert banners, and KPI charts.

Each render tool should:

- Have a precise schema.
- Be available only to agents that need it.
- Broadcast a `ui_render` frame.
- Return a small acknowledgement to keep the model loop healthy.

Do not allow the model to render fabricated analytics. If no tool computes a value, do not create a visual that implies it is measured.

## Extension Checklist

When adding a new lao-shi-fu feature:

- Identify the bounded context and repository owner.
- Decide whether the feature is an MCP data tool, local agent write tool, local render tool, REST endpoint, or WebSocket event.
- Add or update Pydantic/type contracts before prompts.
- Keep units, timestamp formats, row caps, no-data behavior, and error behavior explicit.
- Add agent safety nets for any loop that can run longer than a single request.
- Verify the operator-visible state transition, not only the backend function.
