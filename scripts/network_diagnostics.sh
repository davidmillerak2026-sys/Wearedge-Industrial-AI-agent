#!/usr/bin/env bash
set -Eeuo pipefail

echo "== WearEdge Pro network diagnostics =="
date -u +"utc=%Y-%m-%dT%H:%M:%SZ"

echo
echo "== interfaces =="
ip -br addr || true

echo
echo "== routes =="
ip route || true

echo
echo "== dns =="
cat /etc/resolv.conf || true
if command -v resolvectl >/dev/null 2>&1; then
  resolvectl status || true
elif command -v systemd-resolve >/dev/null 2>&1; then
  systemd-resolve --status || true
fi

echo
echo "== gateway ping =="
gateway="$(ip route | awk '/^default/ {print $3; exit}')"
if [[ -n "${gateway:-}" ]]; then
  ping -c 4 "$gateway" || true
else
  echo "No default gateway detected."
fi

echo
echo "== public connectivity =="
ping -c 4 8.8.8.8 || true
ping -c 4 github.com || true
ping -c 4 huggingface.co || true

echo
echo "== https probes =="
curl -4 -I --max-time 12 https://github.com || true
curl -4 -I --max-time 12 https://huggingface.co || true
curl -4 -I --max-time 12 https://hf-mirror.com || true

echo
echo "== git network config =="
git config --global --get http.version || true
git config --global --get http.postBuffer || true

echo
echo "== recommended stable git settings =="
echo "git config --global http.version HTTP/1.1"
echo "git config --global http.postBuffer 524288000"

echo
echo "== summary hints =="
echo "- If gateway ping fails, fix Wi-Fi/router first."
echo "- If 8.8.8.8 works but domains fail, fix DNS."
echo "- If GitHub/HF HTTPS probes timeout while gateway works, use Windows download + scp fallback."
echo "- If git clone fails with HTTP2/TLS errors, force HTTP/1.1 or use a zip archive fallback."
