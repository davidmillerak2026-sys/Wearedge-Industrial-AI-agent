---
name: iqc
description: >-
  Build, adapt, or review IQC in-process quality check workflows for manufacturing lines. Use when Codex needs to design or implement quality gates, control plans, inspection plans, SPC monitoring, measurement capture, defect triage, nonconformance handling, rework disposition, CAPA handoff, MES/QMS integration, operator evidence collection, or agent/tool workflows for line-side process quality. In this skill, IQC means in-process quality check, not incoming quality control.
---

# IQC

## Purpose

Use this skill to apply the IQC pattern: turn control plans, work instructions, CTQ characteristics, live measurements, defect logs, operator observations, and process context into an agentic in-process quality workflow that can catch drift early, hold suspect material, explain evidence, and close the loop with QMS actions.

## Load References

- Read `references/iqc-playbook.md` when designing a new IQC system, modifying an IQC-like codebase, adding an inspection or QMS tool, or reviewing whether an implementation follows the IQC architecture.
- If working inside a source repository with local quality documents, prefer exact local contracts first: control plans, PFMEA, SOPs, inspection forms, MES/QMS schemas, gauge specs, and customer requirements. Use this skill as the operating checklist.

## Operating Loop

1. Start from the process step, not the model. Identify the line, station, product variant, CTQ characteristics, inspection frequency, sampling rule, measurement method, operator decision, and downstream risk.
2. Build the quality plan before detection. Combine control plan, PFMEA, work instruction, drawing tolerances, gauge capability, and customer-specific rules; never let the model invent limits or sampling rules.
3. Put data access behind tools. Agents should call an MCP-style tool surface for work orders, lots, serials, measurements, limits, gauges, defects, hold/release state, rework, and QMS records; they should not query production databases directly.
4. Monitor with deterministic checks. Let SPC or quality-gate code evaluate limits, control rules, missing checks, gauge status, repeated defects, and sampling compliance before spawning deeper analysis.
5. Investigate with bounded agency. Let an IQC Investigator gather evidence, compare shifts and lots, inspect trend windows, review defect photos or notes, consult quality knowledge, and emit a structured disposition under max-turn, timeout, and exception guards.
6. Close the loop. Convert the finding into pass, hold, rework, scrap, deviation, or CAPA handoff; persist the failure mode and corrective action so later checks recognize recurrence.
7. Keep operator interaction fast. Use chat for explanations, missing-info prompts, status, and lightweight handoffs; reserve long-running defect correlation or root-cause loops for asynchronous workers.

## Design Rules

- Treat inspection evidence as traceable production data. Preserve lot, serial, station, fixture, gauge, operator, shift, timestamp, unit, nominal, tolerance, result, and photo or note references.
- Keep missing limits explicit as pending quality-engineering approval. Unknown tolerances, sampling intervals, and disposition rules should produce hold or needs-review states, not fabricated acceptance.
- Reuse one quality-rule evaluator everywhere. Do not let SPC jobs, REST endpoints, agent prompts, and UI badges each interpret pass, fail, warning, hold, and release differently.
- Separate engineering thresholds from operating observations. Operator notes can explain symptoms, but they cannot silently overwrite CTQ limits or customer requirements.
- Make tool responses bounded. Bucket time series, cap measurement rows, aggregate defect clusters, and include truncation hints so model calls do not drown in inspection data.
- Return recoverable tool failures. Surface unavailable gauges, stale MES records, and QMS write errors as structured tool results so the model can recover inside the same turn.
- Protect auditability. Every automated recommendation should include evidence ids, rule ids, versioned control-plan references, and the human or system that made the final disposition.
- Mirror frontend and workflow contracts exactly. Event names, status enums, artifact schemas, and QMS payload fields should be treated as public contracts.
- Persist learning after every nonconformance. Defect signatures, escape risks, containment actions, and verified fixes should write back to defect history or CAPA knowledge.

## Implementation Checklist

- Define bounded contexts first: quality plan, measurement, gauge, lot/serial genealogy, defect, hold/release, rework, CAPA, chat, events, and simulator/demo data if needed.
- Design the tool catalogue before prompts. Include tool descriptions that state units, tolerance semantics, time formats, filters, row caps, no-data behavior, and audit side effects.
- Make each write tool narrow and explicit. IQC write points are usually `record_measurement`, `record_defect`, `place_quality_hold`, `release_quality_hold`, `submit_disposition`, and `create_capa_request`.
- Separate local UI render tools from data tools. `render_*` tools should broadcast inspection artifacts and return a small acknowledgement; they should not mutate quality state.
- Add tests or smoke checks around the contracts with the highest blast radius: rule evaluation, sampling compliance, measurement validation, hold/release state transitions, defect taxonomy mapping, QMS payload shape, and WebSocket or event frames.

## Response Style

When using this skill, explain decisions in quality language: CTQ, tolerance, evidence, sampling, gauge status, defect mode, containment, disposition, escape risk, corrective action, and residual risk. Prefer concise manufacturing guidance over generic agent hype.
