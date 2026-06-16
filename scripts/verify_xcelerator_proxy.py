from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAYLOAD = REPO_ROOT / "workflows" / "wearedge_wfc_poc_payload.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "submission-assets" / "live-evidence" / "xcelerator"
DEFAULT_PROXY_BASE_URL = "https://apig.developers.siemens-x.com.cn/scps4pw78kj6B2PFEmZX"


def normalize_base_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Xcelerator proxy URL must be an https URL with a host")
    return value.strip().rstrip("/")


def load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def call_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                parsed: Any = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"raw": raw[:800]}
            return {"ok": True, "status": response.status, "json": parsed}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw": raw[:800]}
        return {"ok": False, "status": exc.code, "json": parsed, "error": raw[:800]}
    except Exception as exc:
        return {"ok": False, "status": None, "json": None, "error": str(exc)}


def classify_platform_response(result: dict[str, Any]) -> list[str]:
    payload = result.get("json")
    if not isinstance(payload, dict):
        return ["response is not JSON"]
    if payload.get("ok") is True:
        return []
    if payload.get("code") == -107:
        return [
            "Xcelerator proxy returned code -107: selector configuration is missing or not bound to the imported API path"
        ]
    if "code" in payload or "msg" in payload:
        return [f"Xcelerator proxy returned platform response: code={payload.get('code')} msg={payload.get('msg')}"]
    return ["response JSON does not contain Wearedge ok=true"]


def verify(proxy_base_url: str, payload_path: Path, skip_decision: bool = False) -> dict[str, Any]:
    proxy_base_url = normalize_base_url(proxy_base_url)
    payload = load_payload(payload_path)
    checks: dict[str, dict[str, Any]] = {
        "runtime_profile": call_json("GET", f"{proxy_base_url}/v1/edge/runtime-profile"),
        "healthz": call_json("GET", f"{proxy_base_url}/v1/healthz"),
    }
    if not skip_decision:
        checks["workflow_canvas_decision"] = call_json(
            "POST",
            f"{proxy_base_url}/v1/workflow-canvas/decision",
            payload=payload,
        )

    failures: list[str] = []
    for name, result in checks.items():
        result["path"] = {
            "runtime_profile": "/v1/edge/runtime-profile",
            "healthz": "/v1/healthz",
            "workflow_canvas_decision": "/v1/workflow-canvas/decision",
        }[name]
        if result.get("status") != 200:
            failures.append(f"{name}: HTTP status {result.get('status')}")
        failures.extend(f"{name}: {failure}" for failure in classify_platform_response(result))

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "proxy_base_url": proxy_base_url,
        "ready": not failures,
        "failures": failures,
        "checks": checks,
        "interpretation": (
            "ready=True means the tenant/internal Xcelerator proxy is forwarding to the Wearedge API. "
            "ready=False with code -107 means the backend may be filled, but API selector/path binding still needs platform configuration."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Xcelerator Proxy Verification",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Proxy base URL: `{result['proxy_base_url']}`",
        f"- Ready: {result['ready']}",
        "",
        "## Checks",
        "",
        "| Check | Path | HTTP Status | Payload signal |",
        "| --- | --- | ---: | --- |",
    ]
    for name, check in result["checks"].items():
        payload = check.get("json")
        if isinstance(payload, dict) and payload.get("ok") is True:
            signal = "Wearedge ok=true"
        elif isinstance(payload, dict) and "code" in payload:
            signal = f"platform code={payload.get('code')} msg={payload.get('msg')}"
        else:
            signal = str(check.get("error") or "unknown")[:120]
        lines.append(f"| {name} | `{check.get('path', '')}` | {check.get('status')} | {signal} |")
    lines += ["", "## Failures", ""]
    lines += [f"- {failure}" for failure in result["failures"]] or ["- None"]
    lines += ["", "## Interpretation", "", result["interpretation"], ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the tenant/internal Xcelerator proxy for Wearedge.")
    parser.add_argument("--proxy-base-url", default=DEFAULT_PROXY_BASE_URL)
    parser.add_argument("--payload", type=Path, default=DEFAULT_PAYLOAD)
    parser.add_argument("--skip-decision", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = verify(args.proxy_base_url, args.payload, skip_decision=args.skip_decision)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.write_evidence:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "xcelerator-proxy-verification.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (args.output_dir / "xcelerator-proxy-verification.md").write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_report(result))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
