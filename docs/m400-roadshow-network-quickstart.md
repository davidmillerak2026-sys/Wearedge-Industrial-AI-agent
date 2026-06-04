# M400 Roadshow Network Quickstart

Date: 2026-05-22

## Validated Demo Path

This is the field-demo network path validated before shutdown:

1. Windows laptop manages Jetson over direct Ethernet.
2. Jetson Ethernet stays on `192.168.55.1/24`.
3. Windows Ethernet stays on `192.168.55.2/24`, with no default gateway.
4. Jetson runs the `WearEdge-Pro` Wi-Fi hotspot.
5. M400 connects to the Jetson hotspot and receives a `10.42.0.x` address.
6. M400 WearEdge app uses Gateway URL `http://10.42.0.1:8081`.
7. Jetson Gateway and llama.cpp remain local on the Jetson:
   - Gateway: `0.0.0.0:8081`
   - llama.cpp: `0.0.0.0:8080`

Validated result:

- M400 joined `WearEdge-Pro` hotspot as `10.42.0.253`.
- M400 pinged Jetson hotspot gateway `10.42.0.1` successfully.
- M400 app `Check Gateway` returned `health.ok=true`.
- M400 captured and uploaded a real frame through the hotspot path.
- Jetson returned a maintenance lao-shi-fu follow-up result.
- The session moved from `4 gaps` to `3 gaps`.

Latest validated inference:

- `request_id`: `fe64852073824cfba8ea3ab915f50e51`
- `latency_ms`: `44812`
- Jetson upload path: `/mnt/nvme/wearedge/uploads/1779421017937.jpg`
- Channel: `maintenance_identification_required`
- Priority: `medium`

## Evidence Snapshots

Local evidence captured on the Windows workspace:

- `docs/poc-results/m400-hotspot-gateway-check.png`
- `docs/poc-results/m400-hotspot-followup-result.png`
- `docs/poc-results/m400-hotspot-audit-recent.json`
- `docs/poc-results/m400-hotspot-agent-runs-recent.json`

## Roadshow Startup Checklist

On Windows:

```powershell
netsh interface ip set address name="以太网" static 192.168.55.2 255.255.255.0 none
ping 192.168.55.1
ssh ryn@192.168.55.1
curl.exe -m 5 http://192.168.55.1:8081/healthz
```

On Jetson:

```bash
cd ~/WearEdge-Pro
sudo nmcli con up wearedge-wired-admin
sudo nmcli con up WearEdge-Pro-hotspot

ip -br addr
nmcli device status

systemctl is-active ssh
systemctl is-active wearedge-llama.service
systemctl is-active wearedge-gateway.service

sudo ss -ltnp | grep -E ':22|:8080|:8081'
curl -sS -w "\nHTTP_STATUS=%{http_code} TIME=%{time_total}\n" http://127.0.0.1:8081/healthz | head -c 800
```

Expected Jetson network state:

```text
wlP1p1s0   UP   10.42.0.1/24
enP8p1s0   UP   192.168.55.1/24
```

Expected active connections:

```text
WearEdge-Pro-hotspot  wifi      wlP1p1s0
wearedge-wired-admin  ethernet  enP8p1s0
```

## M400 Startup Checklist

M400 should connect to the Jetson hotspot:

- SSID: `WearEdge-Pro`
- Gateway URL in WearEdge app: `http://10.42.0.1:8081`
- Expected M400 IP range: `10.42.0.x`

If USB/ADB is connected from Windows, verify:

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb devices -l
& $adb shell cmd wifi status
& $adb shell ip addr show wlan0
& $adb shell ping -c 3 10.42.0.1
```

Launch the M400 app with the hotspot gateway:

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$pkg = "com.wearedge.m400demo"
& $adb shell am start -n "$pkg/.MainActivity" --es gateway_url http://10.42.0.1:8081 --es device_id m400-demo-01 --es location_hint demo-zone --es capture_mode m400-lao-shi-fu-session --es analysis_mode maintenance --es evidence_type maintenance_initial_frame
```

Use the app UI to confirm:

- `Check Gateway` shows `health.ok=true`.
- `Capture photo` captures a preview.
- `Accept` uploads to Jetson.
- M400 returns a follow-up prompt or final result.

## Shutdown Checklist

Before shutdown:

```bash
sync
systemctl is-active wearedge-llama.service
systemctl is-active wearedge-gateway.service
sudo shutdown -h now
```

After shutdown:

- Wait until Jetson power LEDs/fan behavior confirms halt.
- Then remove power.
- Keep Windows Ethernet config and M400 saved hotspot profile unchanged for the roadshow.

## Demo Risk Notes

- Windows will not normally reach `10.42.0.1` directly because that subnet is for M400-to-Jetson hotspot traffic. Windows manages Jetson through `192.168.55.1`.
- If the Jetson hotspot starts, the old `tcxf` Wi-Fi IP such as `192.168.0.155` will disappear. This is expected.
- If M400 remains on `tcxf`, use the M400 Wi-Fi menu or ADB to switch it back to `WearEdge-Pro`.
- Do not put demo token or hotspot password into public evidence screenshots or public docs.
