from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "collect_edge_runtime_evidence.py"
SOURCE_REPORT = REPO_ROOT / "docs" / "finals-local-gateway-latency-benchmark-report.md"
SOURCE_JSON = REPO_ROOT / "docs" / "submission" / "evidence" / "finals-local-gateway-latency-benchmark.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("collect_edge_runtime_evidence", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_collect_edge_runtime_evidence_copies_benchmark_files(tmp_path: Path) -> None:
    module = _load_module()

    manifest = module.collect_edge_runtime_evidence(
        output_dir=tmp_path,
        source_report=SOURCE_REPORT,
        source_json=SOURCE_JSON,
    )

    assert manifest["ok"] is True
    assert manifest["evidence_tier"] == "local_fastapi_http_gateway"
    assert manifest["mode"] == "http"
    assert manifest["sample_count"] > 0
    assert manifest["resource_sample_count"] > 0
    assert manifest["edge_hardware_claim"]["is_final_edge_hardware"] is False
    assert (tmp_path / "06-http-resource-benchmark-report.md").is_file()
    assert (tmp_path / "06-http-resource-benchmark.json").is_file()
    assert (tmp_path / "07-edge-runtime-evidence-manifest.md").is_file()

    saved = json.loads((tmp_path / "06-http-resource-benchmark.json").read_text(encoding="utf-8"))
    assert saved["evidence_tier"] == "local_fastapi_http_gateway"


def test_edge_runtime_evidence_manifest_states_boundary(tmp_path: Path) -> None:
    module = _load_module()
    manifest = module.collect_edge_runtime_evidence(output_dir=tmp_path)

    text = Path(manifest["manifest_path"]).read_text(encoding="utf-8")

    assert "Edge Runtime Evidence Manifest" in text
    assert "Final edge hardware: False" in text
    assert "final plant edge node" in text
