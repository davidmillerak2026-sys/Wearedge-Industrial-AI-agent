# Gemma 4 开发者大赛项目记忆与差距分析

本文档把本次对 Gemma 4 开发者大赛官网的爬取结果固化为项目记忆，并对 WearEdge Pro 当前 GitHub 仓库内容做一次面向参赛提交的工程对比。目标不是写宣传稿，而是明确：我们现在强在哪里、弱在哪里、接下来每一步应该补什么证据。

## 1. 本次爬取信息记忆

主要来源：

- Gemma 4 开发者大赛中文官网：https://hackathon.googdg.cn/?lang=zh-CN
- Gemma 4 Hackathon English page：https://hackathon.googdg.cn/?lang=en
- 2025 赛事回顾：https://hackathon.googdg.cn/hackathon/2025

官网关键信息：

| 事项 | 官网信息 | 对 WearEdge Pro 的含义 |
| --- | --- | --- |
| 当前状态 | 报名进行中 | 需要尽快把 repo、技术报告、视频脚本和可演示链路收口 |
| 决赛席位 | 15-30 支队伍 | 需要从“能跑”升级为“评委一眼看懂差异化” |
| 线下决赛 | 2026 Google I/O Connect 中国站 | 需要准备稳定、短平快、可现场复现的硬件演示 |
| 资源支持 | 最高 `$200,000` 资源扶持 | 技术报告要说明后续可用 Google / edge 生态扩展 |
| 核心模型规则 | 必须使用 Gemma 4，任意规格均可 | 当前 Gemma 4 E2B GGUF 路线符合核心规则 |
| 合规规则 | 必须披露训练数据来源并符合数据隐私法 | 我们应明确“不训练用户数据、图片默认不保存、仅元数据审计” |
| 团队 | 1-5 人 | 单人项目可以参赛，但要把工程自动化和文档做得更像团队产物 |

赛程记忆：

| 节点 | 日期 | 要求 |
| --- | --- | --- |
| 启动与报名 | 4 月 18 日 | 注册开启，合作伙伴招募 |
| Workshop 系列 | 4 月 18 日 - 5 月 18 日 | 模型基础、多模态、Agent 构建、边缘部署 |
| 报名截止 | 5 月 18 日 | 团队锁定，1-5 人，可跨城市组队 |
| 开发期 | 5 月 18 日 - 6 月 8 日 | 开放式开发 |
| 导师指导 | 5 月 18 日 - 6 月 8 日 | 专家与 GDE 在线答疑 |
| 最终提交 | 6 月 8 日 23:59 | 代码仓库、5 分钟内演示视频、技术报告、在线演示链接 |
| 评审阶段 | 6 月 9 日 - 7 月 15 日 | 技术委员会审核，每赛道 Top 5 |
| 决赛名单 | 7 月 15 日 | 公布入围名单 |
| 全国总决赛 | 8 月，Google I/O Connect 中国站 | 现场路演与颁奖 |

赛道记忆：

| 赛道 | 官网定位 | WearEdge Pro 匹配度 |
| --- | --- | --- |
| A. AI Agent | 多步规划、工具调用、原生函数调用，自主 Agent | 高。项目已有 5-agent route、action_card、runtime_stream、bounded tool plan |
| B. Multimodal | 深度整合视觉、音频和语言 | 中高。视觉+语言已跑通，音频仍在设计路线 |
| C. Edge AI | E2B/E4B 离线部署在手机、树莓派或嵌入式硬件，需真实硬件演示 | 最高。Jetson Orin Nano 8GB + Gemma 4 E2B 本地推理是核心亮点 |
| D. AI for Social Good | 无障碍、气候、公共卫生、教育公平、灾害响应 | 中。工业安全有社会价值，但需要把工伤预防、老师傅经验传承讲清楚 |

奖项记忆：

| 奖项 | 官网信息 | 我们的目标策略 |
| --- | --- | --- |
| 全场总冠军 | 1 名，20,000 Cloud Credit、GDE 提名机会、Google for Startups 合作机会 | 需要完整商业叙事、现场稳定演示和清晰社会影响 |
| 赛道优胜奖 | 4 名，每赛道专项奖励 | 重点冲刺 Edge AI 赛道，同时兼顾 AI Agent 叙事 |
| 最佳移动应用奖 | 1 名 | M400 Android 端若真机跑通，可作为副目标 |
| 最佳边缘部署奖 | 1 名 | 当前最适合争取，必须强化“真实硬件离线部署”证据 |
| 优秀奖 | 10 名 | 保底目标取决于 demo 完整度和文档质量 |

评审权重记忆：

| 维度 | 权重 | 我们必须展示什么 |
| --- | ---: | --- |
| 真实影响力 | 30% | 工业安全、维修、质检的真实痛点、ROI、受众和扩展路径 |
| 技术卓越度 | 25% | Jetson 本地 Gemma 4、多模态、输出契约、Agent 编排、测试和架构质量 |
| 功能完备性 | 20% | 可运行 demo、M400/Jetson 链路、异常处理、审计、自动验收 |
| 创新性 | 15% | 算力与感知分离、可穿戴工业 Agent、老师傅 follow-up loop |
| 演示表现 | 10% | 5 分钟视频、技术报告、README 路径、现场命令和结果 |

提交材料记忆：

- 代码仓库。
- 5 分钟内演示视频。
- 技术报告。
- 在线演示链接。

2025 赛事参照：

- 2025 前三名得分非常接近：第 1 名 7.50，第 2 名 7.44，第 3 名 7.43。
- 2025 评分强调完成度、创新、实用效果和社会价值。
- 这说明“能运行、能讲清楚、能体现真实场景”的项目比纯概念更有优势。

## 2. 当前仓库事实基线

当前远端 `origin/main` 已对齐到：

```text
1570960 Add runtime POC artifacts and Jetson package
```

本地测试结果：

```text
82 passed
```

当前已推到 GitHub 的核心能力：

| 模块 | 仓库证据 | 状态 |
| --- | --- | --- |
| Jetson E2B 部署主线 | `docs/e2b-deployment-runbook.md`、`scripts/setup_jetson.sh`、`scripts/run_llama_server.sh` | 已沉淀 |
| Gemma 4 E2B 端侧推理 | `docs/gemma4-e2b-poc-summary.md`、`docs/gemma4-e2b-model-manifest.lock` | 已验证 |
| M400 图片推理接口 | `docs/m400-inference-contract.md`、`jetson/app.py` | 已实现 |
| 输出契约硬化 | `jetson/output_contract.py`、`tests/test_output_contract.py` | 已测试 |
| 5 类工业 Agent | `jetson/agent_profiles.py`、`jetson/agent_loop.py`、`docs/five-agent-poc-validation.md` | 已验证 |
| Agently-style workflow | `jetson/agently_orchestrator.py`、`tests/test_agently_orchestrator.py` | 已实现 |
| Action card / integration event | `jetson/agent_loop.py`、`docs/m400-inference-contract.md` | 已实现 |
| Runtime stream | `jetson/agently_orchestrator.py`、`docs/m400-inference-contract.md` | 已实现 |
| Follow-up evidence loop | `jetson/follow_up_plan.py`、`docs/lao-shi-fu-maintenance-poc.md` | 已有主线 |
| M400 Android MVP | `clients/m400/android/` | 已可构建，真机待验证 |
| 工业 RAG 样例 | `industrial-rag-agent/` | 已有样例 |
| 核心软硬件 BOM | `docs/core-bom.md` | 已生成 |
| 网络问题复盘 | `docs/network-troubleshooting.md` | 已沉淀 |

当前本地还有未提交草稿：

| 类型 | 文件 | 说明 |
| --- | --- | --- |
| API / workflow 增强 | `jetson/app.py`、`jetson/agently_orchestrator.py`、`jetson/follow_up_plan.py` | 维护会话和 evidence loop 相关增强 |
| 新模块 | `jetson/maintenance_session.py` | 维护会话状态管理草稿 |
| 新脚本 | `scripts/run_maintenance_session_poc.sh` | 维护会话 PoC 脚本 |
| 新测试 | `tests/test_maintenance_session.py`、`tests/test_maintenance_session_api.py` | 当前本地测试已覆盖并通过 |
| 文档 | `docs/maintenance-session-evidence-loop.md` | 维护会话 evidence loop 说明 |
| 打包产物 | `wearedge-pro-latest.tar` | 二进制包变更，是否纳入 Git 需要谨慎判断 |

## 3. 和比赛要求的匹配度评分

| 评审维度 | 当前匹配度 | 证据 | 主要短板 |
| --- | --- | --- | --- |
| 真实影响力 30% | 7.5 / 10 | 工业安全、预测性维护、质检、作业指导、换型五场景已定义 | 缺少量化 ROI、客户画像、事故/停机成本模型 |
| 技术卓越度 25% | 8.5 / 10 | Jetson 离线 Gemma 4 E2B、llama.cpp CUDA、contract repair、5-agent workflow、82 tests | 还需更清晰展示 Gemma 4 特性深度、端侧性能曲线和边界测试 |
| 功能完备性 20% | 7 / 10 | Jetson 服务、smoke test、M400 Android debug 构建、审计和 API 契约 | M400 真机未验证，音频/AR 展示未闭环，在线 demo 未定 |
| 创新性 15% | 8 / 10 | 算力与感知分离、老师傅 follow-up loop、端侧 Agent action card | 需要把创新点压成 3 个一句话可记住的 demo punchline |
| 演示表现 10% | 6.5 / 10 | 文档多、代码路径清楚、样例结果多 | 视频脚本、5 分钟节奏、演示首页和提交材料还未成型 |

综合判断：

```text
当前项目已经具备 Edge AI + AI Agent 双赛道竞争力。
最适合主攻：赛道 C Edge AI / 最佳边缘部署奖。
辅助叙事：赛道 A AI Agent / 最佳移动应用奖。
最大风险：不是算法没有跑通，而是演示材料没有把硬核工程证据压缩成评委能快速理解的故事。
```

## 4. 目前最强优势

### 4.1 真正的端侧 Gemma 4，不是云 API 套壳

比赛明确强调 Edge AI 需要 E2B/E4B 真正离线部署在嵌入式硬件并提供真实硬件演示。WearEdge Pro 已经完成：

- Jetson Orin Nano 8GB 上运行 Gemma 4 E2B GGUF。
- `llama.cpp` CUDA 后端加载主模型和 `mmproj-F16.gguf`。
- FastAPI 网关本地调用 `llama-server`。
- systemd 开机自启。
- 本地 smoke test 验证健康、文本推理、图片推理、输出契约和审计回查。

这是项目最硬的参赛资产。

### 4.2 工业 Agent 不是一次 prompt，而是可追踪 workflow

仓库已经把 Agent 从“模型回答”推进到：

```text
normalize_agent
  -> select_agent_route
  -> collect_evidence
  -> bounded_react_tools
  -> build_contract_prompt
  -> model_infer
  -> validate_contract / repair_contract
  -> identify_context
  -> uncertainty_guard
  -> build_action_card
  -> build_follow_up_plan
  -> build_integration_event
  -> runtime_stream
```

这比普通黑客松项目更像可交付工程系统。

### 4.3 输出契约解决了工业落地的真实问题

很多 VLM demo 的问题是“看起来会说话，但下游不能用”。WearEdge Pro 已经把模型输出强制解析为结构化字段，并用 action channel 映射到确定性动作：

- Hazard：`scene/risk/action`
- Maintenance：`machine/symptom/maintenance_risk/evidence_needed/action`
- IQC：`product/quality_risk/disposition/action`
- WI：`machine/work_instruction/risk_control/action`
- Changeover：`machine/sku/changeover_step/verification/action`

这是技术卓越度和功能完备性的重要证据。

### 4.4 老师傅 predictive maintenance 有差异化

`lao-shi-fu` 不是泛泛的安全检测，而是工业现场很有说服力的“经验传承 + 证据补采”场景：

- 先识别设备和症状。
- 不直接编造根因。
- 要求 M400 继续拍铭牌、HMI、温度表、润滑记录、维修记录。
- 收集操作员感官反馈。
- 最后生成带 human gate 的维护 action card。

这个故事天然适合视频演示。

### 4.5 文档和测试已经明显超过普通 PoC

已有：

- 核心 BOM。
- 技术架构白皮书。
- M400 接口契约。
- 网络问题复盘。
- 五 agent POC matrix。
- Gemma 4 E2B PoC 记录。
- lao-shi-fu POC 记录。
- 82 个本地测试通过。

这能支撑“代码质量、架构设计、文档完善”的评审维度。

## 5. 主要短板和风险

### 5.1 真实影响力还缺量化

目前 README 讲了工业痛点，但还没有把价值量化成评委容易记住的数字。

需要补：

- 一次误停机成本：例如包装线停机每小时损失。
- 一次安全事故成本：医疗、停工、合规罚款、保险。
- 一次质检漏检成本：返工、召回、客户索赔。
- 老师傅经验断层：培训周期、人员流失、夜班无人支援。

没有这些，30% 的真实影响力会被削弱。

### 5.2 M400 真机链路仍是最大功能风险

Android MVP 已能构建，但当前仍缺真机验证：

- Camera2 实际预览方向。
- M400 实际支持分辨率。
- 拍照后 JPEG 大小是否稳定低于 4MB。
- 局域网连接 Jetson 是否稳定。
- 佩戴场景下按钮、文字、亮度是否可用。
- request_id、action_card、audit recent 是否能在眼镜上顺畅呈现。

这直接影响“最佳移动应用奖”和现场演示可信度。

### 5.3 音频和 AR 还停留在规划层

项目愿景包含骨传导耳机和 AR 提示，但当前闭环主要是图片上传和屏幕结果显示。需要避免在提交时过度承诺。

建议表述：

- 当前已完成：第一视角图片 -> Jetson -> 结构化 action。
- 下一阶段：action 语音播报、连续帧检测、AR overlay。
- 不要把未完成的音频能力讲成已完成。

### 5.4 在线演示链接尚未成型

官网提交要求包含在线演示链接。当前最真实的是局域网 Jetson 演示，但这不是公网在线 demo。

可选策略：

- 提供 GitHub Pages / static demo page 展示固定样例、接口响应和视频。
- 提供 Hugging Face Space 或 Cloud Run 的“模拟版网关”，不跑本地模型，只回放已保存样例。
- 技术报告明确真实推理在 Jetson 本地，在线 demo 作为 replay / simulator。

### 5.5 模型资产管理还需要更专业

当前大模型文件不进 Git 是正确的，但需要让评委一眼知道如何复现：

- 模型来源。
- 文件大小。
- SHA256。
- 下载命令。
- 网络失败时的手动传输方式。
- 为什么不把 GGUF 放进普通 Git。

这已经有 manifest 和 BOM，但 README 中需要更显眼。

### 5.6 技术路线容易被误解为“过度文档化”

仓库文档多、概念强，但评委第一眼可能看不出“最短运行路径”。

需要补一个非常短的评委入口：

```text
1. What it is
2. Why Gemma 4
3. Why edge
4. How to run demo
5. What evidence proves it works
```

也就是需要一个 `docs/submission-brief.md` 或 README 顶部 `Judge Quick Path`。

## 6. 需要改善的地方

### 6.1 README 首屏要从愿景变成可评审入口

建议新增：

- `Demo in one minute`。
- `Hackathon track fit`。
- `What is already working`。
- `Evidence links`。
- `How to reproduce`。

README 当前叙事很完整，但评委时间有限。首页应先给出最强证据，再展开愿景。

### 6.2 补一张系统架构图和一张评审证据图

需要两张图：

1. 技术架构图：

```text
M400 Camera2 -> Jetson Gateway -> llama.cpp Gemma 4 E2B -> Agent workflow -> Action card -> Audit log
```

2. 评审证据图：

```text
Repo code -> tests -> Jetson smoke result -> Android APK build -> POC images -> final response JSON
```

这会显著提高演示表现。

### 6.3 把 Jetson 性能数据做成表格

至少记录：

- 首次加载耗时。
- hazard 单图延迟。
- maintenance 高视觉 token 单图延迟。
- 内存占用。
- CPU/GPU/温度。
- `LLAMA_IMAGE_MIN/MAX_TOKENS` 对延迟的影响。

当前已有零散 `latency_ms`，但还没有系统 benchmark。

### 6.4 把老师傅完整会话做成正式 submission demo

当前 `docs/lao-shi-fu-maintenance-poc.md` 很强，但还可以进一步整理为：

- 7 张图片缩略图。
- 每一步的 agent 输出。
- 最后一张行动卡。
- 一页“为什么这不是普通 VLM 看图说话”。

这非常适合 5 分钟视频主体。

### 6.5 明确数据隐私和安全边界

建议新增：

- 图片默认不保存。
- 审计日志只保存元数据和结构化输出。
- token 鉴权。
- 大模型本地运行。
- 不做最终维修放行，关键动作需要 human gate。
- 不替代法定安全流程和 LOTO。

这对工业项目可信度很重要。

### 6.6 建立“演示降级方案”

现场硬件演示必须有 fallback：

- Jetson live inference。
- 如果 M400 不稳定，用 Windows Web 上传到 Jetson。
- 如果网络不稳定，用本地 saved JSON replay。
- 如果模型服务冷启动太慢，提前启动并保留 health 页面。

## 7. 详尽跟进计划

### P0：参赛提交硬门槛

| 优先级 | 任务 | 产物 | 验收标准 |
| --- | --- | --- | --- |
| P0 | 建立 `docs/submission-brief.md` | 评委快速入口 | 3 分钟内能看懂项目、赛道、运行证据 |
| P0 | README 顶部加入 Judge Quick Path | README 快速导航 | 链到 demo、架构、BOM、PoC、测试、视频 |
| P0 | 补比赛报名信息 | 报名表草稿 | 项目名、赛道、摘要、成员、repo、demo link 可直接复制 |
| P0 | 明确主赛道 | 提交策略 | 主打 Edge AI，副打 AI Agent / Best Edge Deployment |
| P0 | 固化在线演示策略 | GitHub Pages 或 replay demo | 即使没有公网 Jetson，评委也能打开演示链接 |
| P0 | 准备 5 分钟视频脚本 | `docs/demo-video-script.md` | 结构为痛点 30s、架构 60s、实机 150s、Agent 90s、价值 60s |
| P0 | 准备技术报告骨架 | `docs/technical-report.md` | 覆盖 Gemma 4、边缘部署、Agent、测试、隐私、限制 |

### P1：最佳边缘部署证据

| 优先级 | 任务 | 产物 | 验收标准 |
| --- | --- | --- | --- |
| P1 | 重新跑 Jetson smoke test 并保存输出 | `docs/poc-results/jetson-smoke-latest.json` 或 markdown | 包含 health、image inference、contract、audit recent |
| P1 | 记录 tegrastats / systemd / ports | `docs/edge-runtime-benchmark.md` | 有内存、延迟、服务自启、端口状态 |
| P1 | 固化模型 manifest 复现说明 | README + manifest | 模型来源、SHA、大小、下载/手动传输方案清楚 |
| P1 | 做视觉 token benchmark | 表格 | 70/140/280/560 token 对延迟和质量的影响 |
| P1 | 将 deployment runbook 简化成 judge commands | 一页命令 | 评委能看到真实硬件运行证据 |

### P2：M400 客户端完成度

| 优先级 | 任务 | 产物 | 验收标准 |
| --- | --- | --- | --- |
| P2 | 真机安装 debug APK | 安装截图 / 运行记录 | M400 能打开 app |
| P2 | 真机 Check Gateway | 截图 / 日志 | M400 访问 Jetson `/healthz` 成功 |
| P2 | 真机拍照上传 | 视频 / response JSON | 能拿到 `action_card` 和 `request_id` |
| P2 | M400 UI 优化 | Android patch | action、risk、latency、request_id 在眼镜上可读 |
| P2 | 增加“演示模式” | replay 或 sample image | 无网络/无相机也能展示界面 |
| P2 | 骨传导播报最小实现 | Android TextToSpeech 或音频提示 | 播报 action，不必先做语音输入 |

### P3：老师傅 Agent 强化

| 优先级 | 任务 | 产物 | 验收标准 |
| --- | --- | --- | --- |
| P3 | 合并 maintenance session 草稿 | 代码 + 测试 | 当前 82 tests 继续通过 |
| P3 | 正式记录 session API | `docs/maintenance-session-evidence-loop.md` | 说明一次 request family 如何跨多帧补证据 |
| P3 | 做最终完整 demo JSON | `docs/poc-results/maintenance-session-demo.json` | 包含初始帧、follow-up、最终 action_card |
| P3 | 接入 RAG 样例证据 | 维护手册片段 | evidence_plan 不再只有 missing tools |
| P3 | 生成工单样例 | CMMS mock event | `integration_event` 能映射到工单字段 |

### P4：影响力和商业化补强

| 优先级 | 任务 | 产物 | 验收标准 |
| --- | --- | --- | --- |
| P4 | 写工业 ROI 页面 | `docs/impact-and-roi.md` | 有停机、安全、质检、培训四类价值 |
| P4 | 定义首批客户画像 | 文档表格 | 智能制造、航空维修、石化巡检、仓储物流 |
| P4 | 写用户故事 | 3-5 个场景 | 每个包含 before/after 和可量化指标 |
| P4 | 写数据合规声明 | `docs/privacy-and-safety.md` | 数据不出厂、默认不存图、人工确认边界 |
| P4 | 规划合作伙伴问题定义 | outreach brief | 可发给工厂/赛事合作方征集真实场景 |

### P5：提交材料打磨

| 优先级 | 任务 | 产物 | 验收标准 |
| --- | --- | --- | --- |
| P5 | 录制 5 分钟视频 | MP4 | 不超过 5 分钟，出现 Jetson、M400/Web、实际 response |
| P5 | 准备 10 页路演稿 | PPTX | 1 页问题、1 页方案、1 页架构、2 页 demo、1 页技术、1 页影响、1 页路线图、1 页团队、1 页 ask |
| P5 | 准备 FAQ | `docs/judge-faq.md` | 覆盖为什么 Gemma 4、为什么 Jetson、为什么不云端、为什么不是普通 VLM |
| P5 | 做最终 repo cleanup | git status clean | 不提交无关 runtime、大 tar、临时 token |
| P5 | 打 tag | `hackathon-submission` | 提交时 repo 状态可回溯 |

## 8. 建议的提交定位

推荐主标题：

```text
WearEdge Pro: Offline Gemma 4 Industrial Agent on Jetson for Wearable Frontline Workers
```

一句话：

```text
WearEdge Pro runs Gemma 4 E2B locally on Jetson and turns M400 first-person images into auditable industrial action cards for safety, maintenance, quality, work instruction, and changeover.
```

中文一句话：

```text
WearEdge Pro 把 Gemma 4 E2B 真正部署到 Jetson 边缘硬件上，让 M400 第一视角图片变成可审计、可执行、可接工厂系统的工业 Agent 行动卡。
```

主赛道：

```text
Track C: Edge AI
```

副叙事：

```text
Track A: AI Agent
Best Edge Deployment
Best Mobile App
```

最强演示故事：

```text
老师傅预测性维护：
M400 看到包装线驱动站异常 -> Jetson 本地 Gemma 4 E2B 判断设备状态 -> Agent 不编造根因，而是要求补拍证据 -> 收集温度、振动、润滑、维修记录和操作员感官反馈 -> 输出需要人工确认的 maintenance_stop action card。
```

## 9. 下一轮执行建议

下一轮最应该做的不是继续加概念，而是收口提交材料：

1. 新增 `docs/submission-brief.md`，让评委快速进入项目。
2. 新增 `docs/demo-video-script.md`，围绕 Jetson 真实推理和 lao-shi-fu POC 写 5 分钟脚本。
3. 新增 `docs/edge-runtime-benchmark.md`，把 Jetson 性能数据从日志变成表格。
4. 整理 README 顶部导航，把“已运行证据”前置。
5. 决定是否提交当前 maintenance session 草稿；若提交，先排除 `wearedge-pro-latest.tar` 这类大包风险。

## 10. 2026-05-14 推进记录：Jetson benchmark 表

本轮已新增：

```text
docs/edge-runtime-benchmark.md
```

本轮目的：

- 把已有 Jetson / Gemma 4 E2B / M400-style POC 结果从零散日志整理成评委可读的 benchmark。
- 明确区分“已实测”“脚本已具备但待补跑”和“下一步性能矩阵”。
- 把之前每个 milestone 和 learning 记录成可滚动维护的工程 ledger。

关键 benchmark 结论：

| 指标 | 当前记录 |
| --- | --- |
| 安全场景 3.17MB 图片本地推理 | 6 次记录，`3503-13205 ms`，平均 `8579 ms` |
| 首次 Jetson 图片 PoC | `5824 ms`，证明本地 Gemma 4 E2B 图片推理跑通 |
| systemd 重启后浏览器复验 | `8734 ms`，证明不是临时终端 demo |
| 审计 smoke test | `9884 ms`，`request_id` 可回查，`saved_path=null` |
| lao-shi-fu 高细节维护路线 | `LLAMA_IMAGE_MIN/MAX_TOKENS=560/560` 已验证 |
| 7 轮 prompt-carried 维护 POC | 平均 `42187 ms`，最大 `48568 ms`，证明 prompt stuffing 是慢路径 |
| 最终修复后维护 recheck | `7470 / 7646 ms`，证明中文 action starter normalizer 修复后路径稳定 |

本轮新增 learning：

- Edge claim 现在有 latency、systemd、audit、model manifest 和 token budget 证据，不再只是“Jetson 能跑”的口头说法。
- `70/70` 默认视觉 token 更适合安全场景和现场快速演示；`560/560` 适合读取 HMI、小字、铭牌、仪表和维修记录。
- 48 秒级慢路径主要来自高视觉 token 加长 prompt 证据携带，不应作为最终 M400 现场 SLA。
- maintenance session evidence loop 的价值更明确：让 Jetson 管理证据状态，避免每一轮把历史证据塞回 prompt。
- 下一步性能证据不能只看 `latency_ms`，还要补 `tegrastats`、内存、温度、端口、systemd、冷启动和 M400 真机 Wi-Fi 延迟。

本轮仍未解决的风险：

- 还没有新鲜的 `tegrastats` / GPU / RAM / 温度表格。
- `140/140` 和 `280/280` 视觉 token 中间档尚未跑成可引用数据。
- maintenance session API 已有脚本和本地测试，但最新 Jetson 数字结果仍需归档到 `docs/poc-results/`。
- M400 真机 latency、Camera2 方向、分辨率和佩戴可读性仍未验证。

更新后的下一步：

1. 新增 `docs/submission-brief.md`，把 `edge-runtime-benchmark.md` 链进去。
2. 跑一次 Jetson `tegrastats + smoke_test.sh`，保存最新 health、latency、audit、memory、temperature。
3. 跑同一图片集的 `70/140/280/560` 视觉 token 矩阵。
4. 把 maintenance session POC 的 Jetson 最新响应和 trace 归档为 `docs/poc-results/maintenance-session-demo.json`。
5. 再写 5 分钟视频脚本，主线使用“快路径安全 demo + 高细节老师傅维护 demo + 慢路径为何已被 session loop 修复”的故事结构。

## 11. 2026-05-14 推进记录：Impact and ROI

本轮已新增：

```text
docs/impact-and-roi.md
```

本轮目的：

- 把“真实影响力 30%”从愿景描述推进到可量化 ROI 框架。
- 搜集公开行业 benchmark，用停机、安全、质量、培训四类价值池支撑 WearEdge Pro 的工业落地叙事。
- 明确区分外部行业平均值、WearEdge 可影响的环节、以及后续试点需要验证的 KPI。

新增公开 benchmark 记忆：

| 价值池 | 外部 benchmark | WearEdge Pro 用法 |
| --- | --- | --- |
| 停机 | Siemens Senseye: FMCG 低端 `$36,000/hour`，SME 高端 `$150,000/hour`，汽车 `$2.3M/hour`；大型工厂平均 `27 hours/month` 非计划停机 | 用于证明“节省分钟也有价值”，但不把行业平均值说成项目实测收益 |
| 安全 | NSC: 2023 美国工伤成本 `$176.5B`，每起 medically consulted injury `$43,000`；OSHA: disabling nonfatal injury 直接工伤赔偿超过 `$1B/week` | 用于量化 hazard route 和 near-miss evidence capture 的价值池 |
| 质检 | IISE: COPQ 在制造业常见为销售额 `5%-35%`，平均约 `15%`；APQC 可见中位数 `$28.50 / $1,000 revenue` | 用于量化 IQC action card、quality hold 和 QMS event 的价值池 |
| 培训 | NAM / Manufacturing Institute: 制造商每年培训投入 `$31.9B`，新员工平均 `47.6 hours` 培训；ATD: `2024` 每学习小时平均 `$165` | 用于量化 lao-shi-fu 经验传承和 work instruction guidance |

新增 ROI 公式记忆：

```text
Annual gross value =
  downtime value
+ safety value
+ quality value
+ training / knowledge-transfer value

WearEdge-attributable value =
  annual gross value * attribution factor
```

建议在正式材料中使用 `10%-30%` attribution factor，直到有真实工厂 pilot 数据。这样比直接宣称节省全部停机/工伤/废品成本更可信。

本轮新增量化例子：

| 场景 | 保守测算 |
| --- | --- |
| 停机 | 只按 Siemens FMCG 低端 `$36,000/hour`，每月节省 `10 minutes`，年化 gross opportunity 为 `$72,000/year` |
| 安全 | 避免 1 起 medically consulted injury 每 2 年，年化 gross opportunity 约 `$21,500/year` |
| 质量 | `$20M` 年产线，把 COPQ 降低 `0.25 percentage points`，年化 gross opportunity 为 `$50,000/year` |
| 培训 | 每位新员工 `47.6 hours`，降低 `20%` 支持时间，按 `$165/hour` 约 `$1,571/new hire` |
| 单线保守 pilot | gross value pool 约 `$108.5k/year`，按 `25%` attribution，WearEdge-attributable value 约 `$27.1k/year` |
| 中型供应商 pilot | gross value pool 约 `$478.6k/year`，按 `25%` attribution，WearEdge-attributable value 约 `$119.6k/year` |

本轮新增 learning：

- 全场总冠军叙事需要的不只是“我们能跑 Gemma 4”，还要能回答“为什么值得部署”。
- ROI 文档要用公开 benchmark 建立价值池，用 pilot KPI 证明归因，不能直接用外部平均值冒充实际节省。
- 停机价值最容易打动评委，因为分钟级改善就能产生年化数字。
- 安全价值必须保持克制，强调 near-miss、风险识别和 human gate，不把 AI 描述成安全放行者。
- 质检价值要和 ASQ/IISE 的 COPQ 口径对齐，便于评委理解 scrap、rework、warranty、complaint handling。
- 培训价值是 lao-shi-fu 的社会影响和商业价值交汇点：不是替代老师傅，而是把老师傅的排查步骤变成可复制的 evidence loop。

本轮仍未解决的风险：

- 这些 ROI 仍是 public benchmark + scenario model，不是 WearEdge 真实客户数据。
- 需要后续补真实 plant baseline：downtime cost/hour、MTTR、near-miss rate、scrap/rework、training hours、expert interruption hours。
- 大型汽车 `$2.3M/hour` 场景很强，但除非目标客户确实是该类高吞吐产线，否则正式提交中应优先使用 `$36,000/hour` 和 `$150,000/hour` 的保守例子。

更新后的下一步：

1. 在 `docs/submission-brief.md` 中加入 `impact-and-roi.md` 的 4 类价值池摘要。
2. 将 5 分钟视频脚本前 30 秒改成“停机分钟 + 安全事故 + 质量返工 + 老师傅断层”的量化痛点。
3. 准备一个 pilot KPI 表：baseline、WearEdge metric、90-day success signal。
4. 后续若有真实工厂/演示数据，优先替换公开 benchmark 场景，形成 project-specific ROI。

## 12. 2026-05-15 推进记录：README 当前仓库内容重构

本轮已更新：

```text
README.md
```

本轮目的：

- 将 README 的“当前仓库内容”从逐文件清单改成评审可读的工程地图。
- 延续公开首页口径：首屏和主叙事使用 `deterministic agent workflow`、`bounded workflow runtime` 等产品化表达。
- 避免在 README 公开入口堆放外部工具感名称，让评委先理解项目能力、证据边界和目录结构。

本轮 README 调整：

| 区域 | 改动 |
| --- | --- |
| 总览表 | 新增按层级组织的仓库地图：runtime、evidence modules、wearable client、industrial RAG、deployment scripts、evidence docs、automated tests |
| Runtime And Gateway | 明确 `jetson/` 是当前可运行主线，模型解释证据，动作路由和人工确认由确定性规则层控制 |
| Evidence Modules | 合并 maintenance、IQC、WI/changeover 的证据层说明，强调不凭空给结论 |
| Edge Deployment And Hardware | 前置 Jetson runbook、model manifest、hardware milestones、NVMe、PB551、巡检脚本等证据 |
| Client / RAG / Assets | 将 M400 客户端、工业 RAG 包和 POC 图片资产归为演示与集成材料 |
| Documentation And Validation | 把 benchmark、ROI、test log、contract、maintenance session、five-agent validation 作为评审入口 |
| Tests | 不再列一长串测试文件，改为概括 `122 passed` 覆盖范围 |

本轮 learning：

- README 应该是项目入口，不是完整技术目录；技术深度应该由 `docs/` 承接。
- “当前仓库内容”最重要的是帮助评委判断仓库成熟度：哪些能跑、哪些有证据、哪些用于复现、哪些用于测试。
- 二进制部署包和过细测试文件不应该成为首页重点；首页应优先展示可复现路径和证据链。
- 中性命名能让项目显得更专业，避免评委把注意力放到工具生态，而不是 WearEdge Pro 自身。

更新后的下一步：

1. 继续重构 README 首屏，加入 `Judge Quick Path`。
2. 将长代码片段逐步移出 README，保留链接到技术深页。
3. 在 `docs/submission-brief.md` 中复用 README 的工程地图，但进一步压缩为 3 分钟评审入口。
