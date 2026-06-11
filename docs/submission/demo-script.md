# Demo Script

更新日期：2026-06-09

## 3-5 分钟演示脚本

### 0:00-0:30 开场

Wearedge Industrial AI Agent 面向多 SKU 柔性产线，基于西门子 Xcelerator 和工易魔方，把设备运维、质量管控、能源管理、柔性生产和 Workflow Canvas 智能体统一成可解释、可审批、可回写的工业闭环。我们的企业组差异化是：智能体运行时可以部署在 Jetson、IPC、本地工控机或边缘服务器上，贴近设备和产线运行。

### 0:30-1:10 痛点

多品种小批量制造现场常见问题是：订单变化触发换型，设备状态、质量风险、能耗窗口和交期压力互相影响。传统系统各管一段，现场依赖人工协调，异常响应慢，证据难追溯。

### 1:10-2:10 技术方案

Wearedge Agent Service 接收来自 MES、设备信号、质量检测、能源表和工易魔方工作流的上下文。端侧运行多模态推理、工业 RAG、确定性守卫、结构化 action card 和审计日志；Xcelerator / 工易魔方负责平台编排、审批和数据回写。大模型只负责解释证据，关键指标、动作通道、责任人、人工确认和残余风险由确定性逻辑生成，避免模型直接控制 OT。

### 2:10-3:10 演示

先打开 `/v1/industrial-agent/solution-profile`，展示 Wearedge 解决的跨域异常协同决策问题、Gemma 4 E2B/llama.cpp 模型角色、KPI 决策矩阵和 HumanApprovalGate 安全边界。再打开 `/v1/edge/runtime-profile`，展示 Wearedge 可作为 Jetson/IPC/local server 端侧 Agent Runtime。随后运行 Workflow Canvas decision smoke test。输入包含维护、质量、能源、生产和 WFC 上下文，输出包含 `decision_mechanism`、`competition_metrics`、`collaborative_decision` 和 `workflow_canvas.function_blocks`。结果可以写回全局数据表和 Dashboard，并进入 `HumanApprovalGate`。

### 3:10-4:00 指标

打开离线评估报告，展示维护 F1、预警提前时间、根因 Top3、能源预测准确率、节能率、质量提升、调度效率和延迟目标。说明这是当前模拟/离线验证，后续会在工易魔方或 Xcelerator PoC 环境复现。

### 4:00-5:00 商业价值与共创

目标客户是汽车零部件、电子装配、包装、食品、医药等多 SKU 离散制造工厂。商业模式包括联合 PoC、工易魔方场景模板授权、边缘 Agent Runtime 部署集成和持续运营支持。与西门子共创的价值在于把端侧智能体能力变成可执行的 Xcelerator / 工易魔方联合解决方案。

## 必须避免的表述

- 不说“已经完成真实客户生产验证”，除非有客户现场证据。
- 不说“AI 自动控制 PLC 停机或放行”，高风险动作必须人工确认。
- 不说“替代质量工程师或维护工程师”，应表达为证据辅助和协同决策。
