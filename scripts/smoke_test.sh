#!/usr/bin/env bash
set -Eeuo pipefail

GATEWAY_BASE="${GATEWAY_BASE:-http://127.0.0.1:8081}"
LLAMA_BASE="${LLAMA_BASE:-http://127.0.0.1:8080}"
DEVICE_ID="${DEVICE_ID:-m400-smoke-test}"
FRAME_TS="${FRAME_TS:-}"
LOCATION_HINT="${LOCATION_HINT:-}"
CAPTURE_MODE="${CAPTURE_MODE:-manual-smoke-test}"
ANALYSIS_MODE="${ANALYSIS_MODE:-hazard}"
case "$ANALYSIS_MODE" in
  safety|hazard-exposure|hazard_exposure|ehs|risk|safety_agent) ANALYSIS_MODE="hazard" ;;
  lao_shi_fu|laos_shi_fu|predictive_maintenance|pm|maintenance_agent) ANALYSIS_MODE="maintenance" ;;
  quality|inspection|quality_inspection|product_quality|iqc_agent) ANALYSIS_MODE="iqc" ;;
  work_instruction|work_instructions|instruction|general_wi|wi_agent) ANALYSIS_MODE="wi" ;;
  sku_changeover|model_changeover|turnover|changeover_agent) ANALYSIS_MODE="changeover" ;;
esac
export DEVICE_ID
export CAPTURE_MODE
export ANALYSIS_MODE
if [[ -z "${CONTRACT_PROMPT:-}" ]]; then
  case "$ANALYSIS_MODE" in
    maintenance)
      CONTRACT_PROMPT="Identify the visible machine and maintenance symptoms, then give bounded predictive-maintenance guidance."
      ;;
    iqc)
      CONTRACT_PROMPT="Assess this in-process product image for visible quality risk and containment need."
      ;;
    wi)
      CONTRACT_PROMPT="Identify the visible machine and answer the operator question with work-instruction guidance."
      ;;
    changeover)
      CONTRACT_PROMPT="Identify the visible machine and SKU context, then guide the next controlled changeover step."
      ;;
    *)
      CONTRACT_PROMPT="Return exactly this format and nothing else:
- Scene: <detailed visible area description with at least sixteen words>
- Risk: <specific hazard exposure description with at least sixteen words>
- Action: <one safe next action for the operator with at least sixteen words>

Rules:
Scene must describe the visible place, people, equipment, obstruction, or work area using a complete sentence.
Risk must name a hazard and explain who or what could be exposed.
Action must start with Stop, Inspect, Wear, Keep, or Report.
Each line must be more than 15 words.
Do not add any introduction."
      ;;
  esac
fi

echo "[1/3] Gateway health"
curl -fsS "$GATEWAY_BASE/healthz" | jq .

echo "[2/3] llama-server text health"
curl -fsS "$LLAMA_BASE/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma4",
    "messages": [{"role": "user", "content": "Return one short health check sentence."}],
    "chat_template_kwargs": {"enable_thinking": false},
    "max_tokens": 48,
    "temperature": 0.0
  }' \
  | tee /tmp/wearedge-llama-health.json \
  | jq .

jq -e '
  (.choices[0].message.content | type == "string" and length > 0)
' /tmp/wearedge-llama-health.json >/dev/null

echo "llama-server text health passed."

if [[ -n "${TEST_IMAGE:-}" ]]; then
  if [[ -z "${DEMO_TOKEN:-}" ]]; then
    echo "Set DEMO_TOKEN before running the image upload smoke test." >&2
    exit 1
  fi
  echo "[3/3] Gateway image upload"
  curl -fsS "$GATEWAY_BASE/v1/infer" \
    -H "Authorization: Bearer $DEMO_TOKEN" \
    -F "prompt=$CONTRACT_PROMPT" \
    -F "device_id=$DEVICE_ID" \
    -F "frame_ts=$FRAME_TS" \
    -F "location_hint=$LOCATION_HINT" \
    -F "capture_mode=$CAPTURE_MODE" \
    -F "analysis_mode=$ANALYSIS_MODE" \
    -F "image=@$TEST_IMAGE;type=image/jpeg" \
    | tee /tmp/wearedge-smoke-response.json \
    | jq .

  jq -e '
    .request_id as $request_id
    | .ok == true
    and (.action | type == "string" and length > 0)
    and (.request_id | type == "string" and length > 0)
    and .api_version == "wear-edge-infer.v1"
    and .analysis_mode == env.ANALYSIS_MODE
    and .device.device_id == env.DEVICE_ID
    and .device.capture_mode == env.CAPTURE_MODE
    and (.audit.logged | type == "boolean")
    and .contract.ok == true
    and (.contract.violations | length == 0)
    and .agent_loop.version == "wear-edge-agent-loop.v1"
    and .agent_loop.mode == env.ANALYSIS_MODE
    and (.agent_loop.validation_attempts | type == "number" and . >= 1)
    and (.agent_loop.decision.channel | type == "string" and length > 0)
    and (.agent_loop.decision.owner | type == "string" and length > 0)
    and (.agent_loop.decision.requires_human | type == "boolean")
    and (.agent_loop.stages | type == "array" and length >= 7)
    and .action_card.version == "wear-edge-action-card.v1"
    and .action_card.mode == env.ANALYSIS_MODE
    and (.action_card.title | type == "string" and length > 0)
    and (.action_card.priority as $priority | ["critical", "high", "medium", "low"] | index($priority) != null)
    and (.action_card.integration_target | type == "string" and length > 0)
    and (.action_card.required_confirmations | type == "array" and length > 0)
    and .follow_up_plan.version == "wear-edge-follow-up-plan.v1"
    and .follow_up_plan.mode == env.ANALYSIS_MODE
    and (.follow_up_plan.status | type == "string" and length > 0)
    and (.follow_up_plan.requests | type == "array")
    and .integration_event.version == "wear-edge-integration-event.v1"
    and (.integration_event.event_type | type == "string" and length > 0)
    and .integration_event.target == .action_card.integration_target
    and (.integration_event.status | type == "string" and length > 0)
    and (.integration_event.idempotency_key | type == "string" and contains($request_id))
    and .integration_event.payload.request_id == $request_id
    and .integration_event.payload.action_card.channel == .action_card.channel
    and .integration_event.payload.follow_up_plan.status == .follow_up_plan.status
    and (.modality_plan.visual_token_budget.recommended.max_tokens | type == "number")
    and (.modality_plan.visual_token_budget.status as $status | ["matched", "requires_server_restart"] | index($status) != null)
    and (.modality_plan.audio_fusion.route | type == "string" and length > 0)
    and .agently_trace.version == "wear-edge-agently-trace.v1"
    and .agently_trace.triggerflow.definition_id == "m400_infer"
    and .agently_trace.triggerflow.entrypoint == "m400_infer"
    and .agently_trace.triggerflow.execution_state == "closed"
    and (.agently_trace.action_runtime.action_logs | type == "array" and length >= 1)
    and .runtime_stream.version == "wear-edge-runtime-stream.v1"
    and .runtime_stream.definition_id == "m400_infer"
    and .runtime_stream.request_id == $request_id
    and .runtime_stream.mode == env.ANALYSIS_MODE
    and .runtime_stream.closed == true
    and (.runtime_stream.events | type == "array" and length >= 8)
    and .runtime_stream.events[-1].event == "workflow.closed"
    and (
      if env.ANALYSIS_MODE == "iqc" then
        (.product | type == "string" and length > 0)
        and (.quality_risk | type == "string" and length > 0)
        and (.disposition | type == "string" and length > 0)
      elif env.ANALYSIS_MODE == "maintenance" then
        (.machine | type == "string" and length > 0)
        and (.symptom | type == "string" and length > 0)
        and (.maintenance_risk | type == "string" and length > 0)
        and (.evidence_needed | type == "string" and length > 0)
      elif env.ANALYSIS_MODE == "wi" then
        (.machine | type == "string" and length > 0)
        and (.work_instruction | type == "string" and length > 0)
        and (.risk_control | type == "string" and length > 0)
      elif env.ANALYSIS_MODE == "changeover" then
        (.machine | type == "string" and length > 0)
        and (.sku | type == "string" and length > 0)
        and (.changeover_step | type == "string" and length > 0)
        and (.verification | type == "string" and length > 0)
      else
        (.scene | type == "string" and length > 0)
        and (.risk | type == "string" and length > 0)
      end
    )
  ' /tmp/wearedge-smoke-response.json >/dev/null

  echo "Gateway output contract passed."

  if jq -e '.audit.logged == true' /tmp/wearedge-smoke-response.json >/dev/null; then
    REQUEST_ID="$(jq -r '.request_id' /tmp/wearedge-smoke-response.json)"
    echo "[audit] Gateway recent audit events"
    curl -fsS "$GATEWAY_BASE/v1/audit/recent?limit=1" \
      -H "Authorization: Bearer $DEMO_TOKEN" \
      | tee /tmp/wearedge-audit-recent.json \
      | jq .

    jq -e --arg request_id "$REQUEST_ID" '
      .ok == true
      and .enabled == true
      and (.events | length >= 1)
      and .events[0].request_id == $request_id
      and .events[0].runtime_stream.request_id == $request_id
    ' /tmp/wearedge-audit-recent.json >/dev/null

    echo "Gateway audit query passed."

    echo "[agent-runs] Gateway recent agent runs"
    curl -fsS "$GATEWAY_BASE/v1/agent-runs/recent?limit=1" \
      -H "Authorization: Bearer $DEMO_TOKEN" \
      | tee /tmp/wearedge-agent-runs-recent.json \
      | jq .

    jq -e --arg request_id "$REQUEST_ID" '
      .ok == true
      and .enabled == true
      and (.runs | length >= 1)
      and .runs[0].request_id == $request_id
      and .runs[0].runtime_stream.request_id == $request_id
      and .runs[0].last_event.event == "workflow.closed"
    ' /tmp/wearedge-agent-runs-recent.json >/dev/null

    echo "Gateway agent run query passed."
  fi
else
  echo "[3/3] Skipped image upload. Set TEST_IMAGE=/path/to/frame.jpg to enable it."
fi
