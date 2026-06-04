# WearEdge Pro 核心软硬件 BOM

本文档基于 GitHub `main` 分支最新项目结构整理，目标是把 WearEdge Pro 当前可运行主线、已验证依赖、模型资产、客户端组件和下一阶段候选项收敛成一张工程 BOM。BOM 以“能支撑 M400 / Web 图片进入 Jetson 本地多模态推理，并输出可执行工业 Agent 动作”为边界。

当前主线：

```text
M400 / Web JPEG
  -> Jetson FastAPI Gateway :8081
  -> llama.cpp llama-server :8080
  -> Gemma 4 E2B Q4_K_S GGUF + mmproj-F16
  -> NVMe runtime storage /mnt/nvme
  -> output_contract / agent_loop / action_card
  -> audit log / M400 display / future AR or system integration
```

## 1. 核心硬件 BOM

| 层级 | 物料 / 设备 | 核心规格 | 数量 | 当前状态 | 项目用途 | 仓库证据 / 配置 |
| --- | --- | --- | ---: | --- | --- | --- |
| 边缘算力 | NVIDIA Jetson Orin Nano Developer Kit | 8GB 统一内存，aarch64，JetPack 6.2.1 / L4T R36.4.4 | 1 | 已作为当前 PoC 主线 | 随身边缘算力大脑，运行本地 VLM 推理、FastAPI 网关、审计日志 | `docs/hardware-baseline.json`、`docs/project-status.md`、`docs/technical_architecture.md` |
| 本地模型存储 | M.2 NVMe SSD | WD_BLACK SN7100 2TB，ext4，`WEAREDGE_NVME`，挂载点 `/mnt/nvme` | 1 | 已挂载并迁移模型 | 存放 GGUF 模型、mmproj、上传缓存、推理审计日志、RAG 索引、测试数据；512MiB fsync 写入实测约 576 MB/s | `docs/hardware-baseline.json`、`.env.example` |
| 启动存储 | microSD / 系统盘 | 约 128GB，`/dev/mmcblk0p1` 挂载 `/` | 1 | 已用于系统启动 | Jetson OS、项目代码、Python venv、systemd；不承载大模型和高频运行数据 | `docs/e2b-deployment-runbook.md`、`docs/hardware-baseline.json` |
| 可穿戴视觉端 | Vuzix M400 | Android 设备，Camera2 采图，局域网 HTTP 上传 | 1 | 客户端 MVP 已开发，真机验证待完成 | 采集第一视角图片，选择 agent 模式，显示 action / risk / request_id | `clients/m400/android/`、`docs/m400-inference-contract.md` |
| 开发工作站 | Windows PC | Core Ultra 9 185H，32GB RAM，RTX 3090 24GB，x64 Windows | 1 | 已用于下载模型、Android 构建、GitHub 维护 | 模型预下载、Android Studio 构建、资料整理和本地测试 | `docs/e2b-deployment-runbook.md`、`clients/m400/android/README.md` |
| 显示与调试 | 显示器 + DP/HDMI 转接 | Jetson 首次启动和本地桌面调试 | 1 套 | 已使用 | 首次系统设置、网络连接、终端调试 | 部署过程记录 |
| 网络 | Wi-Fi / LAN | M400、Windows、Jetson 同网段；Jetson 网关 `:8081` | 1 套 | 已验证局域网访问 | M400 / Web 上传图片，Windows SSH 调试 | `docs/network-troubleshooting.md`、`scripts/network_diagnostics.sh` |
| 音频交互 | 骨传导耳机 / 麦克风 | 语音播报和语音输入候选 | 1 套 | 下一阶段候选 | 播报 `action`，后续接入 30s 内语音输入 | `docs/technical_architecture.md` 的 Audio Fusion 规划 |
| 可穿戴移动供电 | PB551 100W USB-C PD 移动电源 | 72Wh，USB-C OUT 3 支持 20V/5A 100W；经 PD 20V trigger 转 5.5x2.5mm DC 圆口 | 1 | 已选型，待做供电稳定基线 | 给 Jetson 算力盒子供电，形成可穿戴移动部署；25W 平均功耗粗算约 2.4 小时 | `docs/sensing_compute_architecture.md`、`docs/hardware-baseline.json` |
| 供电与散热 | 原装 DC 电源、主动散热、SSD 散热片 | 原装电源用于基线对照；移动电源用于穿戴测试 | 1 套 | 建议固化 | 支撑长时间模型服务、SSD 写入和 Wi-Fi 外设稳定；先确认供电稳定再跑模型压力 | `docs/sensing_compute_architecture.md`、`docs/hardware-baseline.json` |

## 2. 边缘运行软件 BOM

| 层级 | 软件 / 组件 | 版本 / 配置 | 当前状态 | 项目用途 | 仓库证据 |
| --- | --- | --- | --- | --- | --- |
| 操作系统 | Ubuntu on Jetson | Ubuntu 22.04 / JetPack 6.2.1 / L4T R36.4.4 | 已验证 | Jetson 端系统底座 | `docs/project-status.md`、`docs/technical-evidence.md` |
| CUDA 工具链 | NVIDIA CUDA Toolkit | CUDA 12.6 路线，`nvcc` 用于 `llama.cpp` CUDA 编译 | 已验证 | GPU 加速 GGUF 推理 | `docs/e2b-deployment-runbook.md` |
| C/C++ 构建工具 | `build-essential`、`cmake`、`git`、`git-lfs` | 由 `scripts/setup_jetson.sh` 安装 | 已纳入脚本 | 编译 `llama.cpp`，拉取模型和依赖 | `scripts/setup_jetson.sh` |
| Python 运行时 | Python 3.10+ / venv | `.venv` 本地虚拟环境 | 已纳入脚本 | 运行 FastAPI 网关、测试脚本、验证工具 | `scripts/setup_jetson.sh` |
| HTTP 网关 | FastAPI | `fastapi>=0.115` | 已实装 | 提供 `/healthz`、`/v1/infer`、`/v1/audit/recent` | `jetson/requirements.txt`、`jetson/app.py` |
| ASGI 服务 | Uvicorn | `uvicorn[standard]>=0.30` | 已实装 | 启动 FastAPI 服务 | `jetson/requirements.txt`、`scripts/run_fastapi.sh` |
| 文件上传解析 | python-multipart | `python-multipart>=0.0.9` | 已实装 | 接收 JPEG/PNG multipart 上传 | `jetson/requirements.txt` |
| 模型下载工具 | Hugging Face Hub CLI | `huggingface_hub[hf_xet]` | 已纳入脚本；网络不稳时改手动传输 | 下载 GGUF 模型和 mmproj | `scripts/setup_jetson.sh`、`scripts/download_models.sh` |
| 本地推理服务 | `llama.cpp` / `llama-server` | OpenAI-compatible `/v1/chat/completions`，CUDA 后端 | 已验证 | 承载 Gemma 4 E2B 图片+文本推理 | `scripts/build_llama_cpp.sh`、`scripts/run_llama_server.sh` |
| 服务自启 | systemd | `wearedge-llama.service`、`wearedge-gateway.service` | 已有模板；实机按用户名调整 | 开机自启模型服务和网关 | `deploy/systemd/` |
| 网络诊断 | Shell diagnostics | `scripts/network_diagnostics.sh` | 已实装 | 判断 SSH、DNS、GitHub、HF、镜像访问问题 | `docs/network-troubleshooting.md` |

## 3. 模型与 AI 资产 BOM

| 类别 | 资产 | 当前规格 | 大小 / 校验 | 当前状态 | 用途 | 仓库证据 |
| --- | --- | --- | --- | --- | --- | --- |
| VLM 文本主模型 | Gemma 4 E2B IT GGUF | `gemma-4-E2B-it-Q4_K_S.gguf` | 3,043,932,288 bytes；SHA256 `0a2fac16...50c99` | 已验证，不提交普通 Git | Jetson 本地多模态推理主模型 | `docs/gemma4-e2b-model-manifest.lock` |
| 视觉投影器 | Gemma 4 mmproj | `mmproj-F16.gguf` | 985,654,080 bytes；SHA256 `140be8d7...215fa` | 已验证，不提交普通 Git | 把图像编码接入 Gemma 4 E2B | `docs/gemma4-e2b-model-manifest.lock` |
| 模型目录 | 本地模型目录 | 当前 Jetson `.env` 指向 `/mnt/nvme/models/gemma4-e2b`；旧路径 `/home/ryn/WearEdge-Pro/models/gemma4-e2b` 仅作为迁移前记录 | N/A | 已迁移到 NVMe | 存放 GGUF 大文件，避免 SD card 成为容量、速度和寿命瓶颈 | `.env.example`、`scripts/run_llama_server.sh`、`docs/hardware-baseline.json` |
| E4B 候选模型 | Gemma 4 E4B GGUF | `ggml-org/gemma-4-E4B-it-GGUF`，`*Q4_K_M*.gguf` | 待实测 | 候选路线，不是 8GB 首版主线 | 更高质量、多模态实验 | `docs/technical_architecture.md` |
| 企业推理候选 | NVIDIA NIM / vLLM | OpenAI-compatible endpoint | 待实测 | 后续企业化候选 | 音频融合、服务化运维、统一观测 | `docs/technical_architecture.md` |
| RAG 知识样例 | SOP / IQC / 维修日志 | Markdown + CSV | 小文件，已提交 | 已实装样例 | 老师傅、质检、SOP 问答检索 | `industrial-rag-agent/data/sample_knowledge/` |

## 4. Jetson 网关与 Agent 软件 BOM

| 模块 | 文件 / 包 | 当前功能 | 输入 | 输出 | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| FastAPI 网关 | `jetson/app.py` | 鉴权、图片上传、模式选择、调用模型、返回结构化 JSON | `prompt`、`image`、`analysis_mode`、设备元数据 | `answer`、结构化字段、`action_card`、`agent_loop`、`audit` | 已实装 |
| 模型请求客户端 | `jetson/llama_client.py` | 构造 OpenAI-compatible 图片+文本 payload | Prompt、图片 bytes、模型配置 | llama-server completion | 已实装 |
| 输出契约 | `jetson/output_contract.py` | 校验和解析不同 agent 的字段格式 | 模型自然语言输出 | `structured`、`violations` | 已实装 |
| Agent profile | `jetson/agent_profiles.py` | 定义五类 agent 和别名 | `analysis_mode` | 规范化 mode | 已实装 |
| Agent loop | `jetson/agent_loop.py` | 选择契约、做动作路由、生成 action card | mode + structured fields | `decision`、`action_card`、`agent_loop` | 已实装 |
| Agently 风格编排 | `jetson/agently_orchestrator.py` | 生成 trace / runtime stream / integration event | action card、request context | 可审计编排事件 | 已提交主线 |
| 证据计划 | `jetson/evidence_plan.py` | Agent 输出证据要求和保护栏 | mode / action | evidence plan | 已提交主线 |
| 五类 POC 验证 | `jetson/agent_poc_validation.py` | 固定场景验证五类 agent 确定性输出 | scenario fixture | PASS/FAIL matrix | 已提交主线 |
| 审计日志 | `jetson/audit_log.py` | JSONL 追加和最近事件读取 | response body | event log / recent events | 已实装 |
| 设备上下文 | `jetson/device_context.py` | 生成 `request_id`、清洗设备字段 | device_id、frame_ts 等 | response device block | 已实装 |
| 多模态预算 | `jetson/modality_pipeline.py` | 视觉 token 预算、音频融合路径规划 | mode、image size、audio seconds | env budget / fusion plan | 已提交主线 |

## 5. 五类工业 Agent BOM

| Agent | `analysis_mode` | 核心字段 | 典型动作通道 | 负责人 | 集成目标 | 当前 POC 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| Hazard Exposure | `hazard` | `scene`、`risk`、`action` | `stop_and_make_safe`、`inspect_area`、`ehs_report` | operator / EHS | `ehs_case`、`safety_observation` | 已验证 |
| Lao-shi-fu Predictive Maintenance | `maintenance` | `machine`、`symptom`、`maintenance_risk`、`evidence_needed`、`action` | `schedule_maintenance`、`maintenance_stop`、`condition_inspection` | maintenance planner / engineer | `maintenance_work_order`、`cmms_observation` | 已验证 |
| IQC Online Quality | `iqc` | `product`、`quality_risk`、`disposition`、`action` | `quality_hold`、`expand_inspection`、`stop_production`、`capa_request` | quality engineer / shift lead | `qms_quality_event` | 已验证 |
| General Work Instruction | `wi` | `machine`、`work_instruction`、`risk_control`、`action` | `guided_operation`、`wi_human_support`、`wi_stop` | operator / line lead | `wi_reference` | 已验证 |
| Changeover Guidance | `changeover` | `machine`、`sku`、`changeover_step`、`verification`、`action` | `changeover_verification`、`changeover_hold` | operator_quality / line lead | `changeover_checklist` | 已验证 |

## 6. M400 / Android 客户端 BOM

| 层级 | 组件 | 版本 / 配置 | 当前状态 | 用途 | 仓库证据 |
| --- | --- | --- | --- | --- | --- |
| Android 项目 | `clients/m400/android` | Kotlin + Android Gradle Project | 已可构建 debug APK | M400 客户端 MVP | `clients/m400/android/README.md` |
| Android SDK | compileSdk / targetSdk | compileSdk 35，targetSdk 35，minSdk 26 | 已配置 | 覆盖 M400 Android 运行环境 | `app/build.gradle.kts` |
| App 版本 | WearEdge M400 Demo | `versionName=0.2.0` | 已配置 | 当前客户端版本标识 | `app/build.gradle.kts` |
| HTTP 客户端 | OkHttp | `com.squareup.okhttp3:okhttp:4.12.0` | 已配置 | multipart 上传、health/audit 查询 | `app/build.gradle.kts` |
| 权限 | Android Manifest | `CAMERA`、`INTERNET`、`ACCESS_NETWORK_STATE` | 已配置 | Camera2 采图和局域网访问 Jetson | `AndroidManifest.xml` |
| 相机链路 | Camera2 + ImageReader | 16:9，目标不超过 1280x720 JPEG | MVP 已实装 | 应用内预览和单帧采集 | `MainActivity.kt` |
| 调试入口 | `Check Gateway` / `Audit Recent` | `/healthz`、`/v1/audit/recent` | 已实装 | M400 端现场诊断 | `WearEdgeM400Client.kt` |
| 构建镜像源 | Aliyun Maven + official fallback | google/public/gradle-plugin mirrors | 已配置 | 国内网络下提升 Gradle 同步成功率 | `settings.gradle.kts` |

## 7. API、配置与运行参数 BOM

| 类别 | 名称 | 默认值 / 形态 | 作用 | 当前状态 |
| --- | --- | --- | --- | --- |
| API | `GET /healthz` | 无需图片 | 健康检查、模型名、auth、observability、agent profiles | 已实装 |
| API | `POST /v1/infer` | multipart form | 图片推理主入口 | 已实装 |
| API | `GET /v1/audit/recent?limit=5` | Bearer token | 查询最近 JSONL 审计事件 | 已实装 |
| 鉴权 | `DEMO_TOKEN` | 必须替换默认值 | 演示访问口令，不是 Hugging Face token | 已实装 |
| 模型服务 URL | `LLAMA_BASE_URL` | `http://127.0.0.1:8080` | FastAPI 调 llama-server | 已配置 |
| 网关模型名 | `LLAMA_MODEL` | `gemma4` | OpenAI-compatible model 字段 | 已配置 |
| 图片大小 | `WEAREDGE_MAX_IMAGE_MB` | `4` | 上传图片大小保护 | 已配置 |
| Thinking | `WEAREDGE_ENABLE_THINKING` | `true` in example；实测可按需要关闭 | 控制 Gemma thinking 模板输出 | 已配置 |
| 输出长度 | `WEAREDGE_MAX_TOKENS` | `260` | 控制返回 token | 已配置 |
| 温度 | `WEAREDGE_TEMPERATURE` | `0.2` | 降低输出漂移 | 已配置 |
| 契约词数 | `WEAREDGE_CONTRACT_MIN_WORDS` | `16` | `more than 15 words` 的实现值 | 已配置 |
| 契约修复 | `WEAREDGE_CONTRACT_REPAIR_ENABLED` | `true` | 不合格时自动二次修正 | 已配置 |
| 上下文 | `LLAMA_CONTEXT` | `2048` | 控制 KV cache 和内存压力 | 已配置 |
| 视觉 token | `LLAMA_IMAGE_MIN_TOKENS/MAX_TOKENS` | `70/70` | 安全场景低延迟主线 | 已配置 |
| GPU layers | `LLAMA_NGL` | `99` | 尽可能走 CUDA | 已配置 |
| 批处理 | `LLAMA_BATCH_SIZE` / `LLAMA_UBATCH_SIZE` | `512 / 512` | 平衡吞吐与内存 | 已配置 |
| 上传缓存 | `WEAREDGE_UPLOAD_DIR` | 当前 Jetson `.env` 配置为 `/mnt/nvme/wearedge/uploads` | 调试时保存上传图片和外感采集样本 | 实机已启用 |
| 审计日志 | `WEAREDGE_EVENT_LOG` | 当前 Jetson `.env` 配置为 `/mnt/nvme/wearedge/events/inference-events.jsonl` | 隐私优先元数据审计 | 实机已启用 |

## 8. 开发、测试与验收 BOM

| 类型 | 工具 / 脚本 | 作用 | 当前状态 |
| --- | --- | --- | --- |
| Python 测试 | `pytest` | 单元测试和契约测试 | 已覆盖 Jetson 网关、RAG、agent loop |
| Jetson smoke test | `scripts/smoke_test.sh` | 健康检查、文本推理、图片契约、审计回查 | 已实装 |
| 五类 Agent POC | `scripts/validate_agent_pocs.py` | 验证 maintenance / iqc / changeover / wi / hazard 五类动作包 | 已实装 |
| Android 构建 | `gradlew.bat :app:assembleDebug` | 生成 M400 debug APK | 已验证无真机构建 |
| 模型下载 | `scripts/download_models.sh` | 拉取 GGUF 和 mmproj | 已实装；大文件可手动下载后传 Jetson |
| 依赖安装 | `scripts/setup_jetson.sh` | 系统包、venv、HF CLI、NVMe 目录 | 已实装 |
| 网络诊断 | `scripts/network_diagnostics.sh` | 路由、DNS、GitHub、HF、镜像诊断 | 已实装 |

## 9. 当前不纳入核心 BOM 的事项

| 项目 | 原因 | 后续处理 |
| --- | --- | --- |
| GGUF 模型二进制进 Git | 常规模型文件超过 GitHub 普通文件限制，且 Git LFS 配额受账号限制 | 继续使用 NVMe + manifest；必要时发布到 Hugging Face Hub 或 Git LFS |
| E4B / BF16 主线 | 8GB Orin Nano 首版稳定性和内存压力不确定 | 放到 RTX 3090 和更高规格 Jetson 做 A/B 测试 |
| 原生音频输入 | 当前 llama.cpp E2B Orin 路径不作为音频主线 | 后续走 vLLM/NIM 音频分支 |
| QMS / CMMS / MES 真系统连接器 | 当前 POC 只生成 action_card 和 integration_event，不直接写外部系统 | 下一阶段按客户系统逐个实现 connector |
| M400 真机量产行为 | 真机尚需验证方向、分辨率、对焦曝光、连续采集、佩戴体验 | M400 到手后按 checklist 验证 |

## 10. 最小可运行 BOM 组合

如果只要复现当前最小闭环，优先准备这些物料：

| 优先级 | 必需项 | 说明 |
| --- | --- | --- |
| P0 | Jetson Orin Nano 8GB + JetPack 6.2.1 | 边缘推理主机 |
| P0 | 2TB NVMe SSD 或足够空间的本地模型盘 | 存放模型、上传缓存、审计日志、RAG 索引和部署产物；SD card 只做系统启动和代码 |
| P0 | Gemma 4 E2B Q4_K_S GGUF + `mmproj-F16.gguf` | 当前已验证模型组合 |
| P0 | `llama.cpp` CUDA build | 本地模型服务 |
| P0 | FastAPI Gateway + `.env` | 网关、鉴权、契约和审计 |
| P0 | 一张固定 JPEG 测试图 | `smoke_test.sh` 验收 |
| P1 | Vuzix M400 + Android debug APK | 可穿戴采图入口 |
| P1 | 稳定 Wi-Fi / LAN | M400、Windows、Jetson 同网段 |
| P1 | 100W USB-C PD 移动电源 + 20V PD trigger 转 DC 圆口 | 可穿戴部署供电；跑模型前先做供电稳定基线 |
| P2 | 骨传导耳机 / 音频输入链路 | 后续语音播报和语音输入 |
| P2 | QMS / CMMS / MES connector | 后续从 action_card 进入企业系统 |
