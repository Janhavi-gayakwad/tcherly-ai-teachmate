// Builds the pdfmake document for a TeachMate lesson report (A4, vector text, Roboto).
// A pure function of the report JSON, so it can also be rendered and checked outside the browser.

const C = {
  ink: "#2d2a49",
  accent: "#5b54a6",
  soft: "#f4f3fa",
  line: "#e3e1ef",
  text: "#2b2b35",
  muted: "#6b6b78",
  white: "#ffffff",
  difficult: "#ff7785",
  easy: "#ffbc55",
  boring: "#9f8cff",
  engaging: "#69b9a6",
  strategyFill: "#f3faf7",
};

const PAGE_WIDTH = 595.28; // A4 in points
const MARGIN_X = 40;
const CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN_X;

const KIND_COLORS = {
  "most difficult": C.difficult,
  easiest: C.easy,
  "most boring": C.boring,
  "most engaging": C.engaging,
};

const STATES = [
  ["difficult", "reported Difficult"],
  ["easy", "reported Easy"],
  ["boring", "reported Boring"],
  ["engaging", "reported Engaging"],
];

const INLINE = /(\*\*[^*]+\*\*|\[E\d+(?:\s*,\s*E\d+)*\]|\*[^*\s][^*]*\*|`[^`]+`)/g;

// Characters Roboto may not have; replace them so nothing prints as an empty box.
function clean(text) {
  return String(text || "")
    .replace(/→/g, "->")
    .replace(/[✓✔]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

// Markdown-ish model text -> pdfmake inline fragments; [E3] becomes a small superscript reference.
function inline(text, base = {}) {
  const parts = clean(text).split(INLINE).filter((p) => p !== "");
  const out = [];
  parts.forEach((part) => {
    if (/^\[E\d/.test(part)) {
      const prev = out[out.length - 1];
      if (prev && typeof prev.text === "string") prev.text = prev.text.replace(/\s+$/, "");
      out.push({ text: part.slice(1, -1).replace(/\s*,\s*/g, ","), sup: true, fontSize: 6, color: C.accent });
    } else if (part.startsWith("**") && part.endsWith("**")) {
      out.push({ text: part.slice(2, -2), bold: true, ...base });
    } else if (part.startsWith("`") && part.endsWith("`")) {
      out.push({ text: part.slice(1, -1), ...base });
    } else if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      out.push({ text: part.slice(1, -1), italics: true, ...base });
    } else {
      out.push({ text: part, ...base });
    }
  });
  return out;
}

const para = (text, style = {}) => ({ text: inline(text), ...style });

function sectionTitle(title) {
  return {
    stack: [
      { text: title, fontSize: 12.5, bold: true, color: C.ink },
      { canvas: [{ type: "line", x1: 0, y1: 0, x2: CONTENT_WIDTH, y2: 0, lineWidth: 0.7, lineColor: C.line }], margin: [0, 4, 0, 0] },
    ],
    margin: [0, 18, 0, 8],
  };
}

// A section title glued to its first block, so a title never ends up alone at the bottom of a page.
function section(title, first, ...rest) {
  return [{ stack: [sectionTitle(title), first], unbreakable: true }, ...rest];
}

function label(text, color = C.muted) {
  return { text: text.toUpperCase(), fontSize: 6.8, bold: true, color, characterSpacing: 0.6, margin: [0, 6, 0, 1] };
}

const noLines = {
  hLineWidth: () => 0,
  vLineWidth: () => 0,
  paddingLeft: () => 0,
  paddingRight: () => 0,
  paddingTop: () => 0,
  paddingBottom: () => 0,
};

// One-cell box with a coloured bar on the left.
function box(stack, { fill = C.soft, bar = C.accent, border = null, padding = [12, 9, 12, 9] } = {}) {
  return {
    table: { widths: ["*"], body: [[{ stack, fillColor: fill }]] },
    layout: {
      hLineWidth: () => (border ? 0.7 : 0),
      vLineWidth: (i) => (i === 0 ? 3 : border ? 0.7 : 0),
      hLineColor: () => border || C.line,
      vLineColor: (i) => (i === 0 ? bar : border || C.line),
      paddingLeft: () => padding[0],
      paddingTop: () => padding[1],
      paddingRight: () => padding[2],
      paddingBottom: () => padding[3],
    },
  };
}

function headerBand(stats, createdAt) {
  const meta = [stats.course, `${stats.minutes} min video`, `Generated ${createdAt}`].filter(Boolean).join("   ·   ");
  return {
    table: {
      widths: [PAGE_WIDTH],
      body: [
        [
          {
            fillColor: C.ink,
            stack: [
              { text: "TEACHMATE  ·  LESSON REPORT", fontSize: 8, bold: true, color: "#b9b4e8", characterSpacing: 1.2 },
              { text: stats.lesson || "Lesson", fontSize: 24, bold: true, color: C.white, margin: [0, 6, 0, 4], lineHeight: 1.05 },
              { text: meta, fontSize: 9, color: "#d6d3f0" },
            ],
          },
        ],
      ],
    },
    layout: {
      ...noLines,
      paddingLeft: () => MARGIN_X,
      paddingRight: () => MARGIN_X,
      paddingTop: () => 34,
      paddingBottom: () => 24,
    },
    margin: [-MARGIN_X, -40, 0, 18],
  };
}

function statTiles(stats) {
  const tiles = [
    { value: stats.responders, label: `of ${stats.watched} students gave feedback (${stats.participation_pct}%)`, color: C.accent },
    ...STATES.map(([key, text]) => ({ value: (stats.states || {})[key], label: text, color: C[key] })),
    { value: stats.bookmarks, label: "saved reflections", color: C.ink },
  ];
  return {
    table: {
      widths: tiles.map(() => "*"),
      body: [
        tiles.map((t) => ({
          fillColor: C.soft,
          stack: [
            { canvas: [{ type: "rect", x: 0, y: 0, w: 22, h: 3, r: 1.5, color: t.color }] },
            { text: String(t.value == null ? "-" : t.value), fontSize: 19, bold: true, color: C.ink, margin: [0, 6, 0, 1] },
            { text: t.label, fontSize: 7.2, color: C.muted, lineHeight: 1.15 },
          ],
        })),
      ],
    },
    layout: {
      hLineWidth: () => 0,
      vLineWidth: (i, node) => (i === 0 || i === node.table.widths.length ? 0 : 5),
      vLineColor: () => C.white,
      paddingLeft: () => 8,
      paddingRight: () => 6,
      paddingTop: () => 9,
      paddingBottom: () => 9,
    },
    margin: [0, 0, 0, 14],
  };
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// Minute-by-minute line chart (same values as the dashboard), with the key moments shaded.
function chartSvg(series, moments, minutes) {
  const W = CONTENT_WIDTH;
  const H = 170;
  const pad = { left: 26, right: 6, top: 16, bottom: 20 };
  const pw = W - pad.left - pad.right;
  const ph = H - pad.top - pad.bottom;
  const n = Math.max(minutes || series.length, 1);
  const peak = Math.max(4, ...series.map((p) => Math.max(Math.abs(p[1]), Math.abs(p[2]))));
  const yMax = Math.ceil(peak / 5) * 5;
  const x = (minute) => pad.left + (minute / n) * pw; // minute boundary
  const xm = (minute) => pad.left + ((minute - 0.5) / n) * pw; // middle of a minute bucket
  const y = (v) => pad.top + ((yMax - v) / (2 * yMax)) * ph;

  const parts = [];
  (moments || []).forEach((m) => {
    const x0 = x(m.start_min);
    const x1 = x(m.end_min);
    parts.push(`<rect x="${x0.toFixed(1)}" y="${pad.top}" width="${(x1 - x0).toFixed(1)}" height="${ph}" fill="${C.accent}" fill-opacity="0.09"/>`);
    parts.push(`<text x="${((x0 + x1) / 2).toFixed(1)}" y="${pad.top - 5}" font-size="6.5" fill="${C.accent}" text-anchor="middle">${esc(m.window)}</text>`);
  });
  [-yMax, -yMax / 2, 0, yMax / 2, yMax].forEach((v) => {
    const yy = y(v).toFixed(1);
    const isZero = v === 0;
    parts.push(`<line x1="${pad.left}" y1="${yy}" x2="${W - pad.right}" y2="${yy}" stroke="${isZero ? "#9a97b5" : C.line}" stroke-width="${isZero ? 0.8 : 0.5}"/>`);
    parts.push(`<text x="${pad.left - 5}" y="${(+yy + 2.2).toFixed(1)}" font-size="6.5" fill="${C.muted}" text-anchor="end">${v > 0 ? "+" : ""}${v}</text>`);
  });
  const step = n > 20 ? 5 : n > 10 ? 2 : 1;
  for (let t = 0; t <= n; t += step) {
    parts.push(`<text x="${x(t).toFixed(1)}" y="${H - pad.bottom + 11}" font-size="6.5" fill="${C.muted}" text-anchor="middle">${t}</text>`);
  }
  if (n % step) parts.push(`<text x="${x(n).toFixed(1)}" y="${H - pad.bottom + 11}" font-size="6.5" fill="${C.muted}" text-anchor="middle">${n}</text>`);

  [
    [1, C.difficult],
    [2, C.engaging],
  ].forEach(([idx, color]) => {
    const pts = series.map((p) => `${xm(p[0]).toFixed(1)},${y(p[idx]).toFixed(1)}`).join(" ");
    parts.push(`<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>`);
    series.forEach((p) => parts.push(`<circle cx="${xm(p[0]).toFixed(1)}" cy="${y(p[idx]).toFixed(1)}" r="1.5" fill="${color}"/>`));
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${parts.join("")}</svg>`;
}

function legendItem(color, text, shaded = false) {
  return {
    width: "auto",
    columns: [
      {
        width: 14,
        canvas: shaded
          ? [{ type: "rect", x: 0, y: 1, w: 12, h: 7, color: C.accent, fillOpacity: 0.12 }]
          : [{ type: "line", x1: 0, y1: 4.5, x2: 12, y2: 4.5, lineWidth: 1.8, lineColor: color }],
      },
      { width: "auto", text, fontSize: 7.5, color: C.muted },
    ],
    columnGap: 4,
  };
}

function chartBlock(report) {
  const series = (report.stats && report.stats.series) || [];
  if (series.length < 2) return [];
  return section("Minute by minute", { svg: chartSvg(series, report.moments, report.stats.minutes), width: CONTENT_WIDTH },
    {
      columns: [
        legendItem(C.difficult, "Net difficulty (difficult - easy)"),
        legendItem(C.engaging, "Net engagement (engaging - boring)"),
        legendItem(null, "Key moments, described below", true),
      ],
      columnGap: 16,
      margin: [26, 4, 0, 2],
    },
    { text: "Horizontal axis: video minute. Above zero, more students found that minute difficult (red) or engaging (green). Same values as the dashboard line chart.", fontSize: 7.5, color: C.muted, margin: [26, 2, 0, 0] }
  );
}

function bullets(items, markerColor) {
  return { ul: items.map((t) => para(t, { margin: [0, 0, 0, 4] })), markerColor, margin: [4, 0, 0, 0] };
}

function momentCard(moment, meta) {
  const kinds = (meta && meta.kinds) || [];
  const tags = kinds.map((k, i) => ({ text: (i ? "   " : "") + k, color: KIND_COLORS[k] || C.muted, bold: true }));
  const windowText = clean(moment.window);
  const pillWidth = windowText.length * 4.3 + 14; // Roboto Medium 7.5pt is ~4.3pt per character
  const stack = [
    {
      columns: [
        {
          width: pillWidth,
          stack: [
            { canvas: [{ type: "rect", x: 0, y: 0, w: pillWidth, h: 14, r: 7, color: C.ink }] },
            { text: windowText, color: C.white, bold: true, fontSize: 7.5, alignment: "center", relativePosition: { x: 0, y: -11.5 } },
          ],
        },
        { width: "*", text: clean(moment.title), bold: true, fontSize: 10.5, color: C.ink, margin: [8, 0, 0, 0] },
      ],
    },
  ];
  if (tags.length) stack.push({ text: tags, fontSize: 6.8, margin: [0, 5, 0, 0], characterSpacing: 0.3 });
  stack.push(para(moment.what_happened, { margin: [0, 6, 0, 0] }));
  if (moment.students_said) {
    stack.push(label("What students said"));
    stack.push(para(moment.students_said, { color: "#444444" }));
  }
  return { ...box(stack, { fill: C.white, bar: C.accent, border: C.line }), margin: [0, 0, 0, 8], unbreakable: true };
}

function strategyCard(strategy) {
  return {
    ...box(
      [
        para(strategy.option, { bold: true, color: C.ink, fontSize: 10 }),
        ...(strategy.based_on ? [label("Based on"), para(strategy.based_on)] : []),
        label("Responds to"),
        para(strategy.addresses),
        label("How to tell if it helped"),
        para(strategy.check),
      ],
      { fill: C.strategyFill, bar: C.engaging }
    ),
    margin: [0, 0, 0, 8],
    unbreakable: true,
  };
}

function evidenceBlock(report) {
  const g = report.grounding || {};
  const ids = Object.keys(report.citations || {}).sort((a, b) => Number(a.slice(1)) - Number(b.slice(1)));
  const statement = g.grounded
    ? { text: `All ${g.checked_numbers} numbers in this report were checked against your class data.`, color: "#2e7d5b", bold: true }
    : { text: `${(g.unsupported || []).length + (g.unknown_ids || []).length} statement(s) couldn't be verified against the data. Please check them on the dashboard.`, color: "#b26a00", bold: true };
  return [
    ...section("Data behind this report", { text: [statement, { text: "  Each small reference (E3, E7…) in the text points to one of these facts, computed from the dashboard data.", color: C.muted }], fontSize: 8.5, margin: [0, 0, 0, 8] }),
    {
      table: {
        widths: [24, "*"],
        body: ids.map((id, i) => [
          { text: id, bold: true, color: C.accent, fillColor: i % 2 ? null : C.soft },
          { text: clean(report.citations[id]), color: "#444444", fillColor: i % 2 ? null : C.soft },
        ]),
      },
      layout: { ...noLines, paddingLeft: () => 5, paddingRight: () => 5, paddingTop: () => 3, paddingBottom: () => 3 },
      fontSize: 7.4,
    },
  ];
}

function formatDate(value) {
  return new Date(value).toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function buildReportDoc(report) {
  const s = report.sections || {};
  const stats = report.stats || {};
  const created = formatDate(report.created_at);
  const momentMeta = (report.moments || []).reduce((acc, m) => ({ ...acc, [m.window]: m }), {});

  const content = [
    headerBand(stats, created),
    statTiles(stats),
    box([para(s.headline, { fontSize: 11.5, bold: true, color: C.ink, lineHeight: 1.3 })], { padding: [14, 11, 14, 11] }),
    ...section("At a glance", bullets(s.at_a_glance || [], C.accent)),
    ...chartBlock(report),
    ...section("Key moments", ...(s.key_moments || []).map((m) => momentCard(m, momentMeta[m.window]))),
    ...section("What worked", bullets(s.what_worked || [], C.engaging)),
    ...section("Your reflections so far", bullets(s.reflections || [], C.ink)),
    ...section("Questions to explore", { ol: (s.open_questions || []).map((t) => para(t, { margin: [0, 0, 0, 5] })), markerColor: C.accent, margin: [4, 0, 0, 0] }),
    ...section(
      "Options to consider",
      { text: "Ideas you can adopt, adapt or reject. You know your class best.", fontSize: 8.5, color: C.muted, italics: true, margin: [0, 0, 0, 8] },
      ...(s.strategies || []).map(strategyCard)
    ),
    ...evidenceBlock(report),
  ];

  return {
    pageSize: "A4",
    pageMargins: [MARGIN_X, 40, MARGIN_X, 46],
    info: { title: `TeachMate report - ${stats.lesson || "lesson"}`, author: "TeachMate (Tcherly)", subject: "Lesson report", creator: "TeachMate" },
    defaultStyle: { font: "Roboto", fontSize: 9.5, lineHeight: 1.28, color: C.text },
    content,
    header: (page) =>
      page === 1
        ? null
        : {
            columns: [
              { text: `TeachMate lesson report  ·  ${stats.lesson || ""}`, color: C.muted },
              { text: created, alignment: "right", color: C.muted },
            ],
            fontSize: 7.5,
            margin: [MARGIN_X, 18, MARGIN_X, 0],
          },
    footer: (page, pages) => ({
      columns: [
        { text: `Generated by TeachMate (Google Gemini, ${report.model || "model"}). Based on voluntary student feedback; interpretations and decisions are yours.`, color: C.muted, width: "*" },
        { text: `${page} / ${pages}`, alignment: "right", color: C.muted, width: 40 },
      ],
      fontSize: 7,
      margin: [MARGIN_X, 16, MARGIN_X, 0],
    }),
  };
}

function reportFileName(report) {
  const lesson = String((report.stats && report.stats.lesson) || "lesson").replace(/[\\/:*?"<>|]+/g, "").trim();
  const date = new Date(report.created_at).toISOString().slice(0, 10);
  return `TeachMate report - ${lesson} - ${date}.pdf`;
}

module.exports = { buildReportDoc, reportFileName };
