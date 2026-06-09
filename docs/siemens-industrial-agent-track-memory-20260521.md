# Siemens Industrial Agent Track Memory

更新日期：2026-06-09

来源文件：

```text
C:/Users/ryan hui/Downloads/第十一届创客中国工业智能体专题赛-西门子工业智能体赛题细则-20260521.pdf
```

抽取文本：

```text
extracted_texts/siemens-industrial-agent-rules-20260521.txt
```

## 一句话记忆

Wearedge 参赛方向必须被表达为：**基于西门子 Xcelerator / 工易魔方的多智能体协同决策与自主执行系统**，不是普通工业 Chatbot，也不是只做边缘推理的单点 demo。

## 赛道硬要求

| 项目 | 要求 |
| --- | --- |
| 业务场景 | 西门子数字化工业真实产线环境。 |
| 核心场景 | 智能产线协同、预测性维护、质量闭环控制。 |
| 总体目标 | 从“单点智能”走向“产线级智能”。 |
| 智能体方向 | 质量管控、能源管理、设备运维、生产制造-柔性生产协同决策、基于工易魔方开发的智能体。 |
| 决赛组合 | 从五个方向中选取不少于三个方向完成联合解决方案。 |
| 平台验证 | 在 Xcelerator 智能体开发平台端到端验证，或在工易魔方软件工程环境实现工作流执行验证。 |
| 人机协同 | 需要自然语言交互和决策过程可视化。 |

## 初赛指标

- 完成单智能体核心功能开发。
- 故障预测准确率不低于 85%，或调度优化效率提升不低于 20%。
- 提交技术方案文档与算法原型代码，或提交可执行的工易魔方工作流。
- 通过离线数据集验证。

## 决赛指标

- 不少于三个智能体方向形成联合解决方案。
- 系统响应延迟不高于 500ms。
- 决策准确率不低于 90%。
- 在 Xcelerator 或工易魔方环境完成端到端/工作流执行验证。
- 界面支持自然语言交互和决策可视化。

## 专项指标

| 方向 | 指标记忆 |
| --- | --- |
| 质量管控 | 检测准确率或良品率相对传统方案提升 5%；加分项是新增 1-2 个过去未实现的质量能力，或异常响应/监测/预防效率提升 10%。 |
| 能源管理 | 能耗预测准确度目标不低于 95%；AI 智能节能率不低于 10%。 |
| 设备运维 | F1 Score 大于 85%；故障预警提前时间大于 24 小时；根因定位 Top3 命中率大于 90%。 |
| 柔性生产 | 看工艺切换方法、订单变更响应、新型谱产品适配、订单交期/成本价值、敏捷度、灵活度、人工依赖降低、组件标准化和复用率。 |
| 工易魔方开发 | 看与工易魔方融合协同程度、现有功能组件利用率、新组件商业价值与复用潜力、跨领域/标准/协议融合、AI/数字孪生落地。 |

## 报名条件记忆

- 项目必须基于西门子 Xcelerator 智能体开发平台开发和应用，并符合 Xcelerator 共创需求。
- 报名阶段必须提交联合产品共创思路：拟开发智能体、目标客户群、产品优势、商业模式等。
- 初赛入围后，西门子专家团队会联系洽谈共创合作，并支持联合解决方案 PoC 准备。
- 决赛阶段需要提交成功的联合解决方案 PoC。
- 企业需要拥有自主知识产权，无产权纠纷，无不良记录。
- 创客中国报名后，还需要通过 Xcelerator 官网申请试用，并注明“创客中国参赛”。

## Wearedge 战略对齐

Wearedge 当前最贴合的组合：

```text
设备运维智能体
  + 质量管控智能体
  + 柔性生产协同决策智能体
  + 工易魔方 / Workflow Canvas 开发智能体
  + 能源管理作为加分方向
```

主线叙事：

```text
订单变化或产线异常
  -> 读取 MES / 设备 / 质量 / 能源 / WFC 上下文
  -> 多智能体协同评估
  -> 输出主方向、证据、指标、建议动作、责任人、残余风险
  -> HumanApprovalGate 人工确认
  -> 工易魔方工作流执行或模拟执行
  -> 数据表和 Dashboard 回写
```

## 当前仓库证据

| 要求 | 仓库证据 |
| --- | --- |
| 多智能体联合决策 | `jetson/competition.py`、`POST /v1/workflow-canvas/decision` |
| 离线数据集验证 | `evals/competition_offline_dataset.jsonl`、`scripts/run_competition_eval.py` |
| 工易魔方接入 | `docs/workflow-canvas-poc-runbook.md`、`docs/workflow-canvas-api-schema.md`、`workflows/wearedge_wfc_poc_payload.json` |
| Xcelerator API World 接入 | `docs/xcelerator-apiworld-onboarding.md`、`openapi/wearedge-xcelerator-apiworld.openapi.json` |
| 演示证据 | `docs/submission/demo-script.md`、`docs/submission/screenshots-checklist.md`、`scripts/capture_submission_screenshots.py` |
| 提交包自检 | `scripts/verify_submission_package.py`、`docs/submission/submission-package-manifest.md` |

## 仍需平台/人工补齐

- Xcelerator 平台申请试用通过记录。
- API World 应用、X 认证、API 服务、接口导入和调试调用截图。
- 工易魔方资源块、Python Function Block、Dashboard、数据表和运行日志截图。
- 企业名称、统一社会信用代码、联系人、知识产权承诺、无不良记录承诺。
- 3-5 分钟演示视频和最终报名系统提交截图。

## 决策提醒

- 不要把项目写成“工业问答助手”。
- 不要让大模型直接控制 PLC、设备停机或质量放行。
- 不要声称已完成真实客户生产验证，除非有平台/现场日志和截图。
- 所有指标引用必须能追溯到离线评估报告、测试记录或平台 PoC 证据。
