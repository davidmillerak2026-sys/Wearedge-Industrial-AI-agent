# WearEdge Pro 技术证据链

本文档用于技术展示和工程复盘。它的目标不是重复产品愿景，而是把 WearEdge Pro 当前已经完成的工程事实讲清楚：真实边缘硬件、真实图片输入、真实本地模型推理、真实 HTTP 网关、真实结构化输出、真实自动验收。

## 一句话技术结论

WearEdge Pro 已在 Jetson Orin Nano 8GB 上跑通 Gemma 4 E2B 多模态图片推理，并把模型自然语言结果硬化为可被 M400、AR 显示、语音播报和工单系统直接消费的 `scene / risk / action` JSON 字段。

## 已验证链路

```text
Windows browser or smoke test image
  -> FastAPI Gateway :8081
  -> llama.cpp llama-server :8080
  -> Gemma 4 E2B Q4_K_S text model
  -> mmproj-F16 vision projector
  -> structured Scene / Risk / Action response
  -> output contract parser and repair loop
```

这条链路的关键点是：图片没有发送到云端大模型 API，而是在局域网内进入 Jetson，由 Jetson 本地完成视觉语言推理。

## 可复验硬证据

| 证据 | 结果 | 技术含义 |
| --- | --- | --- |
| Jetson 系统 | JetPack 6.2.1 / L4T R36.4.4 / Ubuntu 22.04 / aarch64 | 与官方 Orin Nano 当前生产主线对齐 |
| 模型部署 | `gemma-4-E2B-it-Q4_K_S.gguf` + `mmproj-F16.gguf` | 文本模型和视觉投影器在边缘节点本地加载 |
| 推理服务 | `llama-server` 监听 `0.0.0.0:8080` | 模型能力被封装成 OpenAI-compatible HTTP 接口 |
| 产品网关 | FastAPI 监听 `0.0.0.0:8081` | 后续可接 M400、AR、MES 或巡检系统 |
| 设备请求追踪 | `/v1/infer` 返回 `api_version`、`request_id`、`device` | 每次 M400 采图推理都可被日志、工单和演示脚本追踪 |
| 开机自启 | `wearedge-llama.service` 与 `wearedge-gateway.service` 均为 `enabled + active` | 不是临时终端 Demo，已具备设备化运行能力 |
| 输出契约 | `scene`、`risk`、`action` 三个字段稳定返回 | 下游系统不需要再解析自然语言段落 |
| 自动修正 | `contract.repaired` 可标记是否经历二次修正 | 模型不稳定时由后端兜底，提高工程可靠性 |
| 审计日志 | 可选 `WEAREDGE_EVENT_LOG` 记录 JSONL 推理事件 | 不保存图片，也能追踪每次设备请求和安全判断 |
| 自动验收 | `scripts/smoke_test.sh` 输出 `Gateway output contract passed.` | 现场可一条命令复验，不依赖人工肉眼判断 |

## 输出契约硬化

模型原始输出不适合直接交给工业系统，因为它可能出现长段落、缺字段、动作建议格式不稳定等问题。WearEdge Pro 在 FastAPI 网关层加入了输出契约硬化：

1. 网关统一注入稳定 Prompt，要求只返回三行：`Scene`、`Risk`、`Action`。
2. 后端解析模型输出，强制生成 `scene`、`risk`、`action` 三个独立字段。
3. 每个字段必须满足最少词数，目前规则为 `Each line must be more than 15 words.`，实现上对应至少 16 个词。
4. `Action` 必须以 `Stop`、`Inspect`、`Wear`、`Keep` 或 `Report` 开头。
5. 如果第一次模型输出不合格，后端会带原图和前一次回答自动修正一次。
6. 如果仍不合格，接口返回明确的契约错误，而不是把坏结果静默交给前端。

合格响应示例：

```json
{
  "ok": true,
  "answer": "- Scene: ...\n- Risk: ...\n- Action: ...",
  "scene": "...",
  "risk": "...",
  "action": "...",
  "contract": {
    "ok": true,
    "repaired": true,
    "min_words": 16,
    "violations": []
  }
}
```

这一步是项目从 PoC Demo 走向工程系统的关键：前端、M400、AR 端和工单系统可以直接读字段，不必猜测模型自然语言。

## 真实图片稳定性验证

在 Jetson 实机上使用同一张 3.17MB 工业风险图片连续运行三次网页推理：

| 轮次 | contract.ok | repaired | latency_ms | 说明 |
| --- | --- | --- | ---: | --- |
| 1 | true | true | 13205 | 第一次输出不完全合格，后端自动修正后通过 |
| 2 | true | false | 3503 | 模型首次输出即通过 |
| 3 | true | true | 10322 | 后端自动修正后通过 |

三次均返回：

```json
{
  "contract": {
    "ok": true,
    "violations": []
  }
}
```

这说明当前不是“偶然跑出一次好结果”，而是已经有了可重复、可观测、可验收的稳定接口行为。

## 自动验收命令

Jetson 上可使用固定测试图直接复验：

```bash
cd ~/WearEdge-Pro
source .env

TEST_IMAGE=/home/ryn/WearEdge-Pro/testdata/unsafety.jpeg \
DEMO_TOKEN="$DEMO_TOKEN" \
scripts/smoke_test.sh
```

通过时必须看到：

```text
llama-server text health passed.
Gateway output contract passed.
```

这两句分别证明：

- 模型服务本身可返回可见文本内容，而不是只返回 thinking。
- 网关图片推理返回了合格的 `scene/risk/action`，且 `contract.violations` 为空。

## 隐私优先审计日志

WearEdge Pro 支持可选 JSONL 审计日志。开启方式：

```bash
WEAREDGE_EVENT_LOG=/home/ryn/WearEdge-Pro/runtime/inference-events.jsonl
```

审计日志只记录 `request_id`、设备元数据、延迟、图片字节数、`scene/risk/action` 和契约状态，不保存图片二进制内容。这让项目同时具备两种能力：

- 对工业客户：生产画面默认不落盘，降低数据泄露风险。
- 对工程复盘：每次推理都有可复盘事件，可以追踪设备、请求和模型判断。

Jetson 实测审计日志验证：

```text
healthz.observability.event_log_enabled -> true
response.audit.logged                   -> true
response.request_id                     -> 5b33c68044d748dda77b2a5546968c8f
event_log.request_id                    -> 5b33c68044d748dda77b2a5546968c8f
event_log.saved_path                    -> null
event_log.image_bytes                   -> 3170693
event_log.latency_ms                    -> 9884
event_log.contract.ok                   -> true
event_log.contract.violations           -> []
```

这次实测说明：同一帧推理从 HTTP 响应到 JSONL 审计日志可以用同一个 `request_id` 串起来，同时 `saved_path: null` 证明默认没有保存图片文件。

为了便于现场展示，网关还提供受 token 保护的只读查询接口：

```text
GET /v1/audit/recent?limit=5
```

它返回最近 JSONL 审计事件，不暴露本地文件路径。`scripts/smoke_test.sh` 在 `audit.logged=true` 时会自动调用该接口，并校验最新事件的 `request_id` 与本次推理响应一致。

## 技术亮点

| 亮点 | 展示说法 |
| --- | --- |
| 真边缘推理 | 我们没有调用云端大模型 API，而是在 Jetson Orin Nano 8GB 上本地跑 Gemma 4 E2B 多模态模型。 |
| 真工业闭环 | 图片上传、模型推理、安全判断、结构化输出都在局域网边缘节点完成。 |
| 真工程接口 | 输出不是一段不可控文本，而是 API 级别的 `scene/risk/action` 字段。 |
| 真可靠性设计 | 模型输出不合格时，后端会自动修正一次，并暴露 `contract.repaired` 和 `violations`。 |
| 真设备化运行 | 通过 systemd 实现开机自启，重启后无需手动启动模型和网关。 |
| 真可追踪 | 每个设备请求都有 `request_id`，可选审计日志能记录结构化推理事件。 |
| 真可复验 | `smoke_test.sh` 可以一条命令复验健康检查、文本推理和图片输出契约。 |
| 真可穿戴客户端入口 | `clients/m400/android/` 已提供 Camera2 Android MVP，含网关预检和审计回查，并已在无真机条件下通过 `assembleDebug`。 |

## 当前边界和下一步

当前阶段已经完成 Jetson 端到端图片推理 PoC、输出契约硬化、审计日志和首版 M400 Camera2 Android MVP。Windows 本地已经完成无真机构建验证，`clients/m400/android` 可生成 debug APK：

```text
.\gradlew.bat :app:assembleDebug --no-daemon
BUILD SUCCESSFUL
app/build/outputs/apk/debug/app-debug.apk
```

下一步要把客户端从“可编译 Camera2 MVP”推进到真实 M400 设备验证：

1. 用 Android Studio 将 `clients/m400/android/` 安装到 M400，验证同一 Wi-Fi 下的 Camera2 拍照上传。
2. 用 M400 app 内置的 `Check Gateway` 和 `Audit Recent` 对齐 M400 端 `request_id` 和 Jetson 审计日志。
3. 确认 M400 可用分辨率、对焦曝光行为和连续采集稳定性。
4. 根据 `action` 做 AR 提示或骨传导语音播报。

这会把 WearEdge Pro 从“浏览器可演示”推进到“可穿戴设备现场工作流”。
