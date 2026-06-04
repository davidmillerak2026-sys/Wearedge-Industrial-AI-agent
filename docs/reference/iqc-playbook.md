# IQC System Playbook

This reference summarizes the IQC pattern for building an in-process quality check assistant. Here IQC means in-process quality check. It is a line-side quality pattern, not incoming material inspection.

## Product Pattern

IQC is a manufacturing quality pattern for catching process drift, defects, and missed checks while work is still in process. The core promise is to turn control plans, work instructions, measurements, gauge status, operator evidence, MES context, and QMS actions into a reliable quality gate that protects downstream stations and customers.

The emotional center is "the quality engineer who knows which tiny deviation becomes tomorrow's escape." Preserve that judgment as explicit rules, evidence, and review paths instead of letting an agent make undocumented calls.

## Canonical Topology

- Quality Plan Builder: convert drawings, control plans, PFMEA, SOPs, inspection forms, and customer requirements into versioned CTQ checks.
- Tool or MCP server: expose the agent-facing data surface for lots, serials, work orders, measurements, limits, gauges, defects, holds, rework, CAPA, and genealogy.
- Gate Monitor: run deterministic pass/fail/warn/hold checks for limits, SPC rules, missing inspection records, stale gauge calibration, and sampling compliance.
- IQC Investigator: perform bounded defect or drift analysis using trends, lots, stations, shifts, operators, equipment state, defect history, and quality-plan knowledge.
- Disposition Handler: turn findings into pass, hold, rework, scrap, deviation, release, or CAPA request with auditable evidence.
- Operator Q&A: provide fast explanations, prompts for missing inspection data, and handoffs to deeper investigation.
- Event/UI layer: stream status changes and `render_*` artifacts so operators and quality engineers can see the evidence behind each decision.

## Data and Tool Boundaries

Use this separation when adapting IQC:

- Repositories own SQL, QMS/MES connectors, and data integrity.
- Routers own HTTP, WebSocket, and event transport.
- Tool surfaces own LLM-facing data contracts.
- Agents call tools; agents do not directly query production or quality databases.
- Frontend type maps are public contracts for inspection states, defect artifacts, and disposition payloads.

Useful read tools:

- `get_quality_plan`: return CTQ characteristics, tolerances, sampling rules, control-plan version, and rule ids.
- `get_measurement_history`: return bounded measurement windows by product, line, station, lot, serial, feature, and time range.
- `get_spc_summary`: return rule breaches, control-limit context, and trend windows instead of raw endless points.
- `get_gauge_status`: return gauge id, calibration status, MSA capability, due date, and blocked-use semantics.
- `get_defect_history`: return defect modes, counts, recurrence, station, shift, lot, photo/note ids, and containment status.
- `get_lot_genealogy`: return upstream lots, serials, equipment, operators, and process steps needed for containment.

Useful write tools:

- `record_measurement`: validate units, feature ids, gauge ids, value type, timestamp, and operator/source before writing.
- `record_defect`: store taxonomy, severity, evidence ids, station, lot/serial scope, suspected cause, and containment need.
- `place_quality_hold`: freeze a lot, serial, batch, or work order with reason, scope, evidence, and required release authority.
- `release_quality_hold`: require release evidence and authorized role; do not let the model release by prose alone.
- `submit_disposition`: persist pass, hold, rework, scrap, deviation, or use-as-is decisions with rule ids and approver state.
- `create_capa_request`: open a CAPA or corrective-action handoff when recurrence, severity, escape risk, or customer impact crosses policy.

All time windows should be offset-aware ISO 8601 timestamps. All measurement values should include units, feature ids, and tolerance basis.

## Quality Plan Rules

Build the quality plan through three flows:

- Document extraction: convert drawings, control plans, SOPs, PFMEA rows, inspection sheets, and customer-specific requirements into structured checks.
- Engineer calibration: ask quality engineers to confirm missing CTQ limits, sampling rules, defect severities, gauge choices, and reaction plans.
- Plan Q&A: expose a side-effect-free function for other agents to ask product or station-specific quality questions.

Important invariants:

- Pre-stub missing limits and sampling rules as pending approval instead of inventing values.
- Keep plan versions immutable once released; create a new version for changed tolerance, gauge, frequency, or reaction-plan rules.
- Treat `onboarding_complete` or `plan_released` as a gate for automated production decisions.
- Store tolerance semantics precisely: bilateral, unilateral upper, unilateral lower, nominal plus/minus, attribute check, visual check, or derived calculation.
- Keep quality-plan Q&A side-effect free and return degraded structured answers instead of throwing.

## Gate Monitor and Investigator Rules

The Gate Monitor should be deterministic and audit-friendly:

- Tick on a fixed interval or event boundary.
- Look back over a bounded recent window.
- Use one shared quality-rule evaluator.
- Check tool error flags and stale data before making a status decision.
- Detect missing required checks before accepting a lot or station completion.
- Aggregate repeated defects or SPC breaches into windows.
- Place a hold only through the hold tool and include scope, reason, rule ids, and evidence ids.
- Spawn investigation asynchronously for complex patterns.

The IQC Investigator should be powerful but bounded:

- Inject relevant defect and CAPA history before the run starts.
- Use tools for evidence gathering.
- Use local tools for disposition submission, CAPA handoff, and UI rendering.
- Cap turns and wall-clock time.
- On timeout or crash, write a visible needs-review result rather than a silent pass.
- Never change quality state without an explicit write tool call and an auditable payload.

The durable learning loop is: Gate Monitor detects drift or defect -> quality hold or needs-review -> Investigator submits evidence and disposition -> QMS/CAPA stores outcome -> future checks see the prior pattern.

## SPC and Sampling Rules

SPC should summarize evidence before model reasoning:

- Evaluate control limits, specification limits, Western Electric or Nelson-style rules only when the project explicitly chooses them.
- Distinguish control-limit breach from specification failure.
- Return trend windows, breach counts, and representative points rather than every raw sample.
- Show stale or insufficient sample states explicitly.
- Do not let an agent infer process capability from too little data.

Sampling compliance should be treated as a first-class quality gate:

- Store required frequency, sample size, lot scope, skip-lot policy, and trigger conditions.
- Flag missing checks, late checks, wrong station, wrong gauge, and wrong product variant.
- Treat missed required inspection as hold or needs-review according to the released reaction plan.
- Keep acceptance sampling decisions separate from SPC trend warnings.

## Nonconformance, Rework, and CAPA Rules

Nonconformance handling should preserve containment clarity:

- Define hold scope precisely: lot, serial, batch, work order, station output, time window, or upstream/downstream genealogy.
- Capture suspected defect mode, observed condition, severity, escape risk, and affected quantity.
- Distinguish temporary containment from final disposition.
- Require human authority where local policy requires MRB, quality engineer, customer waiver, or regulatory approval.
- Persist rework instructions, verification checks, and post-rework results separately from the original defect.

CAPA handoff should be used when recurrence, severity, customer impact, audit requirement, or systemic cause crosses policy:

- Include evidence ids, recurrence summary, containment already taken, suspected root cause, affected products/lots, and requested owner.
- Avoid claiming root cause until evidence supports it.
- Link corrective action verification back to future IQC checks.

## Generative UI Rules

Treat `render_*` tools as local artifact emitters, not data tools. Useful artifacts include quality-gate cards, SPC charts, defect-cluster views, lot containment maps, inspection checklists, gauge status cards, nonconformance summaries, and CAPA handoff cards.

Each render tool should:

- Have a precise schema.
- Be available only to agents that need it.
- Broadcast a `ui_render` frame.
- Return a small acknowledgement to keep the model loop healthy.

Do not allow the model to render fabricated analytics. If no tool computes a value, do not create a visual that implies it is measured.

## Extension Checklist

When adding a new IQC feature:

- Identify the bounded context and repository owner.
- Decide whether the feature is a data tool, local write tool, local render tool, REST endpoint, WebSocket event, or QMS/MES connector.
- Add or update schemas before prompts.
- Keep units, tolerance semantics, sampling rules, time formats, row caps, no-data behavior, and error behavior explicit.
- Add safety nets for any agent loop that can run longer than a single request.
- Verify the operator-visible and quality-engineer-visible state transition, not only the backend function.
