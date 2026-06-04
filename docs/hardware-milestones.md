# WearEdge Pro Hardware Milestones

本文档记录 WearEdge Pro 硬件开发中的关键里程碑。每条记录使用同一证据结构：**日期、假设、测试、证据、结论、风险边界**。

目标读者包括项目评审、客户工程团队、现场试用负责人和后续维护者。本文只记录已经在实机上验证过的工程事实；没有实测支撑的部分统一写入风险边界。

## 当前硬件结论

截至 2026-05-18，WearEdge Pro 已经完成一条可复现的真实 M400 + 随身边缘算力硬件路径：

```text
Vuzix M400 as real sensing endpoint
  -> Camera2 JPEG capture
  -> local Wi-Fi LAN
  -> Jetson Orin Nano 8GB compute box
  -> microSD boots the system
  -> 2TB NVMe stores model/runtime data
  -> PB551 100W USB-C PD power bank can power the box through a 20V trigger cable
  -> local Gemma 4 E2B multimodal inference
  -> M400 operator result and audit confirmation
```

工程口径：

- **已确认**：真实 Vuzix M400 已通过 USB/ADB 调试、同一 Wi-Fi、Camera2 JPEG 采集、Jetson Gateway 上传、本地多模态推理、M400 端结果展示和 `Audit Recent` 同 request_id 匹配。
- **已确认**：WearEdge Voice Adapter 已在真实 M400 App 内跑通：`maintenance`、`health`、`capture`、`upload`、`audit` 命令可以映射到现有控件动作，并完成一次 `capture_mode=voice-adapter-camera2` 的真实 M400 -> Jetson lao-shi-fu 推理与 audit 匹配。
- **已确认**：Vuzix 原生语音服务已接入项目内 Voice Adapter，自定义短语 `check gateway`、`capture frame`、`maintenance mode`、`upload to Jetson` 可以直接触发 WearEdge App 动作；其中 `upload to Jetson` 已完成一次真实 M400 -> Jetson `maintenance` 推理，`request_id=2eb9f7cfa49f48f090f82cf387b13b66`。
- **已确认**：M400 自带 Vuzix 系统语音控制可以通过 `Hello Vuzix` 与屏幕数字气泡操作 WearEdge App 的可见控件；本轮已用语音触发 `Capture Camera2 JPEG`，并触发 `Upload To Jetson` 按钮路径。
- **已确认**：PB551 100W USB-C PD + 20V PD trigger + 5.5x2.5mm DC barrel 接线方案可以支撑当前 WearEdge Jetson PoC 启动、NVMe 存储、服务运行和多模态推理巡检，并已通过 36% 起始电量到 24% 结束电量的 60 分钟低电量段巡检；在 2026-05-18 M400 实物调试日，按满电开机到 16:02 剩余 34% 估算，已连续支撑约 5 小时 37 分钟，平均功耗约 8.5W。
- **未声明**：这不是量产安规认证、不是本安防爆认证、不是全生命周期可靠性测试。
- **下一门槛**：M400 佩戴姿态下的现场可用性、嘈杂环境语音命中率、全语音 audit/复核闭环、UI 操作效率、线缆扰动、满负载余量、机械固定、保险保护和更低电量段输出降档观察。

里程碑按倒叙排列，最新验证记录在前。

## HW-2026-05-18-05: Vuzix Native Custom Voice Phrase Validation

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-18 |
| 假设 | 真实 Vuzix M400 可以通过原生 Vuzix Speech SDK 注册 WearEdge 专属短语，让操作者说 `Hello Vuzix` 后直接说 `check gateway`、`capture frame`、`maintenance mode`、`upload to Jetson`，并触发同一套 M400 App 控件动作与 Jetson Gateway 推理链路；整个过程不需要新增或改变 WearEdge Gateway API/schema。 |
| 测试 | 在 M400 Android App 中加入 `com.vuzix:sdk-speechrecognitionservice:1.97.1`，通过 `VuzixSpeechClient.insertPhrase(spokenPhrase, substitution)` 注册 12 个自定义短语，并监听 Vuzix 原生 `com.vuzix.action.VOICE_COMMAND` 的 `phrase` extra；该原生事件再进入项目内 `WearEdgeVoiceAdapter`。构建安装 debug APK 到真实 M400 `M005043620` 后，用 Windows TTS 模拟现场语音，依次测试 `Hello Vuzix` -> `check gateway`、`capture frame`、`maintenance mode`、`upload to Jetson`。 |
| 证据 | Gradle 构建成功，APK 安装成功；M400 debug UI 显示 `Vuzix custom voice phrases registered: 12.`；logcat 显示 `recognized phrase check gateway -> wearedge_check_gateway`，M400 UI 显示 `Gateway health OK.`；logcat 显示 `recognized phrase capture frame -> wearedge_capture_frame`，M400 UI/log 显示 `Captured Camera2 JPEG 1280x720: 167 KB.`；logcat 显示 `recognized phrase maintenance mode -> wearedge_maintenance_mode`，App 状态切到 `analysis_mode=maintenance`；logcat 显示 `recognized phrase upload to Jetson -> wearedge_upload_to_jetson`，Jetson 返回 `ok=true`、`request_id=2eb9f7cfa49f48f090f82cf387b13b66`、`latency_ms=45122`、`saved_path=/mnt/nvme/wearedge/uploads/1779098027600.jpg`、`channel=maintenance_identification_required`、`priority=medium`。该上传 JPEG 已从 Jetson NVMe 拉取为仓库快照 `custom-voice-jetson-upload-1779098027600.jpg`，SHA256 `6A4B30396FDE613B87FF654C47216AB25DDD33804B38C91537952E65E8B22CA5`。ADB shell 试图伪造 `com.vuzix.action.VOICE_COMMAND` 时被系统拒绝，证明 Vuzix 原生 action 是受保护入口；工程测试仍使用项目内 ADB action。 |
| 结论 | WearEdge 已从“系统数字气泡语音控制”和“项目内 ADB/adapter 命令”推进到“Vuzix 原生自定义短语”阶段。操作者可以用自然短语直接触发 Gateway health、Camera2 拍照、maintenance mode 设置和 Jetson 上传推理；其中上传推理已经完成真实 M400 -> Jetson lao-shi-fu agent 闭环，并保留了 M400 UI、logcat、audit JSON 和 Jetson 原图快照。 |
| 风险边界 | 本轮验证在受控 bench 环境下完成，输入源为 Windows TTS 与 M400 麦克风，不等同于嘈杂工厂、多人声线、佩戴姿态、远场说话、离线唤醒可靠性或生产级权限模型验证。当前动态 receiver 为接收 Vuzix 外部服务广播而导出，生产版应增加更严格的来源校验或权限保护。 |

相关证据文件：

- `docs/poc-results/m400-custom-voice-phrases-2026-05-18/evidence-manifest.md`
- `docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-result-summary.json`
- `docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-audit-recent.json`
- `docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-jetson-upload-1779098027600.jpg`
- `docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-current-result-screen.png`
- `docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-current-request-screen.png`
- `docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-current-debug-screen.png`
- `docs/poc-results/m400-custom-voice-phrases-2026-05-18/tts-capture-frame-log.txt`
- `docs/poc-results/m400-custom-voice-phrases-2026-05-18/tts-upload-to-jetson-2-log.txt`

## HW-2026-05-18-04: WearEdge Voice Adapter Real-M400 Validation

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-18 |
| 假设 | 在不改变 Jetson Gateway API/schema 的前提下，可以在 M400 Android App 内增加一个 WearEdge 自有 Voice Adapter，把语音事件或测试广播稳定映射到现有控件动作，从而实现更可控的 hands-free 操作路径。 |
| 测试 | 在 `clients/m400/android` 新增 `WearEdgeVoiceAdapter.kt`，并在 `MainActivity` 注册动态 command receiver：`com.wearedge.m400demo.action.VOICE_COMMAND`。使用真实 Vuzix M400 `M005043620` 构建安装 debug APK；通过 ADB 广播依次发送 `maintenance`、`health`、`capture`、`upload`、`audit`。App 内 demo token 通过 masked password field 输入，证据截图不显示明文。 |
| 证据 | Windows 构建 `.\gradlew.bat :app:assembleDebug --no-daemon` 成功，`adb install -r app-debug.apk` 成功。`maintenance` 命令把 `analysis_mode` 设置为 `maintenance`；`health` 命令显示 `Gateway health OK.`；`capture` 命令触发 Camera2，显示 `Captured Camera2 JPEG 1280x720: 67 KB`，并将 `capture_mode` 改为 `voice-adapter-camera2`；`upload` 命令完成真实 Jetson lao-shi-fu 推理，产生 `request_id=68a79723fbde47f2a276cc2e9208bf4f`、`latency_ms=46778`、`saved_path=/mnt/nvme/wearedge/uploads/1779096333543.jpg`、`channel=maintenance_identification_required`；`audit` 命令显示 `request_id_matched=true`。Jetson 上传图已复制为仓库快照 `voice-adapter-jetson-upload-1779096333543.jpg`。 |
| 结论 | WearEdge 已拥有一层项目内可控的 Voice Adapter：它不依赖修改 Gateway，也不把业务逻辑绑死到某个语音 SDK；目前可由 ADB 或后续 Vuzix 自定义语法触发同一命令面。该适配层已经在真实 M400 上完成“语音适配器命令 -> Camera2 采集 -> Jetson lao-shi-fu agent -> M400 audit 同 request_id”的闭环。 |
| 风险边界 | 本轮验证的是 app-level command adapter 与真实设备链路，不等同于生产级 ASR 词表、噪声环境识别率、佩戴姿态可用性或 Vuzix 专有 SDK 深度集成。Vuzix 原生系统语音气泡仍是当前直接人机语音入口；如需 `capture frame` 这类无气泡自定义短语，应在下一轮把 Vuzix custom grammar/SDK 事件接到本 adapter。 |

相关证据文件：

- `docs/poc-results/m400-voice-adapter-2026-05-18/evidence-manifest.md`
- `docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-result-summary.json`
- `docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-maintenance2.png`
- `docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-health.png`
- `docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-capture.png`
- `docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-upload-action.png`
- `docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-audit-match.png`
- `docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-jetson-upload-1779096333543.jpg`

## HW-2026-05-18-03: Vuzix M400 Voice-Control Functional Validation

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-18 |
| 假设 | 真实 Vuzix M400 的系统语音控制可以不改 WearEdge Gateway API，通过设备自带 `Hello Vuzix` 语音入口与屏幕数字气泡，操作 WearEdge M400 App 的可见按钮，为现场免手操作提供第一条可行路径。 |
| 测试 | M400 通过 C-C 连接 Windows ADB；确认 `com.vuzix.speechrecognitionservice` 正在运行；先用语音/扬声器输入 `Hello Vuzix` 与 `Command list` 验证系统语音识别；随后启用 Vuzix 自带 `com.vuzix.accessibilityservice/.AccessibilitySpeechInput`，让 WearEdge App 可点击控件生成数字气泡；在 WearEdge M400 App 按钮区执行 `Hello Vuzix` -> `three` 与 `Hello Vuzix` -> `four`。 |
| 证据 | 初始状态下 `Hello Vuzix` 与 `Command list` 可打开 Vuzix `Speech command list`，但 app 内 `Select this` 不稳定；ADB 显示 `enabled_accessibility_services=null` 且日志提示 `No accessibility service is configured`。启用 `AccessibilitySpeechInput` 后，`enabled_accessibility_services=com.vuzix.accessibilityservice/.AccessibilitySpeechInput`、`accessibility_enabled=1`；WearEdge 页面出现数字气泡：`3=Capture Camera2 JPEG`、`4=Upload To Jetson`、`5=Check Gateway`、`6=Audit Recent`。语音 `three` 被识别为 `3`，触发 Camera2 JPEG 捕获，页面显示 `Captured Camera2 JPEG 1280x720: 100 KB`，并使 `Upload To Jetson` 变为可用；语音 `four` 触发 upload 按钮路径，因当前 app 会话未输入 demo token，停在预期本地校验 `Gateway URL and demo token are required.`。 |
| 结论 | M400 的系统级语音控制可以驱动 WearEdge M400 App 的现有按钮，不需要新增 Gateway API/schema。当前可把 `Hello Vuzix` + 数字气泡视为第一版 hands-free 操作路径：用户可语音触发拍照，也可语音进入上传按钮路径。 |
| 风险边界 | 该测试验证的是系统语音气泡操作，不是生产级自定义语音语法；尚未实现 `capture frame`、`upload to Jetson`、`check gateway` 这类 WearEdge 专属短语；由于当前 app 会话未重新输入 demo token，本次没有完成“语音触发真实上传推理”的第二次 full-chain。下一步应加入安全持久配置/预配置 token、M400 佩戴姿态语音命中率测试，以及自定义命令或快捷流程，避免现场编辑文本字段。 |

相关证据文件：

- `docs/test-log-history.md`
- `docs/poc-results/m400-voice-control-2026-05-18/evidence-manifest.md`
- `docs/poc-results/m400-voice-control-2026-05-18/m400-voice-after-tts-command-list.png`
- `docs/poc-results/m400-voice-control-2026-05-18/m400-voice-number-bubbles-before-three.png`
- `docs/poc-results/m400-voice-control-2026-05-18/m400-voice-after-say-three.png`
- `docs/poc-results/m400-voice-control-2026-05-18/m400-voice-upload-bubbles-before-four.png`
- `docs/poc-results/m400-voice-control-2026-05-18/m400-voice-after-say-four-upload-local-check.png`

## HW-2026-05-18-02: PB551 Same-Day M400 Debug Runtime Observation

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-18 |
| 假设 | M400 实物全链路调试日的混合负载，包含 Jetson 开机、服务修复、模型恢复、Wi-Fi/Gateway 调试、M400 上传推理、长时间待机和后续网络排障，能够代表现场调试日的真实随身算力盒功耗区间。 |
| 测试 | Jetson 从上午开机测试开始持续运行到 16:02 CST，中途未手动关机；用户观察移动电源剩余电量为 34%。上午服务调试日志显示 10:41:41 CST 时系统 `up 16 min`，反推本轮开机约为 10:25 CST；按 10:25 到 16:02 计算，持续约 5 小时 37 分钟。 |
| 证据 | PB551 额定能量按 `docs/hardware-baseline.json` 记录为 72Wh；若按开机测试开始时为 100% 估算，到 16:02 剩余 34%，消耗 66 个百分点，折算约 `72Wh * 0.66 = 47.52Wh`；持续时间约 5.62h，反推平均功耗约 `47.52Wh / 5.62h = 8.46W`。剩余 34% 约等于 24.48Wh，按同一平均功耗估算理论剩余约 2.9h。路由器断电导致 Windows 到 Jetson LAN 不可达，但这属于网络基础设施中断，不等同于 Jetson 掉电。 |
| 结论 | PB551 + 20V trigger 方案不仅能跑 60 分钟巡检，也能支撑半天级别的 M400 实物调试日混合负载。当前观察下，WearEdge Jetson 算力盒在该负载形态下平均功耗约 8.5W，符合前次 36%->24% 低电量 60 分钟巡检反推的约 9.0W 区间。 |
| 风险边界 | 该估算依赖移动电源百分比显示和“开机时满电”假设，百分比曲线可能非线性；路由器断电后无法从 Windows 实时拉取 Jetson `uptime`、`dmesg` 或原始上传图确认，所以应在 Jetson 重新联网后补充 `uptime`、`last -x reboot`、`dmesg` 和 battery timestamp 证据。实际可用剩余时间应保守低于 2.9h，建议现场按 2.0-2.5h 规划安全余量。 |

相关证据文件：

- `docs/hardware-baseline.json`
- `docs/hardware-milestones.md`
- 待补 Jetson 复联网后证据：`uptime`、`last -x reboot`、`dmesg`

## HW-2026-05-18-01: Vuzix M400 Real-Device Full-Chain Validation

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-18 |
| 假设 | 真实 Vuzix M400 可以作为 WearEdge 的第一现场采集端：通过 Camera2 采集现场 JPEG，经同一 Wi-Fi 上传到 Jetson Gateway，由本地 Gemma 4 E2B 多模态模型完成 `maintenance` Agent 推理，并在 M400 端看到结果；同一次请求还应能通过 M400 `Audit Recent` 匹配同一个 `request_id`。 |
| 测试 | M400 通过 C-C 直接连接 Windows 进行 ADB 调试，避免移动电源 USB-C 口不支持数据透传的问题；启用/确认 M400 Wi-Fi 后连接到与 Jetson 相同网络；M400 App 配置 Gateway `http://192.168.0.155:8081`、`device_id=m400-demo-01`、`capture_mode=camera2-manual-trigger`、`analysis_mode=maintenance`；执行 `Check Gateway`、`Capture Camera2 JPEG`、`Upload To Jetson`、`Audit Recent`。Jetson 侧在测试前从备份恢复丢失的 Gemma 4 E2B GGUF 与 mmproj 文件到 NVMe，并恢复 `/home/ryn/WearEdge-Pro/models/gemma4-e2b` symlink。 |
| 证据 | M400 ADB 识别为 `Vuzix_M400 / M005043620`；M400 Wi-Fi IP 观察为 `192.168.0.159`，Jetson Gateway 为 `192.168.0.155:8081`；Jetson `wearedge-llama.service` active 且 `llama-server` 监听 `0.0.0.0:8080`，`wearedge-gateway.service` active 且 FastAPI 监听 `0.0.0.0:8081`；模型恢复后 `/v1/models` 返回 `gemma-4-E2B-it-Q4_K_S.gguf`。M400 端 `Check Gateway` 成功，Camera2 显示 `JPEG 1280x720`，上传返回 `ok=true`、`request_id=e30eb8d0a20d441dba5b0b5f849351e1`、`latency_ms=44907`、`saved_path=/mnt/nvme/wearedge/uploads/1779077307340.jpg`、`contract.ok=true`、`audit.logged=true`。M400 `Audit Recent` 显示 `audit.ok=true`、`audit.enabled=true`、`latest_request_id=e30eb8d0a20d441dba5b0b5f849351e1`、`last_inference_request_id=e30eb8d0a20d441dba5b0b5f849351e1`、`request_id_matched=true`。 |
| 结论 | WearEdge 已跑通真实 M400 实物闭环：M400 Camera2 采图 -> Wi-Fi -> Jetson Gateway -> 本地 llama.cpp/Gemma 4 E2B 多模态推理 -> structured maintenance action -> M400 显示结果 -> M400 Audit Recent 同 request_id 追溯。这是项目从“Jetson + 模拟图片/客户端”进入“真实头戴采集端 + 真实边缘推理盒子”的硬件里程碑。 |
| 风险边界 | 该测试证明一次真实 M400 maintenance 拍照上传推理闭环，不等于完成生产 UI、语音优先操作、离线配网体验、佩戴姿态下长时间可用性、弱网恢复、批量设备管理或机器级维修建议授权。当前推理结果正确触发 `maintenance_identification_required`，因为图像未包含可信机器身份、遥测历史或维护 KB 阈值证据；后续需要接入资产牌照片、HMI/温度表细节、Telemetry/CMMS/Manual KB 后才能给出机器特定建议。 |

时间线与截图证据：

| 时间 | 事件 | 证据 |
| --- | --- | --- |
| 2026-05-18 10:41 CST | Jetson 服务启动失败定位：`run_llama_server.sh` 与 `run_fastapi.sh` 权限导致 systemd `203/EXEC`。 | `/home/ryn/wearedge-m400-service-debug-20260518-104141.log` |
| 2026-05-18 10:50 CST 左右 | `git pull --ff-only` 拉取脚本可执行位修复，`chmod +x scripts/*.sh` 后 Gateway 恢复，`:8081/healthz` 成功；llama 仍因模型文件缺失继续重启。 | 终端输出；`wearedge-gateway.service` active |
| 2026-05-18 11:41 CST | 定位 llama 失败原因为缺少 `/home/ryn/WearEdge-Pro/models/gemma4-e2b/gemma-4-E2B-it-Q4_K_S.gguf`。 | `journalctl -u wearedge-llama.service` |
| 2026-05-18 11:51 CST 左右 | 从 Jetson worktree backup 恢复 `gemma-4-E2B-it-Q4_K_S.gguf` 与 `mmproj-F16.gguf` 到 `/mnt/nvme/models/gemma4-e2b`，恢复 symlink；8080 `/v1/models` 成功。 | 终端输出；模型 SHA256：`0a2fac16...0c99` 与 `140be8d...15fa` |
| 2026-05-18 12:08:27 CST | M400 `Upload To Jetson` 请求被 Gateway 接收，`frame_ts=2026-05-18T04:08:27Z`，开始 real-device maintenance 推理。 | `received_at=2026-05-18T04:08:27.340251Z` |
| 2026-05-18 12:09:12 CST 左右 | 模型推理完成，`latency_ms=44907`，生成 maintenance action card、follow-up plan、runtime stream 33 events，上传图保存到 NVMe。 | `/mnt/nvme/wearedge/uploads/1779077307340.jpg` |
| 2026-05-18 12:11:33 CST | M400 上传结果页截图留存，页面可见 `request_id`、`analysis_mode=maintenance`、`latency_ms=44907`、`jpeg_size=1280x720` 与完整 JSON 调试信息。 | `docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-after-upload2.png` |
| 2026-05-18 12:13:40 CST | M400 `Audit Recent` 结果截图留存，页面可见 `audit.ok=true`、`audit.enabled=true`、`latest_request_id`、`last_inference_request_id`、`request_id_matched=true`。 | `docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-audit-details.png` |
| 2026-05-18 12:13:59 CST | Windows 侧拉取 `/v1/audit/recent?limit=1` JSON 留底，保存结构化审计证据。 | `docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-audit-recent-latest.json` |
| 2026-05-18 16:17:46 CST | Jetson 复联网后，从 `/mnt/nvme/wearedge/uploads/1779077307340.jpg` 拉取 raw 上传 JPEG 到仓库证据目录，作为本地保存的原始采集图快照。 | `docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-captured-frame-1779077307340.jpg`；SHA256 `1EEF797D78A7C6F7EABB4A7FA922715CF8076A7418B07BC2830E02D208BD867C` |

相关证据文件：

- `docs/test-log-history.md`
- `docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-to-jetson-lao-shi-fu-process-report.md`
- `docs/poc-results/m400-real-device-full-chain-2026-05-18/performance-summary.json`
- `docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-after-upload2.png`
- `docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-audit-details.png`
- `docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-audit-recent-latest.json`
- `docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-captured-frame-1779077307340.jpg`
- Jetson raw 上传图原始路径：`/mnt/nvme/wearedge/uploads/1779077307340.jpg`

## HW-2026-05-15-06: PB551 Low-Battery 60-Minute Patrol Validation

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-15 |
| 假设 | PB551 在 36% 起始电量的低电量段仍可维持 20V PD 输出，不发生降档、瞬断、服务退出、NVMe reset、热降频或推理网关异常。 |
| 测试 | 使用 PB551 供电运行 `pb551-patrol-60min-lowbat36`：1 次 text-health，2 次 warm-up 图片请求，12 轮 patrol 图片请求；patrol 请求按 maintenance、WI、IQC 轮换，每轮间隔 300 秒。测试通过 `nohup` 后台运行，避免 SSH 会话中断影响测试进程。 |
| 证据 | Run ID: `pb551-patrol-60min-lowbat36-20260515-195048`；起始电量 36%，结束电量 24%，约 57.65 分钟消耗 12 个百分点，折算约 8.64Wh，平均约 9.0W。`summary.jsonl` 共 15 行，符合 1 次 text-health、2 次 warm-up、12 次 patrol。全部请求 `HTTP 200`，`contract_ok=true`，`audit=true`。maintenance 延迟约 5.5-5.8s，WI 约 4.2-4.5s，IQC 约 3.9-4.3s。结束后 `wearedge-llama.service` 与 `wearedge-gateway.service` 均为 active，`/healthz` ok。21:03 CST 手动 `dmesg` 未观察到 undervoltage、NVMe reset、thermal throttle、OOM 或异常 shutdown，`last -x reboot` 显示 15:06 开机仍在运行。 |
| 结论 | PB551 接线方案通过 36% 起始电量的 60 分钟低电量段 WearEdge 巡检。当前 PoC 可以把该方案视为短现场巡检可行的随身算力供电候选。 |
| 风险边界 | 电量百分比来自移动电源显示，存在量化误差；尚未验证 20% 以下的 PD 降档行为、线缆扰动、背负固定、热堆积、满负载同时推理与 NVMe 写入。该测试仍不构成量产电源设计认证或本安防爆认证。 |

相关证据文件：

- `scripts/pb551_patrol_stress_check.sh`
- `docs/hardware-baseline.json`
- Jetson 原始日志：`/home/ryn/wearedge-patrol-stress/pb551-patrol-60min-lowbat36-20260515-195048/`

## HW-2026-05-15-05: PB551 Patrol Stress Validation

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-15 |
| 假设 | 20 分钟级别的轻巡检压力可以暴露移动供电下常见的短时问题，例如 PD 降档、瞬断、服务退出、NVMe reset、热降频或网关异常。 |
| 测试 | 使用 PB551 供电运行 `pb551-patrol-20min`：1 次 text-health，2 次 warm-up 图片请求，6 轮 patrol 图片请求；patrol 请求按 maintenance、WI、IQC 轮换，每轮间隔 180 秒。 |
| 证据 | Run ID: `pb551-patrol-20min-20260515-155544`；所有请求均 `HTTP 200`。请求耗时：text-health 0.78s，warm maintenance 6.04s，warm IQC 4.25s，6 轮 patrol 为 6.05s、4.52s、4.06s、5.57s、4.34s、4.30s。结束后 `wearedge-llama.service` 和 `wearedge-gateway.service` 均为 active，`/healthz` ok，内核日志未观察到 undervoltage、NVMe reset、thermal throttle、OOM 或异常 shutdown。 |
| 结论 | PB551 接线方案通过约 20 分钟 WearEdge 巡检式轻压测。当前 PoC 可以把该移动供电方案作为可穿戴/随身算力盒子的工程候选方案。 |
| 风险边界 | 首版脚本的 `jq` 摘要提取存在 `label` 关键字 bug，但 HTTP 请求和模型响应均成功；首版脚本末尾 `sudo dmesg` 等待密码导致收尾拖长，不代表系统卡死。新版脚本已修复这两个工具层问题。后续仍需做 60-90 分钟、低电量段、线缆扰动和满负载余量测试。 |

相关证据文件：

- `scripts/pb551_patrol_stress_check.sh`
- `docs/hardware-baseline.json`
- Jetson 原始日志：`/home/ryn/wearedge-patrol-stress/pb551-patrol-20min-20260515-155544/`

## HW-2026-05-15-04: PB551 Staged Inference Validation

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-15 |
| 假设 | 移动电源不仅要能让 Jetson 启动，还要能支撑 WearEdge 的真实推理路径：llama-server、FastAPI gateway、图片上传、结构化 action card、审计日志和 NVMe 上传持久化。 |
| 测试 | 在 PB551 供电下运行文本健康推理、maintenance 单图推理、IQC 单图推理、WI 单图推理，以及 3 次 300 秒间隔的 maintenance 图片请求。 |
| 证据 | 文本健康推理 `HTTP 200`，29 tokens，生成约 15.18 token/s；3 个单图请求均 `HTTP 200`，maintenance 约 50.18s、IQC 约 46.17s、WI 约 44.36s；后续 3 次 maintenance 间隔请求均 `HTTP 200`，耗时约 45.32s、5.78s、5.96s；`contract_ok=true`，`audit=true`；推理后服务 active；内核日志未出现欠压、NVMe reset、thermal throttle、OOM 或异常 shutdown。 |
| 结论 | PB551 接线方案可以支撑 WearEdge 本地多模态推理闭环，不只是空载供电。模型、网关、上传持久化、action card 和审计链路都能在移动供电下工作。 |
| 风险边界 | 首轮图片请求耗时较高，后续重复图像请求明显变快，可能受模型 warm cache、prompt path 或视觉投影缓存影响；仍需用更多图像、不同模式、低电量段和更长时间巡检确认性能分布。当前 runtime visual token budget 仍为 560/560，存在后续延迟优化空间。 |

相关证据文件：

- `docs/hardware-baseline.json`
- `docs/sensing_compute_architecture.md`

## HW-2026-05-15-03: PB551 Mobile Power Wiring Feasibility

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-15 |
| 假设 | PB551 100W USB-C PD 移动电源可通过 20V PD trigger/adapter 输出到 5.5x2.5mm DC barrel，为 Jetson 算力盒子提供稳定供电，支撑 WearEdge PoC 的边缘推理负载。 |
| 测试 | 关闭 Jetson，切换到 PB551；冷启动后 SSH 登录；检查系统、NVMe、power mode、服务状态、`/healthz`；运行 120 秒 idle `tegrastats`；执行 256MiB NVMe 写入；检查 suspicious kernel logs。 |
| 证据 | PB551 供电后 Jetson 成功启动；系统为 Ubuntu 22.04.5 LTS / Linux 5.15.148-tegra；`nvpmodel -q` 为 `25W`；NVMe `WD_BLACK SN7100 2TB` 正常挂载；256MiB 写入约 661 MB/s；idle VDD_IN 稳定约 4.36-4.44W，启动/服务 warm-up 峰值约 6.29W；服务 active；`/healthz` ok；内核日志未出现欠压、NVMe reset、thermal throttle、OOM 或异常 shutdown。 |
| 结论 | **PB551 USB-C OUT 3 100W PD -> 20V PD trigger -> 5.5x2.5mm DC barrel -> Jetson DC input** 接线方案在当前 WearEdge PoC 上可行。它可以支撑 Jetson 启动、NVMe runtime storage 和基础服务运行。 |
| 风险边界 | 该结论是 PoC 可行性确认，不等于量产电源设计认证；需要确认插头中心正极、线缆额定电流、机械防松、弯折应力、保险保护、低电量降档行为和现场温度范围。该移动电源和接线方案不构成本安防爆方案。 |

相关证据文件：

- `docs/hardware-baseline.json`
- `docs/sensing_compute_architecture.md`
- `docs/core-bom.md`

## HW-2026-05-15-02: Original Power Baseline

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-15 |
| 假设 | 在切换到移动电源前，需要先用原装/原始 DC 供电建立对照基线，确认 NVMe、服务、健康检查和内核日志都处于正常状态。 |
| 测试 | 运行 baseline 脚本采集 uptime、`findmnt /mnt/nvme`、`df -h`、NVMe 写入 pulse、`systemctl` 状态、`/healthz`、`dmesg` suspicious log。 |
| 证据 | Jetson 处于 `25W` power mode；`/mnt/nvme` 正常挂载；256MiB NVMe 写入约 557 MB/s；`wearedge-llama.service` 与 `wearedge-gateway.service` 均为 active；`/healthz` 返回 ok；内核日志没有 undervoltage、NVMe reset、thermal throttle、OOM 或异常 shutdown。 |
| 结论 | 原始供电下系统处于可用、稳定的对照状态，可以作为 PB551 移动供电验证的基线。 |
| 风险边界 | 该基线是短时健康检查，不代表持续满载热稳定；仍需针对不同负载 profile 做更长时间对照。 |

相关证据文件：

- `scripts/power_baseline_check.sh`
- `docs/hardware-baseline.json`

## HW-2026-05-15-01: NVMe Runtime Storage Baseline

| 字段 | 记录 |
| --- | --- |
| 日期 | 2026-05-15 |
| 假设 | Jetson 系统盘只负责启动和控制面；2TB NVMe SSD 负责模型文件、上传缓存、审计日志、RAG 索引和测试数据，可降低 microSD 写入压力并提升模型运行稳定性。 |
| 测试 | 挂载 `/dev/nvme0n1p1` 到 `/mnt/nvme`，设置 ext4 label `WEAREDGE_NVME`，迁移 Gemma 4 E2B GGUF 与 mmproj 文件，更新 `.env` 的 `MODEL_DIR`、`WEAREDGE_UPLOAD_DIR`、`WEAREDGE_EVENT_LOG`，执行写入 smoke test。 |
| 证据 | `/mnt/nvme` 已挂载；容量约 1.8T；512MiB fsync write 约 576 MB/s；后续 256MiB 写入在原装电源下约 557 MB/s，在 PB551 下约 661 MB/s。模型路径为 `/mnt/nvme/models/gemma4-e2b`，上传路径为 `/mnt/nvme/wearedge/uploads`，审计事件路径为 `/mnt/nvme/wearedge/events/inference-events.jsonl`。 |
| 结论 | NVMe 已成为 WearEdge 的 workload/data plane；microSD 保持为 boot/control plane。这一分层适合后续模型、RAG、审计和现场样本沉淀。 |
| 风险边界 | 尚未做长时间高写入磨损测试；SSD 需要散热片或导热垫；客户现场需要确认固定方式、抗震、掉电恢复和数据保留策略。 |

相关证据文件：

- `docs/hardware-baseline.json`
- `docs/sensing_compute_architecture.md`
- Jetson 原始日志：`/home/ryn/wearedge-power-baseline-*.log`

## Evidence Index

| 类型 | 路径 / 提交 | 用途 |
| --- | --- | --- |
| 结构化硬件基线 | `docs/hardware-baseline.json` | 机器可读硬件事实、测试结果、请求耗时和结论 |
| 架构说明 | `docs/sensing_compute_architecture.md` | 外感采集端 + 随身算力盒子架构叙事 |
| BOM | `docs/core-bom.md` | 硬件与软件组件清单 |
| 电源 baseline 脚本 | `scripts/power_baseline_check.sh` | 原始电源与 PB551 baseline 复验 |
| 巡检压测脚本 | `scripts/pb551_patrol_stress_check.sh` | PB551 长一点的推理巡检复验 |
| 低电量 60 分钟原始日志 | `/home/ryn/wearedge-patrol-stress/pb551-patrol-60min-lowbat36-20260515-195048/` | 36% 到 24% 电量段的 60 分钟巡检证据 |
| Git 提交 | `285107b docs: add PB551 power validation artifacts` | 固化 PB551/NVMe 验证文档和脚本 |
| Git 提交 | `2d36bbb docs: record PB551 patrol stress result` | 固化 PB551 巡检结果和脚本修复 |
| Git 提交 | `536e026 scripts: avoid jq label variable in patrol check` | 固化 patrol 脚本 jq 兼容性修复 |

## Forward Validation Plan

| 下一项 | 目标 | 通过标准 |
| --- | --- | --- |
| 更低电量段观察 | 验证 PB551 在 20% 以下电量是否降档或瞬断 | Jetson 不掉电；PD 输出保持 20V；推理请求无异常 |
| 线缆扰动测试 | 验证背负/移动/插头受力场景 | 无重启、无服务退出、无 NVMe reset |
| 满负载余量测试 | 同时运行推理、NVMe 写入和 `tegrastats` 采样 | 无欠压、无 thermal throttle，VDD_IN 与温度趋势可接受 |
| 机械与安全设计 | 从 PoC 接线进入可携带样机 | 有固定支架、应力释放、极性标识、保险/保护策略和热设计记录 |
