import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..");
const outputDir = process.env.CNMAKER_ATTACHMENTS_DIR
  ? path.resolve(process.env.CNMAKER_ATTACHMENTS_DIR)
  : path.join(repoRoot, "submission-assets", "live-evidence", "cnmaker-required-attachments");
const previewDir = path.join(outputDir, "roadshow-preview");
const pptxPath = path.join(outputDir, "Wearedge-路演PPT-初赛提交.pptx");
const artifactEntry = process.env.ARTIFACT_TOOL_ENTRY ||
  path.join(process.env.USERPROFILE || "", ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "node", "node_modules", "@oai", "artifact-tool", "dist", "artifact_tool.mjs");

const { Presentation, PresentationFile } = await import(pathToFileURL(artifactEntry).href);

const W = 1280;
const H = 720;
const page = { left: 64, top: 54, width: 1152, height: 612 };
const colors = {
  navy: "#0B2545",
  blue: "#155A9C",
  teal: "#0FA3B1",
  amber: "#F2C94C",
  ink: "#17202A",
  muted: "#607080",
  light: "#F5F8FB",
  line: "#D7E0E8",
  green: "#1E8E5A",
  red: "#B42318",
  white: "#FFFFFF",
};
const typeface = "Microsoft YaHei";

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function readImageBlob(imagePath) {
  const bytes = await fs.readFile(imagePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function textbox(slide, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface,
    fontSize: style.fontSize ?? 22,
    bold: style.bold ?? false,
    color: style.color ?? colors.ink,
    alignment: style.alignment ?? "left",
  };
  return shape;
}

function rect(slide, position, fill, line = colors.line, radius = "rounded-lg") {
  return slide.shapes.add({
    geometry: "roundRect",
    position,
    fill,
    line: { style: "solid", fill: line, width: 1 },
    borderRadius: radius,
  });
}

function title(slide, text, kicker = "WEAREDGE INDUSTRIAL AI AGENT") {
  textbox(slide, kicker, { left: page.left, top: 28, width: 540, height: 24 }, {
    fontSize: 12,
    bold: true,
    color: colors.teal,
  });
  textbox(slide, text, { left: page.left, top: 58, width: 860, height: 58 }, {
    fontSize: 34,
    bold: true,
    color: colors.navy,
  });
  slide.shapes.add({
    geometry: "rect",
    position: { left: page.left, top: 124, width: 146, height: 4 },
    fill: colors.amber,
    line: { style: "solid", fill: colors.amber, width: 0 },
  });
}

function footer(slide, n) {
  textbox(slide, "第十一届“创客中国”工业智能体专题赛 · 企业组初赛", {
    left: page.left,
    top: 682,
    width: 760,
    height: 20,
  }, { fontSize: 10, color: colors.muted });
  textbox(slide, String(n).padStart(2, "0"), {
    left: 1178,
    top: 678,
    width: 40,
    height: 24,
  }, { fontSize: 12, bold: true, color: colors.muted, alignment: "right" });
}

function bulletCard(slide, x, y, w, h, heading, body, accent = colors.teal) {
  rect(slide, { left: x, top: y, width: w, height: h }, colors.white, colors.line, "rounded-xl");
  slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: 8, height: h },
    fill: accent,
    line: { style: "solid", fill: accent, width: 0 },
  });
  textbox(slide, heading, { left: x + 22, top: y + 16, width: w - 36, height: 30 }, {
    fontSize: 20,
    bold: true,
    color: colors.navy,
  });
  textbox(slide, body, { left: x + 22, top: y + 54, width: w - 36, height: h - 66 }, {
    fontSize: 15,
    color: colors.ink,
  });
}

async function addImage(slide, imagePath, position, alt) {
  try {
    await fs.access(imagePath);
    const blob = await readImageBlob(imagePath);
    slide.images.add({
      blob,
      contentType: "image/png",
      alt,
      fit: "contain",
      position,
      geometry: "roundRect",
      borderRadius: "rounded-xl",
      line: { style: "solid", fill: colors.line, width: 1 },
    });
  } catch {
    rect(slide, position, colors.light, colors.line, "rounded-xl");
    textbox(slide, alt + "\n素材未找到，保留占位", {
      left: position.left + 20,
      top: position.top + 24,
      width: position.width - 40,
      height: position.height - 48,
    }, { fontSize: 16, color: colors.muted });
  }
}

function addFlow(slide) {
  const steps = [
    ["现场数据", "MES/QMS/EMS/CMMS\n设备信号/图像/SOP"],
    ["端侧智能体", "Jetson / IPC / 工控机\nGemma 4 E2B + KPI矩阵"],
    ["平台编排", "Xcelerator / 工易魔方\n资源块 + Function Block"],
    ["审批回写", "Dashboard / 数据表\nHumanApprovalGate"],
  ];
  const x0 = 92;
  const y = 322;
  const w = 236;
  const gap = 46;
  for (let i = 0; i < steps.length; i++) {
    const x = x0 + i * (w + gap);
    rect(slide, { left: x, top: y, width: w, height: 138 }, colors.white, colors.line, "rounded-xl");
    textbox(slide, steps[i][0], { left: x + 18, top: y + 18, width: w - 36, height: 28 }, {
      fontSize: 21,
      bold: true,
      color: i === 1 ? colors.teal : colors.navy,
      alignment: "center",
    });
    textbox(slide, steps[i][1], { left: x + 18, top: y + 58, width: w - 36, height: 62 }, {
      fontSize: 15,
      color: colors.ink,
      alignment: "center",
    });
    if (i < steps.length - 1) {
      textbox(slide, "→", { left: x + w + 8, top: y + 45, width: 30, height: 44 }, {
        fontSize: 34,
        bold: true,
        color: colors.amber,
        alignment: "center",
      });
    }
  }
}

function addMetric(slide, x, y, value, label, color = colors.teal) {
  rect(slide, { left: x, top: y, width: 250, height: 132 }, colors.white, colors.line, "rounded-xl");
  textbox(slide, value, { left: x + 18, top: y + 24, width: 214, height: 52 }, {
    fontSize: 37,
    bold: true,
    color,
    alignment: "center",
  });
  textbox(slide, label, { left: x + 18, top: y + 82, width: 214, height: 36 }, {
    fontSize: 14,
    color: colors.ink,
    alignment: "center",
  });
}

async function build() {
  await fs.mkdir(outputDir, { recursive: true });
  await fs.mkdir(previewDir, { recursive: true });
  const p = Presentation.create({ slideSize: { width: W, height: H } });

  // 1
  {
    const s = p.slides.add();
    s.background.fill = colors.light;
    textbox(s, "WEAREDGE", { left: 64, top: 42, width: 200, height: 28 }, { fontSize: 17, bold: true, color: colors.teal });
    textbox(s, "端侧工业智能体\n协同决策系统", { left: 74, top: 156, width: 720, height: 150 }, { fontSize: 54, bold: true, color: colors.navy });
    textbox(s, "基于西门子Xcelerator / 工易魔方，把Jetson、IPC、本地工控机上的端侧智能体编排成可执行、可审批、可回写的产线级工作流。", {
      left: 78,
      top: 330,
      width: 700,
      height: 92,
    }, { fontSize: 22, color: colors.ink });
    addMetric(s, 840, 132, "5类", "维护 / 质量 / 能源 / 柔性生产 / WFC", colors.blue);
    addMetric(s, 840, 288, "4500", "Jetson HTTP决策路径样本", colors.teal);
    addMetric(s, 840, 444, "6ms", "端侧FastAPI路径p95延迟", colors.green);
    footer(s, 1);
  }

  // 2
  {
    const s = p.slides.add();
    s.background.fill = colors.white;
    title(s, "具体工业问题：多SKU产线的跨系统协同决策");
    bulletCard(s, 80, 174, 340, 360, "现场问题", "订单变化、换型压力、设备振动、首件质量、能耗峰值同时出现，维护、质量、能源、生产调度各自判断，响应慢且证据链断裂。", colors.red);
    bulletCard(s, 470, 174, 340, 360, "AI落地难点", "工业场景不能让大模型直接控制PLC、机器人、停线或质量放行。模型需要变成有指标、有边界、有审批的工作流节点。", colors.amber);
    bulletCard(s, 860, 174, 340, 360, "Wearedge答案", "端侧智能体靠近产线数据运行，平台负责编排、Dashboard、人机协同和回写，把单点智能升级为产线级协同。", colors.teal);
    footer(s, 2);
  }

  // 3
  {
    const s = p.slides.add();
    s.background.fill = colors.light;
    title(s, "解决方案架构：端侧运行时 + 平台编排");
    textbox(s, "模型负责解释证据，KPI矩阵和确定性守卫负责最终动作边界；高风险动作进入HumanApprovalGate。", {
      left: 88,
      top: 160,
      width: 1000,
      height: 48,
    }, { fontSize: 21, color: colors.ink });
    addFlow(s);
    footer(s, 3);
  }

  // 4
  {
    const s = p.slides.add();
    s.background.fill = colors.white;
    title(s, "联合智能体：覆盖不少于三个赛题方向");
    const agents = [
      ["设备运维", "预测性维护、根因Top3、工单建议", colors.blue],
      ["质量管控", "缺陷隔离、扩检、质量确认", colors.teal],
      ["能源管理", "能耗预测、空转识别、节能窗口", colors.green],
      ["柔性生产", "换型约束、排产建议、首件验证", colors.amber],
      ["Workflow Canvas", "资源块、功能块、数据表、Dashboard", colors.navy],
    ];
    agents.forEach((a, i) => {
      const x = 88 + (i % 3) * 374;
      const y = 170 + Math.floor(i / 3) * 180;
      bulletCard(s, x, y, 330, 132, a[0], a[1], a[2]);
    });
    textbox(s, "当前初赛主口径：设备运维核心功能已完成；柔性生产调度效率作为加强证据。决赛继续强化维护、质量、能源、柔性生产和WFC五方向协同。", {
      left: 88,
      top: 562,
      width: 1060,
      height: 52,
    }, { fontSize: 18, color: colors.ink });
    footer(s, 4);
  }

  // 5
  {
    const s = p.slides.add();
    s.background.fill = colors.light;
    title(s, "Xcelerator / 工易魔方平台证据");
    await addImage(s, path.join(repoRoot, "submission-assets/live-evidence/xcelerator/16-openapi-four-apis-imported.png"), { left: 72, top: 162, width: 520, height: 328 }, "Xcelerator OpenAPI四接口导入截图");
    await addImage(s, path.join(repoRoot, "submission-assets/live-evidence/gongyi-mofang/05-run-log-ok-true.png"), { left: 632, top: 162, width: 520, height: 328 }, "工易魔方运行日志ok=true截图");
    textbox(s, "证据说明：Xcelerator中完成API草稿/接口导入；工易魔方中完成WFC项目、Python Function Block、数据表、Dashboard、运行日志与人工确认证据。", {
      left: 86,
      top: 530,
      width: 1050,
      height: 50,
    }, { fontSize: 17, color: colors.ink });
    footer(s, 5);
  }

  // 6
  {
    const s = p.slides.add();
    s.background.fill = colors.white;
    title(s, "端侧证据：Jetson FastAPI决策路径");
    addMetric(s, 90, 176, "300", "benchmark iterations", colors.blue);
    addMetric(s, 370, 176, "4500", "HTTP samples", colors.teal);
    addMetric(s, 650, 176, "6/33ms", "p95 / max latency", colors.green);
    addMetric(s, 930, 176, "32.33MB", "gateway RSS max", colors.amber);
    await addImage(s, path.join(repoRoot, "submission-assets/live-evidence/edge-runtime/02-runtime-profile.png"), { left: 110, top: 360, width: 500, height: 190 }, "Edge runtime profile截图");
    await addImage(s, path.join(repoRoot, "submission-assets/live-evidence/edge-runtime/01-healthz.png"), { left: 670, top: 360, width: 430, height: 190 }, "Healthz截图");
    textbox(s, "边界：该证据测量Workflow Canvas协同决策HTTP路径，不等同于高分辨率图像/VLM推理耗时。", {
      left: 100,
      top: 574,
      width: 1000,
      height: 34,
    }, { fontSize: 15, color: colors.muted });
    footer(s, 6);
  }

  // 7
  {
    const s = p.slides.add();
    s.background.fill = colors.light;
    title(s, "初赛指标：单智能体核心功能 + 离线数据集验证");
    slideChart(s, 94, 178);
    const rows = [
      ["维护F1", "87.0%", ">=85%", "PASS"],
      ["调度效率提升", "21.0%", ">=20%", "PASS"],
      ["离线样例", "5/5", "通过验证", "PASS"],
      ["决策准确率估算", "95.0%", ">=90%", "PASS"],
    ];
    addTableLike(s, rows, 730, 172, 410, 282);
    textbox(s, "数据来源：evals/competition_offline_dataset.jsonl；脚本：scripts/run_competition_eval.py；边界：离线/仿真验证，不声称客户真实产线数据。", {
      left: 94,
      top: 520,
      width: 1020,
      height: 54,
    }, { fontSize: 17, color: colors.ink });
    footer(s, 7);
  }

  // 8
  {
    const s = p.slides.add();
    s.background.fill = colors.white;
    title(s, "商业化：面向可复制的行业模板");
    bulletCard(s, 82, 178, 334, 310, "目标客户", "汽车零部件、电子装配、包装、食品、医药、多品种小批量离散制造企业；优先服务已有MES/QMS/EMS/CMMS或计划使用Xcelerator/工易魔方的客户。", colors.blue);
    bulletCard(s, 474, 178, 334, 310, "商业模式", "联合PoC服务、工易魔方场景模板授权、边缘Agent Runtime部署集成、知识库与规则持续运营。", colors.teal);
    bulletCard(s, 866, 178, 334, 310, "ROI方向", "减少非计划停机、降低缺陷与返工、优化能耗、缩短换型协调时间、复制一线专家经验。", colors.amber);
    footer(s, 8);
  }

  // 9
  {
    const s = p.slides.add();
    s.background.fill = colors.light;
    title(s, "与西门子共创：从初赛PoC走向决赛端到端验证");
    const items = [
      ["初赛提交", "商业计划书、路演PPT、技术方案、算法代码、离线验证、平台证据"],
      ["入围后", "与西门子专家确认行业场景、数据表、WFC工作流和验收指标"],
      ["决赛阶段", "在Xcelerator或工易魔方完成端到端执行验证，强化HMI自然语言和可视化"],
      ["产品化", "沉淀可复制行业模板：维护、质量、能源、柔性生产、WFC协同"],
    ];
    items.forEach((it, i) => {
      const y = 166 + i * 104;
      rect(s, { left: 110, top: y, width: 1040, height: 72 }, colors.white, colors.line, "rounded-xl");
      textbox(s, `${i + 1}`, { left: 130, top: y + 12, width: 42, height: 42 }, { fontSize: 28, bold: true, color: colors.teal, alignment: "center" });
      textbox(s, it[0], { left: 196, top: y + 14, width: 180, height: 26 }, { fontSize: 22, bold: true, color: colors.navy });
      textbox(s, it[1], { left: 388, top: y + 15, width: 700, height: 38 }, { fontSize: 17, color: colors.ink });
    });
    footer(s, 9);
  }

  // 10
  {
    const s = p.slides.add();
    s.background.fill = colors.navy;
    textbox(s, "为什么有机会争第一", { left: 92, top: 74, width: 820, height: 62 }, { fontSize: 44, bold: true, color: colors.white });
    const wins = [
      "创新性：不是云端Chatbot，而是端侧产线级协同智能体。",
      "技术水平：API、OpenAPI、WFC资源块、评估脚本、Jetson证据均可复验。",
      "应用前景：维护、质量、能源、柔性生产模板可复制到多行业产线。",
      "可行性：真实平台证据 + 本地备用演示 + 明确安全边界。",
    ];
    wins.forEach((w, i) => {
      textbox(s, `0${i + 1}`, { left: 116, top: 186 + i * 82, width: 56, height: 34 }, { fontSize: 22, bold: true, color: colors.amber });
      textbox(s, w, { left: 186, top: 184 + i * 82, width: 900, height: 38 }, { fontSize: 24, bold: false, color: colors.white });
    });
    textbox(s, "提交边界：离线/仿真指标和平台PoC证据如实标注；企业主体、联系人、签章承诺由负责人在报名系统最终补齐。", {
      left: 116,
      top: 584,
      width: 980,
      height: 42,
    }, { fontSize: 17, color: "#D7E0E8" });
    footer(s, 10);
  }

  for (const [index, slide] of p.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(previewDir, `${stem}.png`), await p.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(previewDir, `${stem}.layout.json`), await layout.text());
  }
  await writeBlob(path.join(previewDir, "deck-montage.webp"), await p.export({ format: "webp", montage: true, scale: 1 }));
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(pptxPath);
  const manifest = {
    generatedAt: new Date().toISOString(),
    pptxPath,
    slideCount: p.slides.items.length,
    previewDir,
    montagePath: path.join(previewDir, "deck-montage.webp"),
    artifactToolEntry: artifactEntry,
    boundary: "Deck uses offline/simulated metrics and platform PoC evidence; it does not claim production deployment.",
  };
  await fs.writeFile(path.join(outputDir, "roadshow-deck-manifest.json"), JSON.stringify(manifest, null, 2));
  console.log(JSON.stringify(manifest, null, 2));
  process.exit(0);
}

function slideChart(slide, x, y) {
  rect(slide, { left: x, top: y, width: 560, height: 284 }, colors.white, colors.line, "rounded-xl");
  slide.charts.add("bar", {
    position: { left: x + 46, top: y + 48, width: 468, height: 190 },
    categories: ["维护F1", "调度提升", "准确率估算"],
    series: [
      { name: "当前", values: [87, 21, 95], fill: colors.teal },
      { name: "目标", values: [85, 20, 90], fill: colors.amber },
    ],
    hasLegend: true,
    dataLabels: { showValue: true, position: "outEnd" },
    yAxis: { majorGridlines: { style: "solid", fill: colors.line, width: 1 } },
  });
}

function addTableLike(slide, rows, x, y, w, h) {
  rect(slide, { left: x, top: y, width: w, height: h }, colors.white, colors.line, "rounded-xl");
  const cols = [0, 154, 252, 342];
  textbox(slide, "指标", { left: x + 18, top: y + 18, width: 120, height: 24 }, { fontSize: 14, bold: true, color: colors.navy });
  textbox(slide, "结果", { left: x + cols[1], top: y + 18, width: 80, height: 24 }, { fontSize: 14, bold: true, color: colors.navy });
  textbox(slide, "目标", { left: x + cols[2], top: y + 18, width: 80, height: 24 }, { fontSize: 14, bold: true, color: colors.navy });
  textbox(slide, "状态", { left: x + cols[3], top: y + 18, width: 60, height: 24 }, { fontSize: 14, bold: true, color: colors.navy });
  rows.forEach((r, i) => {
    const top = y + 58 + i * 48;
    textbox(slide, r[0], { left: x + 18, top, width: 132, height: 30 }, { fontSize: 13, color: colors.ink });
    textbox(slide, r[1], { left: x + cols[1], top, width: 92, height: 30 }, { fontSize: 13, bold: true, color: colors.teal });
    textbox(slide, r[2], { left: x + cols[2], top, width: 88, height: 30 }, { fontSize: 13, color: colors.ink });
    textbox(slide, r[3], { left: x + cols[3], top, width: 58, height: 30 }, { fontSize: 13, bold: true, color: colors.green });
  });
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
