#!/usr/bin/env bash
set -u

LABEL="${1:-original-power}"
DURATION_SECONDS="${WEAREDGE_POWER_BASELINE_SECONDS:-120}"
WRITE_MIB="${WEAREDGE_POWER_BASELINE_WRITE_MIB:-256}"
OUT_DIR="${WEAREDGE_POWER_BASELINE_DIR:-$HOME/wearedge-power-baselines}"
OUT_FILE="$OUT_DIR/${LABEL}-$(date +%Y%m%d-%H%M%S).log"

mkdir -p "$OUT_DIR"
exec > >(tee -a "$OUT_FILE") 2>&1

section() {
  printf '\n== %s ==\n' "$1"
}

run_or_note() {
  "$@" || true
}

section "baseline"
echo "label=$LABEL"
echo "duration_seconds=$DURATION_SECONDS"
echo "write_mib=$WRITE_MIB"
echo "log=$OUT_FILE"
date
whoami
hostname
hostname -I || true

section "system uptime and reboot history"
uptime
last -x reboot -n 8 || true

section "storage"
findmnt /mnt/nvme || true
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,LABEL,MODEL || true
df -h / /mnt/nvme || true

section "nvme"
if command -v nvme >/dev/null 2>&1; then
  sudo nvme list || true
else
  echo "nvme cli not installed"
fi

section "power mode"
nvpmodel -q || true

section "services before baseline"
systemctl is-active ssh || true
systemctl is-active wearedge-llama.service || true
systemctl is-active wearedge-gateway.service || true
systemctl status wearedge-llama.service --no-pager -l | tail -n 40 || true
systemctl status wearedge-gateway.service --no-pager -l | tail -n 40 || true
ss -ltnp | grep -E ':8080|:8081' || true
curl -sS -w '\nHTTP_STATUS=%{http_code} TIME=%{time_total}\n' http://127.0.0.1:8081/healthz | head -c 1500 || true
echo

section "idle tegrastats"
if command -v tegrastats >/dev/null 2>&1; then
  timeout "$DURATION_SECONDS" tegrastats --interval 1000 || true
else
  echo "tegrastats not found"
fi

section "nvme write pulse"
mkdir -p /mnt/nvme/wearedge/power-test
TEST_FILE="/mnt/nvme/wearedge/power-test/${LABEL}-write-test.bin"
dd if=/dev/zero of="$TEST_FILE" bs=1M count="$WRITE_MIB" conv=fsync status=progress
sync
ls -lh "$TEST_FILE"
rm -f "$TEST_FILE"
sync

section "services after baseline"
systemctl is-active wearedge-llama.service || true
systemctl is-active wearedge-gateway.service || true
curl -sS -w '\nHTTP_STATUS=%{http_code} TIME=%{time_total}\n' http://127.0.0.1:8081/healthz | head -c 1500 || true
echo

section "recent service logs"
journalctl -u wearedge-llama.service --since "20 minutes ago" --no-pager -n 120 || true
journalctl -u wearedge-gateway.service --since "20 minutes ago" --no-pager -n 120 || true

section "suspicious kernel logs"
sudo dmesg -T | grep -iE "voltage|under|power|thermal|thrott|nvme|reset|shutdown|oom|error" | tail -n 120 || true

section "summary"
echo "baseline_log=$OUT_FILE"
echo "pass_hint=no reboot, no service restart, healthz 200, no undervoltage, no nvme reset, no thermal throttle"
