# WearEdge Pro 技术架构白皮书

更新日期：2026-05-12

本文档记录 WearEdge Pro 在受限 Jetson 硬件上运行本地多模态模型的技术架构。重点说明算法科学家团队如何把模型压缩、运行时加速、长上下文、视觉 token 预算、音频融合和工业 Agent 输出契约组合成可复验的端侧系统。

## 一句话结论

WearEdge Pro 当前主线不是云端套壳，而是在 Jetson Orin Nano 8GB（项目内简称 Jetson Nano 8GB）和 2TB NVMe SSD 上，用 Gemma 4 E2B Q4 GGUF、`llama.cpp` CUDA 后端、Flash Attention、受控上下文长度、动态视觉 token 预算和结构化输出契约，把工业图片推理压缩到可以随身部署的边缘形态。

```text
M400 / Web JPEG
  -> FastAPI Gateway :8081
  -> Gemma 4 output contract prompt
  -> llama.cpp llama-server :8080
  -> Gemma 4 E2B Q4_K_S GGUF + mmproj-F16
  -> scene / risk / action or agent-specific structured fields
  -> optional privacy-preserving audit log
```

## 当前硬件边界

| 项目 | 当前基线 | 工程含义 |
| --- | --- | --- |
| 边缘算力 | Jetson Orin Nano 8GB Developer Kit | 首版 PoC 以 E2B 为稳定主线，E4B 作为更高规格 Jetson 的实验路线 |
| 本地存储 | 2TB M.2 NVMe SSD，挂载 `/mnt/nvme` | 存放 GGUF 模型、mmproj、可选上传缓存、审计日志和部署产物 |
| 功耗预算 | 25W 可演示，30W 以上更稳 | 视觉推理、SSD 峰值写入和 Wi-Fi 外设需要供电余量 |
| 运行系统 | JetPack 6.2.1 / L4T R36.4.4 | 与当前 Orin Nano 边缘 AI 工具链对齐 |

机器可读硬件清单见 [`hardware-baseline.json`](hardware-baseline.json)。

## 算法科学家团队压缩分工

| 团队角色 | 负责问题 | 当前落点 |
| --- | --- | --- |
| 模型压缩科学家 | 在 8GB 统一内存内装入可用多模态模型 | 选择 Gemma 4 E2B Q4_K_S GGUF，避免首版直接上 E4B/26B |
| 运行时加速科学家 | 把模型服务变成可启动、可复验、可自启的本地服务 | `llama.cpp` CUDA、`--flash-attn on`、`-ngl 99`、systemd |
| 多模态预算科学家 | 在速度与细节之间动态分配视觉 token | [`jetson/modality_pipeline.py`](../jetson/modality_pipeline.py) 的 `choose_visual_token_budget()` |
| 音频融合科学家 | 规划语音、图像、文本的统一输入路径 | [`jetson/modality_pipeline.py`](../jetson/modality_pipeline.py) 的 `plan_audio_fusion()` |
| 工业契约科学家 | 防止模型输出漂移，保障下游系统可读 | `jetson/output_contract.py`、`jetson/agent_loop.py` |
| 硬件稳定性科学家 | 控制功耗、温度、SSD 路径和部署复现 | `docs/hardware-baseline.json`、`scripts/setup_jetson.sh` |

## 端侧量化工具链

当前仓库实装的端侧量化链路是：

```text
Unsloth / GGUF artifact
  -> Hugging Face CLI download
  -> /mnt/nvme/models/gemma4-e2b
  -> llama.cpp llama-server
  -> FastAPI OpenAI-compatible request
```

对应文件：

| 文件 | 作用 |
| --- | --- |
| [`scripts/download_models.sh`](../scripts/download_models.sh) | 下载 `unsloth/gemma-4-E2B-it-GGUF`、`*Q4_K_S*.gguf` 和 `mmproj-F16.gguf` |
| [`scripts/run_llama_server.sh`](../scripts/run_llama_server.sh) | 启动本地 `llama-server`，设置上下文、Flash Attention、GPU layer、视觉 token 预算 |
| [`docs/gemma4-e2b-model-manifest.lock`](gemma4-e2b-model-manifest.lock) | 记录已验证模型文件大小和 SHA256 |
| [`jetson/llama_client.py`](../jetson/llama_client.py) | 构造 OpenAI-compatible 多模态请求 |

当前默认模型配置：

```bash
TEXT_REPO=unsloth/gemma-4-E2B-it-GGUF
TEXT_GLOB=*Q4_K_S*.gguf
MMPROJ_GLOB=mmproj-F16.gguf
MODEL_DIR=/mnt/nvme/models/gemma4-e2b
```

E4B 的定位是下一阶段实验项，不是 8GB Orin Nano 首版交付主线。更高规格 Jetson 可按 Jetson AI Lab 的 GGUF 路线测试：

```bash
TEXT_REPO=ggml-org/gemma-4-E4B-it-GGUF
TEXT_GLOB=*Q4_K_M*.gguf
```

NVIDIA NIM 在本项目中的定位是企业化推理服务候选，不是当前 8GB 原型机上的量化来源。当前原型机使用 `llama.cpp` 直接承载 GGUF；后续如果迁移到 NIM/vLLM，只需要让 `LLAMA_BASE_URL` 指向 NIM 或 vLLM 的 OpenAI-compatible `/v1/chat/completions` 服务，并复用 FastAPI 网关和输出契约。

## 加速调优参数

当前 `scripts/run_llama_server.sh` 的关键参数：

```bash
llama-server \
  -m "$TEXT_MODEL" \
  --mmproj "$MMPROJ_MODEL" \
  -c "${LLAMA_CONTEXT:-2048}" \
  --image-min-tokens "${LLAMA_IMAGE_MIN_TOKENS:-70}" \
  --image-max-tokens "${LLAMA_IMAGE_MAX_TOKENS:-70}" \
  --ubatch-size "${LLAMA_UBATCH_SIZE:-512}" \
  --batch-size "${LLAMA_BATCH_SIZE:-512}" \
  -ngl "${LLAMA_NGL:-99}" \
  --flash-attn on \
  --no-mmproj-offload \
  --jinja \
  -np "${LLAMA_PARALLEL:-1}"
```

调优含义：

| 参数 | 当前值 | 作用 |
| --- | ---: | --- |
| `LLAMA_CONTEXT` | 2048 | 首版演示控制 KV cache，避免长上下文把 8GB 内存吃满 |
| `LLAMA_IMAGE_MIN_TOKENS/MAX_TOKENS` | 70 | 工业安全场景优先低延迟，复杂质检/OCR 再提升 |
| `LLAMA_BATCH_SIZE` / `LLAMA_UBATCH_SIZE` | 512 | 控制吞吐与显存/统一内存压力 |
| `LLAMA_NGL` | 99 | 尽可能把 transformer 层放到 CUDA 路径 |
| `--flash-attn on` | 开启 | 降低注意力计算和显存压力 |
| `--no-mmproj-offload` | 开启 | 当前路径优先稳定加载，避免视觉 projector 与主模型同时抢占 GPU 内存 |
| `LLAMA_PARALLEL` | 1 | 单用户可穿戴演示优先稳定低延迟，不追求并发吞吐 |

## Gemma 4 E2B/E4B 混合注意力与长上下文

Gemma 4 E2B/E4B 的长上下文能力来自模型结构本身，而不是应用层手写 attention layer。模型卡说明 E2B/E4B 采用混合注意力：局部 sliding window attention 与 full global attention 交错，最后一层保持 global；小模型上下文窗口为 128K tokens。

WearEdge 在应用层的配置原则是：

1. **不修改模型内部 attention 拓扑**：GGUF 或 vLLM checkpoint 已包含混合注意力结构。
2. **控制可用上下文窗口**：`LLAMA_CONTEXT=2048` 是演示默认值；RAG 和维修手册场景可逐步测试 `8192 / 16384 / 32768`。
3. **用 Flash Attention 降低注意力成本**：当前脚本固定启用 `--flash-attn on`。
4. **把长文档先交给 RAG**：不要把整本维修手册塞进 8GB Jetson 的上下文；先检索，再把少量证据片段送入模型。
5. **E4B 只做实验线**：E4B 同样有 128K 长上下文和音频能力，但在 8GB Orin Nano 上会显著挤压 KV cache、视觉 projector 和系统服务内存。

建议分阶段验证：

| 阶段 | 上下文 | 用途 | 验收 |
| --- | ---: | --- | --- |
| Demo | 2048 | 单图安全/质检/维修建议 | `smoke_test.sh` 通过，服务不重启 |
| RAG | 8192 | 少量 SOP 片段 + 图片 | `tegrastats` 稳定，无 swap 抖动 |
| 长文档实验 | 16384-32768 | 维修手册多段证据 | 只在 30W+ 供电和主动散热下测试 |
| 128K 理论上限 | 128K | 模型能力边界 | 不作为 Orin Nano 8GB 交付默认值 |

## 视觉 Token 动态分配

Gemma 4 支持可配置视觉 token 预算。当前代码中负责视觉 token 动态分配的模块是：

```text
jetson/modality_pipeline.py
  -> choose_visual_token_budget()
  -> VisualTokenBudget.as_llama_env()
  -> LLAMA_IMAGE_MIN_TOKENS / LLAMA_IMAGE_MAX_TOKENS
  -> scripts/run_llama_server.sh
```

当前策略：

| 场景 | 默认预算 | 理由 |
| --- | ---: | --- |
| `hazard` 安全风险识别 | 70 | 快速识别场景、风险和动作建议 |
| `maintenance` 预测性维护 | 140 | 需要保留设备、泄漏、磨损、仪表等中等细节 |
| `iqc` 在线质检 | 280 | 需要看到零件边缘、污染、划痕、装配缺陷 |
| `wi` 作业指导 | 280 | 需要读取机器、工位、工装和操作状态 |
| `changeover` 换型指导 | 280 | 需要读取 SKU、HMI、导轨、标签或治具状态 |
| OCR / 小字读取 | 560 | 需要保留文字和仪表细节 |

生产集成时，网关可以根据 `analysis_mode`、图片大小、是否 OCR、是否高细节质检，把预算写入启动环境或切换到多实例模型服务。当前 PoC 先把预算固定在 70，目标是让 25W 供电下的演示稳定。

## 音频融合模块

当前代码中负责音频融合路径决策的模块是：

```text
jetson/modality_pipeline.py
  -> plan_audio_fusion()
  -> AudioFusionPlan
```

工程判断：

| 路线 | 当前状态 | 原因 |
| --- | --- | --- |
| `llama.cpp` + E2B + image/text | 已实装 | Orin Nano 上最直接、最省内存 |
| `llama.cpp` + E2B audio | 暂不启用 | Jetson AI Lab 已提示 Orin 的 E2B llama.cpp 音频路径存在问题 |
| `vLLM` + E2B/E4B audio | 下一阶段 | 小模型原生支持音频，适合骨传导语音输入和 ASR |
| `NIM` + OpenAI-compatible gateway | 企业部署候选 | 适合统一运维、观测和模型服务化，但不作为当前 8GB 原型机量化来源 |

音频融合建议流程：

```text
Bone-conduction mic / M400 audio
  -> 30s 内音频片段
  -> vLLM or NIM Gemma 4 E2B/E4B audio path
  -> ASR / speech translation
  -> text instruction + image frame
  -> WearEdge Agent output contract
```

## 输出契约与工业可靠性

模型压缩只是第一层，工业系统还需要输出稳定。WearEdge 在网关层加入了契约硬化：

| 模块 | 责任 |
| --- | --- |
| `jetson/output_contract.py` | 将模型自然语言解析成结构化字段，检查缺字段、短字段和动作白名单 |
| `jetson/agent_loop.py` | 根据 `hazard / iqc / wi / changeover / maintenance` 选择输出 schema 和动作决策 |
| `jetson/app.py` | 第一次输出不合格时自动带原图修正一次 |
| `scripts/smoke_test.sh` | 演示前自动验证健康检查、文本推理、图片契约和审计回查 |

这使得端侧模型即使偶尔输出不稳定，也不会直接把坏数据交给 M400、AR 显示、语音播报或 MES/工单系统。

## 当前已实装与下一步

已实装：

- E2B Q4_K_S GGUF 模型下载和 manifest 固化。
- `llama.cpp` 本地 OpenAI-compatible 服务。
- FastAPI 多模态图片网关。
- Flash Attention、GPU layer、batch/ubatch、视觉 token 环境参数。
- 输出契约、修正循环、审计日志和 M400 Android MVP。
- 代码中已标注视觉 token 动态分配与音频融合责任模块。

下一步：

- 将 `choose_visual_token_budget()` 接入网关的 `analysis_mode`，为 IQC/OCR 场景动态提升视觉 token。
- 在 30W+ 供电和主动散热下测试 `LLAMA_CONTEXT=8192/16384`。
- 建立 vLLM/NIM 音频分支，让 E2B/E4B 承接 30 秒以内语音输入。
- 对比 E2B Q4_K_S、E4B Q4_K_M、E2B BF16 在 Jetson 与 RTX 3090 上的延迟、内存和输出质量。

## 参考资料

- Google Gemma 4 E2B model card on Hugging Face: https://huggingface.co/google/gemma-4-E2B-it
- Unsloth Gemma 4 E2B GGUF model page: https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF
- Jetson AI Lab Gemma 4 on Jetson tutorial: https://www.jetson-ai-lab.com/tutorials/gemma4-on-jetson/
- Jetson AI Lab Gemma 4 E2B page: https://www.jetson-ai-lab.com/models/gemma4-e2b/
- NVIDIA NIM for LLMs documentation: https://docs.nvidia.com/nim/large-language-models/
