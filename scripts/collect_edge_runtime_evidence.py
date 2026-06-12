from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from benchmark_local_gateway_latency import run_local_gateway_latency_benchmark
from benchmark_workflow_canvas_latency import write_outputs


DEFAULT_ASSETS_DIR = REPO_ROOT / "submission-assets" / "live-evidence"
DEFAULT_OUTPUT_DIR = DEFAULT_ASSETS_DIR / "edge-runtime"
DEFAULT_SOURCE_REPORT = REPO_ROOT / "docs" / "finals-local-gateway-latency-benchmark-report.md"
DEFAULT_SOURCE_JSON = (
    REPO_ROOT / "docs" / "submission" / "evidence" / "finals-local-gateway-latency-benchmark.json"
)
DEFAULT_EDGE_REPORT_NAME = "06-http-resource-benchmark-report.md"
DEFAULT_EDGE_JSON_NAME = "06-http-resource-benchmark.json"
DEFAULT_MANIFEST_NAME = "07-edge-runtime-evidence-manifest.md"


def collect_edge_runtime_evidence(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    source_report: Path = DEFAULT_SOURCE_REPORT,
    source_json: Path = DEFAULT_SOURCE_JSON,
    rerun_benchmark: bool = False,
    final_edge_node: bool = False,
    iterations: int = 20,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / DEFAULT_EDGE_REPORT_NAME
    json_path = output_dir / DEFAULT_EDGE_JSON_NAME
    manifest_path = output_dir / DEFAULT_MANIFEST_NAME

    if rerun_benchmark:
        benchmark = run_local_gateway_latency_benchmark(iterations=iterations)
        write_outputs(benchmark, report_path=report_path, json_path=json_path)
    else:
        if not source_report.is_file():
            raise FileNotFoundError(f"missing source report: {source_report}")
        if not source_json.is_file():
            raise FileNotFoundError(f"missing source json: {source_json}")
        shutil.copyfile(source_report, report_path)
        shutil.copyfile(source_json, json_path)
        benchmark = load_json(json_path)

    manifest = build_manifest(
        output_dir=output_dir,
        report_path=report_path,
        json_path=json_path,
        benchmark=benchmark,
        rerun_benchmark=rerun_benchmark,
        final_edge_node=final_edge_node,
        iterations=iterations,
    )
    manifest_path.write_text(render_manifest(manifest), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain an object")
    return data


def build_manifest(
    *,
    output_dir: Path,
    report_path: Path,
    json_path: Path,
    benchmark: dict[str, Any],
    rerun_benchmark: bool,
    final_edge_node: bool,
    iterations: int,
) -> dict[str, Any]:
    resource_profile = object_or_empty(benchmark.get("resource_profile"))
    platform_profile = object_or_empty(resource_profile.get("platform"))
    return {
        "ok": bool(benchmark.get("ok")) and bool(benchmark.get("target_met")),
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "output_dir": str(output_dir),
        "rerun_benchmark": rerun_benchmark,
        "iterations": iterations,
        "report_path": str(report_path),
        "json_path": str(json_path),
        "evidence_tier": benchmark.get("evidence_tier", "unknown"),
        "mode": benchmark.get("mode", "unknown"),
        "endpoint": benchmark.get("endpoint", "unknown"),
        "sample_count": int(benchmark.get("sample_count", 0)),
        "target_met": bool(benchmark.get("target_met")),
        "wall_latency_ms": object_or_empty(benchmark.get("wall_latency_ms")),
        "resource_sample_count": int(resource_profile.get("sample_count", 0)),
        "process_rss_mb": object_or_empty(resource_profile.get("process_rss_mb")),
        "platform": platform_profile,
        "edge_hardware_claim": classify_edge_hardware(platform_profile, final_edge_node=final_edge_node),
        "boundary": (
            "This manifest proves that the Wearedge HTTP decision path and resource profile are captured "
            "with replayable files. It is final edge-hardware evidence only when rerun on Jetson, IPC, or the "
            "final plant edge node."
        ),
    }


def classify_edge_hardware(platform_profile: dict[str, Any], *, final_edge_node: bool = False) -> dict[str, Any]:
    system = str(platform_profile.get("system", "")).lower()
    machine = str(platform_profile.get("machine", "")).lower()
    processor = str(platform_profile.get("processor", "")).lower()
    text = " ".join([system, machine, processor])
    is_arm_linux = system == "linux" and machine in {"aarch64", "arm64"}
    likely_jetson = is_arm_linux and ("tegra" in text or "aarch64" in text)
    likely_ipc = system in {"linux", "windows"} and machine in {"amd64", "x86_64"} and not likely_jetson
    return {
        "is_final_edge_hardware": bool(final_edge_node),
        "likely_jetson": bool(likely_jetson),
        "likely_ipc_or_local_server": bool(likely_ipc),
        "classification_basis": f"{platform_profile.get('system', 'unknown')} {platform_profile.get('machine', 'unknown')}",
        "boundary": "Set --final-edge-node only when running on the actual Jetson, IPC, or plant edge node used for defense.",
    }


def object_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def render_manifest(manifest: dict[str, Any]) -> str:
    wall = object_or_empty(manifest.get("wall_latency_ms"))
    rss = object_or_empty(manifest.get("process_rss_mb"))
    hardware = object_or_empty(manifest.get("edge_hardware_claim"))
    lines = [
        "# Edge Runtime Evidence Manifest",
        "",
        f"- Generated: {manifest['generated_at']}",
        f"- OK: {manifest['ok']}",
        f"- Evidence tier: {manifest['evidence_tier']}",
        f"- Mode: {manifest['mode']}",
        f"- Endpoint: `{manifest['endpoint']}`",
        f"- Samples: {manifest['sample_count']}",
        f"- Target met: {manifest['target_met']}",
        f"- Wall latency p95/max: {wall.get('p95', 0)} / {wall.get('max', 0)} ms",
        f"- Resource samples: {manifest['resource_sample_count']}",
        f"- Gateway RSS max: {rss.get('max', 0)} MB",
        f"- Edge hardware classification: {hardware.get('classification_basis', 'unknown')}",
        f"- Final edge hardware: {hardware.get('is_final_edge_hardware', False)}",
        "",
        "## Files",
        "",
        f"- Report: `{manifest['report_path']}`",
        f"- JSON: `{manifest['json_path']}`",
        "",
        "## Boundary",
        "",
        manifest["boundary"],
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect ignored live evidence for the Wearedge edge runtime path.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-report", type=Path, default=DEFAULT_SOURCE_REPORT)
    parser.add_argument("--source-json", type=Path, default=DEFAULT_SOURCE_JSON)
    parser.add_argument("--rerun-benchmark", action="store_true")
    parser.add_argument("--final-edge-node", action="store_true")
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest = collect_edge_runtime_evidence(
            output_dir=args.output_dir,
            source_report=args.source_report,
            source_json=args.source_json,
            rerun_benchmark=args.rerun_benchmark,
            final_edge_node=args.final_edge_node,
            iterations=args.iterations,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else render_manifest(manifest))
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
