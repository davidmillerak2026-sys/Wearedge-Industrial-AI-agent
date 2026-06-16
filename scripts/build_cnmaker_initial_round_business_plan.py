from __future__ import annotations

import argparse
import hashlib
import html
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "submission-assets" / "live-evidence" / "cnmaker-required-attachments"
DEFAULT_BROWSER = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_pdf(browser: Path, html_path: Path, pdf_path: Path) -> dict[str, Any]:
    command = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_path.resolve().as_uri(),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return {
        "ok": completed.returncode == 0 and pdf_path.is_file() and pdf_path.stat().st_size > 0,
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
    }


def render_screenshot(browser: Path, html_path: Path, screenshot_path: Path) -> dict[str, Any]:
    command = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--window-size=1200,1600",
        f"--screenshot={screenshot_path.resolve()}",
        html_path.resolve().as_uri(),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return {
        "ok": completed.returncode == 0 and screenshot_path.is_file() and screenshot_path.stat().st_size > 0,
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
    }


def business_plan_html() -> str:
    sections = [
        ("项目定位", [
            "Wearedge端侧工业智能体协同决策系统面向多SKU离散制造产线，解决设备健康、质量风险、能源窗口和换型调度分散决策的问题。",
            "项目计划基于西门子Xcelerator智能体开发平台和工易魔方开发平台，形成可执行、可审批、可回写的联合解决方案。",
            "核心差异化是把工业智能体运行时部署到Jetson、IPC、本地工控机或边缘服务器，让AI决策贴近产线数据，再由平台完成编排、人工确认和数据回写。",
        ]),
        ("工业痛点", [
            "多SKU和小批量订单使换型、首件验证、设备窗口和能耗窗口同时变化，一线人员需要跨MES、QMS、EMS、CMMS和现场记录协调。",
            "传统单点AI只能回答某个局部问题，难以把维护、质量、能源和生产调度形成同一条可追溯工作流。",
            "工业场景需要清楚的安全边界：模型可以解释和建议，但不能直接控制PLC、机器人、停线、质量放行或能源策略切换。",
        ]),
        ("联合解决方案", [
            "Wearedge Agent Service接收MES、设备信号、质量检测、能源数据、维护记录、released checklist和Workflow Canvas上下文。",
            "工易魔方通过Wearedge Agent Service资源块和CallWearedgeDecisionApi Python Function Block调用/v1/workflow-canvas/decision。",
            "输出写入全局数据表和Dashboard，包括主方向、优先级、建议动作、证据摘要、指标、责任人、残余风险和人工确认状态。",
        ]),
        ("技术路线", [
            "端侧推理PoC使用Gemma 4 E2B经llama.cpp/llama-server运行，用于图片、日志、SOP和现场上下文解释。",
            "最终方向选择和动作边界由jetson.competition.build_competition_decision()完成，采用KPI矩阵、优先级排序和确定性守卫。",
            "高风险动作进入HumanApprovalGate，不让模型文本直接写真实OT控制。该边界适合后续与西门子专家共同推进PoC。",
        ]),
        ("商业落地", [
            "目标客户包括汽车零部件、电子装配、包装、食品、医药和多品种小批量离散制造企业。",
            "商业模式包括联合PoC服务、工易魔方场景模板授权、边缘Agent Runtime部署集成和持续运营服务。",
            "预期价值包括减少非计划停机、降低缺陷和返工、优化能耗、缩短换型协调时间，并沉淀一线专家经验。",
        ]),
    ]
    metric_rows = [
        ("设备运维核心功能", "维护F1最低87.0%", ">=85%", "达标"),
        ("柔性生产调度", "调度效率提升最低21.0%", ">=20%", "达标"),
        ("离线样例通过率", "5/5，通过率100.0%", "通过离线数据集验证", "达标"),
        ("决策准确率估算", "最低95.0%", ">=90%", "达标"),
        ("规则决策延迟", "最大1ms", "<=500ms", "达标"),
        ("Jetson端侧HTTP路径", "4500样本，p95/max 6/33ms", "<=500ms", "达标"),
    ]
    agent_rows = [
        ("设备运维智能体", "预测性维护、预警、根因Top3、维护工单建议"),
        ("质量管控智能体", "缺陷隔离、扩检建议、质量工程师确认"),
        ("能源管理智能体", "能耗预测、空转识别、节能窗口建议"),
        ("柔性生产智能体", "换型约束、排产建议、首件验证"),
        ("Workflow Canvas智能体", "资源块、功能块、Dashboard、HumanApprovalGate编排"),
    ]
    roadmap_rows = [
        ("初赛提交", "提交商业计划书、路演PPT、技术方案、算法原型、离线验证和平台PoC证据"),
        ("入围后PoC", "与西门子专家确认行业场景、指标口径、WFC端到端验证路径和真实/仿真数据接入"),
        ("决赛验证", "在Xcelerator或工易魔方软件工程环境中完成工作流执行验证，强化数据表动态写回和HMI可视化"),
        ("产品化共创", "沉淀面向汽车零部件、电子装配、包装等行业的可复用智能体模板"),
    ]

    def paras(items: list[str]) -> str:
        return "".join(f"<p>{html.escape(item)}</p>" for item in items)

    def table(rows: list[tuple[str, ...]], headers: tuple[str, ...]) -> str:
        head = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    section_html = "".join(f"<h2>{html.escape(title)}</h2>{paras(items)}" for title, items in sections)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Wearedge商业计划书-初赛提交</title>
  <style>
    @page {{ size: A4; margin: 16mm 15mm; }}
    body {{ font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif; color: #17202a; line-height: 1.55; }}
    .cover {{ min-height: 210mm; display: flex; flex-direction: column; justify-content: center; border-left: 8px solid #0f5f78; padding-left: 24px; }}
    .kicker {{ color: #0f5f78; font-size: 14px; font-weight: 700; letter-spacing: .06em; }}
    h1 {{ color: #0b2545; font-size: 34px; line-height: 1.18; margin: 14px 0 18px; }}
    .subtitle {{ color: #3d4f61; font-size: 17px; max-width: 760px; }}
    .meta {{ margin-top: 28px; color: #586574; font-size: 12px; }}
    h2 {{ color: #0b2545; font-size: 20px; margin: 22px 0 8px; border-bottom: 1px solid #dbe4ec; padding-bottom: 4px; }}
    h3 {{ color: #0f5f78; font-size: 15px; margin-top: 16px; }}
    p, li {{ font-size: 12.2px; margin: 0 0 7px; }}
    .summary {{ background: #f4f8fb; border-left: 4px solid #0f5f78; padding: 10px 12px; margin: 14px 0 18px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 10px 0 17px; page-break-inside: avoid; font-size: 11.2px; }}
    th, td {{ border: 1px solid #d7e0e8; padding: 7px 8px; vertical-align: top; }}
    th {{ background: #eaf2f8; color: #0b2545; text-align: left; }}
    .pipeline {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 12px 0 18px; }}
    .step {{ border: 1px solid #d7e0e8; border-radius: 8px; padding: 9px; background: #fbfdff; font-size: 11.4px; }}
    .step strong {{ display: block; color: #0f5f78; margin-bottom: 4px; }}
    .boundary {{ margin-top: 18px; padding: 10px 12px; background: #fff8e6; border-left: 4px solid #b7791f; font-size: 11.8px; }}
    .pagebreak {{ page-break-before: always; }}
  </style>
</head>
<body>
  <section class="cover">
    <div class="kicker">第十一届“创客中国”工业智能体专题赛 - 企业组初赛附件</div>
    <h1>Wearedge端侧工业智能体协同决策系统<br>商业计划书</h1>
    <div class="subtitle">端侧智能体运行时 + 西门子Xcelerator / 工易魔方工作流编排，面向多SKU离散制造产线形成可执行、可审批、可回写的联合解决方案。</div>
    <div class="meta">版本：初赛提交版 | 日期：2026-06-15 | 口径：离线/仿真验证 + 平台PoC证据，不声称真实客户量产结果</div>
  </section>

  <section class="pagebreak">
    <h2>执行摘要</h2>
    <div class="summary">
      Wearedge的核心优势不是“会回答问题”，而是把工业智能体运行在靠近设备和产线数据的端侧算力中，再由Xcelerator/工易魔方完成工作流编排、Dashboard展示、人工确认和数据回写。
    </div>
    {section_html}
  </section>

  <section class="pagebreak">
    <h2>多智能体方向与职责</h2>
    {table(agent_rows, ("智能体方向", "主要职责"))}

    <h2>初赛指标与证据</h2>
    {table(metric_rows, ("指标项", "当前结果", "目标/要求", "状态"))}

    <h2>端到端工作流</h2>
    <div class="pipeline">
      <div class="step"><strong>1. 现场上下文</strong>MES、QMS、EMS、CMMS、设备信号、图像、SOP和released checklist。</div>
      <div class="step"><strong>2. 端侧运行时</strong>Jetson / IPC / 本地工控机运行Wearedge Agent Service。</div>
      <div class="step"><strong>3. 平台编排</strong>工易魔方资源块和Python Function Block调用决策API。</div>
      <div class="step"><strong>4. 审批回写</strong>Dashboard、数据表、HumanApprovalGate和审计日志闭环。</div>
    </div>

    <h2>与西门子共创计划</h2>
    {table(roadmap_rows, ("阶段", "共创内容"))}

    <div class="boundary">
      边界说明：当前指标来自自建离线/仿真数据集、真实平台PoC截图和Jetson端侧HTTP决策路径采证；不表述为真实客户生产数据或已量产效果。后续入围后需与西门子专家共同确认PoC场景、数据来源、验收指标和真实工易魔方端到端复现路径。
    </div>
  </section>
</body>
</html>"""


def build(output_dir: Path, browser: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "Wearedge-business-plan-initial-round.html"
    pdf_path = output_dir / "Wearedge-商业计划书-初赛提交.pdf"
    screenshot_path = output_dir / "Wearedge-business-plan-preview.png"
    html_path.write_text(business_plan_html(), encoding="utf-8")
    pdf_result = render_pdf(browser, html_path, pdf_path)
    screenshot_result = render_screenshot(browser, html_path, screenshot_path)
    manifest = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "browser": str(browser),
        "output_dir": str(output_dir),
        "business_plan_html": str(html_path),
        "business_plan_pdf": str(pdf_path),
        "business_plan_pdf_ok": pdf_result["ok"],
        "business_plan_pdf_size": pdf_path.stat().st_size if pdf_path.is_file() else 0,
        "business_plan_pdf_sha256": sha256(pdf_path) if pdf_path.is_file() else None,
        "business_plan_preview": str(screenshot_path),
        "business_plan_preview_ok": screenshot_result["ok"],
        "boundary": "Offline/simulated validation plus platform PoC evidence; not customer production deployment evidence.",
    }
    (output_dir / "business-plan-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CNMaker initial-round business plan PDF.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--browser", type=Path, default=DEFAULT_BROWSER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    manifest = build(args.output_dir, args.browser)
    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else manifest["business_plan_pdf"])
    return 0 if manifest["business_plan_pdf_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
