# WearEdge Pro Impact And ROI

Snapshot date: 2026-05-14

This document quantifies the business impact case for WearEdge Pro using public industry benchmarks and a conservative pilot model. It is not a claim that WearEdge Pro has already delivered these savings. It is the value pool that a plant pilot should measure against.

## Executive Summary

WearEdge Pro creates measurable value in four places:

| Value pool | Public benchmark | WearEdge Pro contribution | Conservative ROI hook |
| --- | --- | --- | --- |
| Downtime | Siemens Senseye reports unplanned downtime costs from `$36,000/hour` in FMCG to `$2.3M/hour` in automotive; a large plant averages `27` unplanned downtime hours/month. | First-person maintenance evidence, earlier escalation, faster fault triage, audit-ready action cards. | Saving only `10 minutes/month` at `$36,000/hour` is a `$72,000/year` gross opportunity. |
| Safety | NSC reports 2023 work injuries cost `$176.5B`; average cost per medically consulted work injury was `$43,000`; OSHA cites more than `$1B/week` in direct workers' compensation costs for disabling nonfatal injuries. | Hazard detection, bounded stop/inspect/report actions, near-miss capture, privacy-preserving audit trail. | Avoiding one medically consulted injury every two years is worth about `$21,500/year` before softer benefits. |
| Quality | IISE reports cost of poor quality in manufacturing commonly ranges from `5%` to `35%` of sales, averaging about `15%`; APQC's visible cross-industry median measure is `$28.50` per `$1,000` revenue. | M400 first-person IQC checks, quality hold action cards, traceable QMS event packages. | A `0.25 percentage point` COPQ reduction on a `$20M` line is `$50,000/year`. |
| Training / know-how | NAM / Manufacturing Institute reports manufacturers spend `$31.9B/year` on training; new U.S. manufacturing employees receive `47.6` training hours on average. | Lao-shi-fu evidence loop, guided work instructions, expert knowledge reuse at the point of work. | Reducing new-hire support time by `20%` at `$165/learning hour` is about `$1,571` per new hire. |

The submission message should be:

```text
WearEdge Pro is not only a VLM demo. It targets measurable industrial losses: downtime minutes, injury risk, scrap/rework, and expert training time. The pilot ROI model is intentionally conservative and can be verified with plant logs, EHS records, QMS events, and training records.
```

## Source Benchmarks

### Downtime

| Benchmark | Public number | How to use it |
| --- | ---: | --- |
| Automotive downtime | `$2.3M/hour`, more than `$600/second` | Use only for large automotive or similarly synchronized high-throughput plants. |
| FMCG low-end downtime | `$36,000/hour` | Good conservative floor for a judge-facing example. |
| SME top-end downtime | Up to `$150,000/hour` | Useful for mid-market factories where one line stop can threaten supplier OTIF. |
| Average large plant downtime | `27 hours/month`, `25 incidents/month` | Use to argue that shaving minutes is meaningful even without preventing every failure. |
| PdM potential | Siemens estimates full condition monitoring / PdM adoption could save `2.1M` downtime hours annually across Fortune Global 500 industrial organizations. | Supports the predictive-maintenance framing, not a WearEdge-specific claim. |

Source: [Siemens Senseye, The True Cost of Downtime 2024](https://assets.new.siemens.com/siemens/assets/api/uuid%3A1b43afb5-2d07-47f7-9eb7-893fe7d0bc59/TCOD-2024_original.pdf)

### Safety

| Benchmark | Public number | How to use it |
| --- | ---: | --- |
| U.S. work injury cost | `$176.5B` in 2023 | Establishes safety as a real economic issue, not only compliance language. |
| Medically consulted injury | `$43,000` per injury | Use for conservative avoided-injury scenarios. |
| Work death | `$1.46M` per death | Do not use as a salesy number; mention as moral and economic severity. |
| Direct workers' compensation | More than `$1B/week` for disabling nonfatal workplace injuries | Shows employer-side hard cost. |
| Safety investment return | NSC cites `$4-$6` return for every `$1` invested in safety. OSHA cites CFO survey results where over `60%` reported `$2+` returned per `$1` invested. | Supports the safety ROI narrative, not a guaranteed return. |

Sources: [NSC economic ROI of safety PDF](https://www.nsc.org/getattachment/30ffe825-c44e-4c09-bd49-e892a43ef640/download), [OSHA Business Case for Safety and Health](https://www.osha.gov/businesscase), [OSHA Safety Pays estimator](https://www.osha.gov/safetypays/estimator)

### Quality

| Benchmark | Public number | How to use it |
| --- | ---: | --- |
| COPQ range | `5%-35%` of manufacturing sales, average around `15%` | Use as the broad manufacturing cost-of-poor-quality envelope. |
| APQC median visible benchmark | `$28.50` per `$1,000` revenue, or `2.85%` | Use as a conservative cross-industry reference point when a plant has no COPQ baseline. |
| ASQ categories | Internal failure: scrap, rework, failure analysis. External failure: warranty, complaints, returns, field repair. | Map WearEdge IQC and action-card value into accepted quality-cost categories. |

Sources: [IISE, Measuring the cost of quality](https://iise.org/Print/?Site=Main&id=22118), [APQC cost of poor quality measure](https://www.apqc.org/what-we-do/benchmarking/open-standards-benchmarking/measures/total-annual-cost-poor-quality-1000), [ASQ Cost of Quality](https://asq.org/quality-resources/cost-of-quality)

### Training And Knowledge Transfer

| Benchmark | Public number | How to use it |
| --- | ---: | --- |
| Manufacturing training spend | `$31.9B/year`, up from `$26.2B` in 2019 | Training is already a major manufacturing budget item. |
| New employee training | `47.6` hours average | Good basis for new-hire onboarding value. |
| Existing employee training | `26.7` hours average | Good basis for annual reskilling / cross-training value. |
| Formal learning cost | ATD reports `$165` average cost per learning hour used in 2024. | Use as a loaded benchmark, but validate against plant labor rates. |
| Skills gap | Deloitte / MI estimate around `3.8M` manufacturing jobs needed from 2024-2033; about `1.9M` may remain unfilled if gaps are not addressed. | Positions WearEdge as workforce leverage, not labor replacement. |
| AR / VR training example | Deloitte reports an executive example where VR reduced welding training time by `50%-60%`. | Supports wearable, in-context guidance as a credible training direction. |

Sources: [NAM, Manufacturers Invest Billions in Workforce Training](https://nam.org/manufacturers-invest-billions-in-workforce-training-36234/?stream=series-input-stories), [Manufacturing Institute training survey page](https://themanufacturinginstitute.org/research/the-state-of-workforce-training-in-manufacturing/), [ATD 2025 State of the Industry release](https://www.td.org/content/press-release/atd-research-optimism-remains-strong-for-future-of-learning-in-organizations), [Deloitte / Manufacturing Institute 2024 talent study](https://www.deloitte.com/us/en/insights/industry/manufacturing-industrial-products/supporting-us-manufacturing-growth-amid-workforce-challenges.html)

## ROI Model

WearEdge ROI should be calculated as:

```text
Annual gross value =
  downtime value
+ safety value
+ quality value
+ training / knowledge-transfer value

WearEdge-attributable value =
  annual gross value * attribution factor

Pilot ROI =
  (WearEdge-attributable value - pilot cost) / pilot cost
```

Use an attribution factor of `10%-30%` until a plant pilot proves otherwise. WearEdge Pro is an assistive detection and workflow layer; it does not own the whole maintenance, safety, quality, or training system.

## Value Pool 1: Downtime

### Formula

```text
annual downtime value =
  downtime_cost_per_hour
* avoided_minutes_per_event / 60
* events_per_month
* 12
```

### Example Values

| Case | Assumption | Annual gross value |
| --- | --- | ---: |
| Conservative FMCG floor | `$36,000/hour`, save `10 min/month` | `$72,000/year` |
| SME / supplier line | `$150,000/hour`, save `10 min/month` | `$300,000/year` |
| Large automotive line | `$2.3M/hour`, save `5 min/month` | `$2.3M/year` |
| One full average recovery event, FMCG floor | `$36,000/hour`, save `81 min` once | `$48,600` |
| One full average recovery event, SME top-end | `$150,000/hour`, save `81 min` once | `$202,500` |

### Why WearEdge Helps

WearEdge Pro does not need to predict every breakdown. It only needs to reduce the time between "something looks wrong" and "the right maintenance action starts":

- M400 captures the asset, HMI, alarm, gauge, lubrication record, maintenance record, and operator sensory evidence.
- Jetson runs local Gemma 4 E2B and lao-shi-fu workflow without sending plant imagery to a cloud API.
- The agent asks for missing evidence instead of inventing root cause.
- The action card routes to `condition_inspection`, `maintenance_report`, `maintenance_stop`, or `maintenance_work_order`.
- The `request_id`, evidence package, and runtime stream reduce handoff time between operator and maintenance engineer.

## Value Pool 2: Safety

### Formula

```text
annual safety value =
  avoided_medically_consulted_injuries_per_year * 43000
+ avoided_severe_incident_expected_value
+ avoided_indirect_costs
```

Do not use safety ROI as a promise to reduce reporting. The goal is better hazard recognition, faster correction, and better near-miss evidence.

### Example Values

| Case | Assumption | Annual gross value |
| --- | --- | ---: |
| One medically consulted injury avoided every 5 years | `0.2 * $43,000` | `$8,600/year` |
| One medically consulted injury avoided every 2 years | `0.5 * $43,000` | `$21,500/year` |
| One medically consulted injury avoided per year | `1.0 * $43,000` | `$43,000/year` |

### Why WearEdge Helps

- The hazard route turns first-person images into `scene / risk / action`.
- Actions are bounded to safe verbs such as `Stop`, `Inspect`, `Wear`, `Keep`, or `Report`.
- The action card requires human confirmation for high-risk channels.
- Audit logs keep `request_id`, structured decision, and metadata while defaulting to `saved_path=null` for images.
- The system supports better near-miss capture: blocked walkways, moving-equipment exposure, missing PPE context, spills, pinch points, and unsafe access conditions.

## Value Pool 3: Quality

### Formula

Two acceptable approaches:

```text
annual quality value =
  annual_line_revenue * COPQ_reduction_percentage_points
```

or:

```text
annual quality value =
  avoided_defect_events
* (scrap + rework + sorting + reinspection + line_hold + warranty + complaint_handling)
```

### Example Values

| Case | Assumption | Annual gross value |
| --- | --- | ---: |
| Small line improvement | `$20M` annual output, reduce COPQ by `0.10 percentage points` | `$20,000/year` |
| Conservative visible improvement | `$20M` annual output, reduce COPQ by `0.25 percentage points` | `$50,000/year` |
| Mid-market quality program | `$50M` annual output, reduce COPQ by `0.25 percentage points` | `$125,000/year` |
| APQC median reference | `$20M` annual revenue * `2.85%` visible median cost measure | `$570,000/year` value pool |

### Why WearEdge Helps

- The IQC route can turn a first-person product image into `product`, `quality_risk`, `disposition`, and `action`.
- The action card can route to `quality_hold`, `expand_inspection`, `stop_production`, `capa_request`, or `qms_quality_event`.
- Earlier containment is cheaper than customer escape. WearEdge should be positioned as an in-process containment and evidence-capture layer, not a replacement for calibrated measurement or formal inspection.
- The same `request_id` can connect operator view, quality hold, defect image, disposition, and downstream QMS event.

## Value Pool 4: Training And Lao-shi-fu Knowledge Transfer

### Formula

```text
annual training value =
  new_hires_per_year
* new_hire_training_hours
* reduction_rate
* cost_per_learning_hour
+
  expert_interruptions_avoided
* expert_loaded_hourly_rate
```

For public benchmark scenarios:

```text
new_hire_training_hours = 47.6
cost_per_learning_hour = 165
```

### Example Values

| Case | Assumption | Annual gross value |
| --- | --- | ---: |
| Per new hire | `47.6 hours * 20% * $165/hour` | `$1,571/new hire` |
| 10 new hires | `10 * 47.6 * 20% * $165` | `$15,708/year` |
| 25 new hires | `25 * 47.6 * 20% * $165` | `$39,270/year` |
| Existing-worker annual guidance | `50 workers * 26.7 hours * 10% * $165` | `$22,028/year` |
| Expert interruption reduction | `200 avoided expert hours * $75/hour` | `$15,000/year` |

### Why WearEdge Helps

WearEdge Pro's lao-shi-fu loop is a knowledge transfer mechanism:

- The expert workflow is encoded as evidence capture: asset plate, condition screen, temperature gauge, lubrication record, recent maintenance record, and sensory observations.
- The agent records what evidence is missing and blocks unsupported claims such as final root cause, remaining useful life, restart permission, or maintenance release.
- Newer operators get stepwise prompts without waiting for the most experienced technician to be physically present.
- Expert time shifts from repeating basic triage to confirming high-value exceptions.

## Pilot Scenarios

These examples are deliberately conservative. They show the value pool and a cautious WearEdge-attributable share.

| Scenario | Gross annual value model | Gross value | Attribution factor | WearEdge-attributable value |
| --- | --- | ---: | ---: | ---: |
| Conservative single-line pilot | `$72k` downtime + `$8.6k` safety + `$20k` quality + `$7.9k` training | `$108.5k` | `25%` | `$27.1k/year` |
| Mid-market supplier pilot | `$300k` downtime + `$14.3k` safety + `$125k` quality + `$39.3k` training | `$478.6k` | `25%` | `$119.6k/year` |
| Large automotive-style plant | `$2.3M` downtime + `$43k` safety + `$500k` quality + `$157k` training | `$3.0M` | `20%` | `$600k/year` |

Do not use the automotive scenario unless the target site actually has synchronized high-throughput downtime economics. For the hackathon, the conservative single-line and mid-market supplier cases are more credible.

## Pilot KPI Plan

| Area | Baseline data needed | 30-90 day pilot metric | Success signal |
| --- | --- | --- | --- |
| Downtime | Unplanned downtime incidents, minutes, cause codes, MTTR, response handoff time. | Minutes from operator observation to maintenance action card; minutes from action card to technician triage. | Faster triage, fewer repeated evidence requests, shorter preventable downtime. |
| Safety | Near-miss logs, EHS observations, recordables, DART, common hazard categories. | Number of hazards captured, action completion rate, repeat hazard rate. | More near-misses captured and corrected before injury. |
| Quality | Scrap, rework, inspection holds, customer escapes, defect category, containment cycle time. | IQC action cards, quality hold accuracy, time to disposition. | Earlier containment and fewer repeated defects or escapes. |
| Training | New-hire training hours, time-to-competency, expert shadowing time, common support calls. | Guided instruction usage, expert interruptions avoided, first-time-right procedure rate. | Faster onboarding and lower dependency on one senior technician. |

## Submission Positioning

Use these three points in the technical report and video:

1. **Downtime math makes minutes matter.** At Siemens' low-end FMCG figure of `$36,000/hour`, saving only ten minutes per month is a `$72,000/year` gross opportunity.
2. **Safety value is both human and financial.** NSC puts the average medically consulted workplace injury at `$43,000`, while OSHA emphasizes that employers always pay indirect costs.
3. **Lao-shi-fu is workforce leverage.** Manufacturing already spends tens of billions on training, and new employees receive almost a full work week of training on average; WearEdge turns expert troubleshooting patterns into repeatable guided evidence loops.

## Current Evidence And Gaps

Current WearEdge evidence:

- Jetson local Gemma 4 E2B inference is documented in `docs/edge-runtime-benchmark.md`.
- Lao-shi-fu maintenance POC is documented in `docs/lao-shi-fu-maintenance-poc.md`.
- Five-agent deterministic validation is documented in `docs/five-agent-poc-validation.md`.
- M400 API contract and audit behavior are documented in `docs/m400-inference-contract.md`.

Remaining proof gaps:

- Need real M400 pilot latency and operator UX data.
- Need plant-specific downtime cost per hour, not only public benchmarks.
- Need real baseline data for injuries, near misses, defects, scrap, rework, training time, and maintenance response time.
- Need to avoid claiming final maintenance root cause or safety clearance; WearEdge outputs bounded action cards that require human confirmation.

## One-Line ROI Claim

```text
WearEdge Pro targets four measurable industrial losses: downtime minutes, workplace injury risk, scrap/rework, and expert training time; even a conservative single-line pilot has a public-benchmark gross value pool above $100k/year before site-specific attribution.
```
