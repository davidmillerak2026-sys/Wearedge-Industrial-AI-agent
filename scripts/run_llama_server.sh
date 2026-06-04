#!/usr/bin/env bash
set -Eeuo pipefail

find_first_gguf() {
  local root="$1"
  shift
  local pattern candidate
  for pattern in "$@"; do
    candidate="$(find "$root" -maxdepth 1 -type f -name "$pattern" | sort | head -n 1 || true)"
    if [[ -n "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"
MODEL_DIR="${MODEL_DIR:-/mnt/nvme/models/gemma4-e2b}"
HOST="${LLAMA_HOST:-0.0.0.0}"
PORT="${LLAMA_PORT:-8080}"

LLAMA_SERVER="${LLAMA_SERVER:-$LLAMA_CPP_DIR/build/bin/llama-server}"
TEXT_MODEL="${TEXT_MODEL:-$(find_first_gguf "$MODEL_DIR" "*Q4_K_M*.gguf" "*Q4_K_S*.gguf" "*UD-Q4*.gguf" "*Q8_0*.gguf")}"
MMPROJ_MODEL="${MMPROJ_MODEL:-$(find_first_gguf "$MODEL_DIR" "*mmproj*.gguf")}"

for path in "$LLAMA_SERVER" "$TEXT_MODEL" "$MMPROJ_MODEL"; do
  if [[ ! -e "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
done

# VISUAL TOKEN DYNAMIC ALLOCATION MODULE:
# jetson/modality_pipeline.py owns the policy. This launcher receives the
# selected budget through LLAMA_IMAGE_MIN_TOKENS and LLAMA_IMAGE_MAX_TOKENS.
#
# AUDIO FUSION MODULE:
# The current Orin Nano GGUF path stays image+text. Native E2B/E4B audio should
# route through the vLLM/NIM path documented in docs/technical_architecture.md.
exec "$LLAMA_SERVER" \
  -m "$TEXT_MODEL" \
  --mmproj "$MMPROJ_MODEL" \
  -c "${LLAMA_CONTEXT:-2048}" \
  --image-min-tokens "${LLAMA_IMAGE_MIN_TOKENS:-70}" \
  --image-max-tokens "${LLAMA_IMAGE_MAX_TOKENS:-70}" \
  --ubatch-size "${LLAMA_UBATCH_SIZE:-512}" \
  --batch-size "${LLAMA_BATCH_SIZE:-512}" \
  --host "$HOST" \
  --port "$PORT" \
  -ngl "${LLAMA_NGL:-99}" \
  --flash-attn on \
  --no-mmproj-offload \
  --jinja \
  -np "${LLAMA_PARALLEL:-1}"
