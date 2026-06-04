---
name: lao-shi-fu
description: >-
  Build, adapt, or review lao-shi-fu industrial predictive-maintenance assistants that preserve experienced operator know-how from manuals, live signals, logbooks, KPIs, and failure history. Use when Codex needs to design or implement a "老师傅" workflow: PDF/manual-to-KB onboarding, anomaly detection, root-cause investigation, work-order generation, maintenance Q&A, MCP tool surfaces, or agent handoffs for factory equipment diagnostics.
---

# 老师傅

## Purpose

Use this skill to apply the lao-shi-fu pattern: turn the retiring expert's practical equipment knowledge into an agentic maintenance workflow that can watch machines, diagnose anomalies, create work orders, and explain itself to operators.

## Load References

- Read `references/lao-shi-fu-playbook.md` when designing a new system, modifying a lao-shi-fu-like codebase, adding an agent/tool, or reviewing whether an implementation follows the lao-shi-fu architecture.
- If working inside the source repository this skill was derived from, prefer the local `docs/architecture/*.md` files for exact contracts, then use this skill as the operating checklist.

## Operating Loop

1. Start from the plant workflow, not the model. Identify the cell, monitored signals, operator notes, maintenance history, KPIs, and the decision an operator must make.
2. Build an equipment KB before detection. Combine manufacturer manuals with a short operator calibration flow; never force the model to invent missing thresholds.
3. Put data access behind tools. Agents should call an MCP-style tool surface for signals, KPIs, KB, logbook, work orders, and hierarchy; they should not query the database directly.
4. Watch continuously with a small deterministic loop. Let Sentinel-style code evaluate thresholds, debounce repeated alerts, open a detected work order, broadcast the event, and spawn deeper diagnosis asynchronously.
5. Diagnose with bounded agency. Let the Investigator gather evidence, correlate signals and human context, consult KB expertise, emit UI artifacts, and submit a structured RCA under max-turn, timeout, and exception guards.
6. Close the loop. Convert the RCA into recommended actions, parts, and a maintenance window; persist the failure so the next diagnosis can recognize recurring patterns.
7. Keep operator chat fast. Use chat for explanations, status, and lightweight handoffs; reserve long-running investigation loops for asynchronous workers.

## Design Rules

- Treat "operator knowledge" as evidence. Capture exact observations, units, conditions, and calibration notes instead of smoothing them into generic prose.
- Keep missing thresholds explicit as pending calibration. Null bounds should evaluate as non-breaches until a human or trusted source fills them.
- Reuse one threshold evaluator everywhere. Do not let Sentinel, tools, REST endpoints, and UI code each interpret alert/trip ranges differently.
- Make tool responses bounded. Bucket time series, aggregate breach windows, cap large responses, and include truncation hints so model calls do not drown in telemetry.
- Return recoverable tool failures. Surface tool errors as structured tool results so the model can recover inside the same turn.
- Wrap long-running agents with `max_turns`, wall-clock timeout, and outer `try/except`; degraded completion is better than a stuck work order.
- Preserve model-provider invariants. For extended thinking or hosted agent paths, keep signed reasoning blocks or session ids exactly as the provider requires.
- Mirror frontend contracts exactly. WebSocket event names, field names, and generated UI artifact schemas should be treated as public contracts.
- Persist learning after every incident. RCA summaries and failure modes should write back to failure history so the system becomes more useful over time.

## Implementation Checklist

- Define the bounded contexts first: KB, signals, KPI, logbook, work order, chat, events, and simulator/demo data if needed.
- Design the MCP catalogue before prompts. Include tool descriptions that state units, time formats, filters, row caps, and no-data semantics.
- Make each agent's write tools narrow and explicit. lao-shi-fu write points are `update_equipment_kb`, `submit_rca`, and `submit_work_order`.
- Separate local UI render tools from data tools. `render_*` tools should broadcast artifacts and return a small acknowledgement; they should not mutate operational state.
- Add tests or smoke checks around the contracts with the highest blast radius: threshold evaluation, KB upsert validation, tool result envelopes, WebSocket frame shape, and work-order state transitions.

## Response Style

When using this skill, explain decisions in maintenance language: evidence, symptoms, thresholds, likely failure modes, operator action, and residual risk. Prefer concise engineering guidance over generic agent hype.
