from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover - exercised only on lean edge images.
    psutil = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from benchmark_workflow_canvas_latency import DEFAULT_ITERATIONS, run_latency_benchmark, write_outputs


DEFAULT_REPORT = REPO_ROOT / "docs" / "finals-local-gateway-latency-benchmark-report.md"
DEFAULT_JSON = REPO_ROOT / "docs" / "submission" / "evidence" / "finals-local-gateway-latency-benchmark.json"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_STARTUP_TIMEOUT_S = 20.0
DEFAULT_RESOURCE_SAMPLE_INTERVAL_S = 0.1
GATEWAY_APP = "jetson.app:app"


def run_local_gateway_latency_benchmark(
    *,
    iterations: int = DEFAULT_ITERATIONS,
    host: str = DEFAULT_HOST,
    port: int | None = None,
    startup_timeout_s: float = DEFAULT_STARTUP_TIMEOUT_S,
    resource_sample_interval_s: float = DEFAULT_RESOURCE_SAMPLE_INTERVAL_S,
    collect_resources: bool = True,
    python_executable: str = sys.executable,
    final_edge_node: bool = False,
    deployment_mode: str | None = None,
    edge_node_id: str | None = None,
) -> dict[str, Any]:
    selected_port = port or find_free_port(host)
    base_url = f"http://{host}:{selected_port}"
    effective_deployment_mode = deployment_mode or (
        "jetson_edge_http_gateway_benchmark" if final_edge_node else "local_http_gateway_benchmark"
    )
    effective_edge_node_id = edge_node_id or (
        "jetson-edge-benchmark" if final_edge_node else "local-gateway-benchmark"
    )
    command = [
        python_executable,
        "-m",
        "uvicorn",
        GATEWAY_APP,
        "--host",
        host,
        "--port",
        str(selected_port),
        "--log-level",
        "warning",
    ]
    env = os.environ.copy()
    env["WEAREDGE_AUTH_DISABLED"] = "1"
    env["WEAREDGE_DEPLOYMENT_MODE"] = effective_deployment_mode
    env["WEAREDGE_EDGE_NODE_ID"] = effective_edge_node_id
    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    sampler: ResourceSampler | None = None
    try:
        healthz = wait_for_health(base_url, timeout_s=startup_timeout_s)
        if collect_resources:
            sampler = start_resource_sampler(process.pid, interval_s=resource_sample_interval_s)
        result = run_latency_benchmark(iterations=iterations, base_url=base_url)
        resource_profile = stop_resource_sampler(sampler) if sampler else unavailable_resource_profile()
        sampler = None
        result["evidence_tier"] = (
            "final_edge_fastapi_http_gateway" if final_edge_node else "local_fastapi_http_gateway"
        )
        result["boundary"] = build_gateway_boundary(final_edge_node=final_edge_node)
        result["gateway"] = {
            "app": GATEWAY_APP,
            "base_url": base_url,
            "healthz_ok": bool(healthz.get("ok")),
            "deployment_mode": healthz.get("deployment_mode", effective_deployment_mode),
            "edge_node_id": effective_edge_node_id,
            "process_started": True,
            "pid": process.pid,
        }
        result["resource_profile"] = resource_profile
        return result
    finally:
        if sampler is not None:
            stop_resource_sampler(sampler)
        stop_process(process)


class ResourceSampler:
    def __init__(
        self,
        *,
        stop_event: threading.Event,
        thread: threading.Thread | None,
        samples: list[dict[str, Any]],
        interval_s: float,
        pid: int,
        backend: str,
    ) -> None:
        self.stop_event = stop_event
        self.thread = thread
        self.samples = samples
        self.interval_s = interval_s
        self.pid = pid
        self.backend = backend


def start_resource_sampler(pid: int, *, interval_s: float = DEFAULT_RESOURCE_SAMPLE_INTERVAL_S) -> ResourceSampler:
    safe_interval = max(interval_s, 0.05)
    samples: list[dict[str, Any]] = []
    stop_event = threading.Event()
    if psutil is None:
        if platform.system().lower() != "linux" or not Path(f"/proc/{pid}").exists():
            return ResourceSampler(
                stop_event=stop_event,
                thread=None,
                samples=samples,
                interval_s=safe_interval,
                pid=pid,
                backend="unavailable",
            )

        def collect_linux_procfs() -> None:
            started = time.perf_counter()
            state: dict[str, Any] = {}
            while not stop_event.is_set():
                sample = sample_linux_procfs_resources(pid, started, state)
                if sample:
                    samples.append(sample)
                stop_event.wait(safe_interval)

        thread = threading.Thread(target=collect_linux_procfs, name="wearedge-procfs-sampler", daemon=True)
        thread.start()
        return ResourceSampler(
            stop_event=stop_event,
            thread=thread,
            samples=samples,
            interval_s=safe_interval,
            pid=pid,
            backend="linux_procfs",
        )

    def collect() -> None:
        started = time.perf_counter()
        try:
            process = psutil.Process(pid)
            process.cpu_percent(interval=None)
        except (psutil.Error, OSError):
            return
        while not stop_event.is_set():
            sample = sample_process_resources(process, started)
            if sample:
                samples.append(sample)
            stop_event.wait(safe_interval)

    thread = threading.Thread(target=collect, name="wearedge-resource-sampler", daemon=True)
    thread.start()
    return ResourceSampler(
        stop_event=stop_event,
        thread=thread,
        samples=samples,
        interval_s=safe_interval,
        pid=pid,
        backend="psutil",
    )


def stop_resource_sampler(sampler: ResourceSampler) -> dict[str, Any]:
    sampler.stop_event.set()
    if sampler.thread is not None:
        sampler.thread.join(timeout=2)
    if not sampler.samples and psutil is not None:
        try:
            process = psutil.Process(sampler.pid)
            sample = sample_process_resources(process, time.perf_counter())
            if sample:
                sampler.samples.append(sample)
        except (psutil.Error, OSError):
            pass
    return summarize_resource_profile(sampler.samples, interval_s=sampler.interval_s, backend=sampler.backend)


def sample_process_resources(process: Any, started: float) -> dict[str, Any] | None:
    try:
        memory = process.memory_info()
        system_memory = psutil.virtual_memory()
        return {
            "elapsed_ms": max(0, int((time.perf_counter() - started) * 1000)),
            "process_cpu_percent": round(float(process.cpu_percent(interval=None)), 2),
            "process_rss_mb": round(memory.rss / (1024 * 1024), 2),
            "process_vms_mb": round(memory.vms / (1024 * 1024), 2),
            "system_memory_percent": round(float(system_memory.percent), 2),
            "system_available_mb": round(system_memory.available / (1024 * 1024), 2),
        }
    except (psutil.Error, OSError):
        return None


def sample_linux_procfs_resources(pid: int, started: float, state: dict[str, Any]) -> dict[str, Any] | None:
    try:
        status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8", errors="replace")
        rss_kb = parse_status_kb(status, "VmRSS")
        vms_kb = parse_status_kb(status, "VmSize")
        memory = read_linux_meminfo()
        proc_ticks = read_process_cpu_ticks(pid)
        total_ticks = read_total_cpu_ticks()
    except (OSError, ValueError):
        return None

    last_proc_ticks = state.get("proc_ticks")
    last_total_ticks = state.get("total_ticks")
    cpu_percent = 0.0
    if isinstance(last_proc_ticks, int) and isinstance(last_total_ticks, int):
        proc_delta = max(0, proc_ticks - last_proc_ticks)
        total_delta = max(1, total_ticks - last_total_ticks)
        cpu_percent = (proc_delta / total_delta) * max(1, os.cpu_count() or 1) * 100
    state["proc_ticks"] = proc_ticks
    state["total_ticks"] = total_ticks

    return {
        "elapsed_ms": max(0, int((time.perf_counter() - started) * 1000)),
        "process_cpu_percent": round(cpu_percent, 2),
        "process_rss_mb": round(rss_kb / 1024, 2),
        "process_vms_mb": round(vms_kb / 1024, 2),
        "system_memory_percent": round(memory.get("used_percent", 0.0), 2),
        "system_available_mb": round(memory.get("available_kb", 0) / 1024, 2),
    }


def parse_status_kb(status: str, key: str) -> int:
    prefix = f"{key}:"
    for line in status.splitlines():
        if line.startswith(prefix):
            parts = line.split()
            if len(parts) >= 2:
                return int(parts[1])
    return 0


def read_linux_meminfo() -> dict[str, float]:
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8", errors="replace").splitlines():
            parts = line.split()
            if len(parts) >= 2:
                values[parts[0].rstrip(":")] = int(parts[1])
    except OSError:
        return {"total_kb": 0, "available_kb": 0, "used_percent": 0.0}
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", 0)
    used_percent = 0.0 if total <= 0 else (1 - available / total) * 100
    return {"total_kb": total, "available_kb": available, "used_percent": used_percent}


def read_process_cpu_ticks(pid: int) -> int:
    stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8", errors="replace")
    after_name = stat.rsplit(")", maxsplit=1)[1].strip().split()
    return int(after_name[11]) + int(after_name[12])


def read_total_cpu_ticks() -> int:
    first_line = Path("/proc/stat").read_text(encoding="utf-8", errors="replace").splitlines()[0]
    return sum(int(part) for part in first_line.split()[1:])


def summarize_resource_profile(samples: list[dict[str, Any]], *, interval_s: float, backend: str) -> dict[str, Any]:
    return {
        "available": bool(samples),
        "backend": backend,
        "sample_interval_s": interval_s,
        "sample_count": len(samples),
        "platform": platform_profile(),
        "process_cpu_percent": stats([float(sample["process_cpu_percent"]) for sample in samples]),
        "process_rss_mb": stats([float(sample["process_rss_mb"]) for sample in samples]),
        "process_vms_mb": stats([float(sample["process_vms_mb"]) for sample in samples]),
        "system_memory_percent": stats([float(sample["system_memory_percent"]) for sample in samples]),
        "samples": samples,
        "boundary": (
            "Resource samples describe the benchmark gateway process on the node that runs this script. "
            "On Jetson, keep this profile together with tegrastats for final-round defense."
        ),
    }


def unavailable_resource_profile() -> dict[str, Any]:
    return {
        "available": False,
        "backend": "unavailable",
        "sample_interval_s": 0,
        "sample_count": 0,
        "platform": platform_profile(),
        "process_cpu_percent": stats([]),
        "process_rss_mb": stats([]),
        "process_vms_mb": stats([]),
        "system_memory_percent": stats([]),
        "samples": [],
        "boundary": "psutil is unavailable, so process resource sampling was skipped.",
    }


def platform_profile() -> dict[str, Any]:
    profile = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
    }
    if psutil is not None:
        memory = psutil.virtual_memory()
        profile.update(
            {
                "cpu_logical_count": psutil.cpu_count(logical=True),
                "cpu_physical_count": psutil.cpu_count(logical=False),
                "total_memory_mb": round(memory.total / (1024 * 1024), 2),
            }
        )
    elif platform.system().lower() == "linux":
        memory = read_linux_meminfo()
        profile.update(
            {
                "cpu_logical_count": os.cpu_count(),
                "cpu_physical_count": None,
                "total_memory_mb": round(memory.get("total_kb", 0) / 1024, 2),
            }
        )
    return profile


def build_gateway_boundary(*, final_edge_node: bool) -> str:
    if final_edge_node:
        return (
            "This benchmark starts the Wearedge FastAPI gateway on the final Jetson/IPC/plant edge node and "
            "measures real HTTP POST calls to /v1/workflow-canvas/decision with process resource sampling. "
            "It measures the collaborative decision path, not high-detail image/VLM inference."
        )
    return (
        "This benchmark starts the Wearedge FastAPI gateway on the current workstation and measures real HTTP "
        "POST calls to /v1/workflow-canvas/decision with process resource sampling. It is stronger than "
        "in-process replay, but it is still not Jetson/IPC hardware evidence until rerun on the final edge node."
    )


def stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0, "p50": 0, "p95": 0, "avg": 0, "max": 0}
    sorted_values = sorted(values)
    return {
        "min": sorted_values[0],
        "p50": percentile(sorted_values, 0.50),
        "p95": percentile(sorted_values, 0.95),
        "avg": round(sum(sorted_values) / len(sorted_values), 2),
        "max": sorted_values[-1],
    }


def percentile(sorted_values: list[float], ratio: float) -> float:
    index = int(round((len(sorted_values) - 1) * ratio))
    return sorted_values[max(0, min(index, len(sorted_values) - 1))]


def find_free_port(host: str = DEFAULT_HOST) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def wait_for_health(base_url: str, *, timeout_s: float = DEFAULT_STARTUP_TIMEOUT_S) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/healthz", timeout=1.0) as response:
                data = json.loads(response.read().decode("utf-8"))
                if isinstance(data, dict) and data.get("ok") is True:
                    return data
                last_error = "healthz returned non-ok payload"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(0.2)
    raise RuntimeError(f"gateway did not become healthy at {base_url}/healthz: {last_error}")


def stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark the local Wearedge FastAPI gateway over HTTP.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--startup-timeout", type=float, default=DEFAULT_STARTUP_TIMEOUT_S)
    parser.add_argument("--resource-sample-interval", type=float, default=DEFAULT_RESOURCE_SAMPLE_INTERVAL_S)
    parser.add_argument("--no-resource-sampling", action="store_true")
    parser.add_argument("--final-edge-node", action="store_true")
    parser.add_argument("--deployment-mode", default=None)
    parser.add_argument("--edge-node-id", default=None)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = run_local_gateway_latency_benchmark(
            iterations=args.iterations,
            host=args.host,
            port=args.port,
            startup_timeout_s=args.startup_timeout,
            resource_sample_interval_s=args.resource_sample_interval,
            collect_resources=not args.no_resource_sampling,
            final_edge_node=args.final_edge_node,
            deployment_mode=args.deployment_mode,
            edge_node_id=args.edge_node_id,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    write_outputs(result, report_path=args.report, json_path=args.json_output)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"mode={result['mode']}")
        print(f"evidence_tier={result['evidence_tier']}")
        print(f"endpoint={result['endpoint']}")
        print(f"sample_count={result['sample_count']}")
        print(f"wall_latency_ms_max={result['wall_latency_ms']['max']}")
        print(f"wall_latency_ms_p95={result['wall_latency_ms']['p95']}")
        resource_profile = result.get("resource_profile", {})
        print(f"resource_sample_count={resource_profile.get('sample_count', 0)}")
        print(f"process_rss_mb_max={resource_profile.get('process_rss_mb', {}).get('max', 0)}")
        print(f"target_met={result['target_met']}")
        print(f"report={args.report}")
        print(f"json_output={args.json_output}")

    return 0 if result["ok"] and result["target_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
