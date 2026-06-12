from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from benchmark_local_gateway_latency import (  # noqa: E402
    find_free_port,
    start_resource_sampler,
    stop_resource_sampler,
    unavailable_resource_profile,
)
from benchmark_workflow_canvas_latency import (  # noqa: E402
    DEFAULT_ITERATIONS,
    run_latency_benchmark,
    write_outputs,
)
from collect_edge_runtime_evidence import build_manifest, render_manifest  # noqa: E402
from jetson.competition import COMPETITION_DECISION_VERSION, COMPETITION_TARGETS, build_competition_decision  # noqa: E402
from jetson.solution_profile import RuntimeProfileInput, build_solution_profile  # noqa: E402


DEFAULT_REPORT = REPO_ROOT / "docs" / "finals-stdlib-gateway-latency-benchmark-report.md"
DEFAULT_JSON = REPO_ROOT / "docs" / "submission" / "evidence" / "finals-stdlib-gateway-latency-benchmark.json"
DEFAULT_MANIFEST = REPO_ROOT / "submission-assets" / "live-evidence" / "edge-runtime" / "07-edge-runtime-evidence-manifest.md"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_RESOURCE_SAMPLE_INTERVAL_S = 0.1
GATEWAY_APP = "scripts.benchmark_edge_stdlib_gateway:StdlibWorkflowCanvasGateway"


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class StdlibWorkflowCanvasHandler(BaseHTTPRequestHandler):
    server_version = "WearedgeStdlibGateway/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._send_json(build_healthz())
            return
        if self.path == "/v1/edge/runtime-profile":
            self._send_json(build_edge_runtime_profile())
            return
        if self.path == "/v1/industrial-agent/solution-profile":
            self._send_json(build_solution_profile(runtime_profile_input()))
            return
        self._send_json({"ok": False, "error": "not_found", "path": self.path}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/v1/workflow-canvas/decision", "/v1/competition/decision"}:
            self._send_json({"ok": False, "error": "not_found", "path": self.path}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                raise ValueError("payload must be a JSON object")
            self._send_json(build_competition_decision(payload))
        except (json.JSONDecodeError, ValueError) as exc:
            self._send_json({"ok": False, "error": "bad_request", "detail": str(exc)}, status=400)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_edge_stdlib_gateway_benchmark(
    *,
    iterations: int = DEFAULT_ITERATIONS,
    host: str = DEFAULT_HOST,
    port: int | None = None,
    resource_sample_interval_s: float = DEFAULT_RESOURCE_SAMPLE_INTERVAL_S,
    collect_resources: bool = True,
    final_edge_node: bool = False,
    deployment_mode: str | None = None,
    edge_node_id: str | None = None,
) -> dict[str, Any]:
    if iterations <= 0:
        raise ValueError("iterations must be positive")

    selected_port = port or find_free_port(host)
    base_url = f"http://{host}:{selected_port}"
    effective_deployment_mode = deployment_mode or (
        "jetson_edge_stdlib_http_gateway_benchmark" if final_edge_node else "local_stdlib_http_gateway_benchmark"
    )
    effective_edge_node_id = edge_node_id or (
        "jetson-orin-nano-8gb" if final_edge_node else "local-stdlib-gateway-benchmark"
    )
    previous_env = {
        "WEAREDGE_DEPLOYMENT_MODE": os.environ.get("WEAREDGE_DEPLOYMENT_MODE"),
        "WEAREDGE_EDGE_NODE_ID": os.environ.get("WEAREDGE_EDGE_NODE_ID"),
        "WEAREDGE_MODEL": os.environ.get("WEAREDGE_MODEL"),
        "WEAREDGE_MODEL_VARIANT": os.environ.get("WEAREDGE_MODEL_VARIANT"),
        "LLAMA_BASE_URL": os.environ.get("LLAMA_BASE_URL"),
    }
    os.environ["WEAREDGE_DEPLOYMENT_MODE"] = effective_deployment_mode
    os.environ["WEAREDGE_EDGE_NODE_ID"] = effective_edge_node_id
    os.environ.setdefault("WEAREDGE_MODEL", "gemma4")
    os.environ.setdefault("WEAREDGE_MODEL_VARIANT", "E2B")
    os.environ.setdefault("LLAMA_BASE_URL", "http://127.0.0.1:8080")

    server = ThreadingHTTPServer((host, selected_port), StdlibWorkflowCanvasHandler)
    thread = threading.Thread(target=server.serve_forever, name="wearedge-stdlib-gateway", daemon=True)
    sampler = None
    try:
        thread.start()
        healthz = wait_for_health(base_url)
        if collect_resources:
            sampler = start_resource_sampler(os.getpid(), interval_s=resource_sample_interval_s)
        result = run_latency_benchmark(iterations=iterations, base_url=base_url)
        resource_profile = stop_resource_sampler(sampler) if sampler else unavailable_resource_profile()
        sampler = None
        result["evidence_tier"] = (
            "final_edge_stdlib_http_gateway" if final_edge_node else "local_stdlib_http_gateway"
        )
        result["boundary"] = build_stdlib_boundary(final_edge_node=final_edge_node)
        result["gateway"] = {
            "app": GATEWAY_APP,
            "base_url": base_url,
            "healthz_ok": bool(healthz.get("ok")),
            "deployment_mode": effective_deployment_mode,
            "edge_node_id": effective_edge_node_id,
            "process_started": True,
            "pid": os.getpid(),
            "dependency_profile": "python_stdlib_no_fastapi_uvicorn",
            "workflow_endpoint": "/v1/workflow-canvas/decision",
            "runtime_profile_endpoint": "/v1/edge/runtime-profile",
        }
        result["resource_profile"] = resource_profile
        return result
    finally:
        if sampler is not None:
            stop_resource_sampler(sampler)
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        restore_environment(previous_env)


def wait_for_health(base_url: str, *, timeout_s: float = 5.0) -> dict[str, Any]:
    import urllib.error
    import urllib.request

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
        time.sleep(0.1)
    raise RuntimeError(f"stdlib gateway did not become healthy at {base_url}/healthz: {last_error}")


def build_healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "api_version": "wearedge-stdlib-edge-gateway.v1",
        "gateway": GATEWAY_APP,
        "deployment_mode": os.environ.get("WEAREDGE_DEPLOYMENT_MODE", "local_stdlib_http_gateway_benchmark"),
        "edge_node_id": os.environ.get("WEAREDGE_EDGE_NODE_ID", "local-stdlib-gateway-benchmark"),
        "dependency_profile": "python_stdlib_no_fastapi_uvicorn",
        "competition": {
            "decision_version": COMPETITION_DECISION_VERSION,
            "workflow_canvas_endpoint": "/v1/workflow-canvas/decision",
            "targets": COMPETITION_TARGETS,
        },
        "boundary": (
            "This dependency-light gateway is for edge evidence when FastAPI/Uvicorn are unavailable. "
            "It reuses the same deterministic Workflow Canvas decision engine."
        ),
    }


def build_edge_runtime_profile() -> dict[str, Any]:
    return {
        "ok": True,
        "api_version": "wearedge-edge-runtime-profile.v1",
        "deployment_mode": os.environ.get("WEAREDGE_DEPLOYMENT_MODE", "local_stdlib_http_gateway_benchmark"),
        "edge_node_id": os.environ.get("WEAREDGE_EDGE_NODE_ID", "local-stdlib-gateway-benchmark"),
        "supported_deployment_modes": ["jetson", "ipc", "local_server", "cloud_proxy"],
        "capabilities": {
            "local_inference_ready": True,
            "workflow_canvas_ready": True,
            "competition_decision_ready": True,
            "audit_log_ready": True,
            "human_approval_gate_required": True,
        },
        "endpoints": {
            "healthz": "/healthz",
            "runtime_profile": "/v1/edge/runtime-profile",
            "solution_profile": "/v1/industrial-agent/solution-profile",
            "workflow_canvas_decision": "/v1/workflow-canvas/decision",
        },
        "safety_boundary": {
            "model_direct_ot_control": False,
            "requires_human_confirmation_for_high_risk_actions": True,
            "direct_plc_writeback": "not_allowed",
        },
        "dependency_profile": "python_stdlib_no_fastapi_uvicorn",
    }


def runtime_profile_input() -> RuntimeProfileInput:
    return RuntimeProfileInput(
        model=os.environ.get("WEAREDGE_MODEL", "gemma4"),
        model_variant=os.environ.get("WEAREDGE_MODEL_VARIANT", "E2B"),
        llama_base_url=os.environ.get("LLAMA_BASE_URL", "http://127.0.0.1:8080"),
        deployment_mode=os.environ.get("WEAREDGE_DEPLOYMENT_MODE", "jetson"),
        edge_node_id=os.environ.get("WEAREDGE_EDGE_NODE_ID", "jetson-orin-nano-8gb"),
    )


def build_stdlib_boundary(*, final_edge_node: bool) -> str:
    if final_edge_node:
        return (
            "This benchmark starts a dependency-light Python stdlib HTTP gateway on the final Jetson/IPC/plant "
            "edge node and measures real HTTP POST calls to /v1/workflow-canvas/decision. It uses the same "
            "jetson.competition.build_competition_decision entry point as the FastAPI gateway, but it is a "
            "fallback evidence path for environments where FastAPI/Uvicorn are not installed. It measures the "
            "collaborative decision path, not high-detail image/VLM inference."
        )
    return (
        "This benchmark starts a dependency-light Python stdlib HTTP gateway on the current machine and measures "
        "real HTTP POST calls to /v1/workflow-canvas/decision. It is stronger than in-process replay, but it is "
        "final edge evidence only when rerun on Jetson, IPC, or the plant edge node."
    )


def write_manifest_file(
    *,
    manifest_path: Path,
    report_path: Path,
    json_path: Path,
    benchmark: dict[str, Any],
    final_edge_node: bool,
    iterations: int,
) -> None:
    manifest = build_manifest(
        output_dir=manifest_path.parent,
        report_path=report_path,
        json_path=json_path,
        benchmark=benchmark,
        rerun_benchmark=True,
        final_edge_node=final_edge_node,
        iterations=iterations,
    )
    manifest["boundary"] = (
        f"{manifest['boundary']} The benchmark gateway dependency profile is "
        "`python_stdlib_no_fastapi_uvicorn`; use FastAPI evidence when that runtime is available."
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(render_manifest(manifest), encoding="utf-8")


def restore_environment(previous: dict[str, str | None]) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark a dependency-light Wearedge stdlib HTTP gateway.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--resource-sample-interval", type=float, default=DEFAULT_RESOURCE_SAMPLE_INTERVAL_S)
    parser.add_argument("--no-resource-sampling", action="store_true")
    parser.add_argument("--final-edge-node", action="store_true")
    parser.add_argument("--deployment-mode", default=None)
    parser.add_argument("--edge-node-id", default=None)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--manifest-output", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = run_edge_stdlib_gateway_benchmark(
            iterations=args.iterations,
            host=args.host,
            port=args.port,
            resource_sample_interval_s=args.resource_sample_interval,
            collect_resources=not args.no_resource_sampling,
            final_edge_node=args.final_edge_node,
            deployment_mode=args.deployment_mode,
            edge_node_id=args.edge_node_id,
        )
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    write_outputs(result, report_path=args.report, json_path=args.json_output)
    if args.manifest_output is not None:
        write_manifest_file(
            manifest_path=args.manifest_output,
            report_path=args.report,
            json_path=args.json_output,
            benchmark=result,
            final_edge_node=args.final_edge_node,
            iterations=args.iterations,
        )

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
        print(f"target_met={result['target_met']}")
        print(f"report={args.report}")
        print(f"json_output={args.json_output}")

    return 0 if result["ok"] and result["target_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
