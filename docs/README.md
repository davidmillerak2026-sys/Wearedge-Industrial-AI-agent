# WearEdge Pro Documentation

This directory is the engineering evidence hub for WearEdge Pro. It is organized so reviewers can move from architecture, to deployment, to reproducible proof, to business impact without digging through runtime output.

## Start Here

| Topic | Document |
| --- | --- |
| Current project status | [`project-status.md`](project-status.md) |
| Siemens Xcelerator co-creation one-pager | [`siemens-xcelerator-co-creation-onepager.md`](siemens-xcelerator-co-creation-onepager.md) |
| Technical architecture | [`technical_architecture.md`](technical_architecture.md) |
| Sensing and compute architecture | [`sensing_compute_architecture.md`](sensing_compute_architecture.md) |
| Jetson Gemma 4 E2B deployment | [`e2b-deployment-runbook.md`](e2b-deployment-runbook.md) |
| Edge runtime benchmark | [`edge-runtime-benchmark.md`](edge-runtime-benchmark.md) |
| Core hardware/software BOM | [`core-bom.md`](core-bom.md) |
| Business impact and ROI | [`impact-and-roi.md`](impact-and-roi.md) |

## Proof And Validation

| Evidence Area | Document |
| --- | --- |
| End-to-end technical evidence | [`technical-evidence.md`](technical-evidence.md) |
| Gemma 4 E2B PoC summary | [`gemma4-e2b-poc-summary.md`](gemma4-e2b-poc-summary.md) |
| Five-agent validation | [`five-agent-poc-validation.md`](five-agent-poc-validation.md) |
| M400 inference contract | [`m400-inference-contract.md`](m400-inference-contract.md) |
| lao-shi-fu maintenance PoC | [`lao-shi-fu-maintenance-poc.md`](lao-shi-fu-maintenance-poc.md) |
| Maintenance evidence loop | [`maintenance-session-evidence-loop.md`](maintenance-session-evidence-loop.md) |
| Test history | [`test-log-history.md`](test-log-history.md) |
| Network troubleshooting | [`network-troubleshooting.md`](network-troubleshooting.md) |

## Directory Map

| Path | Purpose |
| --- | --- |
| [`assets/`](assets/) | Small curated images used by demos, tests, and evidence documents. |
| [`poc-results/`](poc-results/) | Reproducible PoC outputs, screenshots, logs, summaries, and field-test traces. |
| [`submissions/`](submissions/) | Optional external submission deliverables. Large generated videos are ignored unless intentionally forced into Git. |

## Curation Rule

Keep permanent claims in Markdown or JSON summaries. Keep raw runtime folders, model weights, local tar packages, generated videos, and temporary logs out of Git unless they are intentionally selected evidence for a specific review package.
