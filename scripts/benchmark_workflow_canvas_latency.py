from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from jetson.competition import COMPETITION_TARGETS, build_competition_decision
from run_competition_eval import load_dataset
from run_finals_validation import DEFAULT_DATASET


DEFAULT_REPORT = REPO_ROOT / "docs" / "finals-latency-benchmark-report.md"
DEFAULT_JSON = REPO_ROOT / "docs" / "submission" / "evidence" / "finals-latency-benchmark.json"
DEFAULT_ITERATIONS = 20


def run_latency_benchmark(
    *,
    dataset_path: Path = DEFAULT_DATASET,
    iterations: int = DEFAULT_ITERATIONS,
    base_url: str | None = None,
) -> dict[str, Any]:
    if iterations <= 0:
        raise ValueError("iterations must be positive")

    cases = load_dataset(dataset_path)
    samples: list[dict[str, Any]] = []
    mode = "http" if base_url else "in_process"
    endpoint = _endpoint(base_url) if base_url else "jetson.competition.build_competition_decision"

    for iteration in range(1, iterations + 1):
        for case in cases:
            started = time.perf_counter()
            decision = _call_http(endpoint, case) if base_url else build_competition_decision(case)
            elapsed_ms = max(1, int((time.perf_counter() - started) * 1000))
            samples.append(
                {
                    "iteration": iteration,
                    "case_id": str(case.get("case_id", "unknown")),
                    "primary_direction": decision.get("collaborative_decision", {}).get("primary_direction"),
                    "wall_latency_ms": elapsed_ms,
                    "decision_latency_ms": int(decision.get("latency_ms", elapsed_ms)),
                    "ok": bool(decision.get("ok")),
                }
            )

    wall_latencies = [sample["wall_latency_ms"] for sample in samples]
    decision_latencies = [sample["decision_latency_ms"] for sample in samples]
    boundary = (
        "HTTP mode measures the Workflow Canvas collaborative decision path through "
        "/v1/workflow-canvas/decision. For final defense, run it on the Jetson/IPC/local industrial PC gateway "
        "and capture edge hardware resource logs beside the report."
        if base_url
        else (
            "Default in_process mode is a deterministic local replay of the Workflow Canvas decision engine. "
            "Use --base-url against a deployed Jetson/IPC/local-server gateway before claiming deployed endpoint latency."
        )
    )
    summary = {
        "ok": all(sample["ok"] for sample in samples),
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "mode": mode,
        "endpoint": endpoint,
        "dataset_path": str(dataset_path),
        "case_count": len(cases),
        "iterations": iterations,
        "sample_count": len(samples),
        "target_latency_ms": COMPETITION_TARGETS["latency_ms_max"],
        "wall_latency_ms": _latency_stats(wall_latencies),
        "decision_latency_ms": _latency_stats(decision_latencies),
        "target_met": max(wall_latencies) <= COMPETITION_TARGETS["latency_ms_max"],
        "boundary": boundary,
        "samples": samples,
    }
    return summary


def render_report(result: dict[str, Any]) -> str:
    wall = result["wall_latency_ms"]
    decision = result["decision_latency_ms"]
    lines = [
        "# Finals Latency Benchmark Report",
        "",
        f"Generated: {result['generated_at']}",
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
        "## Summary",
        "",
        f"- Evidence tier: {result.get('evidence_tier', result['mode'])}",
        f"- Mode: {result['mode']}",
        f"- Endpoint: `{result['endpoint']}`",
        f"- Dataset cases: {result['case_count']}",
        f"- Iterations: {result['iterations']}",
        f"- Samples: {result['sample_count']}",
        f"- Target latency: <= {result['target_latency_ms']} ms",
        f"- Target met: {result['target_met']}",
        "",
    ]
    gateway = result.get("gateway")
    if isinstance(gateway, dict):
        lines.extend(
            [
                "## Gateway",
                "",
                f"- App: `{gateway.get('app', 'unknown')}`",
                f"- Base URL: `{gateway.get('base_url', 'unknown')}`",
                f"- Healthz OK: {gateway.get('healthz_ok', False)}",
                f"- Workflow endpoint: `{gateway.get('deployment_mode', 'unknown')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Latency Stats",
            "",
            "| Metric | Min | P50 | P95 | Avg | Max |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            (
                f"| Wall-clock replay latency | {wall['min']} ms | {wall['p50']} ms | {wall['p95']} ms | "
                f"{wall['avg']} ms | {wall['max']} ms |"
            ),
            (
                f"| Decision-reported latency | {decision['min']} ms | {decision['p50']} ms | {decision['p95']} ms | "
                f"{decision['avg']} ms | {decision['max']} ms |"
            ),
            "",
            "## Sample Coverage",
            "",
            "| Case | Samples | Max Wall Latency |",
            "| --- | ---: | ---: |",
        ]
    )
    by_case: dict[str, list[int]] = {}
    for sample in result["samples"]:
        by_case.setdefault(sample["case_id"], []).append(int(sample["wall_latency_ms"]))
    for case_id in sorted(by_case):
        values = by_case[case_id]
        lines.append(f"| {case_id} | {len(values)} | {max(values)} ms |")

    lines.extend(
        [
            "",
            "## Next Evidence Upgrade",
            "",
            "- Run the same script with `--base-url http://<edge-host>:<port>` against the deployed FastAPI gateway.",
            "- Capture Jetson / IPC / local industrial PC resource logs beside this report before final-round defense.",
            "- Keep this report separate from model image-inference latency; it measures the Workflow Canvas collaborative decision path.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(result: dict[str, Any], *, report_path: Path = DEFAULT_REPORT, json_path: Path = DEFAULT_JSON) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result), encoding="utf-8")
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def _latency_stats(values: list[int]) -> dict[str, float]:
    if not values:
        return {"min": 0, "p50": 0, "p95": 0, "avg": 0, "max": 0}
    sorted_values = sorted(values)
    return {
        "min": sorted_values[0],
        "p50": _percentile(sorted_values, 0.50),
        "p95": _percentile(sorted_values, 0.95),
        "avg": round(sum(sorted_values) / len(sorted_values), 2),
        "max": sorted_values[-1],
    }


def _percentile(sorted_values: list[int], ratio: float) -> int:
    index = int(round((len(sorted_values) - 1) * ratio))
    return sorted_values[max(0, min(index, len(sorted_values) - 1))]


def _endpoint(base_url: str | None) -> str:
    assert base_url is not None
    return base_url.rstrip("/") + "/v1/workflow-canvas/decision"


def _call_http(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"failed to call {endpoint}: {exc}") from exc
    data = json.loads(body)
    if not isinstance(data, dict):
        raise RuntimeError(f"{endpoint} returned non-object JSON")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark Workflow Canvas decision latency for finals evidence.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--base-url", default=None, help="Optional deployed FastAPI base URL, e.g. http://127.0.0.1:8081")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = run_latency_benchmark(dataset_path=args.dataset, iterations=args.iterations, base_url=args.base_url)
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    write_outputs(result, report_path=args.report, json_path=args.json_output)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"mode={result['mode']}")
        print(f"sample_count={result['sample_count']}")
        print(f"wall_latency_ms_max={result['wall_latency_ms']['max']}")
        print(f"wall_latency_ms_p95={result['wall_latency_ms']['p95']}")
        print(f"target_met={result['target_met']}")
        print(f"report={args.report}")
        print(f"json_output={args.json_output}")

    return 0 if result["ok"] and result["target_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
