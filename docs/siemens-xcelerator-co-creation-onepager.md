# Wearedge x Siemens Xcelerator 联合产品共创思路

更新日期：2026-06-04

## 项目名称

Wearedge Industrial AI Agent：面向柔性可重构产线的多智能体协同决策与自主执行系统。

## 一句话定位

Wearedge 基于西门子 Xcelerator 智能体开发平台和工易魔方开发平台，把设备运维、质量管控、能源管理、柔性生产和 Workflow Canvas 智能体统一为可解释、可审批、可执行、可回写的工业联合解决方案。

## 拟开发智能体

| 智能体方向 | 计划能力 | 当前代码支撑 |
| --- | --- | --- |
| 设备运维智能体 | 根据设备报警、振动、温度、维护记录和知识库生成预测性维护判断、Top 3 根因候选和工单建议 | `analysis_mode=maintenance`、维护知识库、阈值评估、maintenance session evidence loop |
| 质量管控智能体 | 根据视觉缺陷、质检计划、批次和工位证据给出隔离、扩检、停线、返工或 CAPA 建议 | `analysis_mode=iqc`、IQC plan、detector evidence、quality disposition guard |
| 能源管理智能体 | 根据能耗表、峰值负荷、空转状态和生产计划识别节能窗口，输出需确认的优化建议 | `analysis_mode=energy`、energy output contract、energy action card、EMS integration event |
| 柔性生产智能体 | 根据订单变化、目标 SKU、换型清单、设备状态和质量风险建议换型/排程协同动作 | `analysis_mode=changeover`、released checklist guard、first-piece verification |
| Workflow Canvas 智能体 | 将多智能体决策转成工易魔方资源块、功能块、数据表和人工审批节点可执行的工作流 | `POST /v1/workflow-canvas/decision`、competition target evaluator、WFC block payload |

## 目标客户群

| 客户类型 | 典型痛点 | Wearedge 价值 |
| --- | --- | --- |
| 多品种小批量离散制造工厂 | 换型频繁，设备状态、质量风险和交期压力互相影响 | 在换型前后统一评估设备健康、质量风险、能耗和交期，减少人工协调成本 |
| 汽车零部件、电子装配、包装产线 | 缺陷隔离和首件验证依赖经验，异常响应慢 | 让质检证据、工艺清单和生产状态进入同一决策闭环，降低缺陷外流和返工 |
| 高资产密度设备现场 | 维护专家不足，报警和传感器数据难以转成可执行工单 | 将老师傅经验、维护手册、信号阈值和历史工单沉淀为可审计智能体流程 |
| 能耗敏感型生产单元 | 空转、峰值负荷和辅助设备运行缺少生产约束下的协同优化 | 在不越权控制 OT 的前提下提出需审批的节能窗口和排程建议 |

## 产品优势

1. **平台可接入**：Wearedge Agent Service 通过 REST API 暴露给工易魔方 Python Function Block，可由资源块参数绑定 `agentHost`、`agentPort`、`apiKeyRef`、`plantId` 和 `lineId`。
2. **多智能体联合**：同一 runtime 支持维护、质量、能源、换型、作业指导和安全边界，决赛阶段可组合不少于三个赛题方向。
3. **证据优先**：模型只解释图像、文本、表格和设备信号证据；阈值、动作通道、责任人、优先级和人工确认由确定性逻辑执行。
4. **安全可控**：高风险动作不会直接写 PLC 或停止产线，而是进入人工确认、工单、QMS/MES/EMS 事件或 Dashboard 回写。
5. **可验证**：当前仓库已提供离线测试、FastAPI 接口、样例 KB、IQC plan、released source、competition evaluator 和 130 项 pytest 验证。

## 商业模式

| 模式 | 内容 |
| --- | --- |
| PoC 共创服务 | 与西门子专家和目标工厂共同选取一条产线，完成工易魔方工作流、数据表、看板和 Wearedge Agent Service 接入 |
| 场景模板授权 | 提供预测性维护、质量闭环、能耗优化、换型协同等 Workflow Canvas 模板和智能体配置包 |
| 边缘部署与集成 | 在客户 IPC/Jetson/本地服务器部署 Agent Service，对接 MES、QMS、CMMS、EMS、OPC UA、MQTT 或 S7 数据源 |
| 持续运营支持 | 按产线或工厂收取订阅/维护费，覆盖知识库更新、规则校准、指标复盘、模型升级和新场景扩展 |

## 联合解决方案 PoC 计划

### PoC 主题

多 SKU 包装/装配产线的质量-设备-能耗-换型协同优化。

### 演示主线

1. MES 订单变化触发目标 SKU 换型，工易魔方读取目标 SKU、工位、设备状态和换型清单。
2. Wearedge 换型智能体确认 released checklist、线清场和首件验证要求。
3. 设备运维智能体读取振动/温度/报警/维护记录，判断是否存在高风险设备状态。
4. 质量智能体读取视觉检测或质检表，判断是否需要隔离、扩检或质量工程师确认。
5. 能源智能体读取能耗数据和生产计划，识别空转或错峰优化窗口。
6. Workflow Canvas 智能体生成协同决策，写入全局数据表和 Dashboard，经人工确认后模拟执行或调用现有功能块。

### 工易魔方工作流块建议

| 类型 | 名称 | 作用 |
| --- | --- | --- |
| 自定义资源块 | `Wearedge Agent Service` | 绑定 API 地址、认证引用、产线和工厂上下文 |
| 功能块 | `ReadMesOrder` | 读取订单、目标 SKU、交期和换型需求 |
| 功能块 | `ReadEquipmentSignals` | 读取报警、振动、温度、电流或设备状态 |
| 功能块 | `ReadQualityData` | 读取视觉检测、质检表和批次状态 |
| 功能块 | `ReadEnergyMeter` | 读取能耗、峰值、空转和生产计划约束 |
| Python 功能块 | `CallWearedgeDecisionApi` | 调用 `POST /v1/workflow-canvas/decision` |
| 功能块 | `CollaborativeDecisionGate` | 在质量、设备、能耗和交期之间做多目标权衡 |
| 功能块 | `HumanApprovalGate` | 对停机、放行、节能控制或排程调整进行人工确认 |
| 功能块 | `UpdateDashboardDataTable` | 写入建议动作、证据、指标、责任人和残余风险 |

### 成功指标

| 指标 | 目标 |
| --- | --- |
| 端到端工作流 | 工易魔方中完成“读取上下文 -> 调用智能体 -> 决策展示 -> 人工确认 -> 数据回写” |
| 决策方向 | 决赛阶段不少于 3 个智能体方向联合运行，推荐维护 + 质量 + 柔性生产 + 工易魔方，能源作为加分方向 |
| 延迟 | 交互式协同决策接口目标不高于 500ms；长链路视觉诊断可异步化并返回任务状态 |
| 决策准确率 | 离线数据集或仿真案例决策准确率目标不低于 90% |
| 设备运维 | F1 Score 大于 85%，预警提前时间大于 24 小时，根因 Top 3 命中率大于 90% |
| 能源管理 | 能耗预测准确度不低于 95%，智能节能率不低于 10% |
| 质量管控 | 检测准确率或良品率相对提升不低于 5% |
| 柔性生产 | 调度优化效率提升不低于 20%，组件复用和人工依赖降低可展示 |

## 报名阶段可复制摘要

```text
Wearedge Industrial AI Agent 计划基于西门子 Xcelerator 智能体开发平台和工易魔方开发平台，开发面向柔性可重构产线的多智能体协同决策产品。项目拟开发设备运维、质量管控、能源管理、柔性生产和 Workflow Canvas 智能体，通过工易魔方资源块、Python 功能块、数据表和 Dashboard，把 AI 诊断转化为可审批、可执行、可回写的 IT/OT 工作流。目标客户为汽车零部件、电子装配、包装等多 SKU 离散制造工厂，核心价值是降低停机、缺陷、能耗和换型协调成本。产品优势在于低延迟边缘运行、证据优先工业 RAG、确定性动作守卫、人工确认和平台化工作流模板。商业模式包括联合 PoC 服务、场景模板授权、边缘部署集成和持续运营支持。
```

## 当前仓库证据

| 证据 | 路径 |
| --- | --- |
| FastAPI 工易魔方入口 | `jetson/app.py` 中 `/v1/workflow-canvas/decision` |
| 赛事指标评估器 | `jetson/competition.py` |
| 能源智能体合同 | `jetson/output_contract.py`、`jetson/agent_loop.py` |
| 联合决策测试 | `tests/test_competition_decision.py` |
| 工易魔方约束与优化方向 | `docs/赛事要求与Wearedge智能体优化方向.md` |
| 技术架构 | `docs/technical_architecture.md` |
| 工业证据链 | `docs/technical-evidence.md` |

## 仍需人工补齐

| 材料 | 负责人需确认 |
| --- | --- |
| 报名主体 | 企业名称、统一社会信用代码、联系人、手机号、邮箱 |
| 知识产权声明 | 自主知识产权承诺、开源依赖边界、无产权纠纷声明 |
| 无不良记录 | 企业信用/无不良记录承诺 |
| 平台沟通 | 西门子 Xcelerator / 工易魔方平台咨询邮件和对接记录 |
| PoC 截图 | 工易魔方资源块、功能块、Dashboard、数据表和运行日志截图 |
