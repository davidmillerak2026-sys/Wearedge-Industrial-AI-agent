# IP And Compliance Statement Draft

更新日期：2026-06-09

## 自主知识产权口径

Wearedge Industrial AI Agent 的核心工程包括多智能体路由、输出契约、确定性动作守卫、赛事指标 evaluator、Workflow Canvas decision API、离线评估脚本和参赛文档，均在本仓库中维护。

端侧 Agent Runtime、WFC 资源块原型、`/v1/edge/runtime-profile` 和 Xcelerator API World OpenAPI 规格也作为本项目自主工程资产维护。

## 开源依赖边界

| Area | Dependency Type | Notes |
| --- | --- | --- |
| FastAPI gateway | open-source Python packages | Listed in `jetson/requirements.txt`. |
| Tests | pytest, httpx | Development dependencies. |
| RAG agent package | local package under `industrial-rag-agent/` | Included in repository. |
| Model runtime | external model/runtime setup | Model weights are not committed to this repository. |

## 承诺材料待补

以下内容需要企业负责人在最终提交前确认：

- 企业对参赛项目拥有自主知识产权。
- 项目无产权纠纷。
- 企业无不良记录。
- 报名材料真实、准确、可核验。
- 第三方开源依赖遵守对应许可证。

最终填写和签署材料按 `docs/submission/company-info-and-compliance-intake.md` 收口，保存到 `submission-assets/live-evidence/legal/`，不提交到 Git。

## 风险边界

当前仓库是 PoC 到 pilot-ready 的工程材料，不声称已经完成工业安全认证或客户真实产线量产部署。涉及 OT 控制的动作必须经过工易魔方工作流、现场权限和人工确认。
