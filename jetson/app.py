from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import Body, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from .agent_loop import SUPPORTED_AGENT_MODES, resolve_agent_mode
from .agent_profiles import AGENT_PROFILES
from .agently_orchestrator import export_m400_flow_definition, run_m400_agently_workflow
from .audit_log import append_jsonl, read_recent_jsonl
from .config import GatewayConfig
from .competition import COMPETITION_DECISION_VERSION, COMPETITION_TARGETS, build_competition_decision
from .device_context import build_device_context
from .llama_client import LlamaServerError, build_multimodal_payload, post_chat_completion
from .maintenance_session import (
    ALLOWED_EVIDENCE_STATUSES,
    build_workflow_session_context,
    ensure_maintenance_mode,
    maintenance_session_store,
)
from .solution_profile import RuntimeProfileInput, build_solution_profile


API_VERSION = "wear-edge-infer.v1"
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ANALYSIS_MODES = SUPPORTED_AGENT_MODES

app = FastAPI(title="WearEdge Pro Gemma 4 E2B Gateway", version="0.1.0")
config = GatewayConfig.from_env()
logger = logging.getLogger("wearedge.gateway")


@app.get("/", response_class=HTMLResponse)
def demo_page() -> str:
    return _DEMO_HTML


@app.get("/healthz")
@app.get("/v1/healthz")
def healthz() -> dict[str, object]:
    return {
        "ok": True,
        "llama_base_url": config.llama_base_url,
        "model": config.model,
        "api_version": API_VERSION,
        "auth_enabled": config.auth_enabled,
        "upload_persistence": bool(config.upload_dir),
        "observability": {
            "event_log_enabled": config.event_log_path is not None,
        },
        "modality": {
            "current_visual_token_budget": {
                "min_tokens": config.llama_image_min_tokens,
                "max_tokens": config.llama_image_max_tokens,
            },
            "audio_fusion_runtime": config.audio_fusion_runtime,
            "model_variant": config.model_variant,
        },
        "agently": {
            "flow_definition": export_m400_flow_definition(),
        },
        "competition": {
            "decision_version": COMPETITION_DECISION_VERSION,
            "workflow_canvas_endpoint": "/v1/workflow-canvas/decision",
            "competition_endpoint": "/v1/competition/decision",
            "targets": COMPETITION_TARGETS,
        },
        "xcelerator": {
            "x_auth_enabled": config.xcelerator_x_auth_enabled,
            "x_token_header": "X-TOKEN",
            "sign_check_configured": bool(config.xcelerator_app_key),
        },
        "output_contract": {
            "min_words": config.contract_min_words,
            "repair_enabled": config.contract_repair_enabled,
            "analysis_modes": sorted(ANALYSIS_MODES),
            "agent_profiles": {
                mode: {
                    "display_name": profile.display_name,
                    "purpose": profile.purpose,
                    "aliases": list(profile.aliases),
                }
                for mode, profile in AGENT_PROFILES.items()
            },
        },
    }


@app.get("/v1/audit/recent")
def recent_audit_events(
    limit: int = 10,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_token(authorization)
    safe_limit = min(max(limit, 1), 100)
    if config.event_log_path is None:
        return {
            "ok": True,
            "enabled": False,
            "limit": safe_limit,
            "events": [],
        }

    try:
        events = read_recent_jsonl(config.event_log_path, limit=safe_limit)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="failed to read audit event log") from exc
    return {
        "ok": True,
        "enabled": True,
        "limit": safe_limit,
        "events": events,
    }


@app.get("/v1/agent-flow")
def agent_flow_definition(authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require_token(authorization)
    return {
        "ok": True,
        "api_version": API_VERSION,
        "flow_definition": export_m400_flow_definition(),
    }


@app.get("/v1/edge/runtime-profile")
def edge_runtime_profile() -> dict[str, object]:
    return _build_edge_runtime_profile()


@app.get("/v1/industrial-agent/solution-profile")
def industrial_agent_solution_profile() -> dict[str, object]:
    return build_solution_profile(
        RuntimeProfileInput(
            model=config.model,
            model_variant=config.model_variant,
            llama_base_url=config.llama_base_url,
            deployment_mode=config.deployment_mode,
            edge_node_id=config.edge_node_id,
        )
    )


@app.post("/v1/workflow-canvas/decision")
def workflow_canvas_decision(
    payload: dict[str, object] | None = Body(default=None),
    authorization: str | None = Header(default=None),
    x_token: str | None = Header(default=None, alias="X-TOKEN"),
) -> dict[str, object]:
    _require_token(authorization, x_token=x_token)
    return build_competition_decision(payload or {})


@app.post("/v1/competition/decision")
def competition_decision(
    payload: dict[str, object] | None = Body(default=None),
    authorization: str | None = Header(default=None),
    x_token: str | None = Header(default=None, alias="X-TOKEN"),
) -> dict[str, object]:
    return workflow_canvas_decision(payload=payload, authorization=authorization, x_token=x_token)


@app.get("/v1/agent-runs/recent")
def recent_agent_runs(
    limit: int = 10,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_token(authorization)
    safe_limit = min(max(limit, 1), 100)
    if config.event_log_path is None:
        return {
            "ok": True,
            "enabled": False,
            "limit": safe_limit,
            "runs": [],
        }

    try:
        events = read_recent_jsonl(config.event_log_path, limit=safe_limit)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="failed to read agent run log") from exc

    runs = [_agent_run_summary(event) for event in events if event.get("event_type") == "inference.completed"]
    return {
        "ok": True,
        "enabled": True,
        "limit": safe_limit,
        "runs": runs,
    }


@app.post("/v1/maintenance-sessions")
async def create_maintenance_session(
    device_id: str | None = Form(default=None),
    frame_ts: str | None = Form(default=None),
    location_hint: str | None = Form(default=None),
    capture_mode: str | None = Form(default="maintenance-session"),
    operator_id: str | None = Form(default=None),
    initial_prompt: str | None = Form(default=None),
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_token(authorization)
    device_context = build_device_context(
        device_id=device_id,
        frame_ts=frame_ts,
        location_hint=location_hint,
        capture_mode=capture_mode,
    )
    device_response = device_context.as_response()
    session = maintenance_session_store.create_session(
        device=dict(device_response["device"]),
        location_hint=location_hint,
        operator_id=operator_id,
        initial_prompt=initial_prompt,
    )
    return {
        "ok": True,
        "api_version": API_VERSION,
        **device_response,
        "maintenance_session": session.as_dict(),
    }


@app.post("/v1/maintenance-sessions/{session_id}/evidence")
async def add_maintenance_session_evidence(
    session_id: str,
    evidence_type: str = Form(...),
    capture_type: str = Form(default="photo"),
    status: str | None = Form(default=None),
    summary: str | None = Form(default=None),
    source: str = Form(default="m400"),
    fields_json: str | None = Form(default=None),
    request_id: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_token(authorization)
    raw: bytes | None = None
    content_type: str | None = None
    saved_path: Path | None = None
    if image is not None:
        content_type = _normalize_content_type(image.content_type)
        raw = await image.read()
        if not raw:
            raise HTTPException(status_code=400, detail="empty image")
        max_bytes = config.max_image_mb * 1024 * 1024
        if len(raw) > max_bytes:
            raise HTTPException(status_code=413, detail=f"image exceeds {config.max_image_mb} MB")
        saved_path = _persist_upload(raw, image.filename or "maintenance-evidence.jpg") if config.upload_dir else None

    try:
        fields = _parse_fields_json(fields_json)
        evidence = maintenance_session_store.add_evidence(
            session_id,
            evidence_type=evidence_type,
            capture_type=capture_type,
            status=status,
            summary=summary,
            source=source,
            fields=fields,
            image_bytes=len(raw) if raw is not None else None,
            image_content_type=content_type,
            request_id=request_id,
        )
        session = maintenance_session_store.require_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="maintenance session not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "ok": True,
        "api_version": API_VERSION,
        "accepted_statuses": sorted(ALLOWED_EVIDENCE_STATUSES),
        "evidence": evidence.as_dict(),
        "saved_path": str(saved_path) if saved_path else None,
        "maintenance_session": session.as_dict(),
    }


@app.post("/v1/maintenance-sessions/{session_id}/infer")
async def infer_maintenance_session(
    session_id: str,
    prompt: str = Form(...),
    image: UploadFile = File(...),
    device_id: str | None = Form(default=None),
    frame_ts: str | None = Form(default=None),
    location_hint: str | None = Form(default=None),
    capture_mode: str | None = Form(default="maintenance-session-infer"),
    needs_ocr: bool = Form(default=True),
    high_detail: bool = Form(default=True),
    audio_seconds: int = Form(default=0),
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_token(authorization)
    try:
        session = maintenance_session_store.require_session(session_id)
        ensure_maintenance_mode("maintenance")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="maintenance session not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response_body = await _execute_infer_request(
        prompt=prompt,
        image=image,
        device_id=device_id,
        frame_ts=frame_ts,
        location_hint=location_hint,
        capture_mode=capture_mode,
        analysis_mode="maintenance",
        needs_ocr=needs_ocr,
        high_detail=high_detail,
        audio_seconds=audio_seconds,
        session_context=build_workflow_session_context(session),
    )
    session = maintenance_session_store.record_inference(session_id, response_body)
    response_body["maintenance_session"] = session.as_dict()
    response_body["audit"]["logged"] = _append_audit_event(response_body)
    return response_body


@app.get("/v1/maintenance-sessions/{session_id}/trace")
def maintenance_session_trace(
    session_id: str,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_token(authorization)
    try:
        session = maintenance_session_store.require_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="maintenance session not found") from exc
    return {
        "ok": True,
        "api_version": API_VERSION,
        "maintenance_session": session.as_dict(),
        "trace": session.trace(),
    }


@app.post("/v1/infer")
async def infer(
    prompt: str = Form(...),
    image: UploadFile = File(...),
    device_id: str | None = Form(default=None),
    frame_ts: str | None = Form(default=None),
    location_hint: str | None = Form(default=None),
    capture_mode: str | None = Form(default=None),
    analysis_mode: str = Form(default="hazard"),
    needs_ocr: bool = Form(default=False),
    high_detail: bool = Form(default=False),
    audio_seconds: int = Form(default=0),
    detector_evidence_json: str | None = Form(default=None),
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_token(authorization)
    response_body = await _execute_infer_request(
        prompt=prompt,
        image=image,
        device_id=device_id,
        frame_ts=frame_ts,
        location_hint=location_hint,
        capture_mode=capture_mode,
        analysis_mode=analysis_mode,
        needs_ocr=needs_ocr,
        high_detail=high_detail,
        audio_seconds=audio_seconds,
        detector_evidence_json=detector_evidence_json,
    )
    response_body["audit"]["logged"] = _append_audit_event(response_body)
    return response_body


async def _execute_infer_request(
    *,
    prompt: str,
    image: UploadFile,
    device_id: str | None,
    frame_ts: str | None,
    location_hint: str | None,
    capture_mode: str | None,
    analysis_mode: str,
    needs_ocr: bool,
    high_detail: bool,
    audio_seconds: int,
    session_context: dict[str, object] | None = None,
    detector_evidence_json: str | None = None,
) -> dict[str, object]:
    mode = _normalize_analysis_mode(analysis_mode)
    detector_evidence = _parse_optional_json_object(detector_evidence_json, "detector_evidence_json")
    device_context = build_device_context(
        device_id=device_id,
        frame_ts=frame_ts,
        location_hint=location_hint,
        capture_mode=capture_mode,
    )
    content_type = _normalize_content_type(image.content_type)
    raw = await image.read()

    if not raw:
        raise HTTPException(status_code=400, detail="empty image")
    max_bytes = config.max_image_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail=f"image exceeds {config.max_image_mb} MB")
    saved_path = _persist_upload(raw, image.filename or "frame.jpg") if config.upload_dir else None
    try:
        device_response = device_context.as_response()
        workflow = run_m400_agently_workflow(
            prompt=prompt,
            mode=mode,
            image_bytes=len(raw),
            request_id=str(device_response["request_id"]),
            device=dict(device_response["device"]),
            contract_min_words=config.contract_min_words,
            contract_repair_enabled=config.contract_repair_enabled,
            current_image_min_tokens=config.llama_image_min_tokens,
            current_image_max_tokens=config.llama_image_max_tokens,
            audio_runtime=config.audio_fusion_runtime,
            model_variant=config.model_variant,
            audio_seconds=audio_seconds,
            needs_ocr=needs_ocr,
            high_detail=high_detail,
            infer_model=lambda contract_prompt: _run_multimodal_inference(
                prompt=contract_prompt,
                image_bytes=raw,
                image_content_type=content_type,
            ),
            session_context=session_context,
            detector_evidence=detector_evidence,
        )
    except LlamaServerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not workflow.contract.ok or workflow.structured is None:
        raise HTTPException(
            status_code=502,
            detail={
                "message": f"model output did not satisfy the {mode} output contract",
                "violations": workflow.contract.violations,
                "answer": workflow.answer,
                "agently_trace": workflow.agently_trace,
                "runtime_stream": workflow.runtime_stream,
            },
        )

    response_body = {
        "ok": True,
        "api_version": API_VERSION,
        "analysis_mode": mode,
        **device_response,
        "answer": workflow.structured.as_text(),
        **workflow.fields,
        "model": config.model,
        "latency_ms": workflow.latency_ms,
        "image_bytes": len(raw),
        "image_content_type": content_type,
        "modality_plan": workflow.modality_plan,
        "evidence_plan": workflow.evidence_plan,
        "tool_plan": workflow.tool_plan,
        "knowledge_base": workflow.knowledge_base,
        "detector_evidence": workflow.detector_evidence,
        "maintenance_evaluation": workflow.maintenance_evaluation,
        "quality_evaluation": workflow.quality_evaluation,
        "source_evaluation": workflow.source_evaluation,
        "follow_up_plan": workflow.follow_up_plan,
        "saved_path": str(saved_path) if saved_path else None,
        "contract": {
            "ok": True,
            "type": mode,
            "repaired": workflow.repaired,
            "min_words": config.contract_min_words,
            "violations": [],
        },
        "action_card": workflow.action_card.as_dict(),
        "integration_event": workflow.integration_event.as_dict(),
        "agent_loop": workflow.agent_loop,
        "agently_trace": workflow.agently_trace,
        "runtime_stream": workflow.runtime_stream,
        "audit": {
            "logged": False,
        },
    }
    return response_body


def _require_token(authorization: str | None, *, x_token: str | None = None) -> None:
    if not config.auth_enabled:
        return
    if config.xcelerator_x_auth_enabled:
        if x_token:
            if _verify_xcelerator_token(x_token):
                return
            raise HTTPException(status_code=401, detail="invalid Xcelerator X-TOKEN")
        if authorization is None and not config.demo_token:
            raise HTTPException(status_code=401, detail="missing X-TOKEN or Authorization header")
    if not config.demo_token:
        raise HTTPException(status_code=503, detail="DEMO_TOKEN is not configured")
    if authorization != f"Bearer {config.demo_token}":
        raise HTTPException(status_code=401, detail="unauthorized")


def _verify_xcelerator_token(x_token: str) -> bool:
    if not config.xcelerator_app_key:
        raise HTTPException(status_code=503, detail="WEAREDGE_XCELERATOR_APP_KEY is not configured")
    body = json.dumps({"X-TOKEN": x_token}).encode("utf-8")
    request = urllib.request.Request(
        config.xcelerator_sign_check_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "appKey": config.xcelerator_app_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.xcelerator_sign_check_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code in {400, 401, 403}:
            return False
        raise HTTPException(status_code=502, detail="Xcelerator sign check failed") from exc
    except OSError as exc:
        raise HTTPException(status_code=502, detail="Xcelerator sign check unavailable") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="Xcelerator sign check returned invalid JSON") from exc
    return isinstance(payload, dict) and payload.get("code") == 200


def _build_edge_runtime_profile() -> dict[str, object]:
    deployment_mode = str(config.deployment_mode or "local_server").strip().lower()
    if deployment_mode not in {"jetson", "ipc", "local_server", "cloud_proxy"}:
        deployment_mode = "local_server"
    return {
        "ok": True,
        "api_version": "wear-edge-edge-runtime-profile.v1",
        "edge_node": {
            "node_id": config.edge_node_id,
            "deployment_mode": deployment_mode,
            "supported_deployment_modes": ["jetson", "ipc", "local_server", "cloud_proxy"],
            "role": "edge_agent_runtime",
            "data_residency": "Production images, device context, audit logs, and local KB evidence can remain on the edge node.",
        },
        "runtime": {
            "model": config.model,
            "model_variant": config.model_variant,
            "llama_base_url": config.llama_base_url,
            "local_multimodal_inference": True,
            "workflow_decision_api": "/v1/workflow-canvas/decision",
            "wearable_infer_api": "/v1/infer",
            "health_api": "/healthz",
            "cloud_proxy_health_api": "/v1/healthz",
            "audit_log_enabled": config.event_log_path is not None,
            "upload_persistence_enabled": config.upload_dir is not None,
            "auth_enabled": config.auth_enabled,
        },
        "edge_capabilities": {
            "local_multimodal_inference": True,
            "m400_or_ar_first_person_capture": True,
            "industrial_rag": True,
            "deterministic_guards": True,
            "structured_action_cards": True,
            "privacy_preserving_audit": True,
            "offline_or_lan_operation": deployment_mode in {"jetson", "ipc", "local_server"},
            "workflow_canvas_ready": True,
            "xcelerator_api_world_ready": True,
        },
        "platform_integration": {
            "xcelerator": {
                "api_world_import_ready": True,
                "x_auth_enabled": config.xcelerator_x_auth_enabled,
                "x_token_header": "X-TOKEN",
            },
            "gongyi_mofang": {
                "resource_block": "Wearedge Agent Service",
                "python_function_block": "CallWearedgeDecisionApi",
                "data_table_update": "UpdateDashboardDataTable",
                "human_gate": "HumanApprovalGate",
            },
            "industrial_connectors": ["OPC UA", "MES", "QMS", "EMS", "CMMS", "MQTT", "S7"],
        },
        "safety_boundary": {
            "model_direct_ot_control": False,
            "high_risk_actions_require_human": True,
            "required_gate": "HumanApprovalGate",
            "policy": "The model explains evidence; deterministic guards and Workflow Canvas approval decide action boundaries.",
        },
        "competition_evidence": {
            "offline_eval_report": "docs/competition-offline-eval-report.md",
            "workflow_canvas_runbook": "docs/workflow-canvas-poc-runbook.md",
            "edge_runtime_doc": "docs/edge-agent-runtime-for-xcelerator.md",
            "wfc_block_package": "wfc-blocks/wearedge-agent-service/",
        },
    }


def _normalize_content_type(content_type: str | None) -> str:
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized == "image/jpg":
        normalized = "image/jpeg"
    if normalized not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="unsupported image type")
    return normalized


def _normalize_analysis_mode(value: str) -> str:
    try:
        return resolve_agent_mode(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"unsupported analysis_mode: {value}") from exc


def _parse_fields_json(value: str | None) -> dict[str, object]:
    if value is None or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("fields_json must be a JSON object") from exc
    if not isinstance(parsed, dict):
        raise ValueError("fields_json must be a JSON object")
    return parsed


def _parse_optional_json_object(value: str | None, field_name: str) -> dict[str, object] | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"{field_name} must be a JSON object") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail=f"{field_name} must be a JSON object")
    return parsed


def _persist_upload(raw: bytes, filename: str) -> Path:
    assert config.upload_dir is not None
    config.upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png"}:
        suffix = ".jpg"
    path = config.upload_dir / f"{int(time.time() * 1000)}{suffix}"
    path.write_bytes(raw)
    return path


def _run_multimodal_inference(
    *,
    prompt: str,
    image_bytes: bytes,
    image_content_type: str,
):
    payload = build_multimodal_payload(
        prompt=prompt,
        image_bytes=image_bytes,
        image_content_type=image_content_type,
        model=config.model,
        enable_thinking=config.enable_thinking,
        max_tokens=max(config.max_tokens, 260),
        temperature=config.temperature,
    )
    return post_chat_completion(
        base_url=config.llama_base_url,
        payload=payload,
        timeout_seconds=config.timeout_seconds,
    )


def _append_audit_event(response_body: dict[str, object]) -> bool:
    if config.event_log_path is None:
        return False

    event = {
        "event_type": "inference.completed",
        "api_version": response_body["api_version"],
        "analysis_mode": response_body["analysis_mode"],
        "request_id": response_body["request_id"],
        "received_at": response_body["received_at"],
        "device": response_body["device"],
        "model": response_body["model"],
        "latency_ms": response_body["latency_ms"],
        "image_bytes": response_body["image_bytes"],
        "image_content_type": response_body["image_content_type"],
        "modality_plan": response_body["modality_plan"],
        "evidence_plan": response_body["evidence_plan"],
        "tool_plan": response_body["tool_plan"],
        "knowledge_base": response_body.get("knowledge_base"),
        "maintenance_evaluation": response_body.get("maintenance_evaluation"),
        "follow_up_plan": response_body["follow_up_plan"],
        "saved_path": response_body["saved_path"],
        "scene": response_body.get("scene"),
        "risk": response_body.get("risk"),
        "product": response_body.get("product"),
        "quality_risk": response_body.get("quality_risk"),
        "disposition": response_body.get("disposition"),
        "machine": response_body.get("machine"),
        "symptom": response_body.get("symptom"),
        "maintenance_risk": response_body.get("maintenance_risk"),
        "evidence_needed": response_body.get("evidence_needed"),
        "work_instruction": response_body.get("work_instruction"),
        "risk_control": response_body.get("risk_control"),
        "sku": response_body.get("sku"),
        "changeover_step": response_body.get("changeover_step"),
        "asset": response_body.get("asset"),
        "energy_signal": response_body.get("energy_signal"),
        "optimization": response_body.get("optimization"),
        "verification": response_body.get("verification"),
        "action": response_body["action"],
        "contract": response_body["contract"],
        "action_card": response_body["action_card"],
        "integration_event": response_body["integration_event"],
        "agent_loop": response_body["agent_loop"],
        "agently_trace": response_body["agently_trace"],
        "runtime_stream": response_body["runtime_stream"],
    }
    maintenance_session = response_body.get("maintenance_session")
    if maintenance_session is not None:
        event["maintenance_session"] = maintenance_session
    try:
        append_jsonl(config.event_log_path, event)
    except OSError:
        logger.exception("failed to append inference audit event")
        return False
    return True


def _agent_run_summary(event: dict[str, object]) -> dict[str, object]:
    runtime_stream = event.get("runtime_stream")
    stream_events = runtime_stream.get("events", []) if isinstance(runtime_stream, dict) else []
    last_event = stream_events[-1] if stream_events else None
    action_card = event.get("action_card")
    return {
        "request_id": event.get("request_id"),
        "analysis_mode": event.get("analysis_mode"),
        "received_at": event.get("received_at"),
        "runtime_stream": runtime_stream,
        "last_event": last_event,
        "action_card": action_card if isinstance(action_card, dict) else None,
        "follow_up_plan": event.get("follow_up_plan"),
        "integration_event": event.get("integration_event"),
    }


_DEMO_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WearEdge Pro E2B Demo</title>
  <style>
    :root { color-scheme: light dark; font-family: system-ui, sans-serif; }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #101820; color: #f6f7f8; }
    main { width: min(760px, calc(100vw - 32px)); display: grid; gap: 16px; }
    form { display: grid; gap: 12px; padding: 20px; border: 1px solid #344552; border-radius: 8px; background: #162430; }
    label { display: grid; gap: 6px; font-size: 14px; color: #c8d2dc; }
    input, textarea, button { font: inherit; border-radius: 6px; border: 1px solid #526575; padding: 10px; }
    textarea { min-height: 92px; resize: vertical; }
    button { cursor: pointer; background: #58c7a5; color: #06120e; border: 0; font-weight: 700; }
    pre { white-space: pre-wrap; word-break: break-word; min-height: 140px; padding: 16px; border-radius: 8px; background: #0b1218; }
  </style>
</head>
<body>
  <main>
    <h1>WearEdge Pro E2B Demo</h1>
    <form id="infer-form">
      <label>Token <input id="token" name="token" type="password" autocomplete="off"></label>
      <label>Mode
        <select id="analysis_mode" name="analysis_mode">
          <option value="hazard">Hazard Exposure</option>
          <option value="maintenance">Lao-shi-fu Maintenance</option>
          <option value="iqc">IQC Quality</option>
          <option value="energy">Energy Management</option>
          <option value="wi">WI Guidance</option>
          <option value="changeover">Changeover</option>
        </select>
      </label>
      <label>Prompt <textarea id="prompt" name="prompt">Return exactly this format and nothing else:
- Scene: &lt;detailed visible area description with at least sixteen words&gt;
- Risk: &lt;specific hazard exposure description with at least sixteen words&gt;
- Action: &lt;one safe next action for the operator with at least sixteen words&gt;

Rules:
Scene must describe the visible place, people, equipment, obstruction, or work area using a complete sentence.
Risk must name a hazard and explain who or what could be exposed.
Action must start with Stop, Inspect, Wear, Keep, or Report.
Each line must be more than 15 words.
Do not add any introduction.</textarea></label>
      <label>Image <input id="image" name="image" type="file" accept="image/jpeg,image/png" required></label>
      <button type="submit">Run Inference</button>
    </form>
    <pre id="result">Ready.</pre>
  </main>
  <script>
    const form = document.querySelector("#infer-form");
    const result = document.querySelector("#result");
    const promptInput = document.querySelector("#prompt");
    const modeInput = document.querySelector("#analysis_mode");
    const safetyPrompt = `Return exactly this format and nothing else:
- Scene: <detailed visible area description with at least sixteen words>
- Risk: <specific hazard exposure description with at least sixteen words>
- Action: <one safe next action for the operator with at least sixteen words>

Rules:
Scene must describe the visible place, people, equipment, obstruction, or work area using a complete sentence.
Risk must name a hazard and explain who or what could be exposed.
Action must start with Stop, Inspect, Wear, Keep, or Report.
Each line must be more than 15 words.
Do not add any introduction.`;
    const iqcPrompt = `Assess this in-process product image for visible quality risk and containment need.
Use process-quality language suitable for a line-side operator and quality engineer.
Do not make final release, scrap, or customer disposition decisions without quality authority.`;
    const maintenancePrompt = `Identify the visible machine and maintenance symptoms, then give bounded predictive-maintenance guidance.
Separate visible evidence from inferred risk and name the manual, signal, log, or inspection evidence needed next.`;
    const energyPrompt = `Assess the visible or provided production load for energy management opportunity.
Separate measured energy evidence from inferred idle or peak behavior and require baseline verification before any control action.`;
    const wiPrompt = `Identify the visible machine and answer the operator question with work-instruction guidance.
Use only visible machine context and keep hidden parameters or unsafe steps as escalation items.`;
    const changeoverPrompt = `Identify the visible machine and SKU context, then guide the next controlled changeover step.
Do not invent target SKU, tooling, recipe parameters, or first-piece approval authority.`;
    modeInput.addEventListener("change", () => {
      const prompts = { hazard: safetyPrompt, maintenance: maintenancePrompt, iqc: iqcPrompt, energy: energyPrompt, wi: wiPrompt, changeover: changeoverPrompt };
      promptInput.value = prompts[modeInput.value] || safetyPrompt;
    });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      result.textContent = "Running...";
      const data = new FormData();
      data.append("prompt", promptInput.value);
      data.append("image", document.querySelector("#image").files[0]);
      data.append("device_id", "web-demo");
      data.append("capture_mode", "browser-upload");
      data.append("analysis_mode", modeInput.value);
      const response = await fetch("/v1/infer", {
        method: "POST",
        headers: { "Authorization": `Bearer ${document.querySelector("#token").value}` },
        body: data
      });
      const body = await response.json();
      if (body.audit && body.audit.logged) {
        const auditResponse = await fetch("/v1/audit/recent?limit=1", {
          headers: { "Authorization": `Bearer ${document.querySelector("#token").value}` }
        });
        body.recent_audit = await auditResponse.json();
      }
      result.textContent = JSON.stringify(body, null, 2);
    });
  </script>
</body>
</html>
"""
