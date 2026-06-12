# Submission Package Manifest

更新日期：2026-06-11

此文件由 `scripts/verify_submission_package.py --write-manifest` 生成，用于提交前总控检查。

## Repository Readiness

- Repository-controlled package ready: True
- Recommended next action: Replace fallback WFC evidence and fill human-owned registration fields.

## Phase Status

| Phase | Status | Artifacts |
| --- | --- | ---: |
| Phase A - Offline evaluation | ready | 8 / 8 |
| Phase B - Gongyi Mofang PoC package | ready | 18 / 18 |
| Phase C - Demo evidence | ready | 12 / 12 |
| Phase D - Business and technical package | ready | 13 / 13 |
| Phase E - Registration fields | ready | 11 / 11 |

## Validation Status

| Check | Status | Notes |
| --- | --- | --- |
| Generated evidence | ready | offline evidence, WFC smoke snapshot, edge runtime profile, HTTP resource benchmark, and solution profile are present |
| Registration fields | ready | short/mid/long field copy and human-owned fields are separated |
| Offline report boundary | ready | report includes metric table and simulated/offline boundary |
| Submission timeline | ready | internal submit date and official deadline are tracked |

## External Pending Items

- 按 docs/submission/company-info-and-compliance-intake.md 补齐企业名称、统一社会信用代码、联系人、电话、邮箱等真实主体信息
- 用真实 WFC Dashboard / log-manager ok=true / HumanApprovalGate 截图替换当前 fallback 标记的 04/05/06 Gongyi Mofang 证据
- 将临时 PoC HTTPS 地址替换为稳定可复现地址，并在 Xcelerator / WFC 材料中同步更新
- 企业负责人最终签署的知识产权、无产权纠纷、无不良记录承诺
- 报名系统字段填报截图，隐藏证件号等敏感字段后存入 submission-assets/live-evidence/submission/
- 报名系统正式提交成功状态截图

## External Evidence Command

```powershell
python scripts/run_final_readiness_pipeline.py --json
python scripts/verify_live_evidence.py --stage platform --allow-missing --write-manifest
python scripts/verify_live_evidence.py --stage final --allow-missing --write-manifest
```

## Repository Failures

- None.
