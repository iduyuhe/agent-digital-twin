const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.author = "杜玉河";
pres.title = "智能数字孪生系统建设 P0 评审";

const FACE = "Microsoft YaHei";
const BLUE = "2563EB", INK = "0F172A", SLATE = "475569", LIGHT = "F8FAFC",
  SKY = "0EA5E9", AMBER = "F59E0B", GREEN = "15803D", BORDER = "E2E8F0",
  SOFTBLUE = "EFF6FF", GRAYTX = "94A3B8", WHITE = "FFFFFF", DGRAY = "334155";

let PG = 0;
function makeShadow() { return { type: "outer", color: "000000", blur: 7, offset: 3, angle: 135, opacity: 0.12 }; }

// ---------- helpers ----------
function lightSlide(kicker, title) {
  PG++;
  const s = pres.addSlide();
  s.background = { color: LIGHT };
  s.addShape(pres.shapes.RECTANGLE, { x: 0.55, y: 0.5, w: 0.14, h: 0.95, fill: { color: BLUE } });
  s.addText(kicker, { x: 0.85, y: 0.5, w: 11, h: 0.3, fontFace: FACE, fontSize: 12, bold: true, color: BLUE, charSpacing: 2, margin: 0 });
  s.addText(title, { x: 0.85, y: 0.78, w: 11.6, h: 0.7, fontFace: FACE, fontSize: 27, bold: true, color: INK, margin: 0 });
  s.addText(String(PG).padStart(2, "0"), { x: 12.3, y: 0.5, w: 0.6, h: 0.4, align: "right", fontFace: FACE, fontSize: 12, bold: true, color: GRAYTX, margin: 0 });
  s.addShape(pres.shapes.LINE, { x: 0.55, y: 7.02, w: 12.23, h: 0, line: { color: BORDER, width: 1 } });
  s.addText("智能数字孪生系统建设项目 · P0 立项评审", { x: 0.55, y: 7.08, w: 9, h: 0.3, fontFace: FACE, fontSize: 9, color: GRAYTX, margin: 0 });
  return s;
}

function card(s, x, y, w, h, num, title, desc, accent) {
  accent = accent || BLUE;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: WHITE }, line: { color: BORDER, width: 1 }, rectRadius: 0.08, shadow: makeShadow() });
  s.addShape(pres.shapes.OVAL, { x: x + 0.28, y: y + 0.28, w: 0.62, h: 0.62, fill: { color: accent } });
  s.addText(num, { x: x + 0.28, y: y + 0.28, w: 0.62, h: 0.62, align: "center", valign: "middle", fontFace: FACE, fontSize: 18, bold: true, color: WHITE, margin: 0 });
  s.addText(title, { x: x + 1.05, y: y + 0.3, w: w - 1.25, h: 0.6, valign: "middle", fontFace: FACE, fontSize: 15, bold: true, color: INK, margin: 0 });
  s.addText(desc, { x: x + 0.3, y: y + 1.05, w: w - 0.6, h: h - 1.2, fontFace: FACE, fontSize: 12, color: SLATE, lineSpacingMultiple: 1.18, margin: 0 });
}

function pillW(text) {
  let n = 0;
  for (const ch of text) n += (ch.charCodeAt(0) > 255 ? 1 : 0.5);
  return 0.34 + n * 0.155;
}
function drawPill(s, x, y, text, fill, fontColor, h) {
  h = h || 0.42;
  const w = pillW(text);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, rectRadius: h / 2, line: { type: "none" } });
  s.addText(text, { x, y, w, h, align: "center", valign: "middle", fontFace: FACE, fontSize: 11, bold: true, color: fontColor, margin: 0 });
  return w;
}

const headOpt = (t) => ({ text: t, options: { fill: { color: BLUE }, color: WHITE, bold: true, fontFace: FACE, fontSize: 12, align: "left", valign: "middle" } });
const cell = (t, b) => ({ text: t, options: { fontFace: FACE, fontSize: 11, color: b ? INK : SLATE, bold: !!b, valign: "middle", align: "left" } });

// =================================================================
// P1 封面
// =================================================================
(() => {
  const c = pres.addSlide();
  c.background = { color: INK };
  c.addShape(pres.shapes.OVAL, { x: 9.6, y: -1.8, w: 5.2, h: 5.2, fill: { color: BLUE, transparency: 72 }, line: { type: "none" } });
  c.addShape(pres.shapes.OVAL, { x: 11.2, y: 4.2, w: 3.6, h: 3.6, fill: { color: SKY, transparency: 80 }, line: { type: "none" } });
  c.addText("P0 立项评审 · 智能数字孪生系统建设项目", { x: 0.9, y: 1.35, w: 10, h: 0.4, fontFace: FACE, fontSize: 14, bold: true, color: SKY, charSpacing: 2, margin: 0 });
  c.addText("智能数字孪生系统建设", { x: 0.88, y: 1.95, w: 11, h: 1.1, fontFace: FACE, fontSize: 46, bold: true, color: WHITE, margin: 0 });
  c.addText("P0 需求规格与标准符合性基线 · 评审汇报", { x: 0.9, y: 3.2, w: 11, h: 0.5, fontFace: FACE, fontSize: 20, color: "CBD5E1", margin: 0 });
  const tags = ["华为 OGG 几何内核（锁定）", "Agent 通用 MAS 接口（解耦）", "装备 · 车间 · 工厂级全覆盖", "对标 GB/T 国标 · CESI 测评"];
  let tx = 0.9;
  tags.forEach((t, i) => {
    tx += drawPill(c, tx, 4.25, t, SOFTBLUE, BLUE, 0.46) + 0.3;
    if (i === 1) { tx = 0.9; }
  });
  c.addText([
    { text: "日期：2026-08-07", options: { breakLine: true } },
    { text: "汇报人：杜玉河", options: { breakLine: true } },
    { text: "配套文档：P0 需求规格与标准符合性基线 v1.0", options: {} }
  ], { x: 0.9, y: 5.7, w: 11, h: 1.3, fontFace: FACE, fontSize: 13, color: "94A3B8", lineSpacingMultiple: 1.35, margin: 0 });
})();

// =================================================================
// P2 评审议程
// =================================================================
(() => {
  const s = lightSlide("会议导览", "评审议程（建议 60 分钟）");
  s.addText("会上聚焦三件事：确认四项固化要素、拍板六项待确认项、签署基线；签署即触发 P1。", { x: 0.85, y: 1.55, w: 11.8, h: 0.5, fontFace: FACE, fontSize: 13, color: SLATE, margin: 0 });
  const rows = [
    ["1", "项目背景与目标", "8 min", "共识项目定位"],
    ["2", "技术路线与五元架构", "10 min", "认可技术选型"],
    ["3", "标准符合性规划", "8 min", "认可对标口径"],
    ["4", "量化验收基线", "8 min", "认可签约条款"],
    ["5", "待确认项拍板 + 基线签署", "18 min", "签署生效"],
    ["6", "P1 启动安排", "8 min", "排期与资源"]
  ];
  const body = rows.map((r, i) => [
    { text: r[0], options: { fill: { color: i === 4 ? AMBER : SOFTBLUE }, color: i === 4 ? WHITE : BLUE, bold: true, align: "center", fontFace: FACE, fontSize: 14, valign: "middle" } },
    cell(r[1], true),
    { text: r[2], options: { fontFace: FACE, fontSize: 11, color: SLATE, align: "center", valign: "middle" } },
    cell(r[3])
  ]);
  s.addTable([[headOpt("#"), headOpt("环节"), headOpt("时长"), headOpt("产出")]].concat(body), {
    x: 0.55, y: 2.2, w: 12.23, colW: [0.9, 5.2, 1.6, 4.53],
    rowH: [0.5, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62], border: { type: "solid", color: BORDER, pt: 1 },
    fill: { color: WHITE }, valign: "middle", align: "left"
  });
})();

// =================================================================
// P3 一页纸结论
// =================================================================
(() => {
  const s = lightSlide("一页纸结论", "四项固化要素（评审可直接确认）");
  card(s, 0.55, 1.75, 6.0, 2.35, "①", "目标场景", "装备 + 车间 + 工厂级（新建验证 + 存量优化双场景），覆盖“装备—车间—工厂”三层。", BLUE);
  card(s, 6.78, 1.75, 6.0, 2.35, "②", "技术路线", "OGG 几何内核（锁定）+ Agent 通用 MAS 接口（解耦）+ 仿真保真层 + 实时数据底座 + 模型验证体系。", SKY);
  card(s, 0.55, 4.25, 6.0, 2.35, "③", "保真等级", "瞄准“高保真”二级 / 三级（依招标要求锁定，会上待确认）。", GREEN);
  card(s, 6.78, 4.25, 6.0, 2.35, "④", "验收基线", "几何 ≤0.5mm · 仿真 ≤±0.5% · 同步 ≤200ms（行业标尺，非强制）+ 工厂级指标 / 预测精度（测评定）。", AMBER);
})();

// =================================================================
// P4 项目背景与政策牵引
// =================================================================
(() => {
  const s = lightSlide("为什么做", "项目背景与政策牵引");
  const items = [
    ["政策牵引", "数字孪生已列入智能制造标准体系，工信部多份国标于 2025 年密集落地，行业进入“可测评、可认证”阶段。"],
    ["标准落地", "GB/T 45626-2025（装备）、GB/T 45873-2025（车间/工厂）、GB/T 43441 系列（通用要求）构成装备—车间—工厂完整标准栈。"],
    ["自主可控", "几何内核锚定国产开源 OGG（华为，BSD，替代 OCCT），智能层用通用 MAS 接口解耦，规避底层与 AI 双重锁定。"]
  ];
  let y = 1.8;
  items.forEach((it, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y, w: 12.23, h: 1.45, fill: { color: WHITE }, line: { color: BORDER, width: 1 }, rectRadius: 0.08, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.55, y, w: 0.14, h: 1.45, fill: { color: BLUE } });
    s.addText(it[0], { x: 0.95, y: y + 0.22, w: 2.6, h: 1.0, valign: "middle", fontFace: FACE, fontSize: 18, bold: true, color: BLUE, margin: 0 });
    s.addText(it[1], { x: 3.6, y: y + 0.15, w: 8.9, h: 1.15, valign: "middle", fontFace: FACE, fontSize: 13, color: SLATE, lineSpacingMultiple: 1.2, margin: 0 });
    y += 1.62;
  });
})();

// =================================================================
// P5 总体目标
// =================================================================
(() => {
  const s = lightSlide("目标定位", "总体目标");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y: 1.8, w: 12.23, h: 1.7, fill: { color: INK }, rectRadius: 0.1 });
  s.addText([
    { text: "建成覆盖", options: {} },
    { text: "“装备—车间—工厂”", options: { color: SKY, bold: true } },
    { text: " 的 ", options: {} },
    { text: "自主可控、高保真、可认证", options: { color: AMBER, bold: true } },
    { text: " 智能数字孪生系统，通过 CESI 成熟度 / 可信性测评，并在标杆场景完成闭环验收。", options: {} }
  ], { x: 1.0, y: 1.95, w: 11.3, h: 1.4, valign: "middle", fontFace: FACE, fontSize: 19, color: WHITE, lineSpacingMultiple: 1.25, margin: 0 });
  const subs = [
    ["三层全覆盖", "装备物理仿真 + 车间孪生 + 工厂级生产系统仿真（新建与存量双场景）。"],
    ["高保真可认证", "几何 / 仿真 / 同步 / 验证四类保真齐全，走 CESI 测评拿等级证书。"],
    ["闭环可落地", "至少在 1 个装备 + 1 个工厂级场景完成虚拟调试 / 产能优化闭环。"]
  ];
  let x = 0.55;
  subs.forEach((t, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.8, w: 3.94, h: 2.7, fill: { color: WHITE }, line: { color: BORDER, width: 1 }, rectRadius: 0.08, shadow: makeShadow() });
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 4.1, w: 0.7, h: 0.7, fill: { color: BLUE } });
    s.addText(String(i + 1), { x: x + 0.3, y: 4.1, w: 0.7, h: 0.7, align: "center", valign: "middle", fontFace: FACE, fontSize: 20, bold: true, color: WHITE, margin: 0 });
    s.addText(t[0], { x: x + 1.15, y: 4.12, w: 2.6, h: 0.66, valign: "middle", fontFace: FACE, fontSize: 15, bold: true, color: INK, margin: 0 });
    s.addText(t[1], { x: x + 0.35, y: 5.0, w: 3.3, h: 1.4, fontFace: FACE, fontSize: 12, color: SLATE, lineSpacingMultiple: 1.2, margin: 0 });
    x += 4.13;
  });
})();

// =================================================================
// P6 五元分层架构
// =================================================================
(() => {
  const s = lightSlide("技术架构", "五元分层架构（数据流闭环）");
  const blocks = [
    ["①", "华为 OGG", "几何内核（锁定）", "几何保真", BLUE],
    ["②", "Agent 层", "通用 MAS 接口（解耦）", "智能保真", SKY],
    ["③", "仿真保真层", "装备 CAE + 工厂级仿真", "仿真保真", GREEN],
    ["④", "实时数据底座", "边缘采集 + 同步", "同步保真", AMBER],
    ["⑤", "模型验证体系", "标定—虚实对照", "验证保真", "7C3AED"]
  ];
  let x = 0.55;
  const bw = 2.2, gap = 0.207;
  blocks.forEach((b) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.1, w: bw, h: 3.0, fill: { color: WHITE }, line: { color: b[4], width: 1.5 }, rectRadius: 0.08, shadow: makeShadow() });
    s.addShape(pres.shapes.OVAL, { x: x + bw / 2 - 0.4, y: 2.35, w: 0.8, h: 0.8, fill: { color: b[4] } });
    s.addText(b[0], { x: x + bw / 2 - 0.4, y: 2.35, w: 0.8, h: 0.8, align: "center", valign: "middle", fontFace: FACE, fontSize: 22, bold: true, color: WHITE, margin: 0 });
    s.addText(b[1], { x: x + 0.1, y: 3.3, w: bw - 0.2, h: 0.5, align: "center", fontFace: FACE, fontSize: 14, bold: true, color: INK, margin: 0 });
    s.addText(b[2], { x: x + 0.1, y: 3.82, w: bw - 0.2, h: 0.7, align: "center", fontFace: FACE, fontSize: 11, color: SLATE, lineSpacingMultiple: 1.1, margin: 0 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.3, y: 4.55, w: bw - 0.6, h: 0.42, fill: { color: b[4] }, rectRadius: 0.21 });
    s.addText(b[3], { x: x + 0.3, y: 4.55, w: bw - 0.6, h: 0.42, align: "center", valign: "middle", fontFace: FACE, fontSize: 12, bold: true, color: WHITE, margin: 0 });
    x += bw + gap;
  });
  // arrows would overlap; instead a data-flow note bar
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y: 5.45, w: 12.23, h: 1.15, fill: { color: SOFTBLUE }, line: { color: "BFDBFE", width: 1 }, rectRadius: 0.08 });
  s.addText([
    { text: "数据流闭环：", options: { bold: true, color: BLUE } },
    { text: "物理实体 →（④实时采集同步）→ ①OGG 几何模型 + ③仿真模型 ←（⑤虚实对照标定）→ ②Agent 分析预测/故障诊断/决策优化 →（④反馈控制）→ 物理实体。五元件接口标准化，可独立升级替换。", options: { color: SLATE } }
  ], { x: 0.85, y: 5.55, w: 11.6, h: 0.95, fontFace: FACE, fontSize: 12.5, valign: "middle", lineSpacingMultiple: 1.2, margin: 0 });
})();

// =================================================================
// P7 技术选型
// =================================================================
(() => {
  const s = lightSlide("选型决策", "关键构件选型与边界");
  const head = [headOpt("构件"), headOpt("推荐选型"), headOpt("边界说明")];
  const rows = [
    ["① 华为 OGG 几何内核（锁定）", "开源 BSD、替代 OCCT；保留 OCCT 退路", "几何保真核心，自主可控锚点"],
    ["② Agent 智能层（解耦）", "国产 LLM（GLM/通义/DeepSeek）+ 开源框架；通用 MAS 接口", "满足 GB/T 45626 诊断/预测；不锁定厂商"],
    ["③ 仿真保真层", "装备 CAE 国产主力（Simdroid 等）+ 工厂级引擎 POC 定", "物理 + 生产系统仿真双能力"],
    ["④ 实时数据底座", "华为云 IoT 或自选型（边缘采集 + 同步）", "承担 GB/T 43441 同步要求"],
    ["⑤ 模型验证体系", "自建标定—虚实对照—虚实验证流程", "可信闭环，测评必查"]
  ];
  const body = rows.map((r, i) => [
    cell(r[0], true), cell(r[1]), cell(r[2])
  ]);
  s.addTable([head].concat(body), {
    x: 0.55, y: 1.8, w: 12.23, colW: [3.6, 5.0, 3.63], rowH: [0.5, 0.78, 0.78, 0.78, 0.78, 0.78],
    border: { type: "solid", color: BORDER, pt: 1 }, fill: { color: WHITE }, valign: "middle"
  });
  s.addText("说明：①与⑤为系统级自建/锁定项；②/③/④保持解耦、按指标选型，规避单一厂商锁定。", { x: 0.55, y: 6.55, w: 12.23, h: 0.4, fontFace: FACE, fontSize: 11, italic: true, color: GRAYTX, margin: 0 });
})();

// =================================================================
// P8 标准符合性规划
// =================================================================
(() => {
  const s = lightSlide("合规对标", "标准符合性条款追踪矩阵");
  const head = [headOpt("国标"), headOpt("核心要求"), headOpt("由谁承担"), headOpt("满足度")];
  const rows = [
    ["GB/T 43441.1-2023", "通用要求：以适当速率和精度同步", "④数据底座 + ①OGG", "基准"],
    ["GB/T 45626-2025", "装备数字孪生：几何/仿真/诊断/预测/验证", "①几何 ③仿真 ②Agent ⑤验证", "强（需补仿真/验证）"],
    ["GB/T 45873-2025", "车间/工厂孪生：生产系统仿真", "③工厂级仿真引擎（新建+存量）", "需补"],
    ["GB/T 43441.2-2026", "数字实体 · 模型精度", "①OGG 几何精度", "强"]
  ];
  const body = rows.map((r) => [
    cell(r[0], true), cell(r[1]), cell(r[2]),
    { text: r[3], options: { fontFace: FACE, fontSize: 11, color: r[3].indexOf("需补") >= 0 ? AMBER : GREEN, bold: true, valign: "middle", align: "center" } }
  ]);
  s.addTable([head].concat(body), {
    x: 0.55, y: 1.8, w: 12.23, colW: [3.1, 4.6, 3.0, 1.53], rowH: [0.5, 0.85, 0.85, 0.85, 0.85],
    border: { type: "solid", color: BORDER, pt: 1 }, fill: { color: WHITE }, valign: "middle"
  });
  s.addText("组件本身不等于合规——须把五元构件纳入按国标设计的完整系统，再通过 CESI 测评证明符合性。", { x: 0.55, y: 6.55, w: 12.23, h: 0.4, fontFace: FACE, fontSize: 11, italic: true, color: GRAYTX, margin: 0 });
})();

// =================================================================
// P9 目标场景（核心）
// =================================================================
(() => {
  const s = lightSlide("核心 · 场景", "目标场景：装备—车间—工厂全覆盖");
  const cards = [
    ["装备级孪生", "几何保真 + 多物理场 CAE 仿真，支撑虚拟调试、预测性维护。", BLUE],
    ["车间级孪生", "产线/工位实时映射，状态监控与运行优化。", SKY],
    ["工厂级仿真", "生产系统离散事件仿真，覆盖“新建验证 + 存量优化”双场景。", GREEN]
  ];
  let x = 0.55;
  cards.forEach((c, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.85, w: 3.94, h: 4.6, fill: { color: WHITE }, line: { color: c[2], width: 1.5 }, rectRadius: 0.08, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.85, w: 3.94, h: 0.7, fill: { color: c[2] } });
    s.addText(c[0], { x: x + 0.25, y: 1.85, w: 3.5, h: 0.7, valign: "middle", fontFace: FACE, fontSize: 16, bold: true, color: WHITE, margin: 0 });
    s.addText(c[1], { x: x + 0.3, y: 2.8, w: 3.34, h: 1.5, fontFace: FACE, fontSize: 12.5, color: SLATE, lineSpacingMultiple: 1.25, margin: 0 });
    if (i === 2) {
      let py = 4.35;
      s.addText("两类场景并重：", { x: x + 0.3, y: py, w: 3.34, h: 0.35, fontFace: FACE, fontSize: 12, bold: true, color: INK, margin: 0 });
      py += 0.42;
      drawPill(s, x + 0.3, py, "新建工厂虚拟验证", SOFTBLUE, GREEN, 0.46);
      drawPill(s, x + 0.3, py + 0.58, "存量产能优化", SOFTBLUE, GREEN, 0.46);
    } else if (i === 0) {
      drawPill(s, x + 0.3, 4.5, "虚拟调试", SOFTBLUE, BLUE, 0.44);
      drawPill(s, x + 0.3, 5.05, "预测性维护", SOFTBLUE, BLUE, 0.44);
    } else {
      drawPill(s, x + 0.3, 4.5, "状态监控", SOFTBLUE, SKY, 0.44);
      drawPill(s, x + 0.3, 5.05, "运行优化", SOFTBLUE, SKY, 0.44);
    }
    x += 4.13;
  });
})();

// =================================================================
// P10 量化验收基线（核心）
// =================================================================
(() => {
  const s = lightSlide("核心 · 基线", "量化验收基线（签约约束条款）");
  const stats = [
    ["≤ 0.5", "mm", "几何模型精度", "GB/T 43441.2 / OGG", BLUE],
    ["≤ ±0.5", "%", "仿真误差率", "装备 CAE + 工厂级", GREEN],
    ["≤ 200", "ms", "虚实同步延迟", "GB/T 43441.1 / 数据底座", AMBER]
  ];
  let x = 0.55;
  stats.forEach((st) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.95, w: 3.94, h: 2.7, fill: { color: WHITE }, line: { color: BORDER, width: 1 }, rectRadius: 0.08, shadow: makeShadow() });
    s.addText([
      { text: st[0], options: { fontSize: 46, bold: true, color: st[4] } },
      { text: " " + st[1], options: { fontSize: 18, bold: true, color: st[4] } }
    ], { x: x + 0.2, y: 2.25, w: 3.54, h: 1.1, align: "center", fontFace: FACE, margin: 0 });
    s.addText(st[2], { x: x + 0.2, y: 3.45, w: 3.54, h: 0.4, align: "center", fontFace: FACE, fontSize: 14, bold: true, color: INK, margin: 0 });
    s.addText(st[3], { x: x + 0.2, y: 3.9, w: 3.54, h: 0.5, align: "center", fontFace: FACE, fontSize: 11, color: GRAYTX, margin: 0 });
    x += 4.13;
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y: 4.95, w: 12.23, h: 1.6, fill: { color: SOFTBLUE }, line: { color: "BFDBFE", width: 1 }, rectRadius: 0.08 });
  s.addText([
    { text: "其余指标：", options: { bold: true, color: BLUE } },
    { text: "工厂级仿真验收阈值（产能/物流节拍预测误差 ≤X% · 排程达成 ≥Y%）、预测/操控精度、决策一致性 —— 由目标测评等级锁定，P0 末回填。", options: { color: SLATE, breakLine: true } },
    { text: "注：上述 ≤0.5mm / ±0.5% / 200ms 为行业常用标尺，非国标强制数值，最终以官方标准与目标 CESI 测评等级为准。", options: { color: AMBER, fontSize: 11 } }
  ], { x: 0.9, y: 5.1, w: 11.5, h: 1.35, fontFace: FACE, fontSize: 12.5, valign: "middle", lineSpacingMultiple: 1.25, margin: 0 });
})();

// =================================================================
// P11 分期建设路线
// =================================================================
(() => {
  const s = lightSlide("实施路径", "分期建设路线 · P0–P3（18 个月）");
  const phases = [
    ["P0", "立项与标准基线", "2026 Q3 · 1.5月", "需求规格 · 国标差距 · 选型清单", BLUE],
    ["P1", "几何 + 数据底座", "2026 Q4–27 Q2 · 6月", "OGG 建模 + IoT 同步 · M1", SKY],
    ["P2", "仿真 + 智能层", "2027 Q3–Q4 · 6月", "CAE/工厂仿真 + Agent · M2", GREEN],
    ["P3", "集成验证 + 测评", "2028 Q1 · 4.5月", "全条款自检 · CESI 认证", AMBER]
  ];
  let x = 0.55;
  const bw = 2.9, gap = 0.18;
  phases.forEach((p, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.1, w: bw, h: 3.4, fill: { color: WHITE }, line: { color: p[4], width: 1.5 }, rectRadius: 0.08, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 2.1, w: bw, h: 0.85, fill: { color: p[4] } });
    s.addText(p[0], { x: x + 0.2, y: 2.1, w: 1.2, h: 0.85, valign: "middle", fontFace: FACE, fontSize: 24, bold: true, color: WHITE, margin: 0 });
    s.addText(p[1], { x: x + 1.35, y: 2.1, w: bw - 1.5, h: 0.85, valign: "middle", fontFace: FACE, fontSize: 12.5, bold: true, color: WHITE, margin: 0 });
    s.addText(p[2], { x: x + 0.25, y: 3.05, w: bw - 0.5, h: 0.45, fontFace: FACE, fontSize: 12, bold: true, color: p[4], margin: 0 });
    s.addText(p[3], { x: x + 0.25, y: 3.6, w: bw - 0.5, h: 1.6, fontFace: FACE, fontSize: 12, color: SLATE, lineSpacingMultiple: 1.25, margin: 0 });
    if (i < 3) {
      s.addShape(pres.shapes.OVAL, { x: x + bw + gap / 2 - 0.22, y: 3.55, w: 0.44, h: 0.44, fill: { color: DGRAY } });
      s.addText("›", { x: x + bw + gap / 2 - 0.22, y: 3.5, w: 0.44, h: 0.44, align: "center", valign: "middle", fontFace: FACE, fontSize: 18, bold: true, color: WHITE, margin: 0 });
    }
    x += bw + gap;
  });
  s.addText("关键前提：仿真保真（CAE / 工厂级）、同步保真（IoT）、验证保真（建模验证流程）三块必须按计划补齐，单靠 OGG+Agent 达不到“高保真”。", { x: 0.55, y: 5.75, w: 12.23, h: 0.9, fontFace: FACE, fontSize: 12.5, color: SLATE, valign: "middle", lineSpacingMultiple: 1.2, margin: 0 });
})();

// =================================================================
// P12 POC 验证安排
// =================================================================
(() => {
  const s = lightSlide("先试后定", "POC 验证安排（仿真引擎选型）");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y: 1.8, w: 4.6, h: 4.7, fill: { color: WHITE }, line: { color: BORDER, width: 1 }, rectRadius: 0.08, shadow: makeShadow() });
  s.addText("验证目标", { x: 0.85, y: 2.0, w: 4, h: 0.4, fontFace: FACE, fontSize: 15, bold: true, color: BLUE, margin: 0 });
  s.addText([
    { text: "范围：Plant Simulation vs AnyLogic 贴合双场景", options: { bullet: true, breakLine: true } },
    { text: "周期：2–3 周（资源足可压至 2 周）", options: { bullet: true, breakLine: true } },
    { text: "投入：1 仿真工程师 + 0.5 数据工程师", options: { bullet: true, breakLine: true } },
    { text: "取“代表性切片”：新建厂代表产线、存量瓶颈工段", options: { bullet: true, breakLine: true } },
    { text: "只验能力贴合度，不验精度", options: { bullet: true } }
  ], { x: 0.85, y: 2.5, w: 4.05, h: 3.8, fontFace: FACE, fontSize: 12.5, color: SLATE, lineSpacingMultiple: 1.3, margin: 0 });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.4, y: 1.8, w: 7.38, h: 4.7, fill: { color: WHITE }, line: { color: BORDER, width: 1 }, rectRadius: 0.08, shadow: makeShadow() });
  s.addText("决策维度（加权 · 7 维）", { x: 5.7, y: 2.0, w: 6.8, h: 0.4, fontFace: FACE, fontSize: 15, bold: true, color: BLUE, margin: 0 });
  const dims = [
    ["离散事件成熟度", "20%"], ["多方法适配（DES/ABM/SD）", "15%"], ["MES/ERP 接口能力", "15%"],
    ["二次开发开放性", "15%"], ["3D 可视化", "10%"], ["建模效率", "10%"], ["成本", "10%"]
  ];
  let dy = 2.55;
  dims.forEach((d) => {
    s.addText(d[0], { x: 5.7, y: dy, w: 5.8, h: 0.42, fontFace: FACE, fontSize: 12.5, color: INK, valign: "middle", margin: 0 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 11.7, y: dy + 0.04, w: 0.85, h: 0.36, fill: { color: SOFTBLUE } });
    s.addText(d[1], { x: 11.7, y: dy + 0.04, w: 0.85, h: 0.36, align: "center", valign: "middle", fontFace: FACE, fontSize: 12, bold: true, color: BLUE, margin: 0 });
    s.addShape(pres.shapes.LINE, { x: 5.7, y: dy + 0.46, w: 6.85, h: 0, line: { color: BORDER, width: 0.75 } });
    dy += 0.54;
  });
  s.addText("输出：选型建议回填《P0 基线》第五章；国产替代路线（SimPy/开源自研）作为闭环后个性化候选，非 P0 必做。", { x: 5.7, y: 6.0, w: 6.85, h: 0.4, fontFace: FACE, fontSize: 10.5, italic: true, color: GRAYTX, margin: 0 });
})();

// =================================================================
// P13 风险与应对
// =================================================================
(() => {
  const s = lightSlide("风险管控", "主要风险与应对");
  const risks = [
    ["组件 ≠ 合规", "OGG+Agent 是构件非系统；须纳入完整系统设计 + CESI 测评认证。"],
    ["工厂级数据粒度", "存量场景强依赖 MES/ERP/SCADA 接口与历史数据，P1 即规划采集链路。"],
    ["保真指标争议", "P0 将量化阈值写入合同验收基线，避免后期验收扯皮。"],
    ["AI / 仿真锁定", "Agent 用通用 MAS 接口解耦、仿真引擎按指标选型，规避单一厂商锁定。"]
  ];
  let idx = 0;
  for (let r = 0; r < 2; r++) {
    for (let c = 0; c < 2; c++) {
      const x = 0.55 + c * 6.13;
      const y = 1.85 + r * 2.35;
      const rk = risks[idx++];
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.94, h: 2.15, fill: { color: WHITE }, line: { color: BORDER, width: 1 }, rectRadius: 0.08, shadow: makeShadow() });
      s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.3, w: 0.6, h: 0.6, fill: { color: AMBER } });
      s.addText("!", { x: x + 0.3, y: y + 0.3, w: 0.6, h: 0.6, align: "center", valign: "middle", fontFace: FACE, fontSize: 22, bold: true, color: WHITE, margin: 0 });
      s.addText(rk[0], { x: x + 1.05, y: y + 0.32, w: 4.6, h: 0.6, valign: "middle", fontFace: FACE, fontSize: 15, bold: true, color: INK, margin: 0 });
      s.addText(rk[1], { x: x + 0.35, y: y + 1.05, w: 5.3, h: 1.0, fontFace: FACE, fontSize: 12, color: SLATE, lineSpacingMultiple: 1.2, margin: 0 });
    }
  }
})();

// =================================================================
// P14 待确认项与决策（核心）
// =================================================================
(() => {
  const s = lightSlide("核心 · 决策", "待确认项（6 项）与决策点（3 个）");
  const head = [headOpt("项"), headOpt("默认设定"), headOpt("确认方"), headOpt("不确认的影响")];
  const rows = [
    ["目标场景", "装备+车间+工厂级双场景", "业务方", "建模与数据范围漂移"],
    ["保真等级", "二级 / 三级", "业务方+标准", "指标与预算无法锁定"],
    ["部署形态", "私有化 + 边缘", "业务方+安全", "安全架构与选型返工"],
    ["工厂级验收阈值", "误差 ≤X% · 达成 ≥Y%", "业务方+仿真", "合同验收条款缺失"],
    ["预算口径", "系统建设 + 测评", "决策人", "立项金额未定"],
    ["POC 范围", "2–3 周 Plant vs AnyLogic", "技术", "仿真引擎选型不确定"]
  ];
  const body = rows.map((r) => [cell(r[0], true), cell(r[1]), cell(r[2]), cell(r[3])]);
  s.addTable([head].concat(body), {
    x: 0.55, y: 1.75, w: 12.23, colW: [2.6, 4.2, 2.4, 3.03], rowH: [0.45, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
    border: { type: "solid", color: BORDER, pt: 1 }, fill: { color: WHITE }, valign: "middle", fontSize: 11
  });
  const dec = [
    ["决策点 A", "是否通过《P0 需求规格与标准符合性基线》？（通过 → 签署生效）"],
    ["决策点 B", "是否批准启动 P1（几何内核 + 实时数据底座，2026 Q4 起）？"],
    ["决策点 C", "预算口径是否纳入立项金额？（授权 P0 末完成详细预算分解）"]
  ];
  let x = 0.55;
  dec.forEach((d) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.55, w: 3.94, h: 1.25, fill: { color: INK }, rectRadius: 0.08 });
    s.addText(d[0], { x: x + 0.25, y: 5.68, w: 3.5, h: 0.4, fontFace: FACE, fontSize: 13, bold: true, color: SKY, margin: 0 });
    s.addText(d[1], { x: x + 0.25, y: 6.08, w: 3.5, h: 0.65, fontFace: FACE, fontSize: 10.5, color: "CBD5E1", lineSpacingMultiple: 1.15, margin: 0 });
    x += 4.13;
  });
})();

// =================================================================
// P15 签署与下一步（深色）
// =================================================================
(() => {
  const c = pres.addSlide();
  c.background = { color: INK };
  c.addShape(pres.shapes.RECTANGLE, { x: 0.55, y: 0.6, w: 0.14, h: 0.9, fill: { color: SKY } });
  c.addText("签署与下一步", { x: 0.85, y: 0.6, w: 11, h: 0.9, valign: "middle", fontFace: FACE, fontSize: 30, bold: true, color: WHITE, margin: 0 });
  c.addText("基线签署后即触发 P1（几何内核 + 实时数据底座）。", { x: 0.85, y: 1.55, w: 11, h: 0.4, fontFace: FACE, fontSize: 13, color: "94A3B8", margin: 0 });
  const roles = ["业务方负责人", "技术负责人 / 架构师", "标准 / 测评负责人", "项目决策人"];
  let y = 2.25;
  roles.forEach((r) => {
    c.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y, w: 12.23, h: 0.95, fill: { color: "1E293B" }, line: { color: "334155", width: 1 }, rectRadius: 0.06 });
    c.addText(r, { x: 0.95, y, w: 4, h: 0.95, valign: "middle", fontFace: FACE, fontSize: 15, bold: true, color: WHITE, margin: 0 });
    c.addText("签字：________________", { x: 5.2, y, w: 4, h: 0.95, valign: "middle", fontFace: FACE, fontSize: 13, color: "CBD5E1", margin: 0 });
    c.addText("日期：________________", { x: 9.4, y, w: 3.2, h: 0.95, valign: "middle", fontFace: FACE, fontSize: 13, color: "CBD5E1", margin: 0 });
    y += 1.08;
  });
  c.addText("智能数字孪生系统建设项目 · P0 立项评审 · 2026-08-07", { x: 0.55, y: 6.95, w: 12, h: 0.4, fontFace: FACE, fontSize: 10, color: "64748B", margin: 0 });
})();

pres.writeFile({ fileName: "D:/agent_digtaltwin/P0评审汇报.pptx" }).then((fn) => {
  console.log("SAVED:", fn);
}).catch((e) => { console.error("ERR", e); });
