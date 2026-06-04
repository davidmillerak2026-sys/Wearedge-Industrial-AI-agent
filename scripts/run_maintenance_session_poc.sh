#!/usr/bin/env bash
set -Eeuo pipefail

GATEWAY_BASE="${GATEWAY_BASE:-http://127.0.0.1:8081}"
DEVICE_ID="${DEVICE_ID:-m400-maintenance-poc}"
FRAME_TS="${FRAME_TS:-}"
LOCATION_HINT="${LOCATION_HINT:-line-3-drive-station}"
CAPTURE_MODE="${CAPTURE_MODE:-m400-session-poc}"
ASSET_DIR="${ASSET_DIR:-docs/assets/lao-shi-fu-maintenance-poc}"
INITIAL_IMAGE="${INITIAL_IMAGE:-$ASSET_DIR/00_initial_full_frame.png}"
ASSET_IMAGE="${ASSET_IMAGE:-$ASSET_DIR/01_asset_identity.jpg}"
CONDITION_IMAGE="${CONDITION_IMAGE:-$ASSET_DIR/02_condition_monitor.jpg}"
TEMPERATURE_IMAGE="${TEMPERATURE_IMAGE:-$ASSET_DIR/03_temperature_gauges.jpg}"
LUBRICATION_IMAGE="${LUBRICATION_IMAGE:-$ASSET_DIR/04_lubrication_record.jpg}"
WORK_RECORD_IMAGE="${WORK_RECORD_IMAGE:-$ASSET_DIR/05_recent_maintenance_record.jpg}"
SENSORY_IMAGE="${SENSORY_IMAGE:-$ASSET_DIR/06_operator_sensory_check.jpg}"
POC_TMP_DIR="${POC_TMP_DIR:-/tmp/wearedge-maintenance-session-poc}"
GATEWAY_WAIT_SECONDS="${GATEWAY_WAIT_SECONDS:-60}"

if [[ -z "${DEMO_TOKEN:-}" ]]; then
  echo "Set DEMO_TOKEN before running the maintenance session POC." >&2
  exit 1
fi

for command_name in curl jq; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 1
  fi
done

for image_path in "$INITIAL_IMAGE" "$ASSET_IMAGE" "$CONDITION_IMAGE" "$TEMPERATURE_IMAGE" "$LUBRICATION_IMAGE" "$WORK_RECORD_IMAGE"; do
  if [[ ! -f "$image_path" ]]; then
    echo "Missing required image: $image_path" >&2
    exit 1
  fi
done

mkdir -p "$POC_TMP_DIR"

AUTH_HEADER="Authorization: Bearer $DEMO_TOKEN"
SESSION_JSON="$POC_TMP_DIR/01_create_session.json"
RESPONSE_JSON="$POC_TMP_DIR/08_infer_response.json"
TRACE_JSON="$POC_TMP_DIR/09_trace.json"

mime_for() {
  case "${1,,}" in
    *.png) echo "image/png" ;;
    *) echo "image/jpeg" ;;
  esac
}

wait_for_gateway() {
  local health_json="$POC_TMP_DIR/00_healthz.json"
  local deadline=$((SECONDS + GATEWAY_WAIT_SECONDS))
  local attempt=1

  echo "[wait] Gateway readiness at $GATEWAY_BASE/healthz"
  while (( SECONDS < deadline )); do
    if curl -fsS "$GATEWAY_BASE/healthz" > "$health_json"; then
      jq '.ok, .api_version, .agently.flow_definition.supported_modes' "$health_json"
      return 0
    fi
    echo "[wait] gateway not ready yet, retry $attempt"
    attempt=$((attempt + 1))
    sleep 1
  done

  echo "Gateway did not become ready within ${GATEWAY_WAIT_SECONDS}s." >&2
  echo "Check: systemctl status wearedge-gateway.service --no-pager -l" >&2
  echo "Check: journalctl -u wearedge-gateway.service -n 120 --no-pager" >&2
  return 1
}

post_evidence_photo() {
  local evidence_type="$1"
  local image_path="$2"
  local summary="$3"
  local fields_json="$4"
  local output_path="$5"

  echo "[evidence] $evidence_type"
  curl -fsS "$GATEWAY_BASE/v1/maintenance-sessions/$SESSION_ID/evidence" \
    -H "$AUTH_HEADER" \
    -F "evidence_type=$evidence_type" \
    -F "capture_type=photo" \
    -F "status=accepted" \
    -F "summary=$summary" \
    -F "fields_json=$fields_json" \
    -F "image=@$image_path;type=$(mime_for "$image_path")" \
    | tee "$output_path" \
    | jq .

  jq -e --arg evidence_type "$evidence_type" '
    .ok == true
    and .evidence.evidence_type == $evidence_type
    and .evidence.status == "accepted"
    and (.maintenance_session.session_id | type == "string" and length > 0)
  ' "$output_path" >/dev/null
}

post_sensory_check() {
  local fields_json="$1"
  local output_path="$2"
  local summary="${SENSORY_SUMMARY:-Operator reports low-frequency abnormal rumble, slight warm oil smell, stronger guard vibration, warm gearbox housing, and a small oil stain after speed increase.}"

  echo "[evidence] maintenance_operator_sensory_check"
  local curl_args=(
    -fsS "$GATEWAY_BASE/v1/maintenance-sessions/$SESSION_ID/evidence"
    -H "$AUTH_HEADER"
    -F "evidence_type=maintenance_operator_sensory_check"
    -F "capture_type=operator_note"
    -F "status=accepted"
    -F "summary=$summary"
    -F "fields_json=$fields_json"
  )
  if [[ -f "$SENSORY_IMAGE" ]]; then
    curl_args+=(-F "image=@$SENSORY_IMAGE;type=$(mime_for "$SENSORY_IMAGE")")
  fi

  curl "${curl_args[@]}" | tee "$output_path" | jq .

  jq -e '
    .ok == true
    and .evidence.evidence_type == "maintenance_operator_sensory_check"
    and .evidence.status == "accepted"
  ' "$output_path" >/dev/null
}

echo "[1/9] Gateway health"
wait_for_gateway

echo "[2/9] Create maintenance session"
curl -fsS "$GATEWAY_BASE/v1/maintenance-sessions" \
  -H "$AUTH_HEADER" \
  -F "device_id=$DEVICE_ID" \
  -F "frame_ts=$FRAME_TS" \
  -F "location_hint=$LOCATION_HINT" \
  -F "capture_mode=$CAPTURE_MODE" \
  -F "operator_id=${OPERATOR_ID:-operator-demo-01}" \
  -F "initial_prompt=Investigate gearbox vibration, heat, lubrication, and recent maintenance evidence before assigning any final cause." \
  | tee "$SESSION_JSON" \
  | jq .

SESSION_ID="$(jq -r '.maintenance_session.session_id' "$SESSION_JSON")"
export SESSION_ID
if [[ -z "$SESSION_ID" || "$SESSION_ID" == "null" ]]; then
  echo "Failed to create maintenance session." >&2
  exit 1
fi
echo "SESSION_ID=$SESSION_ID"

post_evidence_photo \
  "maintenance_asset_identity_photo" \
  "$ASSET_IMAGE" \
  "Asset plate and station sign identify PKG-L3-GBX-03 packaging line three gearbox drive station." \
  '{"asset_id":"PKG-L3-GBX-03","line_id":"packaging-line-3","station_id":"drive-station"}' \
  "$POC_TMP_DIR/02_asset_identity.json"

post_evidence_photo \
  "maintenance_condition_screen_photo" \
  "$CONDITION_IMAGE" \
  "Condition monitor shows vibration RMS high trend, yellow PLC alarm, motor current, load, and speed context." \
  '{"vibration_rms_mm_s":"7.2","alarm_color":"yellow","alarm_code":"GBX-VIB-HI","motor_current_a":"18.4","load_pct":"82","speed_rpm":"1460"}' \
  "$POC_TMP_DIR/03_condition_screen.json"

post_evidence_photo \
  "maintenance_temperature_gauge_photo" \
  "$TEMPERATURE_IMAGE" \
  "Temperature gauges show elevated gearbox and bearing readings that need manual threshold comparison." \
  '{"motor_temperature_c":"64","bearing_temperature_c":"71","gearbox_temperature_c":"78","temperature_unit":"C"}' \
  "$POC_TMP_DIR/04_temperature_gauge.json"

post_evidence_photo \
  "maintenance_lubrication_record_photo" \
  "$LUBRICATION_IMAGE" \
  "Lubrication record indicates the last gearbox lubrication entry is older than the normal weekly check interval." \
  '{"lubrication_date":"2026-05-07","lubricant_type":"gear oil","lubrication_point":"GBX-03","operator_initials":"LH"}' \
  "$POC_TMP_DIR/05_lubrication_record.json"

post_evidence_photo \
  "maintenance_recent_work_record_photo" \
  "$WORK_RECORD_IMAGE" \
  "Recent maintenance record shows prior vibration inspection and no confirmed bearing replacement yet." \
  '{"last_maintenance_date":"2026-05-10","last_repair_action":"vibration inspection","open_issue":"monitor gearbox vibration","technician_note":"bearing condition not yet confirmed"}' \
  "$POC_TMP_DIR/06_recent_work_record.json"

SENSORY_FIELDS_JSON="${SENSORY_FIELDS_JSON:-$(jq -cn \
  --arg noise "low-frequency abnormal rumble near gearbox" \
  --arg smell "slight warm oil smell" \
  --arg heat "gearbox housing feels warmer than usual but not burning hot" \
  --arg vibration "stronger vibration felt on guard panel after speed increase" \
  --arg leakage "small oil stain near gearbox base" \
  --arg started_when "after speed increase during current shift" \
  '{unusual_noise:$noise, unusual_smell:$smell, felt_heat:$heat, felt_shaking:$vibration, visible_leak:$leakage, started_when:$started_when}')}"
post_sensory_check "$SENSORY_FIELDS_JSON" "$POC_TMP_DIR/07_operator_sensory_check.json"

MAINTENANCE_PROMPT="${MAINTENANCE_PROMPT:-Use the accumulated maintenance session evidence to identify the machine, summarize symptoms, bound the maintenance risk, name evidence still needed, and recommend the next safe maintenance action. Do not analyze EHS/personnel hazard exposure and do not provide final root cause, remaining useful life, restart permission, or maintenance release.}"

echo "[8/9] Run session maintenance inference"
curl -fsS "$GATEWAY_BASE/v1/maintenance-sessions/$SESSION_ID/infer" \
  -H "$AUTH_HEADER" \
  -F "prompt=$MAINTENANCE_PROMPT" \
  -F "device_id=$DEVICE_ID" \
  -F "frame_ts=$FRAME_TS" \
  -F "location_hint=$LOCATION_HINT" \
  -F "capture_mode=$CAPTURE_MODE" \
  -F "needs_ocr=true" \
  -F "high_detail=true" \
  -F "image=@$INITIAL_IMAGE;type=$(mime_for "$INITIAL_IMAGE")" \
  | tee "$RESPONSE_JSON" \
  | jq .

jq -e --arg session_id "$SESSION_ID" '
  .ok == true
  and .analysis_mode == "maintenance"
  and .maintenance_session.session_id == $session_id
  and (.maintenance_session.evidence_state.accepted_evidence_ids | length >= 6)
  and any(.agently_trace.triggerflow.stages[]; .name == "load_session_evidence" and .status == "completed")
  and (.runtime_stream.closed == true)
  and (.action_card.mode == "maintenance")
  and (.action_card.channel | type == "string" and length > 0)
  and (.knowledge_base.status == "matched")
  and (.knowledge_base.hits | length >= 1)
  and (.maintenance_evaluation.status == "breach_detected")
  and (.maintenance_evaluation.risk_level == "high")
  and (.maintenance_evaluation.breaches | length >= 3)
  and (.action_card.channel | IN("maintenance_report", "schedule_maintenance", "maintenance_escalation", "maintenance_stop"))
  and (.action_card.owner | IN("maintenance_engineer", "maintenance_planner"))
  and (.integration_event.target == "maintenance_work_order")
  and (.tool_plan.used_tool_calls >= 1)
  and (.integration_event.payload.maintenance_evaluation.status == .maintenance_evaluation.status)
  and (.integration_event.payload.follow_up_plan.status == .follow_up_plan.status)
' "$RESPONSE_JSON" >/dev/null

echo "[9/9] Fetch maintenance session trace"
curl -fsS "$GATEWAY_BASE/v1/maintenance-sessions/$SESSION_ID/trace" \
  -H "$AUTH_HEADER" \
  | tee "$TRACE_JSON" \
  | jq .

jq -e --arg session_id "$SESSION_ID" '
  .ok == true
  and .maintenance_session.session_id == $session_id
  and (.trace.events | length >= 8)
  and .trace.events[-1].event == "maintenance_session.inference_completed"
' "$TRACE_JSON" >/dev/null

echo "Maintenance session POC passed."
echo "Response: $RESPONSE_JSON"
echo "Trace: $TRACE_JSON"
