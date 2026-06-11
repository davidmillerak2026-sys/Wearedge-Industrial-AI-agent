from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jetson.app import app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the Wearedge industrial-agent solution profile.")
    parser.add_argument(
        "--url",
        default=None,
        help="Optional live endpoint URL, e.g. http://127.0.0.1:8081/v1/industrial-agent/solution-profile",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON response.")
    args = parser.parse_args(argv)

    profile = fetch_profile(args.url)
    failures = validate_profile(profile)
    if args.json:
        print(json.dumps(profile, ensure_ascii=False, indent=2))
    else:
        model_runtime = _object(profile.get("model_runtime"))
        decision = _object(profile.get("decision_mechanism"))
        problem = _object(profile.get("industrial_problem"))
        print(f"ok={profile.get('ok')}")
        print(f"solution_name={profile.get('solution_name')}")
        print(f"problem={problem.get('name')}")
        print(f"primary_model={model_runtime.get('primary_model')}")
        print(f"model_variant={model_runtime.get('model_variant')}")
        print(f"decision_type={decision.get('type')}")
        print(f"model_dependency={decision.get('model_dependency')}")
    if failures:
        for failure in failures:
            print(f"failure={failure}")
        return 1
    return 0


def fetch_profile(url: str | None) -> dict[str, object]:
    if url:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    else:
        client = TestClient(app)
        response = client.get("/v1/industrial-agent/solution-profile")
        response.raise_for_status()
        data = response.json()
    return data if isinstance(data, dict) else {}


def validate_profile(profile: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if profile.get("ok") is not True:
        failures.append("profile ok is not true")
    problem = _object(profile.get("industrial_problem"))
    model_runtime = _object(profile.get("model_runtime"))
    decision = _object(profile.get("decision_mechanism"))
    platform = _object(profile.get("platform_integration"))
    if "cross-domain" not in str(problem.get("name", "")):
        failures.append("industrial problem is not explicit")
    if not model_runtime.get("primary_model"):
        failures.append("primary model missing")
    if decision.get("model_dependency") != "not required for /v1/workflow-canvas/decision":
        failures.append("decision model dependency boundary is unclear")
    matrix = _object(decision.get("key_metrics_matrix"))
    for direction in ("maintenance", "quality", "energy", "flexible_production", "workflow_canvas"):
        if direction not in matrix:
            failures.append(f"missing decision metric direction: {direction}")
    if "gongyi_mofang" not in platform:
        failures.append("missing Gongyi Mofang platform integration")
    return failures


def _object(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
