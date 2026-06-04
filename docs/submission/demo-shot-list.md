# Demo Shot List

更新日期：2026-06-04

目标：录制 3-5 分钟初赛演示，证明 Wearedge 不是普通工业问答，而是可接入工易魔方的多智能体协同决策闭环。

## Shot Sequence

| Shot | 画面 | 说明 | 证据路径 |
| --- | --- | --- | --- |
| 1 | GitHub repository 首页 | 展示项目已工程化托管、README 指向赛事和共创材料 | `README.md` |
| 2 | API health 或本地终端 | 展示 Wearedge Agent Service 可启动 | `jetson/app.py` |
| 3 | Workflow Canvas payload | 展示 MES、维护、质量、能源、生产上下文统一输入 | `workflows/wearedge_wfc_poc_payload.json` |
| 4 | WFC decision smoke test | 展示 `primary_direction`、`latency_ms`、function blocks | `scripts/smoke_workflow_canvas_decision.py` |
| 5 | 离线评估报告 | 展示维护、能源、质量、调度等指标表 | `docs/competition-offline-eval-report.md` |
| 6 | API schema | 展示工易魔方 Python Function Block 如何调用 | `docs/workflow-canvas-api-schema.md` |
| 7 | Dashboard mock 或数据表草图 | 展示指标卡、决策路径、人工确认、残余风险 | `docs/workflow-canvas-poc-runbook.md` |
| 8 | pytest result | 展示完整测试通过，证明不是临时 demo | CI 或本地 pytest 输出 |
| 9 | 共创 one-pager | 展示拟开发智能体、目标客户、商业模式 | `docs/siemens-xcelerator-co-creation-onepager.md` |

## Capture Notes

- 优先录制终端命令和 Markdown/JSON 文档画面，避免依赖尚未接入的真实工易魔方环境。
- 如果有工易魔方账号和环境，再补资源块、Python Function Block、全局数据表、Dashboard 的真实截图。
- 所有模拟数据画面必须口播说明“当前为离线模拟验证，后续将在工易魔方/Xcelerator 环境复现”。
