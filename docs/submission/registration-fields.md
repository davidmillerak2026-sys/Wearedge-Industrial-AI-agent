# Registration Fields Draft

更新日期：2026-06-09

此文件用于 7月1日后打开报名系统时快速复制。当前文本基于仓库已完成的离线验证、工易魔方 PoC 接入包和演示证据包；真实企业信息、联系人、正式截图和视频链接需要最后补齐。

## 短版字段

项目名称：

```text
Wearedge Industrial AI Agent：面向柔性可重构产线的多智能体协同决策与自主执行系统
```

一句话简介：

```text
基于西门子 Xcelerator 和工易魔方，Wearedge 将可部署到 Jetson/IPC/本地工控机的端侧工业智能体，与设备运维、质量管控、能源管理、柔性生产和 Workflow Canvas 编排统一成可解释、可审批、可回写的工业联合解决方案。
```

## 中版字段

项目简介，约 300 字：

```text
Wearedge Industrial AI Agent 面向多 SKU 离散制造产线，构建基于西门子 Xcelerator 智能体开发平台和工易魔方开发平台的多智能体协同决策系统。项目通过部署在 Jetson、IPC、本地工控机或边缘服务器上的 Wearedge Agent Service 接收 MES、设备信号、质量数据、能源数据和 Workflow Canvas 上下文，输出主方向、优先级、建议动作、确认项、残余风险和 Dashboard 数据。系统覆盖设备运维、质量管控、能源管理、柔性生产和 Workflow Canvas 智能体，强调证据优先、确定性守卫和人工确认，避免模型直接控制 OT。当前仓库已实现 /v1/workflow-canvas/decision、/v1/edge/runtime-profile、赛事指标 evaluator、离线评估数据集、评估脚本和工易魔方资源块原型，可用于初赛技术方案和后续联合 PoC 准备。
```

## 长版字段

项目介绍，约 800-1000 字：

```text
Wearedge Industrial AI Agent 是面向柔性可重构产线的工业多智能体协同决策与自主执行系统。项目聚焦多 SKU 离散制造现场中“订单变化、换型压力、设备健康、质量风险、能耗窗口”互相影响但难以协同的问题，计划基于西门子 Xcelerator 智能体开发平台和工易魔方开发平台共创一套可执行、可审批、可回写的联合解决方案。

系统以 Wearedge Agent Service 为核心服务，可部署在 Jetson、IPC、本地工控机或边缘服务器，由工易魔方资源块和 Python Function Block 调用 /v1/workflow-canvas/decision 接口。输入来自 MES、设备信号、质量检测、能源表、released checklist 和 Workflow Canvas 上下文；输出包括主方向、优先级、建议动作、证据、指标、责任人、残余风险、人工确认状态和 Dashboard 数据。智能体方向覆盖设备预测性维护、质量管控、能源管理、柔性生产和 Workflow Canvas 编排，满足不少于三个智能体方向协同的赛事目标。

技术方案采用“证据优先 + 确定性守卫 + 人工确认”的工业安全边界。模型用于解释症状、关联证据和生成可读建议；关键阈值、指标达标、动作权限、审批要求和残余风险由确定性逻辑生成，避免模型文本直接控制 OT。当前仓库已完成离线评估数据集、赛事 evaluator、Workflow Canvas API schema、PoC runbook、smoke test、Dashboard mock、商业计划书和技术方案草稿。离线评估结果明确标注为模拟/离线验证，后续将在工易魔方或 Xcelerator PoC 环境中补充真实平台截图、日志和联合解决方案证据。

目标客户包括汽车零部件、电子装配、包装、离散制造和多品种小批量产线。产品优势在于把分散的维护、质量、能源和生产决策统一成可追溯工作流，帮助客户减少非计划停机、降低缺陷和返工、优化能耗、缩短换型协调时间，并沉淀可复用的行业智能体模板。商业模式包括联合 PoC 服务、场景模板授权、边缘部署集成和持续运营支持。
```

## 联合产品共创思路

与西门子 Xcelerator / 工易魔方共创一套面向柔性可重构产线的工业多智能体产品。通过工易魔方资源块、Python Function Block、全局数据表、Dashboard 和 HumanApprovalGate，把 AI 诊断转化为可执行 IT/OT 工作流，为客户降低停机、缺陷、能耗和换型协调成本。

## 拟开发智能体

| 智能体 | 主要职责 | 工易魔方落点 |
| --- | --- | --- |
| 设备运维智能体 | 预测性维护、阈值证据、根因 Top3、工单建议 | 维护告警、工单、人工确认 |
| 质量管控智能体 | 缺陷 containment、扩检、质量工程师确认 | QMS 数据表、隔离/复检流程 |
| 能源管理智能体 | 能耗预测、空转识别、节能窗口建议 | EMS 指标卡、节能任务 |
| 柔性生产智能体 | 换型、released checklist、首件验证 | MES/工艺表、换型任务 |
| Workflow Canvas 智能体 | 资源块、功能块、Dashboard、审批编排 | WFC 资源块和功能块 |

## 目标客户群

- 多 SKU 包装、电子装配、汽车零部件、离散制造产线。
- 需要缩短换型时间、降低非计划停机、提升质量响应和能耗可视化的中小制造企业。
- 已使用或计划使用西门子 Xcelerator、工易魔方、MES/QMS/EMS/CMMS 的工厂客户。

## 产品优势

- 平台适配：保持 `POST /v1/workflow-canvas/decision` 兼容，工易魔方 Python Function Block 可直接调用。
- 端侧部署：智能体运行时可部署在 Jetson、IPC、本地工控机或边缘服务器，支持数据不出厂和局域网运行。
- 多智能体协同：维护、质量、能源、生产和 WFC 编排同屏决策，而不是单点问答。
- 可解释证据链：每个建议包含症状、指标、证据来源、责任角色、确认项和残余风险。
- 安全边界清楚：高风险动作进入 HumanApprovalGate，不让模型直接写 OT 控制。
- 可验证工程资产：仓库包含离线数据集、评估脚本、smoke test、pytest、PoC runbook 和证据快照。

## 商业模式

- 联合 PoC：按产线/场景收取 PoC 设计、集成和验证服务费。
- 模板授权：沉淀维护、质量、能源和换型模板，按工厂或产线授权。
- 边缘部署集成：提供本地网关、边缘算力、模型配置和工易魔方接入实施。
- 持续运营：提供指标复盘、知识库更新、场景扩展和模型/规则维护服务。

## 知识产权说明

```text
Wearedge Industrial AI Agent 的核心工程包括多智能体路由、输出契约、确定性动作守卫、赛事指标 evaluator、Workflow Canvas decision API、离线评估脚本和参赛文档，均在本仓库中维护。最终提交前由企业负责人确认自主知识产权、无产权纠纷、无不良记录和第三方开源依赖合规。
```

## 附件清单

| 附件 | 仓库路径 |
| --- | --- |
| 共创 one-pager | `docs/siemens-xcelerator-co-creation-onepager.md` |
| 离线评估报告 | `docs/competition-offline-eval-report.md` |
| 工易魔方 PoC runbook | `docs/workflow-canvas-poc-runbook.md` |
| API schema | `docs/workflow-canvas-api-schema.md` |
| Edge Runtime 文档 | `docs/edge-agent-runtime-for-xcelerator.md` |
| WFC 资源块原型 | `wfc-blocks/wearedge-agent-service/` |
| 商业计划书 | `docs/submission/business-plan.md` |
| 技术方案 | `docs/submission/technical-solution.md` |
| 评审打分证据映射 | `docs/submission/judging-scorecard-evidence-map.md` |
| 答辩问答准备 | `docs/submission/defense-qna-playbook.md` |
| 证据索引 | `docs/submission/poc-evidence-index.md` |
| Demo 脚本 | `docs/submission/demo-script.md` |
| Dashboard mock | `docs/submission/dashboard-mock.html` |
| 仓库侧最终提交包 | `submission-assets/live-evidence/submission-bundle/wearedge-industrial-ai-agent-repo-controlled-submission-bundle.zip` |

## 人工待填字段

- 报名主体和联系人。
- 统一社会信用代码、企业地址、营业执照或系统要求材料。
- 团队介绍。
- 企业知识产权和无不良记录承诺。
- 最终 PoC 截图和视频链接。
- 最终指标报告链接。
