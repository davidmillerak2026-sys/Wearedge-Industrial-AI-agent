from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


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
GATEWAY_APP = "jetson.app:app"


def run_local_gateway_latency_benchmark(
    *,
    iterations: int = DEFAULT_ITERATIONS,
    host: str = DEFAULT_HOST,
    port: int | None = None,
    startup_timeout_s: float = DEFAULT_STARTUP_TIMEOUT_S,
    python_executable: str = sys.executable,
) -> dict[str, Any]:
    selected_port = port or find_free_port(host)
    base_url = f"http://{host}:{selected_port}"
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
    env["WEAREDGE_DEPLOYMENT_MODE"] = "local_http_gateway_benchmark"
    env.setdefault("WEAREDGE_EDGE_NODE_ID", "local-gateway-benchmark")
    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        healthz = wait_for_health(base_url, timeout_s=startup_timeout_s)
        result = run_latency_benchmark(iterations=iterations, base_url=base_url)
        result["evidence_tier"] = "local_fastapi_http_gateway"
        result["boundary"] = (
            "This benchmark starts the Wearedge FastAPI gateway on the current workstation and measures real HTTP "
            "POST calls to /v1/workflow-canvas/decision. It is stronger than in-process replay, but it is still "
            "not Jetson/IPC hardware evidence until rerun on the final edge node with resource logs."
        )
        result["gateway"] = {
            "app": GATEWAY_APP,
            "base_url": base_url,
            "healthz_ok": bool(healthz.get("ok")),
            "deployment_mode": healthz.get("competition", {}).get("workflow_canvas_endpoint"),
            "process_started": True,
            "pid": process.pid,
        }
        return result
    finally:
        stop_process(process)


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
        print(f"target_met={result['target_met']}")
        print(f"report={args.report}")
        print(f"json_output={args.json_output}")

    return 0 if result["ok"] and result["target_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
