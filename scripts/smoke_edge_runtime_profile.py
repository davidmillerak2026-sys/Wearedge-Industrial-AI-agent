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
    parser = argparse.ArgumentParser(description="Smoke-test the Wearedge edge runtime profile endpoint.")
    parser.add_argument("--url", default=None, help="Optional live endpoint URL, e.g. http://127.0.0.1:8081/v1/edge/runtime-profile")
    parser.add_argument("--json", action="store_true", help="Print full JSON response.")
    args = parser.parse_args(argv)

    profile = _fetch_profile(args.url)
    failures = _validate_profile(profile)
    if args.json:
        print(json.dumps(profile, ensure_ascii=False, indent=2))
    else:
        edge_node = _object(profile.get("edge_node"))
        capabilities = _object(profile.get("edge_capabilities"))
        safety = _object(profile.get("safety_boundary"))
        print(f"ok={profile.get('ok')}")
        print(f"deployment_mode={edge_node.get('deployment_mode')}")
        print(f"local_multimodal_inference={capabilities.get('local_multimodal_inference')}")
        print(f"workflow_canvas_ready={capabilities.get('workflow_canvas_ready')}")
        print(f"model_direct_ot_control={safety.get('model_direct_ot_control')}")
    if failures:
        for failure in failures:
            print(f"failure={failure}")
        return 1
    return 0


def _fetch_profile(url: str | None) -> dict[str, object]:
    if url:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    else:
        client = TestClient(app)
        response = client.get("/v1/edge/runtime-profile")
        response.raise_for_status()
        data = response.json()
    return data if isinstance(data, dict) else {}


def _validate_profile(profile: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if profile.get("ok") is not True:
        failures.append("profile ok is not true")
    capabilities = _object(profile.get("edge_capabilities"))
    platform = _object(profile.get("platform_integration"))
    safety = _object(profile.get("safety_boundary"))
    if capabilities.get("local_multimodal_inference") is not True:
        failures.append("local multimodal inference not marked ready")
    if capabilities.get("workflow_canvas_ready") is not True:
        failures.append("Workflow Canvas readiness not marked true")
    if "gongyi_mofang" not in platform:
        failures.append("missing Gongyi Mofang integration profile")
    if safety.get("model_direct_ot_control") is not False:
        failures.append("model direct OT control boundary is not false")
    return failures


def _object(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
