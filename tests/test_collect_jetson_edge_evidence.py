from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "collect_jetson_edge_evidence.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("collect_jetson_edge_evidence", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_benchmark_command_marks_final_edge_without_secret() -> None:
    module = _load_module()

    command = module.build_benchmark_command(
        remote_dir="/home/ryn/Wearedge-Industrial-AI-agent",
        iterations=20,
        python_candidates=("/home/ryn/WearEdge-Pro/.venv/bin/python", "python3"),
    )

    assert "--final-edge-node" in command
    assert "--iterations 20" in command
    assert "tegrastats" in command
    assert "JETSON_SSH_PASSWORD" not in command
    assert "password" not in command.lower()


def test_archive_exclusion_rules_keep_secrets_and_generated_media_out() -> None:
    module = _load_module()

    assert module.should_exclude(REPO_ROOT / ".env") is True
    assert module.should_exclude(REPO_ROOT / ".codex-tmp" / "pydeps" / "paramiko.py") is True
    assert module.should_exclude(REPO_ROOT / "submission-assets" / "live-evidence" / "x.png") is True
    assert module.should_exclude(REPO_ROOT / "renders" / "demo.mp4") is True
    assert module.should_exclude(REPO_ROOT / "scripts" / "collect_jetson_edge_evidence.py") is False


def test_remote_dir_validation_protects_existing_wearedge_project() -> None:
    module = _load_module()

    module.validate_remote_dir("/home/ryn/Wearedge-Industrial-AI-agent-competition")

    try:
        module.validate_remote_dir("/home/ryn/WearEdge-Pro")
    except ValueError as exc:
        assert "protected remote directory" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected protected WearEdge-Pro directory to be rejected")
