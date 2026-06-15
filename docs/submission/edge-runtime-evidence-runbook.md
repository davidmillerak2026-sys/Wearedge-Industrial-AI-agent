# Edge Runtime Evidence Runbook

更新日期：2026-06-15

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
| Jetson / IPC edge node | Same HTTP benchmark rerun on final edge hardware, with resource logs. | 当前主证据：2026-06-15 已在 `wearedge-pro.local` 的 FastAPI 隔离目录采集 `final_edge_fastapi_http_gateway`，并同步到公开报告/JSON。 |
| Jetson / IPC stdlib fallback | Dependency-light HTTP benchmark for offline edge nodes without FastAPI/Uvicorn. | 历史备用证据：300 samples，p95 2ms，max 3ms，Linux `5.15.148-tegra` / `aarch64`，并带 `tegrastats`。当前已被 FastAPI 证据升级替代。 |

## 2026-06-15 Jetson Evidence Status

- 当前主路线：`scripts/collect_jetson_edge_evidence.py --host wearedge-pro.local --user ryn --remote-dir /home/ryn/Wearedge-Industrial-AI-agent-fastapi-competition --iterations 20 --skip-deploy`。
- FastAPI 远程隔离目录：`/home/ryn/Wearedge-Industrial-AI-agent-fastapi-competition`；`.venv` 指向该目录内的 `.venv-fastapi`，离线安装 `fastapi==0.115.14`、`uvicorn==0.30.6`、`python-multipart==0.0.20`。
- stdlib 备用目录：`/home/ryn/Wearedge-Industrial-AI-agent-competition`；仅保留为无 FastAPI/Uvicorn 环境下的 fallback 证据路径。
- 旧的 `~/WearEdge-Pro` 项目没有被修改或复用。
- 公开证据：`docs/finals-jetson-gateway-latency-benchmark-report.md` 和 `docs/submission/evidence/finals-jetson-gateway-latency-benchmark.json`。
- 忽略目录证据：`submission-assets/live-evidence/edge-runtime-fastapi/06-http-resource-benchmark.*`、`07-edge-runtime-evidence-manifest.md`、`08-tegrastats-http-resource-benchmark.log`、`09-jetson-edge-evidence-collection-summary.json`。
- 当前证据等级：`final_edge_fastapi_http_gateway`。这是 Jetson 上真实 FastAPI HTTP endpoint 调用 `/v1/workflow-canvas/decision`，不是 in-process replay。
- 当前指标：300 samples，p95 6ms，max 8ms，RSS max 32.47MB，Linux `5.15.148-tegra` / `aarch64`，并带 `tegrastats`。
- FastAPI 升级路径说明：Jetson 本机无法解析公网 pip 源，因此依赖通过 Windows 侧 aarch64/Linux/Python 3.10 wheelhouse 下载后离线上传安装，避免污染旧项目和系统 Python。
- 边界：Jetson 上观察到已有 uvicorn 进程位于 `/home/ryn/WearEdge-Pro`，不把它作为本项目比赛证据路径使用。

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

Do not add competition files into the existing Jetson project used by the separate M400/VLM work. If a new edge-side experiment is needed, create it under `~/Wearedge-Industrial-AI-agent-competition` or a clearly named sibling competition folder, then pull only the generated evidence back into `submission-assets/live-evidence/edge-runtime/`.

To explicitly allow the collector to create an isolated `.venv` and install FastAPI dependencies from the network, add:

```powershell
python scripts/collect_jetson_edge_evidence.py --host wearedge-pro.local --user ryn --iterations 20 --allow-remote-pip-install
```

Isolation rules:

| Item | Competition evidence path |
| --- | --- |
| Runtime checkout | `~/Wearedge-Industrial-AI-agent-fastapi-competition` for current FastAPI evidence; `~/Wearedge-Industrial-AI-agent-competition` for stdlib fallback. |
| Python environment | `~/Wearedge-Industrial-AI-agent-fastapi-competition/.venv-fastapi` for FastAPI evidence; isolated competition `.venv` or system `python3` for fallback. |
| Pulled evidence | `submission-assets/live-evidence/edge-runtime-fastapi/` on this workstation for FastAPI evidence. |
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
