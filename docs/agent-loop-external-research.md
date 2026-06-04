# WearEdge 5-Agent 外部调研与编排取舍

更新日期：2026-05-13

本文档保存 WearEdge Pro 对 5 个工业 agent 的外部项目调研、可借鉴工程模式，以及 LangGraph 与 Agently/TriggerFlow 在本项目中的取舍判断。它是后续重构 agent loop 的设计依据，不改变当前网关接口、M400 客户端或 Jetson 运行代码。

## 一句话结论

WearEdge 的主编排应采用 **Agently/TriggerFlow 风格的确定性工业 workflow**，同时吸收 LangGraph 的 ReAct loop、tool routing、human-in-the-loop、checkpoint 和可视化思想。也就是说：不把 LangGraph runtime 直接引入当前边缘网关，而是把它的成熟 agent loop 经验映射成 Agently/TriggerFlow 的 stage、state、runtime stream、validator 和 Action Runtime logs。

```text
M400 image / audio / device context
  -> normalize_mode
  -> identify_context
  -> collect_evidence
  -> bounded_react_tools
  -> validate_contract
  -> deterministic_action_map
  -> action_card
  -> integration_event
  -> runtime_stream.close
```

## 调研范围

调研时间窗口按当前日期 `2026-05-13` 计算，优先选择 `2025-05-13` 以后创建或仍有更新的项目。筛选重点不是 star 数，而是能否给 WearEdge 的 5 个现场 agent 提供可落地的 workflow、ReAct loop、evidence collection、validator、event escalation 或 POC 数据源。

| 项目 | 最近活动 | 对 WearEdge 的价值 |
| --- | --- | --- |
| [Agently](https://github.com/AgentEra/Agently) | GitHub pushed `2026-05-05` | 主架构参考：contract-first output、TriggerFlow lifecycle、runtime stream、Action Runtime logs |
| [LangGraph](https://github.com/langchain-ai/langgraph) | GitHub pushed `2026-05-13` | ReAct loop、ToolNode、state graph、post-model hook、checkpoint、human-in-the-loop 参考 |
| [PHMForge](https://github.com/DeveloperMindset123/PHMForge-A-Scenario-Driven-Agentic-Benchmark-for-Industrial-Asset-Lifecycle-Maintenance) | GitHub pushed `2026-05-03` | 预测性维护 benchmark、22 个 MCP 工具目录、ReAct/ReActXen 评估指标 |
| [AgentIoT](https://github.com/HySonLab/AgentIoT) | GitHub pushed `2026-02-20` | 工业 IoT edge/fog/cloud 多 agent 分层、自适应阈值和迭代评估 |
| [AWS industrial AgentCore sample](https://github.com/aws-samples/sample-agentic-code-generation-for-industrial-analytics-and-predictive-maintenance) | GitHub pushed `2025-12-03` | 工业传感数据分析、code interpreter、memory、设备规格查询和维护建议模式 |
| [GenAI Work Instructions Updater](https://github.com/camposfabioc/GenAI-Work-Instructions-Updater) | GitHub pushed `2026-05-04` | WI / Changeover 最可借鉴：RAG、structured schema、reference / entailment / glossary validator |
| [AI visual inspection](https://github.com/PPKAnalyst/ai-visual-inspection) | GitHub pushed `2026-03-18` | IQC 两段式视觉管线：YOLOv8 先产出缺陷 evidence，VLM 再解释 |
| [Industrial Safety System](https://github.com/arunprasad-04/AI-Powered-Smart-Industrial-Safety-System) | GitHub pushed `2026-02-25` | Hazard agent 的事件模型：PPE、fall、proximity、geofence、升级规则 |
| [AgentIAD paper](https://hf.co/papers/2512.13671) | Hugging Face paper `2025-12-15` | 工业异常检测 agent：Perceptive Zoomer、Comparative Retriever、逐步验证轨迹 |
| [AssetOpsBench paper](https://hf.co/papers/2506.03828) | Hugging Face paper `2025-06-04` | 工业资产运维 agent benchmark，适合设计 maintenance golden scenarios |
| [PCB defect dataset](https://hf.co/datasets/Tanishjain9/industrial-pcb-defect-detection-dataset) | HF updated `2026-05-01` | IQC / PCB 缺陷 POC 数据源 |
| [PPE Jetson ONNX model](https://hf.co/Tanishjain9/yolov8n-ppe-detection-6classes) | HF updated `2025-11-27` | Hazard agent 可试的边缘 PPE detector |
| [PPE dataset](https://hf.co/datasets/51ddhesh/PPE_Detection) | HF updated `2025-11-27` | PPE / safety detection 训练或回归数据 |
| [MVTec anomaly dataset](https://hf.co/datasets/TheMrguiller/mvtec_anomaly_detection) | HF updated `2025-09-02` | 工业异常检测 baseline 数据源 |

## LangGraph 的可取点

LangGraph 对 WearEdge 最有价值的不是“换一个框架”，而是它已经把工业级 agent loop 中容易失控的部分显性化了：

- **ReAct loop 结构清楚**：典型路径是 `agent -> tools -> agent`，直到没有 tool call 或达到 step limit。WearEdge 应借鉴这个结构做 `bounded_react_tools`，但只允许它补充证据，不允许它直接决定停产、放行或转产完成。
- **状态与路由显性化**：StateGraph、conditional edges、ToolNode、post-model hook 都把状态、工具调用和后处理拆开。WearEdge 可将它映射为 TriggerFlow chunks，而不是藏在一个大 helper 里。
- **post_model_hook 值得借鉴**：它适合做 guardrail、human-in-the-loop、validation 和审计。WearEdge 的对应 stage 是 `validate_contract`、`uncertainty_guard` 和 `deterministic_action_map`。
- **checkpoint / interrupt 是生产级 agent 的关键**：现场流程会遇到人工确认、补拍、扫码、等待 MES/QMS/CMMS 的情况。LangGraph 的 checkpoint 和 interrupt 思想应映射到 Agently 的 `pause_for`、`continue_with`、`save/load`。
- **step limit / recursion limit 防失控**：工业现场不能让模型无限循环。WearEdge 应固定每个 agent 的最大工具轮数、最大模型调用数和失败降级路径。
- **graph visualization 有调试价值**：可视化不是业务结果，但对定位 agent 误判很有帮助。WearEdge 应让 TriggerFlow definition 和 runtime stream 成为可视化来源，避免维护第二份手绘流程图。

不建议当前直接引入 LangGraph runtime 的原因：

- WearEdge 已经有 Agently-style trace、runtime stream、contract repair 和 deterministic action map，直接换 runtime 会增加 Jetson 端依赖与迁移成本。
- 当前 5 个 agent 的核心风险不是“缺图执行引擎”，而是 evidence schema、uncertainty guard、领域 validator 和 action rule 还需要工业化。
- LangGraph 适合作为成熟模式参考，Agently/TriggerFlow 更适合作为本项目的主编排口径。

## Agently 的可取点

Agently 更贴近 WearEdge 当前目标：把模型能力包进可测试、可观测、可恢复的工业应用框架，而不是让 agent 自由聊天。

- **Contract-first output**：每个 agent 都必须输出稳定字段。当前 `jetson/output_contract.py` 已经走在这个方向，后续应升级为 mode-specific structured contract + validator + repair policy。
- **TriggerFlow lifecycle**：`open -> sealed -> closed` 很适合 M400 一次现场请求。`closed` 后 action card 和 integration event 冻结，便于审计和回放。
- **Runtime stream**：M400 UI 不应消费原始 token stream，而应消费业务事件，例如 `evidence.collected`、`contract.validation.completed`、`action.card.created`、`workflow.closed`。
- **Action Runtime logs**：每个 detector、RAG、MCP、telemetry 查询都要有输入、输出、耗时和成功状态。后续对接 DevTools 或审计日志时，这些 action logs 是主要证据。
- **pause / resume**：未识别机器、SKU、产品、WI 来源或证据不足时，workflow 应暂停等待补拍、扫码、人工确认，而不是让模型硬猜。
- **stage 可测试**：每个 stage 都应能单测。尤其是 `identify_context`、`collect_evidence`、`validate_contract`、`deterministic_action_map` 必须独立可测。

LangGraph 到 Agently/TriggerFlow 的映射建议：

| LangGraph 概念 | WearEdge / Agently 映射 |
| --- | --- |
| `StateGraph` | TriggerFlow definition |
| graph node | named chunk / stage |
| graph state schema | execution state + mode-specific domain contract |
| `conditional_edges` | TriggerFlow `if` / `match` / `when` |
| `ToolNode` | Agently Action Runtime / MCP / local function executor |
| `post_model_hook` | `validate_contract` / `uncertainty_guard` / `deterministic_action_map` |
| checkpoint | TriggerFlow `save/load` |
| interrupt | TriggerFlow `pause_for` / `continue_with` |
| streaming updates | WearEdge business `runtime_stream` |
| `remaining_steps` / recursion limit | `bounded_react_tools.max_rounds` |
| structured response | Agently output schema + existing `output_contract` validator |

## 外部项目可取之处

### PHMForge -> lao-shi-fu predictive maintenance agent

PHMForge 的核心价值是把预测性维护拆成可评估的场景、工具和指标，而不是只让 LLM 解释一张照片。它包含 PHM 场景、MCP-native tool catalog、ReAct/ReActXen 对比和 Pass@1 / steps / tokens 等指标。

WearEdge 应采用：

- 建立 `maintenance` agent 的 evidence tools：`load_telemetry_snapshot`、`load_maintenance_history`、`estimate_rul`、`classify_fault`、`check_compliance`、`generate_recommendations`。
- 用 PHMForge 类似指标评估 POC：`correct_action_channel`、`evidence_used`、`steps`、`tokens`、`latency`、`repair_count`。
- 将 `lao-shi-fu` 的经验规则沉淀为 tool 和 rule，而不是写进 prompt 长文本。

不直接采用：

- 不在 Jetson 端复制完整 benchmark runtime 或 WatsonX 模型矩阵。
- 不把预测模型训练放进 M400 同步请求。Jetson 同步链路只读取已准备好的 telemetry / health feature。

### AgentIoT -> edge / fog / cloud 分层

AgentIoT 的 SEMAS 架构把工业异常检测拆成 edge feature extraction、fog orchestration、cloud policy / knowledge update。它适合 WearEdge 的现场形态：M400 和 Jetson 先做低延迟 evidence，后端系统再做长期知识、阈值和闭环。

WearEdge 应采用：

- **Edge**：M400 图像、音频、设备元数据、扫码/OCR。
- **Fog**：Jetson detector、VLM、RAG、contract validation、action card。
- **Cloud / enterprise systems**：QMS、CMMS、MES、EHS、知识库、阈值更新、闭环复盘。
- 允许阈值或规则来自后台策略，但本地 action map 必须可解释并可回退。

不直接采用：

- 不把 MQTT 多 agent pipeline 原样塞进当前 FastAPI gateway。
- 不把模型训练、阈值校准和现场同步推理放在同一个请求里。

### AWS industrial AgentCore sample -> maintenance analytics pattern

AWS sample 中预测维护 sample 仍标注 under development，但 advanced analytics 部分有可借鉴的思路：用安全沙箱执行 Python 分析传感数据，结合 memory 和设备规格查询，生成维护建议。

WearEdge 应采用：

- 后续在维护 agent 中引入 `safe_code_analysis` 或预定义 analytics tools，但同步请求必须限时。
- 保留 conversation / session memory，用于同一台机器连续排查，而不是每张图从零开始。
- 设备规格和历史工单应作为 retrieval evidence，不应让模型凭常识猜参数。

不直接采用：

- 不让现场 M400 请求开放任意代码执行。
- 不依赖云端 AgentCore 作为当前边缘 PoC 的必需组件。

### GenAI Work Instructions Updater -> General WI / Changeover

这个项目最适合 WearEdge 的 WI 和 Changeover。它的核心不是“会生成文字”，而是 RAG、结构化 diff、Pydantic schema、reference validator、entailment validator、glossary validator 组成的生产保护层。

WearEdge 应采用：

- WI / Changeover 必须先检索机器、SKU、recipe、SOP、quality standard 和设备 glossary。
- 输出必须带来源引用或 evidence id；没有来源时进入 `human_confirm_required`。
- 术语、设备 ID、SKU、工装编号、工艺参数必须做 glossary / exact-match validator。
- Changeover 不允许在机器或 SKU 未识别时输出 `ready`、`completed`、`release` 这类完成结论。

不直接采用：

- 不把 WI 更新场景的文档 diff 逻辑原样搬进实时 M400 操作指导。
- 不让 LLM 自动改 WI 或标准；WearEdge 只做现场指导和风险提示。

### AI Visual Inspection / AgentIAD / HF datasets -> IQC agent

IQC 不能只靠 VLM 对整张图描述。更稳的路线是先用检测器、异常检测或局部放大工具生成 evidence，再由 VLM 做解释和处置建议。

WearEdge 应采用：

- `defect_detector` 先输出 `class / confidence / bbox / crop_id`。
- 对低置信度或小缺陷区域做 `perceptive_zoom`，只把关键 crop 交给 VLM。
- 使用 `comparative_retriever` 查找相似良品/不良品案例。
- VLM 输出 `product / quality_risk / disposition / action`，但 disposition 由质量规则二次校验。
- POC 数据源可用 PCB defect、MVTec、NEU-DET，再逐步替换为现场产品数据。

不直接采用：

- 不让 VLM 从一张非产品图直接推断质量风险。
- 不把 detector confidence 等同于最终 QMS 判定；它只是 evidence。

### Industrial Safety YOLO projects -> Hazard Exposure agent

安全场景适合事件化和确定性升级。PPE、fall、proximity、geofence 都可以先由 detector / rule 输出事件，再由 Hazard agent 解释现场、给 operator action。

WearEdge 应采用：

- evidence event 类型：`NO_HELMET`、`NO_VEST`、`FALL_DETECTED`、`PROXIMITY_ALERT`、`DANGER_ZONE_ENTRY`、`UNAUTHORIZED_ACCESS`。
- deterministic escalation：高危事件直接映射 `stop_and_make_safe`、`supervisor_alert`、`ehs_case`。
- LLM 负责解释 `scene/risk/action`，不负责决定是否触发急停或放行。
- 事件去重、冷却时间和 priority mapping 必须是规则，不是 prompt。

不直接采用：

- 不把示例项目里的 Twilio、Windows camera、全局变量状态和本地 GUI 直接移植到 Jetson。
- 不把“生产就绪”声明当成工业安全认证。

## 5 个 Agent 的采用矩阵

| WearEdge agent | 主要借鉴 | 新增 evidence | 决策原则 |
| --- | --- | --- | --- |
| lao-shi-fu predictive maintenance | PHMForge、AgentIoT、AWS analytics | telemetry、history、RUL、fault、compliance | ReAct 查证据，规则定优先级和工单目标 |
| IQC online quality inspection | AI visual inspection、AgentIAD、PCB/MVTec datasets | defect bbox、crop、confidence、similar cases | detector 先产 evidence，VLM 解释，QMS 规则定 disposition |
| Changeover guidance | WI Updater、Agently validators | machine、SKU、recipe、SOP、glossary、OCR | 未识别机器/SKU 必须暂停确认 |
| General WI | WI Updater、RAG validator | machine、WI section、source reference、glossary | 必须带来源；无来源则只给安全的通用建议 |
| Hazard Exposure | Safety YOLO projects、Agently action logs | PPE、fall、proximity、geofence、zone | 高危 action 由规则触发，LLM 只解释和补充 |

## 目标 Agent Loop

后续实现时，5 个 agent 应共享同一条工业 workflow，只在 evidence tools、output contract 和 action rules 上分化：

```text
normalize_mode
  输入: analysis_mode
  输出: mode

identify_context
  输入: image, prompt, device metadata
  输出: machine_id, sku, product_id, area, uncertainty

collect_evidence
  输入: mode, context
  输出: detector_events, rag_sources, telemetry_snapshot, similar_cases

bounded_react_tools
  输入: prompt, context, evidence
  输出: evidence_gap_resolution
  约束: max_rounds, tool allowlist, timeout, no direct final action

model_infer
  输入: contract prompt, selected evidence, image/crop
  输出: structured draft

validate_contract
  输入: draft, mode contract
  输出: contract_ok, violations, repaired_draft

uncertainty_guard
  输入: context, evidence, contract
  输出: need_identification / human_confirm_required / ready_for_action_map

deterministic_action_map
  输入: mode, evidence, validated fields
  输出: action_channel, owner, priority, integration_target

build_action_card
  输入: action decision, evidence ids
  输出: operator-facing card

build_integration_event
  输入: request_id, action_card, evidence
  输出: QMS / CMMS / EHS / MES envelope

close_execution
  输出: agently_trace, runtime_stream, audit record
```

## 工业确定性规则

这些规则应优先于模型输出：

1. `machine_id` 未识别时，Changeover 和 WI 不能输出具体机台步骤，只能要求补拍、扫码或人工选择。
2. `sku` 未识别时，Changeover 不能输出 `ready / completed / release`。
3. `product_id` 或 defect evidence 不足时，IQC 不能输出最终放行，只能输出 `quality_review` 或 `contain_and_inspect`。
4. `FALL_DETECTED / DANGER_ZONE_ENTRY / PROXIMITY_ALERT` 等高危事件命中规则时，Hazard 直接进入安全 action map。
5. Maintenance 没有 telemetry 或历史证据时，只能输出观察、检查、补采信号，不能声称预测到具体 RUL。
6. ReAct loop 只能调用 allowlisted tools，不能绕过 action map。
7. 模型输出修复最多一次；仍失败则返回 `contract_failed` 并要求人工确认。
8. runtime stream 的最后状态必须是 `workflow.closed` 或明确失败状态。

## Golden Scenarios 与验收指标

后续实现每个 agent 至少 5 条 golden scenarios：

| 指标 | 含义 |
| --- | --- |
| `contract_ok` | 输出结构是否合格 |
| `repaired` | 是否触发 bounded repair |
| `evidence_used` | 是否引用 detector / RAG / telemetry / source |
| `action_channel` | 是否命中预期行动通道 |
| `priority` | 优先级是否符合规则 |
| `owner` | operator / quality_engineer / maintenance / ehs 等责任人是否正确 |
| `latency_ms` | Jetson 同步请求是否可接受 |
| `runtime_stream.closed` | workflow 是否正常关闭 |
| `unsafe_final_action_blocked` | 未识别上下文时是否阻止放行/完成类结论 |

建议首批 golden scenarios：

- Maintenance：可见漏油但无 telemetry、异常振动且有历史工单、温升趋势、未知机台、已知停机风险。
- IQC：明显划痕、低置信小缺陷、良品样例、产品未知、需要扩大翻检。
- Changeover：机器和 SKU 都识别、SKU 未识别、步骤中断、清线未完成、验证项失败。
- WI：已识别机台问操作要点、未知机台、涉及 LOTO、涉及参数设定、来源缺失。
- Hazard：无安全帽、人员靠近设备、跌倒、进入禁区、误报/低风险场景。

## 实施顺序建议

1. 新增 shared evidence schema 和 `identify_context` guard。
2. 为 5 个 agent 建立 golden scenarios 和 POC runner。
3. 将现有 `agently_orchestrator` 拆成更显性的 stages，并让 runtime stream 输出 business events。
4. 给 Changeover / WI 接 RAG source stub 和 glossary validator。
5. 给 IQC / Hazard 接 detector evidence stub，先用模拟 evidence 验证 action map，再接真实 YOLO/ONNX。
6. 给 Maintenance 接 telemetry/history stub，再接 Jetson 或后台数据源。
7. 引入 pause/resume 语义：补拍、扫码、人工确认、等待 QMS/CMMS/MES 回执。

## 当前边界

- 本文档只保存外部调研和架构取舍，不代表这些外部项目已经被集成。
- 部分 GitHub 项目是示例或研究项目，不能直接视为工业认证方案。
- Hugging Face 的 PPE / defect 数据源可用于 POC，但现场产品和工位仍需要自有数据校准。
- 当前 Jetson PoC 仍以本地 deterministic Python orchestrator 承载 Agently-style flow；后续才逐步迁移到真实 Agently TriggerFlow runtime。

## 参考链接

- Agently: https://github.com/AgentEra/Agently
- Agently docs: https://agently.tech/docs
- LangGraph: https://github.com/langchain-ai/langgraph
- PHMForge: https://github.com/DeveloperMindset123/PHMForge-A-Scenario-Driven-Agentic-Benchmark-for-Industrial-Asset-Lifecycle-Maintenance
- AgentIoT: https://github.com/HySonLab/AgentIoT
- AWS industrial AgentCore sample: https://github.com/aws-samples/sample-agentic-code-generation-for-industrial-analytics-and-predictive-maintenance
- GenAI Work Instructions Updater: https://github.com/camposfabioc/GenAI-Work-Instructions-Updater
- AI visual inspection: https://github.com/PPKAnalyst/ai-visual-inspection
- Industrial Safety System: https://github.com/arunprasad-04/AI-Powered-Smart-Industrial-Safety-System
- AgentIAD paper: https://hf.co/papers/2512.13671
- AssetOpsBench paper: https://hf.co/papers/2506.03828
- PCB defect dataset: https://hf.co/datasets/Tanishjain9/industrial-pcb-defect-detection-dataset
- PPE Jetson ONNX model: https://hf.co/Tanishjain9/yolov8n-ppe-detection-6classes
- PPE dataset: https://hf.co/datasets/51ddhesh/PPE_Detection
- MVTec anomaly dataset: https://hf.co/datasets/TheMrguiller/mvtec_anomaly_detection
