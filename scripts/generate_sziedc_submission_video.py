# -*- coding: utf-8 -*-
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "submissions" / "sziedc-2026"
VIDEO_PATH = OUT_DIR / "wearedge-pro-sziedc-ai-glasses-submission.mp4"
COVER_PATH = OUT_DIR / "wearedge-pro-sziedc-ai-glasses-cover.jpg"

W, H = 1920, 1080
FPS = 24

FONT_REGULAR = Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_HEI = Path(r"C:\Windows\Fonts\simhei.ttf")

COLORS = {
    "bg": (9, 13, 19),
    "ink": (244, 248, 252),
    "muted": (158, 175, 190),
    "line": (73, 92, 112),
    "cyan": (42, 209, 212),
    "mint": (106, 238, 178),
    "amber": (255, 184, 77),
    "red": (255, 96, 96),
    "blue": (93, 154, 255),
    "panel": (20, 29, 40),
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.exists() else FONT_REGULAR
    if not path.exists():
        path = FONT_HEI
    return ImageFont.truetype(str(path), size=size)


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def ease(x: float) -> float:
    x = clamp(x)
    return x * x * (3 - 2 * x)


def rgba(color: tuple[int, int, int], alpha: int) -> tuple[int, int, int, int]:
    return color[0], color[1], color[2], alpha


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if text_size(draw, candidate, fnt)[0] <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    fill: tuple[int, int, int] | tuple[int, int, int, int] = COLORS["ink"],
    bold: bool = False,
    width: int | None = None,
    line_gap: int = 10,
    anchor: str | None = None,
) -> int:
    fnt = font(size, bold)
    if width is None:
        draw.text(xy, text, font=fnt, fill=fill, anchor=anchor)
        return text_size(draw, text, fnt)[1]

    y = xy[1]
    for line in wrap_text(draw, text, fnt, width):
        draw.text((xy[0], y), line, font=fnt, fill=fill)
        y += text_size(draw, line, fnt)[1] + line_gap
    return y - xy[1]


def rounded_panel(
    img: Image.Image,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int] = COLORS["panel"],
    outline: tuple[int, int, int] = COLORS["line"],
    radius: int = 22,
    alpha: int = 225,
) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle(box, radius=radius, fill=rgba(fill, alpha), outline=rgba(outline, 190), width=2)
    img.alpha_composite(overlay)


def make_background(seed: int = 0) -> Image.Image:
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    base = np.zeros((H, W, 3), dtype=np.float32)
    base[..., 0] = 9 + 9 * y + 8 * x
    base[..., 1] = 13 + 18 * y + 14 * np.sin((x + seed * 0.13) * math.pi)
    base[..., 2] = 20 + 28 * x + 11 * y
    vignette = 1 - 0.58 * np.sqrt((x - 0.5) ** 2 + (y - 0.52) ** 2)
    base *= vignette[..., None]
    base = np.clip(base, 0, 255).astype(np.uint8)
    img = Image.fromarray(base, "RGB").convert("RGBA")

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(11):
        px = int(((i * 277 + seed * 41) % W) - 120)
        py = int(((i * 149 + seed * 89) % H) - 80)
        color = COLORS["cyan"] if i % 3 == 0 else COLORS["blue"]
        d.ellipse((px, py, px + 420, py + 420), fill=rgba(color, 10))
    for x0 in range(-200, W + 200, 120):
        d.line((x0, 0, x0 + 500, H), fill=rgba(COLORS["line"], 38), width=1)
    img.alpha_composite(overlay)
    return img


def load_asset(rel: str) -> Image.Image:
    return Image.open(ROOT / rel).convert("RGBA")


def fit_image(src: Image.Image, size: tuple[int, int], cover: bool = True) -> Image.Image:
    sw, sh = src.size
    tw, th = size
    scale = max(tw / sw, th / sh) if cover else min(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(resized, ((tw - nw) // 2, (th - nh) // 2))
    if cover:
        left = max(0, (nw - tw) // 2)
        top = max(0, (nh - th) // 2)
        return resized.crop((left, top, left + tw, top + th))
    return canvas


def paste_rounded(base: Image.Image, src: Image.Image, box: tuple[int, int, int, int], radius: int = 28) -> None:
    x1, y1, x2, y2 = box
    content = fit_image(src, (x2 - x1, y2 - y1), cover=True)
    mask = Image.new("L", content.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, content.size[0], content.size[1]), radius=radius, fill=255)
    shadow = Image.new("RGBA", content.size, (0, 0, 0, 150))
    shadow_mask = mask.filter(ImageFilter.GaussianBlur(18))
    base.paste(shadow, (x1 + 12, y1 + 18), shadow_mask)
    base.paste(content, (x1, y1), mask)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box, radius=radius, outline=rgba(COLORS["cyan"], 120), width=2)


def draw_glasses(
    img: Image.Image,
    cx: int,
    cy: int,
    scale: float = 1.0,
    alpha: int = 255,
    glow: bool = True,
) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = scale
    lens_w, lens_h = int(330 * s), int(156 * s)
    gap = int(58 * s)
    lx1, ly1 = cx - gap // 2 - lens_w, cy - lens_h // 2
    rx1, ry1 = cx + gap // 2, ly1
    lens_fill = (22, 48, 62, int(alpha * 0.46))
    lens_outline = (68, 235, 232, alpha)
    for box in [(lx1, ly1, lx1 + lens_w, ly1 + lens_h), (rx1, ry1, rx1 + lens_w, ry1 + lens_h)]:
        d.rounded_rectangle(box, radius=int(38 * s), fill=lens_fill, outline=lens_outline, width=max(2, int(4 * s)))
        d.line((box[0] + int(26 * s), box[1] + int(36 * s), box[2] - int(28 * s), box[1] + int(14 * s)), fill=(255, 255, 255, int(alpha * 0.23)), width=max(2, int(3 * s)))
    d.line((lx1 + lens_w, cy, rx1, cy), fill=lens_outline, width=max(2, int(5 * s)))
    d.arc((cx - int(55 * s), cy - int(12 * s), cx + int(55 * s), cy + int(72 * s)), 180, 360, fill=lens_outline, width=max(2, int(4 * s)))
    d.line((lx1, cy - int(18 * s), lx1 - int(210 * s), cy - int(104 * s)), fill=(95, 113, 132, alpha), width=max(3, int(8 * s)))
    d.line((rx1 + lens_w, cy - int(18 * s), rx1 + lens_w + int(210 * s), cy - int(104 * s)), fill=(95, 113, 132, alpha), width=max(3, int(8 * s)))
    d.rounded_rectangle(
        (rx1 + lens_w - int(62 * s), ry1 + int(28 * s), rx1 + lens_w + int(42 * s), ry1 + int(86 * s)),
        radius=int(18 * s),
        fill=(34, 42, 54, alpha),
        outline=(255, 184, 77, alpha),
        width=max(2, int(3 * s)),
    )
    d.ellipse(
        (rx1 + lens_w - int(36 * s), ry1 + int(42 * s), rx1 + lens_w - int(7 * s), ry1 + int(71 * s)),
        fill=(5, 13, 18, alpha),
        outline=(42, 209, 212, alpha),
        width=max(2, int(3 * s)),
    )
    d.rounded_rectangle(
        (lx1 + int(42 * s), ly1 + int(102 * s), lx1 + int(196 * s), ly1 + int(130 * s)),
        radius=int(12 * s),
        fill=(42, 209, 212, int(alpha * 0.28)),
        outline=(42, 209, 212, int(alpha * 0.75)),
        width=max(1, int(2 * s)),
    )
    if glow:
        blur = overlay.filter(ImageFilter.GaussianBlur(int(14 * s)))
        img.alpha_composite(blur)
    img.alpha_composite(overlay)


def draw_badge(
    img: Image.Image,
    xy: tuple[int, int],
    text: str,
    color: tuple[int, int, int] = COLORS["cyan"],
    size: int = 34,
) -> None:
    d = ImageDraw.Draw(img)
    f = font(size, True)
    tw, th = text_size(d, text, f)
    x, y = xy
    d.rounded_rectangle(
        (x, y, x + tw + 42, y + th + 24),
        radius=22,
        fill=(17, 26, 35, 255),
        outline=(color[0], color[1], color[2], 255),
        width=2,
    )
    d.text((x + 21, y + 8), text, font=f, fill=color)


def draw_progress(img: Image.Image, t_global: float, total: float) -> None:
    d = ImageDraw.Draw(img)
    x1, y, x2 = 110, H - 58, W - 110
    d.rounded_rectangle((x1, y, x2, y + 7), radius=4, fill=rgba(COLORS["line"], 120))
    d.rounded_rectangle((x1, y, int(x1 + (x2 - x1) * clamp(t_global / total)), y + 7), radius=4, fill=rgba(COLORS["cyan"], 220))


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, body: str, accent: tuple[int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=24, fill=rgba(COLORS["panel"], 226), outline=rgba(accent, 170), width=2)
    draw.rounded_rectangle((x1, y1, x1 + 9, y2), radius=5, fill=rgba(accent, 230))
    draw.text((x1 + 36, y1 + 28), title, font=font(39, True), fill=accent)
    draw_text(draw, (x1 + 36, y1 + 91), body, 30, fill=COLORS["ink"], width=x2 - x1 - 72, line_gap=8)


def scene_title(t: float, duration: float, total_t: float) -> Image.Image:
    img = make_background(1)
    d = ImageDraw.Draw(img)
    p = ease(t / duration)
    draw_badge(img, (118, 96), "2026 深圳国际眼镜（人工智能）设计大赛｜人工智能眼镜组", COLORS["amber"], 32)
    draw_glasses(img, int(W * 0.67), int(H * 0.47), scale=1.0 + 0.04 * math.sin(t * 2.0), alpha=255)

    x = int(110 + (1 - p) * -90)
    d.text((x, 272), "WearEdge Pro", font=font(92, True), fill=COLORS["ink"])
    d.text((x, 380), "可穿戴边缘工业多模态 AI Agent 系统", font=font(54, True), fill=COLORS["cyan"])
    draw_text(d, (x, 472), "AR/M400 视觉采集 + 随身 Jetson 边缘算力 + 本地多模态模型 + 工业工作流", 34, fill=COLORS["muted"], width=780, line_gap=8)
    d.rounded_rectangle((110, 738, 900, 858), radius=28, fill=rgba((16, 25, 34), 210), outline=rgba(COLORS["cyan"], 135), width=2)
    d.text((145, 765), "数据不出厂｜低延迟｜免脱手｜可审计", font=font(44, True), fill=COLORS["mint"])
    d.text((145, 824), "面向维修、质检、换型、作业指导和安全巡检", font=font(28), fill=COLORS["ink"])
    draw_progress(img, total_t, TOTAL_DURATION)
    return img


def scene_problem(t: float, duration: float, total_t: float, assets: dict[str, Image.Image]) -> Image.Image:
    bg = fit_image(assets["safety"], (W, H), cover=True).filter(ImageFilter.GaussianBlur(2))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(bg)
    overlay = Image.new("RGBA", (W, H), (4, 9, 14, 178))
    img.alpha_composite(overlay)
    d = ImageDraw.Draw(img)
    d.text((110, 100), "工业现场的 AI 眼镜，必须解决现场问题", font=font(56, True), fill=COLORS["ink"])
    d.text((112, 174), "不是把照片发到云端，而是在一线把证据变成行动", font=font(34), fill=COLORS["muted"])
    items = [
        ("数据安全", "生产图像、图纸、工艺参数和维修日志不能随意上传云端。", COLORS["cyan"]),
        ("实时响应", "质检、排障和安全预警需要秒级反馈，不能等待远端链路。", COLORS["amber"]),
        ("免脱手交互", "工人双手被作业占用，需要第一视角采集与轻量提示。", COLORS["mint"]),
    ]
    p = ease(t / duration)
    for i, (title, body, color) in enumerate(items):
        yy = int(300 + i * 185 + (1 - p) * 50)
        card(d, (110, yy, 890, yy + 132), title, body, color)
    draw_glasses(img, 1350, 585, scale=0.72, alpha=230)
    d.line((1275, 640, 1158, 735, 1030, 735), fill=rgba(COLORS["cyan"], 190), width=4)
    d.rounded_rectangle((932, 696, 1150, 775), radius=20, fill=rgba(COLORS["panel"], 220), outline=rgba(COLORS["cyan"], 160), width=2)
    d.text((958, 715), "一线第一视角", font=font(31, True), fill=COLORS["cyan"])
    draw_progress(img, total_t, TOTAL_DURATION)
    return img


def scene_architecture(t: float, duration: float, total_t: float) -> Image.Image:
    img = make_background(3)
    d = ImageDraw.Draw(img)
    d.text((110, 92), "作品结构：感知轻量化，算力随身化", font=font(60, True), fill=COLORS["ink"])
    d.text((112, 171), "把重算力从头部移到随身边缘节点，让眼镜更轻、更稳、更适合长时间佩戴。", font=font(32), fill=COLORS["muted"])

    nodes = [
        ((255, 450), "AR/M400 眼镜", "第一视角图像\n高亮提示显示", COLORS["cyan"]),
        ((630, 450), "骨传导音频", "开放双耳\n保留环境声", COLORS["mint"]),
        ((1045, 450), "Jetson 边缘大脑", "本地 VLM + RAG\n工作流编排", COLORS["amber"]),
        ((1460, 450), "工业系统", "CMMS/QMS/MES/EHS\n人机确认", COLORS["blue"]),
    ]
    p = ease(t / duration)
    for i, (center, title, body, color) in enumerate(nodes):
        x, y = center
        delay = clamp((p - i * 0.1) / 0.55)
        yy = int(y + (1 - ease(delay)) * 40)
        d.rounded_rectangle((x - 190, yy - 110, x + 190, yy + 155), radius=32, fill=rgba(COLORS["panel"], 220), outline=rgba(color, 180), width=3)
        d.ellipse((x - 34, yy - 82, x + 34, yy - 14), fill=rgba(color, 48), outline=rgba(color, 200), width=3)
        d.text((x, yy - 73), str(i + 1), font=font(38, True), fill=color, anchor="ma")
        d.text((x, yy + 4), title, font=font(35, True), fill=COLORS["ink"], anchor="ma")
        for j, line in enumerate(body.split("\n")):
            d.text((x, yy + 61 + j * 38), line, font=font(27), fill=COLORS["muted"], anchor="ma")
    for i in range(len(nodes) - 1):
        x1, y1 = nodes[i][0]
        x2, y2 = nodes[i + 1][0]
        pulse = (math.sin(t * 4 + i) + 1) / 2
        d.line((x1 + 196, y1, x2 - 196, y2), fill=rgba(COLORS["cyan"], int(120 + 100 * pulse)), width=5)
        ax = int(lerp(x1 + 208, x2 - 208, (t * 0.55 + i * 0.2) % 1))
        d.ellipse((ax - 9, y1 - 9, ax + 9, y1 + 9), fill=rgba(COLORS["cyan"], 230))
    d.rounded_rectangle((430, 760, 1490, 880), radius=30, fill=rgba((8, 22, 30), 225), outline=rgba(COLORS["mint"], 145), width=2)
    d.text((960, 790), "模型只解释证据；停机、放行、报修由确定性 action map 决定", font=font(42, True), fill=COLORS["mint"], anchor="ma")
    d.text((960, 846), "让 AI 眼镜可以接入真实工业流程，而不是停留在自然语言建议", font=font(28), fill=COLORS["ink"], anchor="ma")
    draw_progress(img, total_t, TOTAL_DURATION)
    return img


def scene_structure(t: float, duration: float, total_t: float) -> Image.Image:
    img = make_background(5)
    d = ImageDraw.Draw(img)
    d.text((110, 90), "面向佩戴体验的结构设计", font=font(60, True), fill=COLORS["ink"])
    d.text((112, 170), "眼镜端只保留感知、显示和交互；推理、检索、审计由随身边缘节点承担。", font=font(32), fill=COLORS["muted"])
    draw_glasses(img, 710, 510, scale=0.93, alpha=255)
    callouts = [
        ((1040, 290), "微型摄像头", "第一视角采集工位、设备和仪表", COLORS["cyan"], (960, 424)),
        ((1145, 455), "高亮显示", "缺陷框、风险动作、换型步骤投射到视野", COLORS["mint"], (660, 586)),
        ((1080, 650), "骨传导音频", "保留环境警报与机械异响感知", COLORS["amber"], (405, 420)),
        ((250, 765), "算力与感知分离", "头部轻量，随身节点承载本地模型", COLORS["blue"], (870, 425)),
    ]
    for (x, y), title, body, color, target in callouts:
        d.line((x, y + 34, target[0], target[1]), fill=rgba(color, 180), width=3)
        d.ellipse((target[0] - 8, target[1] - 8, target[0] + 8, target[1] + 8), fill=rgba(color, 230))
        d.rounded_rectangle((x, y, x + 570, y + 120), radius=26, fill=rgba(COLORS["panel"], 225), outline=rgba(color, 160), width=2)
        d.text((x + 30, y + 20), title, font=font(34, True), fill=color)
        d.text((x + 30, y + 68), body, font=font(26), fill=COLORS["ink"])
    d.rounded_rectangle((110, 895, 1810, 974), radius=24, fill=rgba((19, 31, 42), 220), outline=rgba(COLORS["line"], 130), width=2)
    d.text((960, 916), "评分对应：结构设计 40%｜穿戴体验 30%｜智能应用 20%｜市场潜力 10%", font=font(34, True), fill=COLORS["ink"], anchor="ma")
    draw_progress(img, total_t, TOTAL_DURATION)
    return img


def scene_demo(t: float, duration: float, total_t: float, assets: dict[str, Image.Image]) -> Image.Image:
    img = make_background(8)
    d = ImageDraw.Draw(img)
    d.text((110, 82), "典型应用：一副眼镜，五类工业 Agent", font=font(58, True), fill=COLORS["ink"])
    d.text((112, 160), "从第一视角图像到本地推理，再到可接系统的 action card。", font=font(32), fill=COLORS["muted"])
    demos = [
        ("maintenance", "预测性维护", "识别温度、振动、润滑、报警，生成维修工单建议", "maintenance", COLORS["amber"]),
        ("iqc", "在线 IQC 质检", "识别毛刺、划痕、污染，触发 quality hold", "iqc", COLORS["cyan"]),
        ("changeover", "换型指导", "读取 SKU、工位、治具状态，核对 released source", "changeover", COLORS["mint"]),
        ("wi", "作业指导", "现场调取 WI 要点，给出可执行的操作提示", "wi", COLORS["blue"]),
        ("hazard", "安全巡检", "识别通道堵塞、夹点、PPE、跌倒等暴露风险", "hazard", COLORS["red"]),
    ]
    index = min(len(demos) - 1, int((t / duration) * len(demos)))
    local_t = (t / duration) * len(demos) - index
    key, title, desc, img_key, accent = demos[index]
    x1, y1, x2, y2 = 110, 245, 1110, 905
    paste_rounded(img, assets[img_key], (x1, y1, x2, y2), radius=32)
    veil = Image.new("RGBA", (x2 - x1, y2 - y1), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    vd.rectangle((0, 0, x2 - x1, y2 - y1), fill=(0, 0, 0, 50))
    img.alpha_composite(veil, (x1, y1))
    d.rounded_rectangle((145, 805, 875, 875), radius=20, fill=rgba((5, 13, 18), 210), outline=rgba(accent, 160), width=2)
    d.text((176, 819), f"{title}｜{key}", font=font(34, True), fill=accent)

    rounded_panel(img, (1180, 245, 1810, 905), fill=(18, 26, 36), outline=accent, radius=32, alpha=232)
    d.text((1225, 293), title, font=font(54, True), fill=accent)
    draw_text(d, (1225, 375), desc, 34, fill=COLORS["ink"], width=510, line_gap=10)
    d.rounded_rectangle((1225, 532, 1758, 780), radius=28, fill=rgba((7, 17, 24), 230), outline=rgba(COLORS["line"], 150), width=2)
    d.text((1260, 565), "Action Card", font=font(36, True), fill=COLORS["mint"])
    fields = {
        "maintenance": [("channel", "maintenance_report"), ("owner", "maintenance_engineer"), ("target", "maintenance_work_order")],
        "iqc": [("channel", "quality_hold"), ("owner", "quality_engineer"), ("target", "qms_quality_event")],
        "changeover": [("channel", "controlled_changeover"), ("owner", "operator_quality"), ("target", "changeover_checklist")],
        "wi": [("channel", "guided_operation"), ("owner", "operator"), ("target", "wi_reference")],
        "hazard": [("channel", "stop_and_make_safe"), ("owner", "operator"), ("target", "ehs_case")],
    }[key]
    for i, (k, v) in enumerate(fields):
        yy = 630 + i * 45
        d.text((1260, yy), k, font=font(27), fill=COLORS["muted"])
        d.text((1435, yy), v, font=font(27, True), fill=COLORS["ink"])
    d.rounded_rectangle((1225, 820, 1758, 858), radius=19, fill=rgba(accent, 44), outline=rgba(accent, 120), width=1)
    d.rectangle((1225, 820, int(1225 + 533 * ease(local_t)), 858), fill=rgba(accent, 115))
    draw_progress(img, total_t, TOTAL_DURATION)
    return img


def scene_evidence(t: float, duration: float, total_t: float) -> Image.Image:
    img = make_background(13)
    d = ImageDraw.Draw(img)
    d.text((110, 90), "工程证据：已跑通的端侧闭环", font=font(60, True), fill=COLORS["ink"])
    d.text((112, 170), "比赛视频展示的是当前 PoC 能力，不夸大为量产状态。", font=font(32), fill=COLORS["muted"])
    facts = [
        ("Jetson Orin Nano 8GB", "本地部署 Gemma 4 E2B GGUF + mmproj，多模态推理不上传云端。", COLORS["cyan"]),
        ("FastAPI Gateway", "M400/Web 图片进入 /v1/infer，输出结构化字段与审计 request_id。", COLORS["blue"]),
        ("5-Agent Runtime", "maintenance / iqc / changeover / wi / hazard 共用同一 bounded workflow。", COLORS["mint"]),
        ("25/25 Golden Passed", "动作通道、负责人、集成目标和 human gate 全部可测试。", COLORS["amber"]),
    ]
    for i, (title, body, color) in enumerate(facts):
        x = 110 + (i % 2) * 890
        y = 275 + (i // 2) * 255
        card(d, (x, y, x + 790, y + 185), title, body, color)

    d.rounded_rectangle((410, 820, 1510, 915), radius=30, fill=rgba((6, 20, 26), 230), outline=rgba(COLORS["cyan"], 170), width=2)
    d.text((960, 846), "模型解释证据，工作流决定动作", font=font(42, True), fill=COLORS["cyan"], anchor="ma")
    d.text((960, 897), "让 AI 眼镜从“看见”走向“可交付、可追溯、可接系统”", font=font(29), fill=COLORS["ink"], anchor="ma")
    draw_progress(img, total_t, TOTAL_DURATION)
    return img


def scene_market(t: float, duration: float, total_t: float) -> Image.Image:
    img = make_background(21)
    d = ImageDraw.Draw(img)
    d.text((110, 88), "市场应用：让老师傅能力随身可调用", font=font(60, True), fill=COLORS["ink"])
    d.text((112, 168), "先从高价值工位切入，再扩展到整条产线和多工厂知识复用。", font=font(32), fill=COLORS["muted"])
    columns = [
        ("减少停机", "更早收集温度、振动、报警、润滑和维修证据", COLORS["amber"]),
        ("降低返工", "一线 IQC 发现缺陷后即时触发 containment", COLORS["cyan"]),
        ("安全近失", "通道、夹点、PPE、跌倒风险可记录可追溯", COLORS["red"]),
        ("训练传承", "把老师傅经验变成现场提示和证据流程", COLORS["mint"]),
    ]
    for i, (title, body, color) in enumerate(columns):
        x = 135 + i * 445
        d.rounded_rectangle((x, 330, x + 365, 690), radius=32, fill=rgba(COLORS["panel"], 225), outline=rgba(color, 165), width=3)
        d.ellipse((x + 132, 375, x + 232, 475), fill=rgba(color, 42), outline=rgba(color, 220), width=4)
        d.text((x + 183, 392), str(i + 1), font=font(48, True), fill=color, anchor="ma")
        d.text((x + 183, 520), title, font=font(39, True), fill=color, anchor="ma")
        draw_text(d, (x + 42, 585), body, 27, fill=COLORS["ink"], width=285, line_gap=8)
    draw_glasses(img, 965, 820, scale=0.47, alpha=210)
    d.text((960, 865), "WearEdge Pro", font=font(68, True), fill=COLORS["ink"], anchor="ma")
    d.text((960, 940), "提交方向：人工智能眼镜组｜工业可穿戴边缘 AI Agent", font=font(34, True), fill=COLORS["cyan"], anchor="ma")
    draw_progress(img, total_t, TOTAL_DURATION)
    return img


def scene_end(t: float, duration: float, total_t: float) -> Image.Image:
    img = make_background(34)
    d = ImageDraw.Draw(img)
    draw_glasses(img, 960, 365, scale=0.95, alpha=255)
    d.text((960, 640), "WearEdge Pro", font=font(92, True), fill=COLORS["ink"], anchor="ma")
    d.text((960, 754), "让工业 AI 戴在一线工人身上", font=font(54, True), fill=COLORS["cyan"], anchor="ma")
    d.text((960, 828), "低延迟｜免脱手｜数据不出厂｜可审计工作流", font=font(34), fill=COLORS["muted"], anchor="ma")
    draw_badge(img, (700, 914), "2026 深圳国际眼镜（人工智能）设计大赛", COLORS["amber"], 34)
    draw_progress(img, total_t, TOTAL_DURATION)
    return img


@dataclass(frozen=True)
class Segment:
    name: str
    duration: float
    renderer: object


def build_assets() -> dict[str, Image.Image]:
    return {
        "safety": load_asset("docs/assets/wearedge-poc-safety-sample.jpeg"),
        "maintenance": load_asset("docs/assets/lao-shi-fu-maintenance-poc/02_condition_monitor.jpg"),
        "iqc": load_asset("docs/assets/iqc-m400-poc/iqc_al_housing_l3_defect_m400.png"),
        "changeover": load_asset("docs/assets/wi-changeover-source-poc/changeover_labeler_fl1_sku_c500_m400.jpg"),
        "wi": load_asset("docs/assets/wi-changeover-source-poc/wi_cartoner_st2_released_wi_m400.jpg"),
        "hazard": load_asset("docs/assets/wearedge-poc-safety-sample.jpeg"),
    }


SEGMENTS = [
    Segment("title", 6.0, scene_title),
    Segment("problem", 7.0, scene_problem),
    Segment("architecture", 9.0, scene_architecture),
    Segment("structure", 9.0, scene_structure),
    Segment("demo", 13.0, scene_demo),
    Segment("evidence", 8.0, scene_evidence),
    Segment("market", 7.0, scene_market),
    Segment("end", 4.0, scene_end),
]
TOTAL_DURATION = sum(s.duration for s in SEGMENTS)


def render_frame(global_t: float, assets: dict[str, Image.Image]) -> Image.Image:
    cursor = 0.0
    for segment in SEGMENTS:
        if global_t <= cursor + segment.duration:
            local_t = global_t - cursor
            if segment.name in {"problem", "demo"}:
                return segment.renderer(local_t, segment.duration, global_t, assets)
            return segment.renderer(local_t, segment.duration, global_t)
        cursor += segment.duration
    return scene_end(SEGMENTS[-1].duration, SEGMENTS[-1].duration, TOTAL_DURATION)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    assets = build_assets()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(VIDEO_PATH), fourcc, FPS, (W, H))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer for {VIDEO_PATH}")

    total_frames = int(TOTAL_DURATION * FPS)
    cover: Image.Image | None = None
    for frame_index in range(total_frames):
        t = frame_index / FPS
        frame = render_frame(t, assets)
        if cover is None and t >= 1.5:
            cover = frame.copy().convert("RGB")
        rgb = np.array(frame.convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        writer.write(bgr)
        if frame_index % FPS == 0:
            print(f"rendered {frame_index // FPS:02d}s / {int(TOTAL_DURATION)}s")
    writer.release()

    if cover is None:
        cover = render_frame(1.5, assets).convert("RGB")
    cover.save(COVER_PATH, quality=94)

    cap = cv2.VideoCapture(str(VIDEO_PATH))
    ok = cap.isOpened()
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if ok else 0
    fps = float(cap.get(cv2.CAP_PROP_FPS)) if ok else 0.0
    cap.release()
    if not ok or frames <= 0 or fps <= 0:
        raise RuntimeError("Video validation failed")
    print(f"wrote {VIDEO_PATH}")
    print(f"duration_seconds={frames / fps:.2f}")
    print(f"cover={COVER_PATH}")


if __name__ == "__main__":
    main()
