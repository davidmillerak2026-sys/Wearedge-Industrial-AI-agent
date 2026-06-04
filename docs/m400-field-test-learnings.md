# M400 Field Test Learnings

本文记录 2026-05-19 真实 Vuzix M400 + Jetson 老师傅链路现场测试中的学习结论、证据和已采取的修复动作。

## 2026-05-19: Voice-First Lao-Shi-Fu Field Loop

### Learning 1: 操作者需要知道当前证据意图，而不是固定第几步

- 观察：语音命令能够触发拍照、上传和 Jetson session infer，但 M400 端只提示“Need next evidence”，没有把它翻译成清楚的现场步骤。
- 影响：操作者不知道当前为什么要拍这一张，也不知道是继续补视觉证据、进入操作者感官问答，还是已经可以给结论。
- 结论：M400 端必须把 Jetson 的 `missing_requested_evidence_ids` 转成现场可执行的当前证据意图，例如 `Problem photo`、`Next evidence: condition screen evidence`、`Operator sensory check`。不应显示 `Step X of 7`，因为现场诊断不是固定路线。
- 修复：Android App 的 Field 面板和语音提示改为动态证据轮次。每次 agent loop 返回后，只展示当前下一项证据意图，不再播报固定总步数。

### Learning 2: 一次要求的信息太多，用户不知道拍一张还是多张

- 观察：Jetson 老师傅 agent 会一次性返回多个 follow-up evidence request，这是正确的诊断边界，但直接展示给眼镜端会造成负担。
- 影响：操作者以为需要一次拍完所有照片，或者不知道一张照片应覆盖多少信息。
- 结论：M400 现场体验应该是“一次只上传一张现场图”，但这张图可以覆盖多个证据点。Jetson 从照片中筛选信息并更新 session，再动态决定哪些视觉缺口仍需补足。不能要求操作者一次拍完整个清单，也不能把一张照片强行绑定成一个证据槽。
- 修复：Jetson follow-up 计划改为返回当前剩余视觉缺口集合；M400 下一轮使用通用 `maintenance_followup_frame` 上传补充图，让 Jetson 判断一张新图覆盖了多少证据点。视觉证据足够后，再进入 operator sensory check。

### Learning 3: Vuzix Voice Command 页面会抢占前台

- 观察：测试过程中前台 Activity 多次切到 Vuzix speech command UI 或 launcher，操作者不清楚如何回到 WearEdge。
- 影响：WearEdge App 失焦后，用户会误以为链路卡住；Camera2 preview 也可能被关闭，需要重新拉起。
- 结论：必须提供一个明确的恢复口令，并让 App 在暂停状态也尽量继续监听项目内自定义短语。
- 修复：Android App 新增 `back to wearedge` / `return to wearedge` / `open wearedge` 语音短语，收到后把 WearEdge 主界面拉回前台；动态语音 receiver 改为在 Activity 生命周期内保持注册，避免一失焦就停止接收。

### Learning 4: 忙碌状态不能自动排队下一步

- 观察：Jetson 推理期间，继续说命令会出现 busy/ignored，现场听起来像失败。
- 2026-05-19 真实语音复测补充：Windows 扬声器触发 Vuzix 语音时，同一条 `hello wearedge` 可能被重复投递多次。如果 busy 状态把命令排队，App 会在 Jetson 返回后自动进入下一项证据采集，操作者还没重新取景就可能连拍。
- 影响：这会破坏“每一步由人确认取景”的维护证据链，尤其是润滑记录、维修记录、状态屏等证据不能被自动跳过。
- 结论：busy 状态只应解释“Jetson 正在运行，请等待下一条证据提示”，不能自动 queue 下一步。
- 修复：移除 busy 时的 `hello wearedge` 自动排队；`back to wearedge` 在 busy 时仍可恢复界面；其他命令提示等待。

### Learning 5: 产品路径应被描述成闭环，而不是按钮组合

- 现场闭环定义：
  1. App 启动并自动连接 Jetson。
  2. App 创建或恢复 maintenance session。
  3. 操作者从现场问题出发，框住当前最有信息量的画面，说 `hello wearedge`。
  4. M400 采集一张 WearEdge image 并上传到 Jetson session。
  5. Jetson 运行老师傅 agent loop，从当前照片和历史证据里筛选所有有效证据点。
  6. 如果证据不足，Jetson 返回当前仍缺的视觉证据点；如果视觉证据足够，返回 operator sensory check；如果证据足够形成边界结论，返回最终 action card。
  7. M400 播报当前下一项证据、逐题感官问答或最终结论。
  8. 重复 3-7，直到 Jetson 返回本轮证据足够。
- 当前验证状态：真实 M400 已经完成至少两轮 session 推进，missing evidence 从 `maintenance_asset_identity_photo` 推进到 `maintenance_condition_screen_photo`，证明闭环有效；本次修复重点是把闭环变成操作者能理解的现场体验。

### Learning 6: 近景和广角需要显式语音控制

- 观察：老师傅 agent 对同一设备会根据画面信息强弱给出不同结论。近景更容易读出状态屏数字，广角更容易判断设备周边、污染、泄漏、铭牌和上下文。
- 2026-05-19 真实语音复测证据：`zoom in` 被 Vuzix 识别后，M400 日志显示 `Camera zoom 1.3x`，随后旧版 field-assist 短语采集 `1.3x zoom` JPEG 并上传 Jetson。Jetson audit 中对应推理读到了 `Speed 1460 RPM`、`Load 82%`、`Current 18.6 A`、`RUNNING` 等画面信息，并继续要求补充润滑记录、维修记录和操作者感官检查。后续已拆分为 `capture photo` 执行证据采集。
- 影响：如果没有语音变焦，操作者需要手动移动身体或在小屏上找控件，现场体验不稳定。
- 修复：新增 `zoom in` / `zoom out` / `closer` / `wide view` 自定义语音短语；Camera2 preview 和 JPEG capture 使用同一个数字变焦 crop；`capture_mode` 会记录 zoom 倍率，便于 audit 区分近景和广角证据。

### Learning 7: session 清空必须同时清 UI、内存和持久化状态

- 观察：调试时如果只清空 UI 上的 session id，而内存中的 `latestMaintenanceSessionId` 仍保留旧值，下一次 evidence upload 会打到旧 session，Jetson 返回 `maintenance session not found`。
- 影响：用户看到拍照成功，却无法上传进入 agent loop，会误判为网络或相机问题。
- 结论：任何配置入口传入空 session，都必须同步清空内存和本地持久化 session。
- 修复：新增 `clearMaintenanceSession()`，在配置 intent 显式传入空 `session_id` 时清除 UI、内存和 SharedPreferences。

### Learning 8: restored session 必须先向 Jetson 验证

- 观察：2026-05-19 三轮真实语音回归的第一轮中，App 从本地 SharedPreferences 恢复了旧 `maintenance_session_id`，但 Jetson 侧 session 已因重启或服务状态变化失效。M400 能拍照并上传，但 Jetson 返回 `maintenance session not found`。
- 影响：操作者会看到相机和网络都像是正常的，实际 agent loop 没有继续推进；这类问题只靠清 UI 不够，因为旧 session 可能来自持久化状态。
- 结论：自动连接时不能盲目信任本地恢复的 session。每次恢复前必须调用 Jetson session trace 验证，验证失败就创建新 session。
- 修复：`autoConnectJetsonAndSession()` 恢复 session 前先调用 `traceMaintenanceSession(restoredSessionId)`。如果失败，记录 `restored_session_invalid`，并自动 `created_new_session`，现场操作者无需手动清 session。

### Learning 9: 结果返回后需要短暂冷却，避免延迟语音误触发下一步

- 观察：第二轮真实语音回归中，busy 状态已经不再 queue 命令，但 Vuzix voice service 仍可能把操作者在 Jetson 推理期间说过的 `hello wearedge` 延迟投递到 App。结果返回后约 2 秒内，App 已切到下一项证据，这条延迟命令会立即触发下一张照片。
- 影响：操作者还没重新取景，就可能从当前证据目标自动跳到下一个证据目标，破坏“每轮由人确认取景”的证据链。
- 结论：除了 busy 不排队，还需要在 Jetson 结果返回后设置短暂输入冷却窗口，让操作者有时间听完下一步并重新对准目标。
- 修复：Jetson 返回下一项证据或最终结论后，旧版 `FIELD_ASSIST` 命令进入 6 秒冷却。后续又将证据采集拆成 `capture photo`，补充证据阶段不再提示或依赖 wake phrase。

### Learning 10: `maintenance_operator_sensory_check` 必须是语音表单，不是照片步骤

- 观察：Jetson 老师傅 session 最后一项证据是 `maintenance_operator_sensory_check`，本质是操作者经验输入：异响、异味、发热、抖动、泄漏、开始时间。早期 M400 UI 仍把它提示成“拍一张照片”，导致操作者不知道应该继续拍照还是说出观察。
- 影响：最后一段不能形成真正的人机交互闭环。模型已经要求 operator sensory evidence，但 M400 没有把这个请求翻译成可执行的语音问答。
- 结论：感官检查必须由 M400 用语音逐项询问，操作者用短语回答，App 识别后作为 `capture_type=operator_note` 上传到 Jetson session，再自动补一张上下文帧触发最终 agent loop。
- 修复：Android App 新增 6 问有界语音表单：`unusual_noise`、`unusual_smell`、`felt_heat`、`felt_shaking`、`visible_leak`、`started_when`。支持回答 `yes`、`no`、`not sure`、`just now`、`today`、`recently`、`stable`、`unstable`。完成后上传结构化 `fields_json`，并自动拍一张 context frame 调用 Jetson 推理。
- 证据：2026-05-19 18:08:10-18:09:17 CST 干净进程回归中，M400 依次播报 6 个问题，每题只出现一次；18:08:24 自动捕获 final context frame；18:08:24 上传 operator voice evidence；18:09:17 Jetson 返回 `Conclusion ready. Operator voice evidence was accepted by Jetson.`。Jetson trace 记录 `evidence_type=maintenance_operator_sensory_check`、`capture_type=operator_note`、`fields={"unusual_noise":"no","unusual_smell":"no","felt_heat":"no","felt_shaking":"no","visible_leak":"no","started_when":"stable","input_method":"m400_voice"}`，最终 request 为 `c5ab47c0ba7142caaa4a1f588d202be2`，`follow_up_status=ready_for_human_confirmation`。

### Learning 11: 语音回答必须是自然一问一答，不能变成命令口令

- 观察：为了降低误识别，曾尝试让操作者回答 `answer no`、`answer stable` 这类前缀短语。现场判断后确认这不符合真实操作习惯；操作者应当听到 M400 问一句，然后自然回答 `yes`、`no`、`not sure`、`stable` 等。
- 影响：如果回答短语过于机器化，用户会感觉自己是在背命令，而不是和老师傅 agent 交互。若 M400 在未识别时反复播报长提示，也会造成“卡住/复读”的错觉。
- 结论：operator sensory check 的产品体验必须是 turn-taking：M400 一次只问当前一个问题，记录当前答案，短暂停顿，再问下一题。非答案语音命令如 `next`、`closer`、`session step` 在该阶段应被静默忽略，不能打断问答或触发拍照。
- 修复：移除 `answer ...` 前缀要求；问题提示恢复为自然回答。每次识别到答案后，UI 记录 `Recorded question N: value`，650 ms 后再播报下一题。回答阶段遇到非答案命令只更新静默状态，不再重复播报等待说明。
- 证据：2026-05-19 18:36:18-18:37:51 CST Windows 扬声器真实语音回归中，M400 识别 `hello wear edge` 后进入第 1 问；逐条记录 Q1-Q6，包括 `Recorded question 1: yes`、`Recorded question 2: no`、`Recorded question 3: no`、`Recorded question 4: no`、`Recorded question 5: no`，第 6 问识别 `just now` 后自动捕获 context frame，并向 Jetson 上传 operator voice evidence。测试中 Vuzix 仍将部分背景语音误识别为 `next`、`session step`，但 App 已按设计静默忽略；18:37:51 返回 `Conclusion ready. Operator voice evidence was accepted by Jetson.`。证据日志保存为 `docs/poc-results/m400-field-loop-continuation-20260519-173222/windows-voice-natural-one-question-complete-logcat.txt`。

### Learning 12: 连续跳题要用硬回合门处理，而不是假设 TTS 读了答案

- 观察：现场反馈确认 M400 并没有把答案选项读出来，但问题仍可能连续出现。这说明根因更接近 Vuzix speech service 的延迟识别事件或环境音残留，而不是 TTS 自己读 `yes/no`。
- 影响：如果 App 在问题刚开始播报时就接受答案事件，残留的 `yes/no/next` 可能直接推进到下一题，操作者会感觉 M400 没有等待回复。
- 结论：每个问题都需要硬回合门：问句开始后先锁定输入，等待播报窗口结束，再接受一个且仅一个答案；答案记录后再次锁定，直到下一题问句播完。
- 修复：新增 `operatorSensoryAcceptAnswerAfterMs` 门控。每次问句开始后 2.8 秒内的语音事件都会被忽略并记录为 early voice event；屏幕仍显示答案选项，但耳机只播报当前问题本身。
- 证据：2026-05-19 18:46:31 CST ADB 门控测试中，问题 1 开始后 0.3 秒注入 `wearedge_answer_no`，App 记录 `Question 1 is still being asked. Early voice event ignored.`；3.3 秒后再次注入 `wearedge_answer_no`，App 才记录 `Recorded question 1: no` 并进入问题 2。18:47:08 CST no-answer hold 测试中，只启动问题 1 并等待 8 秒，不注入答案，日志没有出现问题 2，证明不会自行连续跳题。

### Learning 13: M400 应是无状态采集终端，不能把流程交给系统相机

- 观察：2026-05-19 18:51-18:56 CST 5 分钟全链路监听中，App 停留在旧的 operator sensory question 1；操作者说 `Take a picture` 后，Vuzix 系统命令把前台切到 `org.codeaurora.snapcam`，WearEdge 没有继续上传到 Jetson，也没有进入新的 agent loop。
- 影响：这会让现场人员以为“拍照成功但上传失败”。根因不是 Jetson agent，而是 M400 前台和本地状态被系统相机/旧问题状态打断。
- 结论：WearEdge Pro 运行期间，除非操作者明确退出，否则应始终留在 WearEdge App。M400 只保存当前一帧和当前一题的临时状态；推理返回后清掉本地帧，最终结论后清掉本地 session。完整证据、上传图片、request、audit 和 agent trace 应保存在 Jetson。
- 修复：Android App 增加 `clearTransientM400Evidence()`：每次 Jetson 推理完成后清除 `latestJpeg`、pending capture、operator sensory 临时答案和按钮状态；最终 conclusion 后同步清空 local session/request。`onPause()` 增加短延迟前台恢复，防止系统相机或 launcher 长时间抢占；证据采集提示统一为 `capture photo`，并移除 `take photo` / `take picture` 等容易触发系统相机的自定义短语。
- 证据：监听目录 `docs/poc-results/m400-live-monitor/full-chain-20260519-185131` 记录了抢前台前后的前台 package、语音事件和缺失的 Jetson request；本修复专门针对该失效模式。

### Learning 14: 防跳出不能造成 Camera2 preview 反复重启

- 观察：2026-05-19 19:31-19:33 CST 监测时，M400 前台仍是 WearEdge，但日志中每约 1.4 秒出现一次 `Camera2 opened`、CameraService `disconnect`、再 `Camera2 ready`。未出现 `capturing one JPEG` 或 `evidence frame captured`，说明不是连续保存照片，而是 Camera2 preview 被反复 close/open。
- 影响：操作者会看到相机灯或预览闪动，误以为 App 在持续拍照；同时反复重连相机会增加功耗和不稳定性。
- 结论：前台保护和相机生命周期必须分开。短暂 pause/resume 或系统语音浮层不应释放相机；相机已经 active/opening 时，TextureView、focus、permission 回调都不能重复 open。
- 修复：`onPause()` 仅在 Activity 真正退出或配置变化时关闭 Camera2；普通短暂失焦只尝试把 WearEdge 拉回前台。新增 `startCameraIfNeeded()`，在 `onResume`、`onWindowFocusChanged`、`TextureView` 和权限回调中统一检查 `cameraDevice`、`cameraOpenInFlight`、`captureSession`，避免重复打开。
- 证据：修复后 2026-05-19 19:37 CST 25 秒 ADB 复测：`Camera2 opened count=1`、`Camera2 ready count=1`、`CameraService disconnect count=0`、`capturing JPEG count=0`、`evidence frame captured count=0`、`Camera2 start skipped count=0`。

### Learning 15: 证据循环必须由现场问题动态驱动，一张图可以覆盖多个证据点

- 观察：现场复盘确认，真实老师傅流程不是“按 Step 1 到 Step 7 依次采集”。操作者是遇到一个问题，先拍一张最相关的现场图；Jetson/E2B 应从这张图里筛选出已经获得的信息。若同一张图同时拍到了资产标识、HMI 数值和温度表，就应同时满足多个证据点。
- 影响：固定清单或“一张图只算一个证据点”的设计都会让操作者困惑：不知道到底要一次拍几张、是否必须按顺序拍、以及为什么明明一张图里有多个信息还要重复补拍。它还会把 operator sensory check 提前混在照片任务里，破坏“拍照 -> LLM 判断图中证据覆盖 -> 只补缺口”的人机协作节奏。
- 结论：M400 只显示当前阶段：`Problem photo`、`Follow-up photo`、`Operator sensory check` 或 `Conclusion`。Jetson 每轮从新照片中提取尽可能多的证据点，并返回当前仍缺的视觉缺口；视觉证据足够后，才由 M400 进入一问一答的操作者感官证据采集。
- 修复：Jetson `follow_up_plan` 改为返回 remaining visual evidence gaps；session 增加 satisfied evidence tracking；M400 补充图使用 `maintenance_followup_frame`，不再把照片绑定死为单一证据类型；现场 playbook 改为动态问题驱动流程。

### Learning 16: TTS 不能读出会触发自己的唤醒词

- 观察：2026-05-19 19:48 CST 安装后短测中，M400 前台保持 WearEdge、Camera2 只打开一次，但约 14 秒后出现一次 `Problem photo: capturing one JPEG`。日志没有相机反复重启，说明不是 Camera2 循环；更可能是 App TTS 播报了 `hello wearedge` 这类唤醒词，被 Vuzix speech service 当作真实语音命令。
- 影响：操作者没有说话时也可能自动拍一张，现场会误解为“App 一直在拍照”或“语音控制失控”。这会破坏每轮由人确认取景的证据链。
- 结论：屏幕可以显示准确命令，但耳机/TTS 不应读出会触发自己的 wake/return/zoom 短语。音频提示应使用“wake phrase”“return phrase”等中性表达。
- 修复：Android `speak()` 增加音频侧脱敏：将 `hello/hey/run wearedge` 替换为 `the wake phrase`，将 `back/return/open to wearedge` 替换为 `the return phrase`，将 `zoom in/out` 替换为非触发性的 zoom 描述。UI 文本仍保留原命令，方便人工查看。

### Learning 17: Vuzix wake 事件可能是空命令，不能静默丢弃

- 观察：2026-05-19 20:09 CST 实测中，操作者说了唤醒词后 WearEdge 没有进入下一步；随后手动进入 App，语音控制仍像“没有反应”。ADB 日志显示 WearEdge 已在前台并收到 `Ignoring empty voice command from vuzix-speech-sdk.`，说明 Vuzix speech service 把本次语音报告成 recognizer active/wake 事件，而不是带 `phrase` 的命令事件。
- 影响：操作者会以为“说了 hello wearedge 但 App 不听”。实际是 App 把空 wake 事件当作无效命令丢掉了；如果此时 Vuzix Voice Command 页面抢焦点，Android 还可能阻止后台 receiver 直接拉起 Activity。
- 结论：WearEdge 的现场语音应分两层处理：wake/return phrase 只负责把 App 拉回前台；证据采集 phrase 只负责采图上传。App 不在前台时，Android 可能限制后台启动 Activity，因此可靠现场流程仍是先打开 WearEdge，再全程留在 WearEdge。
- 修复：新增 `WearEdgeVoiceReceiver` 和 `ACTION_VOICE_LAUNCH_COMMAND`，Vuzix 自定义短语通过 `defineIntent` / `insertIntentPhrase` 显式路由回 WearEdge；wake phrase 同时注册为 Vuzix wake phrase；`MainActivity` 对 `RECOGNIZER_ACTIVE_BOOL_EXTRA=true` 的空事件做 1.6 秒延迟兜底，未收到后续命令时只返回 WearEdge，不采集证据。
- 证据：2026-05-19 20:30 CST 安装后日志显示 `Vuzix voice registered: wake=2, routed=24, fallback=0.`；ADB `am start --es command wearedge_zoom_in` 验证 `onNewIntent` 命令路径可执行，M400 前台保持 `com.wearedge.m400demo/.MainActivity`。后续版本输出改为 `Camera zoom ... Frame the target, then say capture photo.`

### Learning 18: 0.3.10 证明 App/Jetson 闭环正常，真实语音入口仍需按 Vuzix 机制调校

- 观察：2026-05-20 15:54-16:03 CST 继续检查时，M400 安装 `0.3.8` 后 Android `SpeechRecognizer.isRecognitionAvailable()` 返回 unavailable，因此 App 内普通 Android ASR 不能作为 `hello wearedge` 的前台兜底。随后安装 `0.3.9`，将 `hello wearedge` 从 Vuzix custom wake word 改成 Vuzix intent phrase，避免同一短语被 wake word 吞掉；Windows TTS 发出 `hello wearedge` 和 `Hello Vuzix -> hello wearedge` 仍未产生 Vuzix phrase callback。ADB deterministic voice adapter 注入 `wearedge_return_to_app` 则立即把 UI 从 `PHOTO | say hello` 切到 `PHOTO | capture photo`。
- 影响：这说明本轮“说了 hello wearedge 没反应”的主要风险不在 Jetson、Camera2 或 WearEdge App 状态机，而在当前实物环境的 M400 语音识别入口、音频命中率或 Vuzix phrase routing。继续在 App 里增加更多同义命令不会解决根因，反而会增加操作者困惑。
- 结论：现场产品主路径应继续保持简单：手动打开 WearEdge 后，屏幕只显示当前状态；`hello wearedge` 只进入 `capture photo` 准备态；`capture photo` 才执行拍照上传。工程验证可用 ADB voice adapter 的 `wearedge_return_to_app` 和 `wearedge_capture_frame` 证明 App/Jetson 闭环；真实语音验证必须单独调 Vuzix speech service 的短语触发可靠性。
- 修复：Android App 升级到 `0.3.10-m400-a11-quiet-voice-noise`。`hello wearedge` 仅作为 Vuzix intent/return phrase 注册，不再注册为 custom wake word；非 ADB 的 unknown voice event 改为静默忽略并写 log，避免复读 `I did not recognize that command` 打断操作者。README 更新 deterministic ADB 命令为 substitution 形式，避免 shell 空格转义导致 `hello wearedge` 被错误解析。
- 证据：2026-05-20 16:01:48 CST 0.3.10 启动后日志显示 `Vuzix voice registered: wake=0, return_intents=12, foreground=20, failed=0`、`SpeechRecognizer unavailable`；16:01:58 ADB 注入 `wearedge_return_to_app` 后 UI 为 `WE 0.3.10 A11 | PHOTO | capture photo | machine view`；16:02:29 ADB 注入 `wearedge_capture_frame` 后 M400 完成 `capturing one JPEG`、`evidence frame captured`、`adding one M400 image and running Jetson multi-evidence agent loop`；16:03:26 Jetson 返回 `Follow-up photo`，UI 为 `WE 0.3.10 A11 | FOLLOW-UP | capture photo | 5 gaps`。

### Learning 19: 拍照后必须先预览确认，不能自动上传

- 观察：用户现场确认后提出，`capture photo` 后应先看到刚采集的图片，只有操作者说 `accept` 或点击 Accept 才能上传 Jetson；如果说 `reject` / `retake`，应丢弃本地帧并重新取景。旧逻辑在 `onJpegCaptured()` 中直接调用 Jetson session step，操作者无法确认取景是否清晰、是否拍错对象。
- 影响：如果照片模糊、角度错、被系统相机/语音噪声误触发，错误证据会进入 Jetson session，后续 agent loop 会基于低质量证据继续追问，现场人员很难判断是模型问题还是取景问题。
- 结论：M400 必须作为“有确认门的证据采集终端”：`capture photo -> PREVIEW -> accept/reject -> Jetson`。确认前，`capture photo` 不应继续拍下一张；确认后，M400 清掉本地预览和临时帧，证据留在 Jetson。
- 修复：Android App 升级到 `0.3.11-m400-a11-photo-confirm`，新增 `CaptureConfirmation` 状态对象，将照片确认状态从 `MainActivity` 主流程中抽离；UI 增加预览图、Accept/Retake 按钮和状态栏 `PREVIEW | accept | or reject`；语音命令新增 `accept`、`reject`、`retake`；`take photo` / `take picture` 仍不注册，避免触发系统相机。
- 额外防护：测试发现预览后若立即触发 Vuzix listening，M400 可能把自己的 TTS 或语音服务残留误识别成 `accept`。因此确认监听延后到播报后，且每次监听启动后有短暂确认门；早到的 Vuzix `accept` 会被记录为 `Ignoring early photo confirmation command`，不会上传。
- 证据：2026-05-20 16:34 CST ADB 回归中，`wearedge_capture_frame` 后 UI 稳定停在 `WE 0.3.11 A11 | PREVIEW | accept | or reject`，显示 150px 预览图和 Accept/Retake。日志中 Vuzix 自动吐出的早到 `accept` 被忽略，24 秒后仍未上传。随后注入 `wearedge_reject_photo`，UI 返回 `PHOTO | capture photo | machine view`；重新拍照后注入 `wearedge_accept_photo`，才出现 `accepted. Sending this photo to Jetson` 和 `adding one M400 image and running Jetson multi-evidence agent loop`。

### Learning 20: 真实 M400 语音入口是 `Hello Vuzix`，不是裸 `hello wearedge`

- 观察：2026-05-20 16:48-16:55 CST 手动实测中，操作者手动进入 WearEdge App 后直接说 `hello wearedge` 没有反应，直接说 `capture photo` 也没有反应；说 `Hello Vuzix` 后，Vuzix 系统语音进入 listening 状态，再说 `capture photo` 可以触发 WearEdge Camera2 capture。预览后说 `accept` 可以上传到 Jetson，Jetson 返回下一轮 visual gaps。但上传后旧版 App 又回到 Vuzix launcher，后续 `capture photo` 不再进 WearEdge。
- 影响：如果 UI 继续提示 `hello wearedge`，操作者会按错误入口操作；如果 App 自己循环触发 idle hello listening，会把前台焦点交给 Vuzix launcher 或 voice command 页面，造成“上传成功后退出 App”的错觉。
- 结论：M400 现场主流程必须承认 Vuzix 系统唤醒机制：先说 `Hello Vuzix`，再说 WearEdge foreground command，例如 `capture photo`、`accept`、`reject`。`hello wearedge` 只能作为兼容的 return phrase，不能作为主要操作说明。
- 修复：Android App 升级到 `0.3.12-m400-a11-vuzix-wake`。启动和 Jetson follow-up 返回后自动进入 ready 状态，顶部状态改为 `vuzix > capture`；移除 not-busy 后的 idle hello keepalive，避免后台每 5 秒触发 Vuzix listening；Jetson 返回下一步或 conclusion 时调用 `bringWearEdgeToFront()` 保持 WearEdge 前台；TTS 将 `Hello Vuzix` 替换成非触发性的 `the Vuzix wake phrase`。
- 证据：2026-05-20 17:03-17:06 CST 安装后验证中，M400 前台保持 `com.wearedge.m400demo/.MainActivity`，日志无 `idle-hello` 循环；启动后 UI 显示 `WE 0.3.12 A11 | FOLLOW-UP | vuzix > capture | 3 gaps`，Jetson session 恢复后继续提示缺 `temperature gauge photo`、`lubrication record photo`、`recent maintenance record photo`。

### Learning 21: 上传等待不能黑屏，下一步语音不能每轮都要求 `Hello Vuzix`

- 观察：2026-05-20 现场佩戴测试中，操作者确认 `accept` 后，M400 上传 Jetson 期间媒体区域变成黑屏；Jetson 返回下一项证据后，UI/TTS 仍要求每次先说 `Hello Vuzix` 再说 `capture photo`。这让操作者无法判断照片是否正在上传，也把每轮交互变成“两段式唤醒”。
- 影响：黑屏会被误解为 App 卡死或相机退出；每轮重复系统唤醒会增加认知负担，也容易把操作者带回 Vuzix Voice Command 页面。
- 结论：`Hello Vuzix` 应作为恢复焦点或系统休眠后的兜底入口，而不是 WearEdge 前台流程的每一步必需动作。WearEdge 在前台、Jetson 返回下一步后，应自动触发下一轮监听，操作者只需要取景后说 `capture photo`。
- 修复：Android App 升级到 `0.3.16-m400-a11-preview-and-continuous-voice`。`accept` 后保留最后一张预览图作为 Jetson 上传等待画面；`shouldArmCaptureVoiceListening()` 打开自动监听门，只在 WearEdge 前台、非 busy、非预览确认、非 operator sensory 且当前证据为 maintenance visual evidence 时触发。所有下一步提示改为“frame target, then say capture photo”。
- 证据：本地构建通过并安装到 M400，`dumpsys package` 显示 `versionCode=18`、`versionName=0.3.16-m400-a11-preview-and-continuous-voice`、`lastUpdateTime=2026-05-20 17:38:37`。

### Learning 22: 结论必须留在 AR 顶部，operator sensory 要像自然问答

- 观察：2026-05-20 17:44-17:49 CST 佩戴实测中，M400 成功完成 `capture photo -> preview -> accept -> Jetson -> operator sensory 六问 -> context frame -> Jetson conclusion`，日志在 17:48:06 返回 `Conclusion ready`。但 AR 顶部随后显示为 `PHOTO | ready | machine view`，操作者看不到最终结论、priority 和 action；operator sensory 的 TTS 仍带有 “Question 1 of 6” 等机械前缀；最后一题操作者回答 `last week` 时词库尚未覆盖。
- 影响：这会让操作者不知道最后该做什么，也会把一问一答变得像表单播报；如果 `last week` 不能被记录，老师傅式时间上下文会丢失。
- 结论：最终 action card 是本轮最重要的现场信息，必须固定在 AR 顶部状态栏。operator sensory 屏幕可以显示 Q1/6，但耳机里只应自然发问当前一句。start-time 答案必须接受现场常用说法，如 `last week`。
- 修复：Android App 升级到 `0.3.17-m400-a11-conclusion-and-sensory`。`renderInferenceResult()` 保存最新 action/priority/channel；final conclusion 通过 `conclusionStatusMessage()` 固定显示在顶部两行；`askOperatorSensoryQuestion()` 的 spoken prompt 改为只读问题本身；start-time 词库新增 `yesterday`、`last week`；Camera2 capture 增加 JPEG orientation、自动白平衡和轻度 AE exposure compensation，预览文案明确“exact upload JPEG”。
- 证据：代码变更覆盖 `MainActivity.kt`、`WearEdgeVoiceAdapter.kt`、Android README 和本 learning 记录；下一轮实物回归应重点确认 final action 顶部可见、`last week` 被记录为 `last_week`、预览亮度/方向与 Jetson 上传 JPEG 一致。

### Learning 23: Final conclusion 后要进入可确认的跟进行动，不应静默失败

- 观察：2026-05-20 18:11 CST 佩戴对比测试证明 M400 到 Jetson 的视觉证据闭环可用，operator sensory 也记录了 `yes yes yes yes no last_week`。但最后一轮 context frame 曾出现 UI 处于 `PREVIEW | accept`、命令处理却提示 `No pending preview` 的状态错位；同时最终结论没有形成可确认的后续动作，`Connection reset` 也容易被误解为没有发生任何恢复。
- 影响：现场操作者不仅要看到结论，还要知道下一步可执行动作，例如通知主管、停机、安排计划停机。网络中断或 Jetson 重置不能静默吞掉，必须在 AR 屏和语音里说明是否可重试、怎样恢复。
- 结论：M400 端最终态应是一个全屏 action panel：先显示结论和风险，再逐个模拟外部 API 跟进行动，并要求操作者口头 `accept` 确认。`accept` 必须能打断冗长播报并进入下一轮；视觉证据完成后的 final analyzing 应由 App 自动补上下文帧，不再把操作者留在手动预览门里。
- 修复：Android App 升级到 `0.3.18-m400-a11-final-actions`。最终结论改为全屏显示；新增模拟 `sim.email.notify_supervisor`、`sim.mes.request_line_stop`、`sim.sap.plan_downtime` 三个跟进行动；`accept` 可确认预览或 final follow-up action；operator sensory 完成后进入 `FINAL ANALYZING` 并自动提交 context frame；`Connection reset` 会保留 retry preview 并提示 `accept` 重试或 `reject` 重拍。
- 证据：Windows 构建和安装通过，M400 `dumpsys package` 显示 `versionCode=20`、`versionName=0.3.18-m400-a11-final-actions`。现场日志证据保存在 `docs/poc-results/m400-worn-comparison-20260520-181119/`，核心索引包括 `m400-log-crawl-report-20260520-181119.md`、`field-test-summary-20260520-181119.md`、`voice-dialogue-timeline-20260520-181119.log`、`camera-upload-timeline-20260520-181119.log`、`jetson-agent-response-extract-20260520-181119.log` 和 `ui-visible-text-timeline-20260520-181119.md`。

## 2026-05-19 Regression Summary

- Run 01 `zoom-in-repeat-busy`：复现旧 session 失效问题。M400 成功识别 `zoom in` 并以 `1.3x zoom` 拍照，但 Jetson 返回 `maintenance session not found`。
- Run 01b `postfix-stale-recovery-zoom-in`：验证 session 恢复修复。App 自动发现旧 session 不可用并创建新 session，`1.3x zoom` 照片上传成功，Jetson 返回下一项 `asset identity photo` 证据请求。
- Run 02 `zoom-out-repeat-busy`：验证 busy 不排队，同时发现 Vuzix 延迟投递语音会在结果返回后误触发下一步。
- Run 03 `postfix-cooldown-force-stop`：验证冷却修复后的主路径。强制重启 App 后，`zoom in`、拍照、上传、Jetson agent loop、下一项证据播报均成功；未再出现 session 404、自动 queue 或结果后立即误拍。
- Run 04 `operator-sensory-voice-form`：验证最后一项 operator sensory evidence。App 通过语音完成 6 问，上传 `operator_note`，自动补 context frame，Jetson 判断本轮证据足够并进入 human confirmation。
- Run 05 `windows-natural-turn-taking-voice`：使用 Windows 扬声器真实发声验证自然一问一答。M400 完成 6 问感官检查、忽略非答案误识别、上传 operator voice evidence，并收到 Jetson conclusion。
- Run 06 `operator-sensory-turn-gate`：验证回合门。早到答案被忽略，延后答案才被记录；无答案等待时不会自动进入下一题。

## Operator Rule

现场操作者只需要记住这组小词库：

```text
capture photo
accept
reject / retake
back to wearedge
zoom in
zoom out
yes / no / not sure
just now / today / yesterday / last week / recently / stable / unstable
```

- `capture photo`：在 WearEdge 前台且下一步监听已打开时，采集当前 WearEdge 证据图并显示预览，不直接发送。
- `accept`：确认当前预览图并发送到 Jetson；在 final conclusion 页面确认当前模拟跟进行动。
- `reject` / `retake`：丢弃当前预览图，重新取景拍摄；在 final conclusion 页面跳过当前模拟跟进行动。
- `back to wearedge`：如果跳到 Vuzix Voice Command 页面、launcher 或其他页面，先说 `Hello Vuzix`，再用它回到 WearEdge。
- `zoom in` / `zoom out`：先调整视角，再说 `capture photo` 执行当前证据采集。
- `yes` / `no` / `not sure` / `just now` / `today` / `yesterday` / `last week` / `recently` / `stable` / `unstable`：只在 operator sensory check 期间回答 M400 的语音问题。

## Evidence Rule

每一轮只采集当前被要求的一项证据：

```text
one visual turn = one WearEdge image = zero, one, or many evidence points extracted by Jetson
```

不要一次拍完全部 follow-up checklist，也不要把一张图当成只能满足一个证据点。Jetson 会在每轮后根据已看到的内容告诉 M400 还缺哪些视觉证据；这些缺口可能减少多个，也可能直接进入感官问答或结论。

`maintenance_operator_sensory_check` 是语音证据项，不要求操作者手动拍照。它只应在视觉证据足够后出现；M400 会逐题询问，再自动补一张上下文帧给 Jetson 推理。
