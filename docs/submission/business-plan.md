# Business Plan Draft

更新日期：2026-06-12

## 项目背景

多 SKU 离散制造现场正在从单一自动化向柔性、可重构、数据驱动生产转型。换型、设备健康、质量风险和能耗优化往往由不同系统和人员分别处理，导致异常响应慢、证据链断裂、人工协调成本高。西门子 Xcelerator 和工易魔方提供了低代码 IT/OT 工作流底座，适合将工业智能体能力转化为可执行、可验证、可回写的联合解决方案。Wearedge 的企业组差异化是把智能体运行时放到 Jetson、IPC、本地工控机或边缘服务器，贴近产线数据运行，再由平台完成编排和审批。

## 项目方案

Wearedge Industrial AI Agent 是面向柔性可重构产线的多智能体协同决策系统。系统通过工易魔方读取 MES、设备信号、质量数据、能源数据和工作流上下文，调用部署在端侧算力上的 Wearedge Agent Service 进行多方向评估，输出主方向、优先级、建议动作、确认项、残余风险和 Dashboard 数据表更新内容。

## 总体框架

```text
M400 / Camera / OPC UA / MES / QMS / EMS / CMMS / released checklist
  -> Wearedge Edge Agent Runtime on Jetson / IPC / local server
  -> 工易魔方资源块和 Python Function Block
  -> 多智能体评估与确定性守卫
  -> 协同决策、Dashboard、全局数据表、HumanApprovalGate
```

## 智能体划分

| Agent | Role |
| --- | --- |
| 设备运维智能体 | 预测性维护、信号阈值评估、根因候选和工单建议 |
| 质量管控智能体 | 缺陷 containment、扩检、停线或质量工程师确认建议 |
| 能源管理智能体 | 能耗预测、空转识别、节能窗口建议 |
| 柔性生产智能体 | 换型、目标 SKU、released checklist 和首件验证 |
| Workflow Canvas 智能体 | 资源块、功能块、数据表、Dashboard 和人工确认编排 |

## 算法设计与模型选择

- 规则和指标层：维护 F1、预警提前时间、根因 Top3、能源预测准确率、节能率、质量提升、调度效率和延迟由确定性 evaluator 计算。
- 智能体层：当前 PoC 默认使用 Gemma 4 E2B 通过 llama.cpp / llama-server 在端侧运行，模型负责把图片、症状、证据和上下文转成可读解释、行动建议和协同摘要。
- 知识层：RAG/KB 保存设备手册、released checklist、维护记录、质量计划和现场校准知识。
- 安全层：高风险动作由确定性守卫标记责任人、确认项和残余风险，进入人工审批。
- 决策边界：工易魔方主接口 `/v1/workflow-canvas/decision` 不依赖模型直接拍板，而是使用 KPI 指标矩阵、规则评分、优先级排序和 `HumanApprovalGate` 做最终动作边界。
- 模型选择：PoC 阶段支持本地/边缘大模型或 OpenAI-compatible API；报名材料不绑定不可获得的专有模型权重。

## 工作流定义

工易魔方侧定义 `Wearedge Agent Service` 自定义资源块，配置 `agentHost`、`agentPort`、`apiKeyRef`、`plantId`、`lineId`。`CallWearedgeDecisionApi` Python Function Block 将上下文 POST 到 `/v1/workflow-canvas/decision`，返回值写入全局数据表和 Dashboard。涉及停机、放行、能耗策略切换等高风险动作时，工作流进入 `HumanApprovalGate`。

## 技术优势

- 证据优先：模型解释证据，确定性逻辑处理指标、动作和责任边界。
- 端侧可部署：可在 Jetson、IPC、本地工控机或边缘服务器运行 Agent Runtime，支持数据不出厂和局域网演示。
- 平台适配：REST API 可由工易魔方 Python Function Block 调用。
- 多智能体联合：可覆盖不少于三个赛题方向。
- 安全边界：高风险动作进入人工确认，不直接控制 OT。
- 可验证：仓库包含离线评估、smoke test、pytest 和工程证据文档。

## 企业组落地能力

企业组提交将 Wearedge 表达为可与 Siemens Xcelerator / 工易魔方共创的联合产品，而不是个人作品或一次性 demo。交付包包括端侧 Agent Runtime、WFC 资源块原型、Xcelerator OpenAPI、离线指标评估、Dashboard 证据和商业计划书。真实企业主体、联系人、知识产权和无不良记录承诺由负责人在最终提交前补齐。

## 预期收益

| Benefit | Measurement |
| --- | --- |
| 减少非计划停机 | 维护 F1、预警提前时间、根因 Top3 |
| 降低质量逃逸和返工 | 质量相对提升、扩检/隔离响应时间 |
| 降低能耗 | 能源预测准确率、节能率 |
| 提高换型效率 | 调度效率提升、组件复用率 |
| 降低人工协调成本 | 决策路径可视化、人工确认闭环 |
| 降低数据合规风险 | 图像、知识库和审计日志可留在端侧节点 |

## 成果截图与证据

当前截图和视频录制清单见 `docs/submission/screenshots-checklist.md` 和 `docs/submission/demo-shot-list.md`。可提交证据索引见 `docs/submission/poc-evidence-index.md`，生成证据快照位于 `docs/submission/evidence/`。当前已具备 Xcelerator API 草稿、WFC 项目/Python block/数据表、live WFC `ok=true` 原生运行日志，以及 Jetson 端侧 HTTP 决策路径 latency/resource 证据；WFC Dashboard 和 HumanApprovalGate 仍需用真实平台执行截图替换 fallback/mock 资产。

## 开发投入

- 已完成：Agent Service、Workflow Canvas decision endpoint、离线评估数据集、赛事 evaluator、工易魔方 PoC runbook、Dashboard mock、Jetson 端侧 HTTP 决策采证、smoke test 和 pytest 基线。
- 待投入：真实工易魔方环境复现、平台截图和演示视频、真实或仿真 SPIDR/IPC 日志接入、客户场景联合 PoC。

## 当前进度

已完成可运行 Agent Service、Workflow Canvas decision endpoint、赛事指标 evaluator、离线数据集、评估脚本、PoC runbook、共创 one-pager、Xcelerator API 草稿、工易魔方项目基础证据、live WFC `ok=true` 运行日志和 Jetson 端侧证据。客户现场数据、WFC Dashboard、HumanApprovalGate 和数据表动态写回仍待平台复现和联合 PoC 合作推进。

## 商业模式

联合 PoC 服务、工易魔方场景模板授权、边缘 Agent Runtime 部署集成和持续运营支持。首批客户建议选择汽车零部件、电子装配、包装、食品和医药等多 SKU 产线。

## 团队、企业与知识产权

团队和企业真实信息由负责人在 `docs/submission/team-and-company-info-template.md` 中补齐。知识产权和合规口径见 `docs/submission/ip-and-compliance-statement.md`，最终提交前需由企业负责人确认自主知识产权、无产权纠纷和无不良记录。
