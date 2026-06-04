# Gemma 4 E2B Jetson 端到端图片推理 PoC

目标：在 Jetson Orin Nano Developer Kit 8GB 上，用 `llama.cpp` CUDA 后端运行 Gemma 4 E2B 多模态模型，并通过 WearEdge Pro FastAPI 网关完成工业图片风险描述 PoC。

这次 PoC 的技术意义是：WearEdge Pro 已经不是云端大模型网页演示，而是在低功耗边缘硬件上完成了从图片输入、网关鉴权、模型推理到结构化安全建议输出的完整闭环。

完整技术证据链见 [`technical-evidence.md`](technical-evidence.md)。

## 成功样例

![WearEdge Pro safety PoC sample](assets/wearedge-poc-safety-sample.jpeg)

端到端验证链路：

```text
Windows browser
  -> Jetson FastAPI gateway :8081
  -> llama.cpp llama-server :8080
  -> Gemma 4 E2B text model + mmproj vision projector
  -> Scene / Risk / Action structured response
```

## 技术验证点

- Jetson 系统：JetPack 6.2.1 / L4T R36.4.4，Ubuntu 22.04，aarch64。
- 根分区：microSD 约 113GB，可用约 88GB。
- 模型：`gemma-4-E2B-it-Q4_K_S.gguf` + `mmproj-F16.gguf`。
- 模型清单：见 [`gemma4-e2b-model-manifest.lock`](gemma4-e2b-model-manifest.lock)，用于核对本地模型文件大小和 SHA256。
- 网关健康检查：`/healthz` 返回 `ok: true`。
- 图片推理：3.17MB JPEG 可以完成多模态分析，端到端延迟约 4.6-10.1 秒。
- 数据路径：图片留在局域网边缘节点内，不依赖云端推理 API。
- 接口形态：FastAPI `multipart/form-data` 上传图片，HTTP JSON 返回结果，便于接入 M400、AR 眼镜或巡检系统。
- 输出契约：结果收敛为 `Scene / Risk / Action` 三段，后续可以进入语音播报、AR 提示或工单字段。
- 设备级启动：已验证 `systemd` 开机自启，Jetson 重启后 `llama-server` 和 FastAPI 网关自动恢复。
- 契约硬化：网关已增加后端解析和自动修正，返回中会提供 `scene`、`risk`、`action` 三个独立字段。
- M400 接口准备：`/v1/infer` 已支持 `device_id`、`frame_ts`、`location_hint`、`capture_mode`，并返回 `request_id` 方便追踪每一帧推理。
- 审计日志：可选 `WEAREDGE_EVENT_LOG` 会记录 JSONL 推理事件；默认不保存图片，兼顾隐私和可复盘性。

## 样例推理结果

对应图片的原始 API 返回已归档为 [`poc-results/gemma4-e2b-safety-sample-result.json`](poc-results/gemma4-e2b-safety-sample-result.json)。

```json
{
  "ok": true,
  "answer": "- Scene: Dusty warehouse interior filled with stacked, disorganized industrial materials and debris.\n- Risk: Trip hazard from scattered debris on the concrete floor presents a significant fall danger.\n- Action: Stop immediately and carefully survey the immediate area for any loose objects or uneven surfaces.",
  "model": "gemma4",
  "latency_ms": 5824,
  "image_bytes": 3170693,
  "image_content_type": "image/jpeg",
  "saved_path": null
}
```

这个结果证明了三件事：

- 视觉侧：`mmproj-F16.gguf` 能把工业现场 JPEG 图像编码进 Gemma 4 E2B 推理链路。
- 语言侧：模型能从画面中抽取工业空间、杂物、地面散落物等风险上下文。
- 产品侧：网关返回结构化 JSON，前端、M400 或巡检系统可以直接消费。

演示时建议使用更短的展示版结果：

```text
- Scene: Dusty industrial storage area with scattered debris.
- Risk: Trip hazard from loose materials on floor.
- Action: Stop entry and inspect area with proper PPE.
```

## 开机自启验证

Jetson 执行 `sudo reboot` 后重新通过 SSH 登录，验证结果如下：

```text
systemctl is-enabled wearedge-llama.service    -> enabled
systemctl is-enabled wearedge-gateway.service  -> enabled
systemctl is-active wearedge-llama.service     -> active
systemctl is-active wearedge-gateway.service   -> active
ss -ltnp                                       -> 0.0.0.0:8080 and 0.0.0.0:8081 listening
curl http://127.0.0.1:8081/healthz             -> {"ok":true,...}
```

浏览器访问 `http://192.168.0.155:8081` 后再次上传同一张 3.17MB 样例图，原始返回已归档为 [`poc-results/gemma4-e2b-autostart-browser-result.json`](poc-results/gemma4-e2b-autostart-browser-result.json)。

```json
{
  "ok": true,
  "answer": "- Scene: Dusty attic space.\n- Risk: Falling debris hazard.\n- Action: Stop and secure loose items.",
  "model": "gemma4",
  "latency_ms": 8734,
  "image_bytes": 3170693,
  "image_content_type": "image/jpeg",
  "saved_path": null
}
```

这一步把 PoC 从“手动启动能跑”推进到了“设备重启后自动恢复并可直接演示”。这说明 WearEdge Pro 的 Jetson 节点已经具备基础设备化能力。

## 稳定 Prompt 模板

```text
Return exactly this format and nothing else:
- Scene: <one short phrase>
- Risk: <one short hazard>
- Action: <one safe next action>

Rules:
Scene must describe the place.
Risk must name a hazard.
Action must start with Stop, Inspect, Wear, Keep, or Report.
Each line must be more than 15 words.
Do not add any introduction.
```

当前生产提示词采用 `Each line must be more than 15 words.`。实测它比过短约束更容易让 Gemma 4 E2B 生成可解释、可展示的工业安全判断。

## 输出契约硬化

FastAPI 网关现在不再只原样返回模型文本，而是执行三步契约控制：

1. 网关会把用户 Prompt 统一补齐为 `Scene / Risk / Action` 输出契约，并把长度规则归一化为 `Each line must be more than 15 words.`。
2. 模型返回后，后端解析三行标签，强制生成 `scene`、`risk`、`action` 三个字段，同时检查每个字段至少 16 个词。
3. 如果第一次输出不合格，网关会带着原图和前一次回答自动重试一次修正；如果仍不合格，接口返回明确的 502 契约错误。

合格响应会同时保留展示用文本和机器可读字段：

```json
{
  "ok": true,
  "answer": "- Scene: ...\n- Risk: ...\n- Action: ...",
  "scene": "...",
  "risk": "...",
  "action": "...",
  "contract": {
    "ok": true,
    "repaired": false,
    "min_words": 16,
    "violations": []
  }
}
```

这一步让 PoC 从 Prompt Demo 往产品接口前进：前端、M400、AR 提示层或工单系统可以直接读字段，不必自己再从自然语言里猜结构。

真实 Jetson 图片推理连续验证结果：

| 轮次 | contract.ok | repaired | latency_ms | 结果 |
| --- | --- | --- | ---: | --- |
| 1 | true | true | 13205 | 自动修正后返回合格 `scene/risk/action` |
| 2 | true | false | 3503 | 首次生成即合格 |
| 3 | true | true | 10322 | 自动修正后返回合格 `scene/risk/action` |

三次均返回 `violations: []`，说明接口层已经能稳定输出机器可读 JSON，而不仅是依赖模型“看起来像”固定格式。

同日，自动验收脚本也已在 Jetson 上通过，终端输出包含：

```text
llama-server text health passed.
Gateway output contract passed.
```

这把人工网页测试进一步固化为可复现验收命令，便于现场快速证明系统状态。

## 审计日志实测

在 Jetson 上开启：

```bash
WEAREDGE_EVENT_LOG=/home/ryn/WearEdge-Pro/runtime/inference-events.jsonl
```

随后使用固定 3.17MB `unsafety.jpeg` 和 M400 模拟元数据运行 `scripts/smoke_test.sh`，返回：

```json
{
  "request_id": "5b33c68044d748dda77b2a5546968c8f",
  "device": {
    "device_id": "m400-demo-01",
    "location_hint": "demo-zone",
    "capture_mode": "manual-trigger"
  },
  "latency_ms": 9884,
  "contract": {
    "ok": true,
    "repaired": true,
    "violations": []
  },
  "audit": {
    "logged": true
  }
}
```

同一条 JSONL 审计事件中出现相同的 `request_id`，并记录：

```json
{
  "event_type": "inference.completed",
  "request_id": "5b33c68044d748dda77b2a5546968c8f",
  "image_bytes": 3170693,
  "latency_ms": 9884,
  "saved_path": null,
  "contract": {
    "ok": true,
    "violations": []
  }
}
```

这里的 `saved_path: null` 是一个重要工程点：系统保留可追踪的推理事件，但默认不保存原始图片，符合工业现场隐私优先原则。

## 项目技术优势表达

从技术角度，这次 PoC 可以支撑 WearEdge Pro 的四个优势：

| 技术点 | 证明内容 | 工程价值 |
| --- | --- | --- |
| 端侧多模态推理 | Jetson Orin Nano 8GB 本地运行 Gemma 4 E2B + mmproj | 不是云端套壳，是真正可落地的边缘 AI |
| 工业数据本地闭环 | 图片从浏览器进入 Jetson，在本地完成推理 | 适合工厂、能源、航空等敏感场景 |
| API 化工程接口 | FastAPI 网关把图片输入和模型输出封装成 HTTP 服务 | 后续可接 M400、AR、MES、巡检系统 |
| 结构化输出控制 | 输出固定为 `Scene / Risk / Action` | 可进入语音播报、工单字段和安全流程 |
| 设备化部署 | systemd 开机自启已通过重启验证 | 现场可直接开机演示，降低人工操作风险 |
| 输出契约硬化 | 后端强制解析字段，并在不合格时自动修正一次 | 从“看起来像结构化”升级到“接口真正可消费” |
| 设备请求追踪 | 响应包含 `api_version`、`request_id` 和 `device` 元数据 | 为 M400、AR 显示、日志归档和工单系统打基础 |
| 隐私优先审计 | 可选 JSONL 事件日志只存元数据和结构化判断，不存图片 | 便于复验和客户复盘，同时降低现场数据风险 |

## 遇到的问题与解决办法

| 问题 | 表现 | 解决办法 |
| --- | --- | --- |
| Jetson 初始系统不确定 | UEFI 显示 Jetson Orin Nano 相关启动信息 | 使用官方 JetPack 6.2.1 SD Card Image 重新烧录 128GB microSD，并完成首次启动 |
| 没有网线，手打命令太慢 | Jetson 本机终端逐字输入容易出错 | 让 Jetson 连 Wi-Fi，再从 Windows 用 SSH 登录，直接复制粘贴命令 |
| Hugging Face 网络不稳定 | `hf auth login`、`curl https://huggingface.co` 失败或超时 | 在 Windows 手动下载 GGUF 模型和 mmproj，再用 `scp` 传到 Jetson |
| Jetson 克隆 llama.cpp 失败 | GitHub clone 出现 HTTP2 / TLS 中断 | 在 Windows 下载 `llama.cpp` 压缩包，传到 Jetson 解压后本地编译 |
| CMake 找不到 CUDA 编译器 | `CMAKE_CUDA_COMPILER-NOTFOUND` | 设置 `PATH`、`LD_LIBRARY_PATH` 和 `CUDACXX=/usr/local/cuda/bin/nvcc`，并显式传入 `CMAKE_CUDA_COMPILER` |
| 启动脚本寻找错误模型目录 | 日志反复提示 `/mnt/nvme/models/gemma4-e2b` 不存在 | 在 `.env` 中改为 `/home/ryn/WearEdge-Pro/models/gemma4-e2b`，并用 `set -a; source .env; set +a` 导出变量 |
| 第一次图片回答为空 | llama-server 返回 200，但网关 `answer` 为空 | 设置 `WEAREDGE_ENABLE_THINKING=false`，避免 thinking 模板吞掉可见回答 |
| 输出格式不够稳定 | 有时返回长段落，有时缺少固定字段 | 收紧 Prompt，只允许 `Scene / Risk / Action` 三行，并限制 Action 的开头动词 |
| 浏览器接口 401 | FastAPI 日志显示 `POST /v1/infer 401 Unauthorized` | 使用本地 demo token；它不是 Hugging Face key，而是 WearEdge 网关自己的访问口令 |
| 服务依赖手动启动 | 重启后需要手动开两个终端启动模型和网关 | 写入 `wearedge-llama.service` 与 `wearedge-gateway.service`，并验证 `enabled + active` |
| 结构化输出只靠 Prompt | 前端拿到的是一整段文本，下游系统仍需自行解析 | 新增后端输出契约模块，解析 `scene/risk/action`，不合格时自动二次修正 |

## 当前结论

PoC 已经跑通：Jetson 能离线承载 Gemma 4 E2B 多模态推理，Windows 浏览器可通过 FastAPI 网关上传图片并得到结构化安全判断。项目已进一步完成 systemd 开机自启验证、输出契约硬化、M400 请求元数据契约和可选审计日志，Jetson 重启后服务会自动恢复，网关会返回机器可读的 `scene/risk/action` 字段。

这条工程链路已经具备清晰的演示价值：它把“可穿戴工业 AI Agent”的核心能力落到了真实边缘硬件和真实图片输入上。下一步应接入 M400 实时采图链路。
