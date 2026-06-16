# WFC Workflow Export Evidence

更新日期：2026-06-16

## 当前完成项

已在真实工易魔方 WFC 项目 `Wearedge WFC PoC` 中完成两类导出：

| 文件 | 说明 | 大小 | SHA256 |
| --- | --- | ---: | --- |
| `submission-assets/live-evidence/gongyi-mofang/workflow-export/199-wfc-workflow-export-20260616.wfcw` | `File -> Export workflow` 导出的工作流文件 | 58096 bytes | `D998C2CBCC0794E50AF04202BB297ECA7EB7E285260393BEC953FB10D4579773` |
| `submission-assets/live-evidence/gongyi-mofang/workflow-export/200-wfc-deployment-data-export-20260616.wfcd` | `File -> Export deployment data` 导出的部署数据文件 | 4096 bytes | `60EE88F2250737A9BA989A1FF641A3AEBC0637D7522E410377319B9893FE6831` |

这些文件保存在 ignored evidence 目录，不进入 Git 仓库。

## 格式判断

`.wfcw` 和 `.wfcd` 文件均表现为高熵二进制内容：

- 不是 JSON 文本。
- 不是 ZIP、gzip、bz2、lzma。
- 文件内容中未直接出现 `CallWearedgeDecisionApi`、`更新数据表`、`output1` 等可读字符串。

因此当前不能用 `scripts/analyze_wfc_workflow_bindings.py` 直接确认 `CallWearedgeDecisionApi 输出1 -> 更新数据表.1 输入` 数据线。脚本已更新为遇到 `.wfcw/.wfcd` 时给出明确边界提示。

## 证据口径

可以写：

```text
已从真实工易魔方 WFC 项目导出 workflow 与 deployment data 文件，证明项目资产可导出、可归档；但导出格式为平台专有二进制，当前无法在仓库内解析连接拓扑。
```

不能写：

```text
已通过导出文件结构化确认 Python 输出动态写入数据表。
```

## 下一步

1. 若平台提供 JSON workflow/project 导出，使用 `scripts/analyze_wfc_workflow_bindings.py <workflow.json> --require-confirmed` 确认绑定。
2. 若只有 `.wfcw/.wfcd`，继续通过 WFC GUI 或运行日志补截图：
   - `198-wfc-output1-to-update-table-data-wire-20260616.png`
   - `197-wfc-data-table-values-after-python-writeback-20260616.png`
3. 当前初赛材料仍以 live `CallWearedgeDecisionApi.output ok=true`、字段准备、数据表静态承载和 runbook 作为主证据，不夸大为原生动态写回已完成。
