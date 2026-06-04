#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/5] Installing system packages"
sudo apt-get update
sudo apt-get install -y \
  build-essential \
  cmake \
  curl \
  git \
  git-lfs \
  htop \
  jq \
  python3-dev \
  python3-pip \
  python3-venv

echo "[2/5] Preparing NVMe directories"
sudo mkdir -p /mnt/nvme/models/gemma4-e2b /mnt/nvme/wearedge/uploads
sudo chown -R "$USER":"$USER" /mnt/nvme/models /mnt/nvme/wearedge

echo "[3/5] Creating Python environment"
cd "$REPO_ROOT"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r jetson/requirements.txt

echo "[4/5] Installing Hugging Face Hub CLI into the venv"
python -m pip install --upgrade "huggingface_hub[hf_xet]"

echo "[5/5] Optional Jetson performance mode"
if command -v nvpmodel >/dev/null 2>&1; then
  sudo nvpmodel -m 2 || true
fi
if command -v jetson_clocks >/dev/null 2>&1; then
  sudo jetson_clocks || true
fi

echo "Setup complete. Activate with: source .venv/bin/activate"
