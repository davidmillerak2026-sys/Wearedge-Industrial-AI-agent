#!/usr/bin/env bash
set -Eeuo pipefail

GATEWAY_BASE="${GATEWAY_BASE:-http://127.0.0.1:8081}"
LLAMA_BASE="${LLAMA_BASE:-http://127.0.0.1:8080}"
LABEL="${1:-pb551-patrol}"
INTERVAL_SECONDS="${WEAREDGE_PATROL_INTERVAL_SECONDS:-180}"
ROUNDS="${WEAREDGE_PATROL_ROUNDS:-6}"
OUT_DIR="${WEAREDGE_PATROL_OUT_DIR:-$HOME/wearedge-patrol-stress}"
RUN_ID="${LABEL}-$(date +%Y%m%d-%H%M%S)"
RUN_DIR="$OUT_DIR/$RUN_ID"
SUMMARY_JSONL="$RUN_DIR/summary.jsonl"
SUMMARY_TXT="$RUN_DIR/summary.txt"

mkdir -p "$RUN_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$SUMMARY_TXT"
}

require_demo_token() {
  if [[ -z "${DEMO_TOKEN:-}" ]]; then
    log "ERROR DEMO_TOKEN is not set. Run from repo root with .env or export DEMO_TOKEN."
    exit 1
  fi
}

snapshot() {
  local label="$1"
  {
    echo "== $label =="
    date
    uptime
    nvpmodel -q || true
    systemctl is-active wearedge-llama.service || true
    systemctl is-active wearedge-gateway.service || true
    timeout 3 tegrastats || true
  } >> "$RUN_DIR/snapshots.log" 2>&1
}

curl_json() {
  local label="$1"
  local url="$2"
  shift 2
  local body="$RUN_DIR/${label}.json"
  local meta="$RUN_DIR/${label}.meta"

  curl -sS --connect-timeout 5 --max-time 180 \
    -w 'HTTP_STATUS=%{http_code} TIME=%{time_total}\n' \
    -o "$body" \
    "$url" "$@" > "$meta"

  cat "$meta" | tee -a "$SUMMARY_TXT"
  if command -v jq >/dev/null 2>&1; then
    jq -c --arg request_label "$label" '
      {
        "label": $request_label,
        ok,
        request_id,
        analysis_mode,
        latency_ms,
        action,
        contract_ok: .contract.ok,
        channel: .action_card.channel,
        priority: .action_card.priority,
        audit: .audit.logged,
        saved_path
      }
    ' "$body" | tee -a "$SUMMARY_JSONL" | tee -a "$SUMMARY_TXT" || true
  fi
}

text_health() {
  local label="$1"
  local body="$RUN_DIR/${label}.json"
  local meta="$RUN_DIR/${label}.meta"
  curl -sS --connect-timeout 5 --max-time 120 \
    -w 'HTTP_STATUS=%{http_code} TIME=%{time_total}\n' \
    -o "$body" \
    "$LLAMA_BASE/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "gemma4",
      "messages": [{"role": "user", "content": "Return one short WearEdge patrol health sentence."}],
      "chat_template_kwargs": {"enable_thinking": false},
      "max_tokens": 48,
      "temperature": 0.0
    }' > "$meta"
  cat "$meta" | tee -a "$SUMMARY_TXT"
  if command -v jq >/dev/null 2>&1; then
    jq -c --arg request_label "$label" '
      {
        "label": $request_label,
        text: .choices[0].message.content,
        prompt_tokens: .usage.prompt_tokens,
        completion_tokens: .usage.completion_tokens,
        total_tokens: .usage.total_tokens,
        prompt_tps: .timings.prompt_per_second,
        completion_tps: .timings.predicted_per_second
      }
    ' "$body" | tee -a "$SUMMARY_JSONL" | tee -a "$SUMMARY_TXT" || true
  fi
}

image_request() {
  local label="$1"
  local mode="$2"
  local image="$3"
  local prompt="$4"

  log "REQUEST $label mode=$mode image=$image"
  snapshot "before-$label"
  curl_json "$label" "$GATEWAY_BASE/v1/infer" \
    -H "Authorization: Bearer $DEMO_TOKEN" \
    -F "prompt=$prompt" \
    -F "analysis_mode=$mode" \
    -F "device_id=pb551-patrol-stress" \
    -F "capture_mode=pb551-patrol-stress" \
    -F "location_hint=bench" \
    -F "image=@$image"
  snapshot "after-$label"
}

require_demo_token

log "RUN_ID=$RUN_ID"
log "RUN_DIR=$RUN_DIR"
log "INTERVAL_SECONDS=$INTERVAL_SECONDS ROUNDS=$ROUNDS"

snapshot "start"

log "TEXT_HEALTH"
text_health "text-health"

image_request "warm-maintenance" "maintenance" \
  "docs/assets/lao-shi-fu-maintenance-poc/03_temperature_gauges.jpg" \
  "Read the visible temperature gauge context and give bounded maintenance guidance. Do not claim final diagnosis."

image_request "warm-iqc" "iqc" \
  "docs/assets/iqc-m400-poc/iqc_al_housing_l3_defect_m400.png" \
  "Assess this in-process product image for visible quality risk and containment need."

for i in $(seq 1 "$ROUNDS"); do
  case $(( (i - 1) % 3 )) in
    0)
      image_request "patrol-${i}-maintenance" "maintenance" \
        "docs/assets/lao-shi-fu-maintenance-poc/03_temperature_gauges.jpg" \
        "Read the visible temperature gauge context and give bounded maintenance guidance. Do not claim final diagnosis."
      ;;
    1)
      image_request "patrol-${i}-wi" "wi" \
        "docs/assets/wi-changeover-source-poc/wi_cartoner_st2_released_wi_m400.jpg" \
        "Identify the visible work instruction context and answer with bounded operator guidance."
      ;;
    *)
      image_request "patrol-${i}-iqc" "iqc" \
        "docs/assets/iqc-m400-poc/iqc_al_housing_l3_defect_m400.png" \
        "Assess this in-process product image for visible quality risk and containment need."
      ;;
  esac

  if [[ "$i" -lt "$ROUNDS" ]]; then
    log "SLEEP ${INTERVAL_SECONDS}s"
    sleep "$INTERVAL_SECONDS"
  fi
done

log "SERVICES_AFTER"
{
  systemctl is-active wearedge-llama.service || true
  systemctl is-active wearedge-gateway.service || true
  curl -sS -w '\nHTTP_STATUS=%{http_code} TIME=%{time_total}\n' "$GATEWAY_BASE/healthz" | head -c 1500 || true
  echo
} | tee -a "$SUMMARY_TXT"

log "KERNEL_LOG_CHECK"
if sudo -n true 2>/dev/null; then
  sudo -n dmesg -T | grep -iE "voltage|under|power|thermal|thrott|nvme|reset|shutdown|oom|error" | tail -n 160 | tee -a "$SUMMARY_TXT" || true
else
  log "KERNEL_LOG_CHECK_SKIPPED sudo timestamp is not active; run sudo -v before a short patrol, or capture dmesg separately after a long patrol."
fi

snapshot "end"
log "SUMMARY_JSONL=$SUMMARY_JSONL"
log "SUMMARY_TXT=$SUMMARY_TXT"
