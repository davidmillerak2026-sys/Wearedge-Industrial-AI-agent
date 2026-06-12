# Finals Foundation Roadmap

更新日期：2026-06-12

## 结论

从决赛目标倒推，当前最好的早期地基不是继续堆单点 Demo，而是把 Wearedge 固定成一个可复验的产线级闭环：

```text
统一产线上下文
  -> 质量 / 能源 / 运维 / 柔性生产 / Workflow Canvas 多智能体协同
  -> 端侧 Wearedge Agent Runtime
  -> Xcelerator / 工易魔方工作流执行
  -> 自然语言交互 + 决策过程可视化
  -> 指标、审批、回写、审计
```

决赛要求是从五个赛题方向中至少选三个方向完成联合解决方案。为了冲第一名，Wearedge 不应只做最低的三个方向，而应保留当前的五方向叙事：设备运维、质量管控、能源管理、柔性生产、基于工易魔方开发的 Workflow Canvas 智能体。

核心业务场景建议固定为：

```text
多 SKU 离散制造产线的跨域异常协同决策。

订单变化和换型压力出现时，设备状态、质量缺陷、能源负荷和交付节拍相互冲突。
Wearedge 在端侧汇聚 MES / QMS / EMS / CMMS / 设备信号 / 视觉证据，
给出主方向、建议动作、证据、指标、责任人、残余风险和人工确认项，
再由工易魔方完成工作流执行、Dashboard 展示和 HumanApprovalGate 审批。
```

## 早期最该打牢的 7 个基础

| 基础 | 为什么现在做 | 当前仓库状态 | 决赛验收目标 |
| --- | --- | --- | --- |
| 统一决策上下文 | 决赛端到端验证需要所有 Agent 使用同一个输入契约。 | `evals/competition_offline_dataset.jsonl`、`workflows/wearedge_wfc_poc_payload.json` 已存在。 | 固化 `plantId / lineId / stationId / assetId / sku / orderId / evidence_refs / metrics / constraints / approval_risk`。 |
| Agent 输出契约 | 多智能体协同不能只靠自然语言，要能写表、审批、复盘。 | `/v1/workflow-canvas/decision` 已输出主方向、指标、确认项和 WFC blocks。 | 每个 Agent 输出 `status / confidence / evidence / action / owner / residual_risk / approval_required`。 |
| 指标评估闭环 | 决赛明确要求延迟 <=500ms、决策准确率 >=90%。 | 初赛离线报告和 15 条决赛验证集均通过；决赛集五个主方向各 3 条；`docs/finals-latency-benchmark-report.md` 已给出本地回放延迟；`docs/finals-local-gateway-latency-benchmark-report.md` 已给出本地 FastAPI HTTP 网关延迟。 | 继续扩大到真实/半真实标签集、真实平台 smoke、Jetson / IPC 端侧延迟日志，并区分模型推理延迟、API 往返延迟与规则决策延迟。 |
| 工易魔方执行主干 | 决赛要在 Xcelerator 或工易魔方中完成端到端/工作流验证。 | 资源块、Python Function Block、runbook、Xcelerator OpenAPI 草稿已具备；WFC 04/05/06 仍是 fallback。 | 真实 WFC 工作流跑通：数据表更新、Dashboard、run log ok=true、HumanApprovalGate。 |
| 人机协同界面 | 决赛要求自然语言交互与决策过程可视化。 | `jetson/app.py` 有 `/v1/infer` 与简易 HTML；`dashboard-mock.html` 和 `finals-hmi-console.html` 提供可视化/HMI 原型。 | 做成正式 HMI：自然语言提问、证据引用、决策路径、指标卡、审批状态、历史审计。 |
| 端侧运行证据 | Wearedge 的差异化是端侧 Agent Runtime，而不是云端 Chatbot。 | `docs/edge-agent-runtime-for-xcelerator.md`、runtime profile、Jetson 文档已具备。 | 采集 Jetson / IPC / 工控机 latency、资源占用、断网可用、数据不出厂证据。 |
| 证据边界和审计 | 决赛答辩必须可信，不能把模拟说成真实。 | final readiness 已标注 6 个最终人工文件和 3 个 WFC fallback。 | 所有图、视频、指标、日志都有来源；模拟、平台 PoC、真实产线证据分层。 |

## 推荐的方向组合

最低合规组合是三个方向，但推荐按五方向保留：

| 方向 | 决赛角色 | 当前证据 |
| --- | --- | --- |
| 设备运维智能体 | 发现设备劣化、预测风险、提出维护动作和停线/降速审批项。 | 维护 F1、提前预警、root cause Top3 离线指标；维护 KB 和阈值守卫。 |
| 质量管控智能体 | 缺陷遏制、首件确认、QMS 事件建议、质量放行边界。 | IQC 质量计划、视觉缺陷 evidence、质量改进指标。 |
| 能源管理智能体 | 峰谷/空载/负荷优化建议，受生产和质量约束。 | 能源预测准确率、节能率、能源表上下文。 |
| 生产制造-柔性生产智能体 | 订单变化、换型、节拍、组件复用和首件确认。 | 调度效率提升、换型 checklist、released source 约束。 |
| 基于工易魔方开发的智能体 | 资源块、Python Function Block、数据表、Dashboard、审批编排。 | WFC 资源块包、runbook、payload、smoke；live Dashboard/run-log/approval 待替换。 |

早期主线应以 `设备运维 + 质量 + 柔性生产 + Workflow Canvas` 为演示骨架，能源作为加分方向嵌入同一产线场景。这样既满足不少于三个方向，又能讲清楚“从单点智能到产线级智能”的跃迁。

## 当前应该优先做什么

1. 固化统一上下文和输出 schema。所有方向都使用同一个 `line_context`，避免后期 WFC 数据表、Dashboard 和评估脚本各写各的。
2. 将当前 15 条决赛验证集继续扩到真实/半真实标签集。决赛指标至少要能解释 `accuracy>=90%` 的样本量、标签来源和失败样例。
3. 把 WFC 04/05/06 fallback 替换成真实平台执行证据。优先级高于继续润色文案。
4. 做正式 HMI 原型。自然语言输入、决策路径、证据引用、指标卡、人工确认状态要在一个界面里出现。
5. 建立端侧性能基线。先用 `python scripts/benchmark_workflow_canvas_latency.py` 固化本地协同决策延迟，再用 `python scripts/benchmark_local_gateway_latency.py` 固化本地 HTTP 网关延迟，最后在 Jetson / IPC 上复跑 HTTP benchmark 并补资源占用日志；规则决策延迟、API 往返延迟、模型推理延迟必须分开测，避免被真实 VLM 图像推理延迟拖累 `<=500ms` 的协同决策指标。
6. 准备双路径演示。A 路是真实 Xcelerator / 工易魔方；B 路是本地 API + Dashboard + 录屏，防止现场环境不稳定。

## 不建议现在过早投入的事

- 不要先把报名文案磨到最终版。最终字段应等真实 WFC/HMI/端侧证据更完整后再收口。
- 不要先训练或替换大模型。当前短板不是模型名字，而是端到端平台执行、HMI 和证据闭环。
- 不要只做一个漂亮大屏。没有数据契约、审批和审计的大屏无法证明工作流执行。
- 不要把离线 1ms 决策延迟写成端侧多模态推理延迟。两者必须分开解释。

## 自动检查

早期地基用以下命令检查：

```powershell
python scripts/verify_finals_foundation.py --json
python scripts/benchmark_workflow_canvas_latency.py
python scripts/benchmark_local_gateway_latency.py
```

该命令只证明 foundation readiness，不证明 finals readiness。决赛完成仍需要真实平台端到端执行证据、正式人机协同界面、签署材料和提交成功截图。
