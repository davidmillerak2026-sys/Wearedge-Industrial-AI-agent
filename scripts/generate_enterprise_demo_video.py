from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "submission-assets" / "live-evidence" / "video"
DEFAULT_VIDEO = "wearedge-enterprise-demo-3-5min.mp4"
DEFAULT_SCRIPT = "wearedge-enterprise-demo-script-final.md"

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\msyhbd.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\arial.ttf"),
]

BG = (12, 18, 25)
PANEL = (24, 34, 46)
INK = (244, 249, 252)
MUTED = (173, 187, 199)
LINE = (72, 91, 111)
CYAN = (29, 187, 191)
MINT = (65, 211, 145)
AMBER = (237, 166, 53)
RED = (226, 80, 77)


@dataclass(frozen=True)
class Scene:
    title: str
    subtitle: str
    bullets: tuple[str, ...]
    duration: int
    assets: tuple[str, ...] = ()
    narration: str = ""
    badge: str = "LIVE / REPO"
    fallback: bool = False


SCENES: tuple[Scene, ...] = (
    Scene(
        title="Wearedge 工业智能体联合解决方案",
        subtitle="端侧智能体 + Xcelerator / 工易魔方产线闭环",
        bullets=(
            "企业组夺冠叙事：AI 决策贴近设备、数据和一线人员",
            "Jetson / IPC / 本地工控机运行智能体，平台负责编排、审批、回写",
            "覆盖设备运维、质量、能源、柔性生产和 Workflow Canvas",
        ),
        duration=20,
        assets=("edge-runtime/02-runtime-profile.png", "xcelerator/41-xcelerator-client-app-home-refresh.png"),
        narration="开场说明 Wearedge 不是工业 Chatbot，而是可部署在端侧算力中的工业智能体运行时，并通过西门子平台形成工作流闭环。",
        badge="CORE STORY",
    ),
    Scene(
        title="具体工业问题：跨域异常协同决策",
        subtitle="订单变化、换型、设备风险、质量波动和能耗窗口同时出现",
        bullets=(
            "传统 MES/QMS/EMS/CMMS 各管一段，现场靠人工协调",
            "Wearedge 把多源上下文归一成结构化 action card",
            "高风险 OT 动作进入 HumanApprovalGate，不由模型直接控制",
        ),
        duration=24,
        assets=("edge-runtime/05-solution-profile.png",),
        narration="说明参赛项目解决的是多 SKU 产线上的协同决策问题：维护、质量、能源和生产目标互相影响，需要一个可解释、可审批的联合决策层。",
        badge="INDUSTRIAL PROBLEM",
    ),
    Scene(
        title="端侧 Agent Runtime",
        subtitle="模型负责解释证据，确定性守卫负责动作边界",
        bullets=(
            "本地 Gemma 4 E2B / llama.cpp 可在边缘节点运行",
            "工业 RAG、KPI 决策矩阵、结构化输出和审计日志可本地化",
            "支持断网或厂内 LAN 场景，降低数据外传与延迟风险",
        ),
        duration=24,
        assets=("edge-runtime/01-healthz.png", "edge-runtime/02-runtime-profile.png"),
        narration="展示端侧部署优势：生产图像、上下文、知识库和审计日志可以留在产线边缘，平台侧只编排流程和审批。",
        badge="EDGE FIRST",
    ),
    Scene(
        title="Xcelerator 草稿证据",
        subtitle="应用、API 服务和 OpenAPI 接口均在租户内草稿中",
        bullets=(
            "已创建 Wearedge 工业智能体服务应用草稿",
            "已导入 4 个接口：solution-profile、decision、runtime-profile、healthz",
            "保持未发布、未上架、未保存密钥，符合当前安全边界",
        ),
        duration=24,
        assets=(
            "xcelerator/41-xcelerator-client-app-home-refresh.png",
            "xcelerator/42-xcelerator-api-detail-refresh.png",
            "xcelerator/43-xcelerator-api-interface-list-refresh-four-endpoints.png",
        ),
        narration="展示真实 Xcelerator Console 证据：Wearedge 应用草稿、API 服务草稿和四个租户内接口，强调未公开发布。",
        badge="LIVE PLATFORM",
    ),
    Scene(
        title="工易魔方 WFC 接入证据",
        subtitle="Python Function Block 已保存 Wearedge 调用源码",
        bullets=(
            "真实 WFC 项目：Wearedge WFC PoC",
            "CallWearedgeDecisionApi 已拖入画布并保存 fb_main.py",
            "数据表字段覆盖方向、优先级、动作、证据、指标、负责人和审批状态",
        ),
        duration=28,
        assets=(
            "gongyi-mofang/02-python-function-block-call-api.png",
            "gongyi-mofang/03-global-data-table-decision-fields.png",
            "gongyi-mofang/102-wfc-python-fb-main-saved.png",
            "gongyi-mofang/103-wfc-log-manager-after-python-run.png",
        ),
        narration="展示真实工易魔方项目证据：Python Block、全局数据表、fb_main.py 保存和 log-manager ready。说明 live ok=true 仍待最终 WFC 运行复现。",
        badge="LIVE WFC",
    ),
    Scene(
        title="API 决策闭环可复验",
        subtitle="本地 smoke 输出 ok=True、主方向、延迟和 function blocks",
        bullets=(
            "scripts/smoke_workflow_canvas_decision.py 已返回 ok=True",
            "输出 collaborative_decision、competition_metrics 和 WFC function_blocks",
            "当前 run-log 图为 fallback API smoke，不冒充 live WFC 日志",
        ),
        duration=24,
        assets=("edge-runtime/03-workflow-canvas-decision-smoke.png", "gongyi-mofang/05-run-log-ok-true.png"),
        narration="展示可复验 API 结果：本地 Wearedge 决策链路可跑通，但 WFC live ok=true 证据仍作为下一步复现目标。",
        badge="FALLBACK MARKED",
        fallback=True,
    ),
    Scene(
        title="Dashboard 与人工确认演示",
        subtitle="当前为 fallback mock，最终替换为真实 WFC Dashboard / HumanApprovalGate",
        bullets=(
            "指标卡展示维护、质量、能源、调度和延迟目标",
            "HumanApprovalGate 表示高风险动作需要人工确认",
            "fallback metadata 会阻止材料误写成 live platform proof",
        ),
        duration=24,
        assets=("gongyi-mofang/04-dashboard-decision-view.png", "gongyi-mofang/06-human-approval-gate.png"),
        narration="展示演示用 Dashboard 和 HumanApprovalGate 画面，同时明确这是备用演示素材，最终需要真实平台截图替换。",
        badge="FALLBACK MOCK",
        fallback=True,
    ),
    Scene(
        title="商业落地与西门子共创价值",
        subtitle="面向汽车零部件、电子装配、包装、食品、医药等多 SKU 产线",
        bullets=(
            "联合 PoC 服务费 + 工易魔方场景模板授权",
            "边缘 Agent Runtime 部署集成 + 持续知识库/规则运营",
            "ROI：减少停机、降低返工、优化能耗、缩短换型时间",
        ),
        duration=22,
        assets=("xcelerator/43-xcelerator-api-interface-list-refresh-four-endpoints.png", "edge-runtime/05-solution-profile.png"),
        narration="收束商业计划：Wearedge 可以作为西门子 Xcelerator / 工易魔方共创模板，服务离散制造企业的跨域协同决策。",
        badge="BUSINESS",
    ),
    Scene(
        title="下一步：把 fallback 替换为 live proof",
        subtitle="提交前目标：7月8日前完成可复制字段、视频、截图和企业承诺材料",
        bullets=(
            "复现 WFC live ok=true 日志和数据表回写",
            "补真实 WFC Dashboard / HumanApprovalGate 截图",
            "负责人补企业主体、联系人、IP 承诺和最终报名成功截图",
        ),
        duration=20,
        assets=("gongyi-mofang/105-wfc-debug-stopped-after-run-attempt.png",),
        narration="结尾说明当前完成度与剩余人工材料，强调不夸大 live 证据，同时保留夺冠叙事和执行路径。",
        badge="FINAL GATE",
    ),
)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = FONT_CANDIDATES[1:] + FONT_CANDIDATES[:1] if bold else FONT_CANDIDATES
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    color: tuple[int, int, int] = INK,
    width: int = 600,
    bold: bool = False,
    line_gap: int = 8,
) -> int:
    fnt = font(size, bold)
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        box = draw.textbbox((0, 0), candidate, font=fnt)
        if box[2] - box[0] <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)

    y = xy[1]
    for line in lines:
        draw.text((xy[0], y), line, font=fnt, fill=color)
        line_h = draw.textbbox((0, 0), line, font=fnt)[3]
        y += line_h + line_gap
    return y - xy[1]


def resolve_asset(path: str) -> Path:
    return REPO_ROOT / "submission-assets" / "live-evidence" / path


def load_asset(path: str) -> Image.Image | None:
    asset_path = resolve_asset(path)
    if not asset_path.exists():
        return None
    return Image.open(asset_path).convert("RGB")


def fit_contain(src: Image.Image, size: tuple[int, int]) -> Image.Image:
    tw, th = size
    src.thumbnail((tw, th), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (10, 14, 20))
    canvas.paste(src, ((tw - src.width) // 2, (th - src.height) // 2))
    return canvas


def gradient_background(width: int, height: int, scene_index: int) -> Image.Image:
    yy = np.linspace(0, 1, height)[:, None]
    xx = np.linspace(0, 1, width)[None, :]
    base = np.zeros((height, width, 3), dtype=np.uint8)
    base[..., 0] = np.clip(BG[0] + 20 * xx + scene_index * 2, 0, 255)
    base[..., 1] = np.clip(BG[1] + 28 * yy + 8 * np.sin(xx * math.pi), 0, 255)
    base[..., 2] = np.clip(BG[2] + 34 * xx + 16 * yy, 0, 255)
    return Image.fromarray(base, "RGB")


def draw_asset_panel(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    asset_path: str,
    label: str,
    fallback: bool,
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=10, fill=PANEL, outline=LINE, width=2)
    src = load_asset(asset_path)
    inner = (x2 - x1 - 28, y2 - y1 - 58)
    if src is None:
        draw.rounded_rectangle((x1 + 14, y1 + 14, x2 - 14, y2 - 44), radius=8, fill=(30, 42, 55), outline=LINE)
        draw_wrapped(draw, (x1 + 34, y1 + 50), f"Missing asset:\n{asset_path}", 22, MUTED, width=inner[0] - 40)
    else:
        fitted = fit_contain(src, inner)
        img.paste(fitted, (x1 + 14, y1 + 14))
    tag = "FALLBACK" if fallback else "EVIDENCE"
    tag_color = AMBER if fallback else CYAN
    draw.text((x1 + 16, y2 - 35), tag, font=font(18, True), fill=tag_color)
    draw_wrapped(draw, (x1 + 130, y2 - 36), label, 17, MUTED, width=x2 - x1 - 150, bold=False, line_gap=2)


def draw_scene(scene: Scene, index: int, total_duration: int, elapsed: int, width: int, height: int) -> Image.Image:
    img = gradient_background(width, height, index)
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((40, 34, width - 40, 86), radius=12, fill=(8, 14, 20), outline=(42, 59, 76))
    badge_color = AMBER if scene.fallback else CYAN
    draw.rounded_rectangle((width - 285, 47, width - 58, 75), radius=6, fill=(18, 28, 37), outline=badge_color)
    draw.text((width - 272, 52), scene.badge, font=font(17, True), fill=badge_color)
    draw.text((60, 50), "Wearedge Industrial AI Agent｜企业组参赛演示初版", font=font(22, True), fill=INK)

    draw_wrapped(draw, (58, 118), scene.title, 42, INK, width=width - 116, bold=True, line_gap=10)
    draw_wrapped(draw, (60, 178), scene.subtitle, 25, MUTED, width=width - 120)

    text_x, text_y = 68, 270
    for bullet in scene.bullets:
        draw.ellipse((text_x, text_y + 10, text_x + 10, text_y + 20), fill=MINT)
        used = draw_wrapped(draw, (text_x + 24, text_y), bullet, 24, INK, width=520, bold=False, line_gap=6)
        text_y += max(58, used + 18)

    if scene.fallback:
        draw.rounded_rectangle((60, height - 150, 650, height - 92), radius=9, fill=(46, 34, 20), outline=AMBER, width=2)
        draw.text((78, height - 134), "边界说明：此页含 fallback/mock 证据，不能表述为 live WFC 成功日志。", font=font(20, True), fill=AMBER)

    if scene.assets:
        panel_area_x = 660
        panel_area_w = width - panel_area_x - 60
        panel_area_y = 250
        panel_area_h = height - panel_area_y - 110
        count = len(scene.assets)
        cols = 2 if count > 1 else 1
        rows = math.ceil(count / cols)
        gap = 16
        pw = (panel_area_w - gap * (cols - 1)) // cols
        ph = (panel_area_h - gap * (rows - 1)) // rows
        for i, asset in enumerate(scene.assets):
            col = i % cols
            row = i // cols
            x1 = panel_area_x + col * (pw + gap)
            y1 = panel_area_y + row * (ph + gap)
            draw_asset_panel(img, draw, (x1, y1, x1 + pw, y1 + ph), asset, Path(asset).name, scene.fallback)

    progress_x1, progress_y = 60, height - 42
    progress_x2 = width - 60
    draw.rounded_rectangle((progress_x1, progress_y, progress_x2, progress_y + 7), radius=4, fill=(42, 52, 64))
    fill_x = int(progress_x1 + (progress_x2 - progress_x1) * min(1, elapsed / max(1, total_duration)))
    draw.rounded_rectangle((progress_x1, progress_y, fill_x, progress_y + 7), radius=4, fill=CYAN)
    draw.text((progress_x1, progress_y - 28), seconds_to_timestamp(elapsed), font=font(17), fill=MUTED)
    draw.text((progress_x2 - 58, progress_y - 28), seconds_to_timestamp(total_duration), font=font(17), fill=MUTED)
    return img


def seconds_to_timestamp(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def render_narration() -> str:
    lines = [
        "# Wearedge 企业组演示视频 Final Narration",
        "",
        "生成日期：2026-06-11",
        "",
        "用途：提交前 3-5 分钟视频脚本，与 `submission-assets/live-evidence/video/wearedge-enterprise-demo-3-5min.mp4` 对齐。",
        "",
        "证据边界：Xcelerator 和 WFC 部分素材来自真实平台；Dashboard、HumanApprovalGate、`ok=true` run-log 当前有 fallback/mock/API-smoke 资产，必须按画面和 metadata 标注，不能声称已完成 live WFC `ok=true`。",
        "",
        "## Timeline",
        "",
    ]
    elapsed = 0
    for scene in SCENES:
        end = elapsed + scene.duration
        lines.extend(
            [
                f"### {seconds_to_timestamp(elapsed)}-{seconds_to_timestamp(end)} {scene.title}",
                "",
                scene.narration,
                "",
                "画面重点：",
            ]
        )
        lines.extend(f"- {bullet}" for bullet in scene.bullets)
        if scene.assets:
            lines.append("")
            lines.append("素材：")
            lines.extend(f"- `submission-assets/live-evidence/{asset}`" for asset in scene.assets)
        if scene.fallback:
            lines.append("")
            lines.append("边界标注：本段包含 fallback/mock 证据，提交讲述时必须说明 live WFC 复现仍是下一步。")
        lines.append("")
        elapsed = end
    return "\n".join(lines)


def render_video(output_dir: Path, fps: int, width: int, height: int) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / DEFAULT_VIDEO
    script_path = output_dir / DEFAULT_SCRIPT
    script_path.write_text(render_narration(), encoding="utf-8")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"could not open video writer: {video_path}")

    total_duration = sum(scene.duration for scene in SCENES)
    elapsed = 0
    missing_assets: list[str] = []
    for index, scene in enumerate(SCENES):
        for asset in scene.assets:
            if not resolve_asset(asset).exists():
                missing_assets.append(asset)
        frame = draw_scene(scene, index, total_duration, elapsed, width, height)
        frame_np = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        for _ in range(scene.duration * fps):
            writer.write(frame_np)
        elapsed += scene.duration
        print(f"rendered {seconds_to_timestamp(elapsed)} / {seconds_to_timestamp(total_duration)}")
    writer.release()

    cap = cv2.VideoCapture(str(video_path))
    opened = cap.isOpened()
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if opened else 0
    actual_fps = float(cap.get(cv2.CAP_PROP_FPS)) if opened else 0.0
    cap.release()
    duration = frames / actual_fps if actual_fps else 0
    return {
        "ok": opened and frames > 0 and 180 <= duration <= 300,
        "video": str(video_path),
        "script": str(script_path),
        "duration_seconds": round(duration, 2),
        "fps": actual_fps,
        "frames": frames,
        "missing_assets": missing_assets,
        "fallback_scenes": sum(1 for scene in SCENES if scene.fallback),
    }


def script_only(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    script_path = output_dir / DEFAULT_SCRIPT
    script_path.write_text(render_narration(), encoding="utf-8")
    return {
        "ok": True,
        "script": str(script_path),
        "duration_seconds": sum(scene.duration for scene in SCENES),
        "scene_count": len(SCENES),
        "fallback_scenes": sum(1 for scene in SCENES if scene.fallback),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Wearedge enterprise-group 3-5 minute demo video.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--script-only", action="store_true", help="Generate narration only; skip MP4 rendering.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = script_only(args.output_dir) if args.script_only else render_video(args.output_dir, args.fps, args.width, args.height)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}={value}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
