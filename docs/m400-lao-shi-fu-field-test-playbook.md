# M400 Lao-Shi-Fu Dynamic Field Test Playbook

Date: 2026-05-20

Purpose: run one real Vuzix M400 to Jetson Lao-Shi-Fu loop from the first field problem photo through the final maintenance conclusion. The operator should not follow a fixed photo checklist. Each turn starts from the current evidence and lets Jetson decide the next most useful evidence request.

## Product Principle

The correct field flow is:

```text
problem happens
operator frames one relevant view
M400 sends one image to Jetson
Jetson extracts every useful evidence point visible in that image
if not enough, Jetson names the remaining visual gaps to cover
repeat until visual evidence is sufficient
then M400 asks operator sensory questions one by one
Jetson returns the bounded Lao-Shi-Fu conclusion
```

This is deliberately not:

```text
step 1 asset plate
step 2 HMI
step 3 temperature
step 4 lubrication
...
```

Those are only possible evidence types. The agent chooses the next one from the current situation.

## Success Criteria

- M400 opens directly into WearEdge Pro and auto-connects to Jetson.
- Foreground remains `com.wearedge.m400demo/.MainActivity`; system camera should not become the workflow.
- M400 never asks the operator to type token/config during normal use.
- Each `capture photo` captures one M400 image, shows the exact upload preview, and only sends it after `accept`.
- `reject` or `retake` discards the preview and returns to framing.
- Jetson returns the current remaining visual gaps to M400, not a fixed checklist.
- Operator sensory questions only begin after targeted visual evidence is sufficient for this pass.
- After visual evidence is sufficient, M400 asks operator sensory questions naturally one at a time, then enters `FINAL ANALYZING`.
- Final conclusion is shown full-screen and offers simulated external follow-up actions that require oral `accept`.
- Connection reset or upload failure is visible on M400 and offers retry/recover behavior; it must not fail silently.
- After each inference, M400 clears transient local JPEG/frame state. After final conclusion, M400 clears local session/request state and is ready for a new inspection.

## Voice Commands

Keep the field command set small:

```text
Hello Vuzix
capture photo
accept
reject / retake
zoom in
zoom out
back to wearedge
yes / no / not sure
just now / today / yesterday / last week / recently / stable / unstable
```

- `Hello Vuzix`: system wake/listening phrase. Use only if the glasses are asleep, launcher is visible, or WearEdge is not hearing foreground commands.
- `capture photo`: capture the current WearEdge evidence frame and show the preview.
- `accept`: send the current preview to Jetson, or confirm the current final follow-up action.
- `reject` / `retake`: discard the current preview and reframe, or skip the current final follow-up action.
- `zoom in` / `zoom out`: adjust the framing before saying `capture photo`.
- `back to wearedge`: recover from Vuzix Voice Command, launcher, or any accidental system screen.
- Short answers are only for the operator sensory stage.

Avoid saying `take picture` or `take photo`, because those phrases may trigger the Vuzix system camera instead of the WearEdge workflow. Follow-up evidence capture should use `capture photo`; it should not require saying `Hello Vuzix` each turn while WearEdge is already foregrounded.

The screen may display the exact command phrases. Audio/TTS should avoid reading those exact phrases back to itself; it should say neutral wording such as `the wake phrase` so Vuzix does not self-trigger.

## Preflight

### Jetson

Run on Jetson:

```bash
cd ~/WearEdge-Pro
systemctl is-active wearedge-llama.service
systemctl is-active wearedge-gateway.service
curl -sS -w "\nHTTP_STATUS=%{http_code} TIME=%{time_total}\n" http://127.0.0.1:8081/healthz | head -c 1200
echo
hostname -I
```

Expected:

- `wearedge-llama.service`: `active`
- `wearedge-gateway.service`: `active`
- Gateway health returns `ok=true`
- Jetson IP is reachable from Windows and M400, usually `192.168.0.155`

### Windows/M400 ADB

Run in PowerShell from the repo root:

```powershell
$repo = "C:\Users\ryan hui\Documents\New project\WearEdge-Pro"
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
Set-Location $repo

& $adb devices
& $adb shell am force-stop com.wearedge.m400demo
& $adb shell am start -n com.wearedge.m400demo/.MainActivity
Start-Sleep -Seconds 5
& $adb shell dumpsys window | Select-String -Pattern "mCurrentFocus|mFocusedApp"
```

Expected:

- Device appears as `device`, for example `M005043620 device`
- Focus is WearEdge:

```text
com.wearedge.m400demo/com.wearedge.m400demo.MainActivity
```

## Monitoring Setup

Create a run folder and begin monitoring before the operator starts:

```powershell
$repo = "C:\Users\ryan hui\Documents\New project\WearEdge-Pro"
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$run = Join-Path $repo ("docs\poc-results\m400-live-monitor\manual-dynamic-loop-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $run | Out-Null

& $adb devices | Tee-Object -FilePath (Join-Path $run "adb-devices.txt")
& $adb logcat -c

$logcat = Start-Process -FilePath $adb `
  -ArgumentList @("logcat","-v","time","WearEdgeM400Demo:I","WearEdgeM400Voice:I","VuzixSpeechClient:I","*:S") `
  -RedirectStandardOutput (Join-Path $run "m400-wearedge-logcat.txt") `
  -PassThru

1..90 | ForEach-Object {
  Add-Content -Path (Join-Path $run "foreground-samples.txt") -Value ("== " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " ==")
  & $adb shell dumpsys window |
    Select-String -Pattern "mCurrentFocus|mFocusedApp" |
    ForEach-Object { Add-Content -Path (Join-Path $run "foreground-samples.txt") -Value $_.Line }
  Start-Sleep -Seconds 5
}
```

Stop logcat after the final conclusion:

```powershell
Stop-Process -Id $logcat.Id -ErrorAction SilentlyContinue
```

## Operator Flow

### 1. Start From The Problem

The operator should start with the real symptom, not with a checklist.

Frame one useful view:

- Whole machine or subsystem around the problem
- Visible alarm, gauge, HMI, leak, abnormal part, or physical symptom
- Enough surrounding context for location/orientation

Then say:

```text
capture photo
```

WearEdge should already be in the foreground. If the launcher or Vuzix Voice Command screen is visible, say `Hello Vuzix`, then `back to wearedge`; once the target is framed, say `capture photo`.

Expected:

- M400 captures exactly one frame inside WearEdge.
- M400 shows a preview of the exact upload JPEG.
- Operator says `accept` to send it, or `reject` / `retake` to discard and reframe.
- Jetson extracts all visible evidence points and returns either a conclusion path, operator sensory check, or the current remaining visual gaps.
- M400 clears the local frame after the inference returns.

### 2. Follow The Current Targeted Evidence Request

M400 should show a dynamic prompt such as:

```text
Follow-up photo. Jetson still needs condition screen evidence and temperature gauge evidence. Frame one view that covers as many of these as possible, then say capture photo.
```

or:

```text
Follow-up photo. Jetson still needs lubrication record evidence and recent work evidence. Frame one view that covers as many of these as possible, then say capture photo.
```

In the ear, follow-up evidence prompts should not say `hello wearedge`. They should say `capture photo` or neutral wording such as `capture the framed evidence`.

Possible requests include:

- Asset identity evidence: asset plate, station sign, line ID, readable tag.
- Condition screen evidence: HMI, vibration, current, load, speed, alarm code.
- Temperature evidence: motor, bearing, gearbox temperature with units.
- Lubrication evidence: oil/grease record, lube point card, date, material, initials.
- Recent work evidence: PM tag, repair note, issue log, work-order summary.

These are examples, not mandatory steps. One photo can satisfy several of them if the image is clear enough.

If text is too small:

```text
zoom in
```

If context is too tight:

```text
zoom out
```

Then say:

```text
capture photo
```

Expected:

- One new frame is previewed, accepted, and sent to the same Jetson session.
- Jetson re-runs the Lao-Shi-Fu agent loop with all accepted evidence.
- Jetson either reduces the remaining visual gaps, moves to operator sensory, or returns a bounded conclusion.

### 3. Operator Sensory Stage

This stage starts only after visual evidence is sufficient for the current pass.

M400 should say:

```text
Operator sensory check. Visual evidence is complete for now. I will ask one question at a time.
```

M400 asks one question, waits for one answer, records it, then asks the next question. Do not answer before the question finishes.

Expected question set:

- Do you hear unusual noise?
- Do you smell burning, oil, or other unusual odor?
- Do you feel abnormal heat near the machine?
- Do you feel abnormal shaking or vibration?
- Do you see oil, smoke, or leakage?
- When did this condition start?

Allowed short answers:

```text
yes
no
not sure
just now
today
recently
stable
unstable
```

After the final answer:

- M400 enters `FINAL ANALYZING`.
- M400 automatically captures one context frame without asking for manual preview confirmation.
- M400 uploads the structured operator note plus context frame to Jetson.
- Jetson runs the final Lao-Shi-Fu loop.
- M400 shows the conclusion full-screen and reads a short action summary.
- M400 offers simulated follow-up actions one at a time, each requiring oral `accept` to confirm.
- M400 clears local session state.

### 4. Final Follow-Up Actions

The current demo simulates external API actions. It should make clear that these are product integrations, not actual factory commands yet.

Expected final actions:

- `sim.email.notify_supervisor`: notify the maintenance supervisor.
- `sim.mes.request_line_stop`: request immediate line stop or controlled hold.
- `sim.sap.plan_downtime`: create a planned downtime / changeover maintenance placeholder.

For each action, M400 should ask one concise confirmation. Say:

```text
accept
```

to confirm the current action. Say:

```text
reject
```

to skip the current action and move on. The final conclusion screen should remain visible while these confirmations happen.

## What To Watch

### Good Signs

- The screen says `Problem photo`, `Next evidence`, `Operator sensory check`, or `Conclusion`; it should not say `Step 1 of 7`.
- The preview fills most of the AR view, with controls floating over the image rather than consuming the image area.
- Each Jetson response names the current remaining visual gaps, not a long fixed checklist.
- M400 waits for the operator to reframe before the next capture.
- During sensory check, M400 asks only one question at a time.
- After sensory completion, M400 shows `FINAL ANALYZING`, then the full-screen conclusion.
- Connection reset shows retry/recover status instead of disappearing.
- Foreground stays in WearEdge Pro.
- New uploads appear under `/mnt/nvme/wearedge/uploads`.

### Bad Signs

- M400 says `Step 1 of 7` or shows a fixed checklist.
- Jetson returns many visual requests to the M400 UI at once.
- Foreground becomes `org.codeaurora.snapcam`.
- M400 repeats the same sentence indefinitely.
- M400 captures a photo without any operator wake phrase after TTS speaks.
- M400 jumps from one sensory question to the next without waiting.
- Operator says `capture photo` while WearEdge is foregrounded and nothing reaches the app.
- Final conclusion is not readable in the AR screen.
- M400 returns to the main screen immediately after final conclusion.
- Upload or connection reset produces no visible retry state.

## Jetson Evidence Check

After the run:

```bash
ls -lt /mnt/nvme/wearedge/uploads | head
sudo journalctl -u wearedge-gateway.service -n 160 --no-pager
```

Expected:

- New uploaded frames exist under `/mnt/nvme/wearedge/uploads`.
- Gateway logs show session/evidence/infer activity.
- Final request id and session trace can be matched to the M400 logcat.

## Evidence To Save

- Run folder path under `docs/poc-results/m400-live-monitor/...`
- M400 screen photo or screenshot at final conclusion
- `m400-wearedge-logcat.txt`
- `foreground-samples.txt`
- Jetson upload filenames
- Final request id
- Final session id if visible
- Final action/channel/priority
- Final follow-up action confirmations
- Whether M400 cleared the session after conclusion

## Failure Triage

### M400 Opens System Camera

Say:

```text
back to wearedge
```

Then check focus with ADB. Do not continue the test through the system camera.

### M400 Does Not Upload

Check:

- M400 and Jetson are on the same Wi-Fi.
- Gateway health is reachable from Windows:

```powershell
curl.exe -m 5 http://192.168.0.155:8081/healthz
```

- `wearedge-gateway.service` is active.
- App is in WearEdge foreground.

### Sensory Check Repeats Or Skips

Wait until M400 finishes speaking the current question, then answer once. If it still skips:

- Save logcat.
- Note the exact question number.
- Note what was spoken before the skip.

### Old Session Returns After Final Conclusion

Restart the app:

```powershell
& $adb shell am force-stop com.wearedge.m400demo
& $adb shell am start -n com.wearedge.m400demo/.MainActivity
```

Expected:

```text
Previous Jetson session is complete. Starting a fresh WearEdge inspection.
Problem photo: Jetson connected. Frame one overview view in WearEdge.
```

## Pass/Fail Form

```text
Run id:
Start time:
Jetson IP:
M400 device id:

Preflight:
[ ] Jetson llama active
[ ] Jetson gateway active
[ ] Gateway health ok
[ ] M400 ADB connected
[ ] WearEdge foreground

Dynamic loop:
[ ] Initial problem photo completed
[ ] Jetson extracted multiple useful evidence points when one image contained them
[ ] Operator captured one useful view per turn, not one fixed evidence slot per turn
[ ] Visual evidence reached sufficient-for-this-pass state
[ ] Operator sensory questions were one-question-at-a-time
[ ] Final analyzing state appeared after sensory completion
[ ] Final conclusion returned
[ ] Final conclusion was full-screen and readable
[ ] Final follow-up actions required oral confirmation
[ ] M400 local session cleared after final conclusion

Robustness:
[ ] No system camera takeover
[ ] No repeated stuck prompt
[ ] No skipped sensory question
[ ] Connection reset path showed retry/recover state if triggered
[ ] No token entry required
[ ] Jetson uploads found
[ ] Logs saved

Final result:
Final action:
Channel / priority:
Remaining evidence:
Issues observed:
```
