# Submission Package Manifest

更新日期：2026-06-09

此文件由 `scripts/verify_submission_package.py --write-manifest` 生成，用于提交前总控检查。

## Repository Readiness

- Repository-controlled package ready: True
- Recommended next action: Capture screenshots/video and fill human-owned registration fields.

## Phase Status

| Phase | Status | Artifacts |
| --- | --- | ---: |
| Phase A - Offline evaluation | ready | 4 / 4 |
| Phase B - Gongyi Mofang PoC package | ready | 11 / 11 |
| Phase C - Demo evidence | ready | 11 / 11 |
| Phase D - Business and technical package | ready | 7 / 7 |
| Phase E - Registration fields | ready | 2 / 2 |

## Validation Status

| Check | Status | Notes |
| --- | --- | --- |
| Generated evidence | ready | offline evidence, WFC smoke snapshot, and edge runtime profile are present |
| Registration fields | ready | short/mid/long field copy and human-owned fields are separated |
| Offline report boundary | ready | report includes metric table and simulated/offline boundary |
| Submission timeline | ready | internal submit date and official deadline are tracked |

## External Pending Items

- 按 docs/submission/company-info-and-compliance-intake.md 补齐企业名称、统一社会信用代码、联系人、电话、邮箱等真实主体信息
- 按 docs/submission/live-platform-evidence-runbook.md 保存真实 Xcelerator / API World 平台截图
- 按 docs/submission/live-platform-evidence-runbook.md 保存真实工易魔方 Workflow Canvas 截图
- 按 docs/submission/video-production-plan.md 输出 3-5 分钟演示视频文件或可访问链接
- 企业负责人最终签署的知识产权、无产权纠纷、无不良记录承诺
- 报名系统正式提交状态截图

## External Evidence Command

```powershell
python scripts/verify_live_evidence.py --stage platform --allow-missing --write-manifest
python scripts/verify_live_evidence.py --stage final --allow-missing --write-manifest
```

## Repository Failures

- None.
