# Edge Runtime Evidence Runbook

更新日期：2026-06-12

## Purpose

This runbook collects the evidence needed to defend the Wearedge edge-runtime claim:

```text
Wearedge runs the industrial agent decision path near the production line,
through a FastAPI gateway that can be deployed on Jetson, IPC, or a plant edge server.
```

It separates three evidence levels:

| Level | Meaning | Current status |
| --- | --- | --- |
| In-process replay | Direct Python call to the decision engine. | Tracked in `docs/finals-latency-benchmark-report.md`. |
| Local HTTP gateway | Real HTTP POST calls to `/v1/workflow-canvas/decision` plus CPU/RSS/system memory sampling. | Tracked in `docs/finals-local-gateway-latency-benchmark-report.md`. |
| Jetson / IPC edge node | Same HTTP benchmark rerun on final edge hardware, with resource logs. | Final defense upgrade. |
| Jetson / IPC stdlib fallback | Dependency-light HTTP benchmark for offline edge nodes without FastAPI/Uvicorn. | Uses the same `jetson.competition.build_competition_decision()` entry point and is explicitly marked as fallback evidence. |

## One-Command Collection

On the current workstation:

```powershell
python scripts/benchmark_local_gateway_latency.py
python scripts/collect_edge_runtime_evidence.py
```

This writes ignored live-evidence files:

```text
submission-assets/live-evidence/edge-runtime/06-http-resource-benchmark-report.md
submission-assets/live-evidence/edge-runtime/06-http-resource-benchmark.json
submission-assets/live-evidence/edge-runtime/07-edge-runtime-evidence-manifest.md
```

## Jetson / IPC Rerun

On Jetson, IPC, or final plant edge gateway:

```bash
cd /path/to/Wearedge-Industrial-AI-agent
python scripts/collect_edge_runtime_evidence.py --rerun-benchmark --iterations 20 --final-edge-node
```

For Jetson, also capture a parallel resource log:

```bash
tegrastats --interval 1000 | tee submission-assets/live-evidence/edge-runtime/08-tegrastats-http-resource-benchmark.log
```

From the Windows workstation, after the Jetson is powered and reachable over SSH, use the remote collector so the deployment, benchmark, `tegrastats`, and evidence pullback happen in one repeatable step:

```powershell
$env:JETSON_SSH_PASSWORD = "<set locally, do not commit>"
python scripts/collect_jetson_edge_evidence.py --host wearedge-pro.local --user ryn --iterations 20
Remove-Item Env:\JETSON_SSH_PASSWORD
```

The remote collector deploys the competition runtime into `~/Wearedge-Industrial-AI-agent-competition` and leaves the older `~/WearEdge-Pro` M400/VLM service untouched.
It also refuses to use a Python interpreter or virtual environment under `~/WearEdge-Pro`. If FastAPI/Uvicorn are already available on the Jetson system Python or isolated competition `.venv`, the collector runs the FastAPI benchmark. If they are not available and the edge node has no internet, it runs `scripts/benchmark_edge_stdlib_gateway.py`, a Python standard-library HTTP gateway that calls the same Workflow Canvas decision engine and writes a report marked as `final_edge_stdlib_http_gateway`.

To explicitly allow the collector to create an isolated `.venv` and install FastAPI dependencies from the network, add:

```powershell
python scripts/collect_jetson_edge_evidence.py --host wearedge-pro.local --user ryn --iterations 20 --allow-remote-pip-install
```

Isolation rules:

| Item | Competition evidence path |
| --- | --- |
| Runtime checkout | `~/Wearedge-Industrial-AI-agent-competition` |
| Python environment | `~/Wearedge-Industrial-AI-agent-competition/.venv` or system `python3` |
| Pulled evidence | `submission-assets/live-evidence/edge-runtime/` on this workstation |
| Protected legacy project | `~/WearEdge-Pro` is not modified or used as a dependency source |

For Windows IPC or plant server, capture Task Manager / Resource Monitor screenshots or an OS-level CSV beside the generated files.

## Acceptance Criteria

| Check | Target |
| --- | --- |
| HTTP endpoint | `/v1/workflow-canvas/decision` |
| Samples | `300` for 15 cases x 20 iterations |
| Latency | p95 and max both `<=500ms` for the collaborative decision path |
| Resource profile | Process RSS and CPU sampling present |
| Boundary | Report states whether it is workstation, Jetson, IPC, or plant edge evidence |

## Boundary

This benchmark measures the Workflow Canvas collaborative decision path, not high-detail visual model inference. Image/VLM latency must stay in the separate Jetson/M400 evidence track.
