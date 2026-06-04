# WearEdge Pro 架构定位：外感采集 + 算力盒子

更新日期：2026-05-15

WearEdge Pro 的硬件特点可以归纳为一句话：**外感采集端矩阵 + 随身算力盒子**。

它不是让每一副眼镜都独立运行大模型，而是把头戴设备、语音设备和工业传感入口都轻量化，让它们负责采集、触发、显示和播报；Jetson 算力盒子统一负责本地推理、RAG、规则判断、审计和企业系统对接。

```text
M400 / HMT / bone-conduction headset
  -> first-person image, voice command, metadata, operator trigger
  -> Wi-Fi / Bluetooth / local LAN
  -> Jetson compute box (microSD boots, NVMe runs workload)
  -> wearable 100W USB-C PD power bank
  -> Gemma 4 E2B + RAG + deterministic agent runtime
  -> action card / AR display / voice feedback / audit log
```

## 外感采集端矩阵

| 外感端 | 主要角色 | 最适合的场景 | 接入方式 |
| --- | --- | --- | --- |
| Vuzix M400 | 第一视角图像采集 + 轻量显示 | 普通工业巡检、质检、维修辅助、演示 PoC | Android Camera2 拍照，multipart JPEG 上传 `/v1/infer` |
| Honeywell / RealWear HMT-1Z1 | 本安防爆头戴采集 + 免手持显示 | 石化、能源、危险区、高噪声现场 | Wi-Fi 上传图片，后续适配 WearHF/语音命令 |
| 骨传导耳机 | 仅语音交互，不承担视觉采集 | 盲操排障、动作播报、保持环境音感知 | Bluetooth 音频，先 ASR-to-text，后续 vLLM/NIM 原生音频 |

## 算力盒子

当前算力盒子基线：

| 模块 | 配置 |
| --- | --- |
| 边缘计算 | Jetson Orin Nano 8GB Developer Kit，项目简称 Jetson Nano 8GB |
| 启动存储 | microSD / eMMC 系统盘，挂载 `/`，只保留 OS、代码、venv 和系统日志 |
| 运行存储 | 2TB M.2 NVMe SSD，挂载 `/mnt/nvme`，承载模型、上传缓存、审计日志、RAG 索引和测试数据 |
| 模型服务 | `llama.cpp` + Gemma 4 E2B Q4 GGUF + `mmproj-F16` |
| 网关 | FastAPI `/v1/infer` |
| 编排 | `maintenance / iqc / changeover / wi / hazard` 五类 agent route |
| 可靠性 | 输出契约、自动修正、action card、审计日志、smoke test |
| 移动供电 | 72Wh 移动电源，USB-C 20V/5A 100W 输出，经 PD 诱骗/转接到 5.5x2.5mm DC 圆口 |

## 存储职责分层

推荐布局是：**SD card 负责开机，SSD 负责干活**。

| 存储 | 项目角色 | 当前用途 | 为什么这样分 |
| --- | --- | --- | --- |
| microSD / 系统盘 | Boot + control plane | Ubuntu / JetPack、系统服务、项目代码、Python venv、systemd unit | 小随机读写和系统启动足够；保持系统盘简单，便于备份和恢复 |
| 2TB NVMe SSD | Workload + data plane | GGUF 模型、`mmproj`、上传图片缓存、推理审计、RAG 索引、benchmark 数据、后续客户现场样本 | 顺序读写和耐久性明显优于 SD card；模型加载、日志写入和数据沉淀都更稳 |

当前 Jetson 实机已经完成 NVMe 落地：

```text
/dev/nvme0n1p1 -> /mnt/nvme
filesystem: ext4
label: WEAREDGE_NVME
uuid: b64b7d4e-aaec-4690-a0ce-457dd9d9d75c
measured write smoke test: 512MiB fsync write at about 576 MB/s
```

推荐目录布局：

```text
/home/ryn/WearEdge-Pro
  -> Git 仓库、启动脚本、Python venv、systemd 配置

/mnt/nvme/models/gemma4-e2b
  -> gemma-4-E2B-it-Q4_K_S.gguf
  -> mmproj-F16.gguf

/mnt/nvme/wearedge/uploads
  -> 调试时保存的上传图片和外感采集样本

/mnt/nvme/wearedge/events
  -> inference-events.jsonl 等审计事件

/mnt/nvme/wearedge/rag
  -> 后续 SOP、维修日志、质检知识库索引

/mnt/nvme/wearedge/benchmarks
  -> SD vs NVMe、供电稳定、长时间推理压测数据
```

当前 `.env` 推荐指向：

```dotenv
MODEL_DIR=/mnt/nvme/models/gemma4-e2b
WEAREDGE_UPLOAD_DIR=/mnt/nvme/wearedge/uploads
WEAREDGE_EVENT_LOG=/mnt/nvme/wearedge/events/inference-events.jsonl
```

这个选择对 WearEdge Pro 很关键：Gemma 4 E2B 当前模型资产约 3.8GB，后续再叠加 E4B 候选、RAG 索引、现场误判样本、审计日志和 A/B 测试数据，SD card 会很快变成容量、速度和寿命瓶颈；NVMe 则可以把 Jetson 变成真正的现场数据底座。

## 可穿戴移动供电

Jetson 算力盒子使用独立移动电源供电，形成可穿戴的边缘算力单元。当前候选移动电源来自实物铭牌：

| 项目 | 规格 |
| --- | --- |
| 型号 | PB551，P/N 55992 |
| 标称能力 | 145W 自带线快充移动电源 |
| 电芯能量 | 72Wh，14.4V 5000mAh |
| 电芯容量 | 20000mAh |
| Jetson 推荐输出口 | USB-C 线 `OUT 3` |
| Jetson 推荐输出档位 | 20V / 5A，100W Max |
| 转接方式 | USB-C PD 20V trigger / adapter -> 5.5x2.5mm DC 圆口 |
| 佩戴方式 | 腰包、背包肩带或算力盒子电池仓，线缆做应力释放 |

接线原则：

```text
PB551 USB-C OUT 3 (20V/5A 100W)
  -> USB-C PD 20V trigger / adapter
  -> 5.5x2.5mm DC barrel plug, center positive
  -> Jetson DC barrel input
```

预计续航按 72Wh 电芯能量、约 85% 转换效率粗算：

| Jetson 侧平均功耗 | 估算续航 | 使用场景 |
| ---: | ---: | --- |
| 20W | 约 3.0 小时 | 网关、轻量推理、短时演示 |
| 25W | 约 2.4 小时 | WearEdge 标准 PoC，M400/HMT 单帧推理 |
| 30W | 约 2.0 小时 | 主动散热、SSD 读写、较频繁推理 |
| 45W | 约 1.3 小时 | 压力测试，不建议作为常态穿戴负载 |

安全检查：

1. 不要用 Jetson 的 USB-C 数据口供电；使用 DC 圆口输入。
2. 转接头必须明确支持 20V PD trigger，不要使用只做物理转接的普通线。
3. 5.5x2.5mm DC 圆口需确认中心正极。
4. 第一次接 Jetson 前，用万用表确认圆口输出约 20V。
5. 线缆和转接头需支持 5A / 100W，优先使用带 E-marker 的 USB-C 线或一体式 PD 诱骗线。
6. 移动电源不是本安防爆设备；进入危险区时，HMT 可作为本安外感端，Jetson 算力盒子和移动电源应按现场安全要求放在安全区或合规防护外壳中。

供电稳定基线按同一脚本做 A/B 对照：

```bash
# 原装电源，先做基线
cd ~/WearEdge-Pro
WEAREDGE_POWER_BASELINE_SECONDS=120 \
WEAREDGE_POWER_BASELINE_WRITE_MIB=256 \
bash scripts/power_baseline_check.sh original-power

# 关机后切换到 PB551 移动电源，再跑同一套命令
cd ~/WearEdge-Pro
WEAREDGE_POWER_BASELINE_SECONDS=120 \
WEAREDGE_POWER_BASELINE_WRITE_MIB=256 \
bash scripts/power_baseline_check.sh pb551-100w-pd
```

判定标准：不重启、不掉 SSH、不掉 `/healthz`、`wearedge-llama.service` 和 `wearedge-gateway.service` 不重启，内核日志里没有 undervoltage、NVMe reset、thermal throttle、OOM 或异常 shutdown。

2026-05-15 A/B 基线结论：

| 电源 | 测试窗口 | 温度 | VDD_IN | NVMe 写入 | 服务状态 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| 原装 DC 电源 | 25W 模式，空闲 120s + 256MiB NVMe 写入 | 约 49.0-50.5°C | 空闲约 4.36-4.45W | 557 MB/s | `llama` / `gateway` active，`healthz` ok | PASS |
| PB551 100W PD | 25W 模式，空闲 120s + 256MiB NVMe 写入 | 约 46.6-48.3°C | 稳态约 4.36-4.44W，启动暖机峰值约 6.29W | 661 MB/s | `llama` / `gateway` active，`healthz` ok | PASS |

这说明 PB551 + 20V PD trigger + 5.5x2.5mm DC 圆口在“启动、服务在线、NVMe 挂载、空闲采样、短时写入脉冲”层面已经可用。下一阶段才进入轻量模型请求和更长时间推理压测。

2026-05-15 PB551 阶梯式推理结论：

| 阶段 | 结果 | 备注 |
| --- | --- | --- |
| 1 次文本健康推理 | PASS | `llama-server` 返回 `HTTP 200`，29 tokens，生成约 15.18 token/s |
| 3 次间隔 maintenance 图像请求 | PASS | `HTTP 200`，`contract_ok=true`，`audit=true`，耗时 `45.32s / 5.78s / 5.96s` |
| 推理后服务检查 | PASS | `wearedge-llama.service` 与 `wearedge-gateway.service` 均为 active，`healthz` ok |
| 推理后内核日志 | PASS | 未观察到 undervoltage、NVMe reset、thermal throttle、OOM 或异常 shutdown |

脚本中出现的 `jq parse error` 来自把 `HTTP_STATUS=...` 文本追加到了同一个响应文件，不代表模型或网关失败；实际响应对象已经正常解析并返回结构化字段。

后续巡检式轻压测使用固化脚本，避免响应 JSON 与 HTTP 状态混写：

```bash
cd ~/WearEdge-Pro
WEAREDGE_PATROL_INTERVAL_SECONDS=180 \
WEAREDGE_PATROL_ROUNDS=6 \
bash scripts/pb551_patrol_stress_check.sh pb551-patrol-20min
```

2026-05-15 PB551 巡检式轻压测记录：

| 检查项 | 结果 | 观测 |
| --- | --- | --- |
| `text-health` | PASS | `HTTP 200`，`0.78s` |
| warm maintenance / warm IQC | PASS | `HTTP 200`，`6.04s / 4.25s` |
| 6 轮 patrol 请求 | PASS | maintenance / WI / IQC 轮换，全部 `HTTP 200`，耗时 `6.05s / 4.52s / 4.06s / 5.57s / 4.34s / 4.30s` |
| 推理后服务检查 | PASS | `wearedge-llama.service` 与 `wearedge-gateway.service` 均为 active，`healthz` ok |
| 推理后内核日志 | PASS | 未观察到 undervoltage、NVMe reset、thermal throttle、OOM 或异常 shutdown |

首版巡检脚本的 `jq` 报错是摘要提取层问题：`jq` 将裸 `label` 识别为关键字，实际 HTTP 请求和模型响应均成功。首版脚本还会在长巡检结束后因 `sudo dmesg` 等待密码而拖长收尾时间；脚本已改成非交互 sudo，不再阻塞巡检结束。

2026-05-15 PB551 低电量段 60 分钟巡检记录：

| 检查项 | 结果 | 观测 |
| --- | --- | --- |
| 电量窗口 | PASS | PB551 从 `36%` 起跑，结束为 `24%`，约 57.65 分钟消耗 12 个百分点，折算平均约 `9.0W` |
| 请求完成度 | PASS | `summary.jsonl` 共 15 行：1 次 text-health、2 次 warm-up、12 轮 patrol |
| 12 轮 patrol 请求 | PASS | maintenance / WI / IQC 轮换，全部 `HTTP 200`，`contract_ok=true`，`audit=true` |
| 推理后服务检查 | PASS | `wearedge-llama.service` 与 `wearedge-gateway.service` 均为 active，`healthz` ok |
| 推理后内核日志 | PASS | 手动 `dmesg` 未观察到 undervoltage、NVMe reset、thermal throttle、OOM 或异常 shutdown |

这把 PB551 方案从“满电和短时可行”推进到“36% 起始电量下可支撑短现场巡检”的证据等级。后续风险主要转向 20% 以下输出降档、线缆扰动、背负固定和满负载余量。

该脚本会保存每次请求的 JSON、HTTP 状态、耗时、`tegrastats` 快照和内核日志检查，默认轮换 maintenance / WI / IQC 三类图像请求。

## 为什么要分离

| 设计选择 | 好处 |
| --- | --- |
| 外感端只做采集和交互 | 头戴设备轻、续航长、发热低，适合现场佩戴 |
| Jetson 统一推理 | 模型、RAG、规则和审计集中管理，便于升级和复验 |
| 多外感端共用一套网关契约 | M400、HMT、网页、后续传感器都能接 `/v1/infer` |
| 语音与视觉分层 | 骨传导耳机可以先做命令和播报，不阻塞视觉 PoC |
| 2TB SSD 做现场数据底座 | 可保存模型、RAG 索引、误判样本、审计日志和 A/B 测试数据 |
| SD card 与 SSD 分工 | 系统盘保持轻量可恢复，NVMe 承担高频读写和大文件资产 |
| 移动电源独立供电 | Jetson 算力盒子可穿戴移动部署，不依赖墙插或现场临时电源 |

## 数据流

1. 外感端采集图片、语音命令和设备元数据。
2. 网关按 `analysis_mode` 选择 `hazard / maintenance / iqc / wi / changeover`。
3. Jetson 本地模型生成结构化候选答案。
4. 输出契约检查字段、字数、动作白名单和工业边界。
5. 不合格时自动修正一次；仍不合格则拒绝下游消费。
6. 通过 action card 把结果回传到头戴端、语音端或工单系统。
7. 可选写入 `/mnt/nvme/wearedge/events/inference-events.jsonl` 做审计。

## 当前可行性判断

| 能力 | 当前成熟度 | 下一步 |
| --- | --- | --- |
| M400 图片上传 | 中高，Android MVP 可编译 | 真机安装和 Camera2 参数验证 |
| HMT 图片上传 | 中高，架构可行 | 先走网页上传，再做 WearHF 客户端 |
| 骨传导播报 | 中 | 把 `action_card.operator_message` 接到 TTS/蓝牙 |
| 语音触发 | 中 | 固定命令词、确认机制、ASR-to-text |
| 原生音频理解 | 中低 | vLLM/NIM 分支，不放进当前 llama.cpp 主线 |
| 连续视频理解 | 低到中 | 前置轻量检测器，只把关键帧送 VLM |
| 可穿戴移动供电 | 中高 | 先用 20V PD 转 DC 圆口验证稳定性，再做线缆固定、散热和续航测试 |

## 产品表达

对外可以这样讲：

> WearEdge Pro 采用“外感采集 + 算力盒子”的分离式架构。M400、HMT 和骨传导耳机负责现场第一视角感知与免手持交互；Jetson 算力盒子由可穿戴 100W USB-C PD 移动电源供电，负责本地多模态推理、工业知识检索、确定性安全规则和审计闭环。这样既保留可穿戴设备的轻量和工业适配性，又把模型能力、数据安全和系统可靠性集中在可管控的边缘节点中。
