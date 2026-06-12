from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_final_submission_bundle.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_final_submission_bundle", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_final_submission_bundle_contains_repo_controlled_artifacts(tmp_path: Path) -> None:
    module = _load_module()

    manifest = module.build_final_submission_bundle(output_dir=tmp_path)

    bundle_path = Path(manifest["bundle_path"])
    manifest_path = Path(manifest["manifest_path"])
    assert manifest["ok"] is True
    assert bundle_path.is_file()
    assert manifest_path.is_file()
    assert manifest["bundle_sha256"] == module.file_sha256(bundle_path)

    with zipfile.ZipFile(bundle_path) as archive:
        names = set(archive.namelist())
        assert "SUBMISSION_BUNDLE_MANIFEST.json" in names
        assert "docs/submission/registration-fields.md" in names
        assert "docs/submission/business-plan.md" in names
        assert "docs/submission/finals-foundation-roadmap.md" in names
        assert "docs/submission/finals-hmi-console.html" in names
        assert "docs/submission/final-human-action-runbook.md" in names
        assert "docs/finals-validation-report.md" in names
        assert "docs/finals-latency-benchmark-report.md" in names
        assert "docs/finals-local-gateway-latency-benchmark-report.md" in names
        assert "docs/submission/evidence/finals-latency-benchmark.json" in names
        assert "docs/submission/evidence/finals-local-gateway-latency-benchmark.json" in names
        assert "evals/finals_validation_dataset.jsonl" in names
        assert "openapi/wearedge-xcelerator-apiworld.openapi.json" in names
        assert "scripts/run_finals_validation.py" in names
        assert "scripts/benchmark_workflow_canvas_latency.py" in names
        assert "scripts/benchmark_local_gateway_latency.py" in names
        assert "scripts/verify_finals_foundation.py" in names
        assert "wfc-blocks/wearedge-agent-service/info.json" in names
        assert "scripts/run_final_readiness_pipeline.py" in names
        assert "generated/wfc-resource-package/wearedge-agent-service-0.1.0.zip" in names
        assert not any(name.startswith("submission-assets/live-evidence/legal/") for name in names)
        saved_manifest = json.loads(archive.read("SUBMISSION_BUNDLE_MANIFEST.json").decode("utf-8"))

    assert saved_manifest["bundle_sha256"] is None
    assert "submission-assets/live-evidence/legal/company-info-filled.md" in manifest["excluded_external_items"]


def test_build_final_submission_bundle_dry_run_does_not_write_files(tmp_path: Path) -> None:
    module = _load_module()

    manifest = module.build_final_submission_bundle(output_dir=tmp_path, dry_run=True)

    assert manifest["ok"] is True
    assert manifest["dry_run"] is True
    assert manifest["bundle_sha256"] is None
    assert not Path(manifest["bundle_path"]).exists()
    assert list(tmp_path.rglob("*")) == []


def test_bundle_secret_scan_detects_assignment_like_secret(tmp_path: Path) -> None:
    module = _load_module()
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("password = real-secret-value\n", encoding="utf-8")
    item = module.BundleFile(
        source=secret_file,
        archive_name="secret.txt",
        size=secret_file.stat().st_size,
        sha256=module.file_sha256(secret_file),
    )

    findings = module.detect_secret_findings([item])

    assert findings
    assert "secret.txt" in findings[0]
