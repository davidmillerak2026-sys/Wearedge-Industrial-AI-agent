#!/usr/bin/env bash
set -Eeuo pipefail

LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"
LLAMA_CPP_REF="${LLAMA_CPP_REF:-master}"

if [[ ! -d "$LLAMA_CPP_DIR/.git" ]]; then
  git config --global http.version HTTP/1.1
  git config --global http.postBuffer 524288000
  if ! git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$LLAMA_CPP_DIR"; then
    cat >&2 <<'EOF'
Failed to clone llama.cpp from GitHub.

Network fallback:
1. Download llama.cpp as a zip archive on a stable Windows/macOS machine.
2. Copy it to Jetson with scp.
3. Extract it to ~/llama.cpp.
4. Re-run scripts/build_llama_cpp.sh.

Run scripts/network_diagnostics.sh to capture router, DNS, GitHub, and Hugging Face connectivity details.
EOF
    exit 1
  fi
fi

cd "$LLAMA_CPP_DIR"
if [[ -d .git ]]; then
  git fetch --tags --prune || true
  git checkout "$LLAMA_CPP_REF"
fi

cmake -B build \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES="87" \
  -DGGML_NATIVE=ON \
  -DCMAKE_BUILD_TYPE=Release

cmake --build build --config Release -j"$(nproc)" --target llama-server llama-cli

echo "Built llama.cpp at $LLAMA_CPP_DIR/build/bin"
