# WearEdge Pro 项目状态总览

本文档用于记录当前阶段的工程事实、已验证能力、剩余边界和下一步计划，便于后续迭代和交付复盘。

## 当前阶段结论

WearEdge Pro 已经从概念说明推进到可运行的边缘多模态 PoC：

```text
M400 / Web JPEG
  -> Jetson FastAPI Gateway
  -> llama.cpp llama-server
  -> Gemma 4 E2B + mmproj
  -> scene / risk / action
  -> optional audit log
```

核心闭环已经在 Jetson Orin Nano 8GB 上完成真实部署验证，并在 Windows 上完成 M400 Android MVP 的无真机构建验证。

## 当前硬件基线

- 边缘算力：Jetson Orin Nano 8GB Developer Kit，项目内简称 Jetson Nano 8GB。
- 本地存储：2TB M.2 NVMe SSD，挂载点 `/mnt/nvme`，用于模型文件、可选上传缓存、审计日志和本地部署产物。
- 机器可读清单：[`hardware-baseline.json`](hardware-baseline.json)。
- 硬件里程碑证据：[`hardware-milestones.md`](hardware-milestones.md)。

## 已完成能力

| 模块 | 当前状态 | 工程意义 |
| --- | --- | --- |
| Jetson 系统 | JetPack 6.2.1 / L4T R36.4.4，systemd 开机自启 | 重启后 `llama-server` 和 FastAPI 网关自动恢复 |
| 本地多模态模型 | Gemma 4 E2B GGUF + mmproj，llama.cpp CUDA 后端 | 不依赖云端大模型 API，生产图像留在现场 |
| FastAPI 网关 | `/v1/infer` 接收图片和设备元数据 | 统一接入 Web、M400、后续 AR 或巡检系统 |
| 输出契约 | 强制返回 `scene/risk/action`，不合格自动修正一次 | 下游系统直接读字段，避免从自然语言里猜结构 |
| 审计日志 | 可选 JSONL，`/v1/audit/recent` 受 token 保护 | 每帧推理可追踪，同时默认不保存原始图片 |
| 自动验收 | `scripts/smoke_test.sh` 检查健康、文本推理、图片契约、审计回查 | 演示前可一条命令复验 Jetson 链路 |
| M400 客户端 | Android Camera2 MVP，可编译 debug APK | 已具备应用内预览、JPEG 捕获、上传、预检和审计回查 |
| 网络排障 | 记录 Hugging Face、GitHub、Maven Central 可达性问题和镜像策略 | 把一次性部署经验沉淀为可复用流程 |

## 真实验证记录

Jetson 侧已经验证：

```text
systemctl is-active wearedge-llama.service  -> active
systemctl is-active wearedge-gateway.service -> active
curl http://127.0.0.1:8081/healthz           -> ok=true
scripts/smoke_test.sh                        -> Gateway output contract passed
```

M400 Android MVP 在 Windows 上已经验证：

```text
cd clients/m400/android
.\gradlew.bat :app:assembleDebug --no-daemon
BUILD SUCCESSFUL
app/build/outputs/apk/debug/app-debug.apk
```

## 技术优势表达

1. **端侧本地推理**：核心图片理解在 Jetson 上完成，适合工业现场数据不出厂的要求。
2. **结构化输出硬化**：模型输出被网关整理成稳定字段，解决“能回答但不能接系统”的问题。
3. **设备级追踪**：`request_id`、`device_id`、`frame_ts`、`capture_mode` 可以把每次 M400 采图和 Jetson 审计事件串起来。
4. **可穿戴客户端已启动**：Android MVP 已经从浏览器上传推进到 Camera2 拍照上传，并支持端上 health/audit 调试。
5. **可复验工程链路**：从 Jetson smoke test 到 Android debug APK 构建，都有命令和结果记录。

## 当前边界

- M400 真机尚未在本轮接入，因此 Camera2 可用分辨率、对焦曝光行为、横竖屏方向和实际佩戴体验仍需真机验证。
- 当前 Android MVP 是 debug 版本，尚未加入发布签名、自动版本号、崩溃上报或离线缓存。
- 端侧语音播报、AR 叠加显示、连续帧节流和后台保活尚未实现。
- 模型文件未提交到 Git 仓库，仓库只保留模型 manifest 和本地部署路径说明。

## 下一步建议

1. M400 真机到手后安装 `app-debug.apk`，验证 `Check Gateway`、Camera2 预览、JPEG 捕获、上传推理、`Audit Recent`。
2. 根据真机结果调整相机方向、分辨率选择和按钮布局。
3. 将 `action` 接入 M400 屏幕提示和骨传导耳机播报。
4. 增加连续采集模式：限频上传、超时取消、重复风险抑制。
5. 准备现场演示脚本：Jetson 服务状态、M400 端预检、实时拍照推理、审计日志对齐。
