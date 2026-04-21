#!/usr/bin/env node
/**
 * AI Document Intelligence — 4-Minute Pitch Deck Generator
 * 
 * Slide plan (3 min talk + 1 min video):
 *   1. Title — hook
 *   2. The Problem — current pain points (from stakeholder slides)
 *   3. Our Solution — platform overview
 *   4. How It Works — 6-step digitized workflow diagram
 *   5. 8 Capabilities — grid mapping to desired outcomes
 *   6. Live Results — metrics + demo video placeholder
 *   7. Call to Action / Q&A
 *
 * Color palette: "Midnight Executive" — navy + ice blue + white
 *   Primary:   1B2A4A (deep navy)
 *   Secondary: 2B4C7E (medium navy)  
 *   Accent:    0891B2 (teal/cyan)
 *   Light:     E8F4F8 (ice blue)
 *   Text:      1E293B (near-black)
 *   Muted:     64748B (slate gray)
 *   White:     FFFFFF
 */

const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

// ─── Palette ────────────────────────────────────────────────
const C = {
  navy: "1B2A4A",
  medNavy: "2B4C7E",
  teal: "0891B2",
  ice: "E8F4F8",
  text: "1E293B",
  muted: "64748B",
  white: "FFFFFF",
  offWhite: "F8FAFC",
  green: "059669",
  orange: "D97706",
  red: "DC2626",
  lightTeal: "CCFBF1",
};

// ─── Helpers ────────────────────────────────────────────────
const mkShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.12 });
const mkSoftShadow = () => ({ type: "outer", color: "000000", blur: 4, offset: 1, angle: 135, opacity: 0.08 });

function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

async function svgToPng(svg) {
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

async function renderIcon(svgContent, color, size = 200) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="${color}">${svgContent}</svg>`;
  return svgToPng(svg);
}

// Simple icon paths (inline SVG)
const ICONS = {
  scan: '<path d="M3 9V5a2 2 0 012-2h4M15 3h4a2 2 0 012 2v4M21 15v4a2 2 0 01-2 2h-4M9 21H5a2 2 0 01-2-2v-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  brain: '<path d="M12 2a7 7 0 017 7c0 2.5-1.3 4.7-3.3 6L14 20H10l-1.7-5C6.3 13.7 5 11.5 5 9a7 7 0 017-7z" fill="none" stroke="currentColor" stroke-width="2"/>',
  route: '<path d="M9 18l6-12M4 6h4M16 18h4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  summary: '<path d="M4 4h16v16H4zM8 8h8M8 12h6M8 16h4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  collab: '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" fill="none" stroke="currentColor" stroke-width="2"/>',
  track: '<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
  search: '<circle cx="11" cy="11" r="8" fill="none" stroke="currentColor" stroke-width="2"/><path d="M21 21l-4.35-4.35" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="none" stroke="currentColor" stroke-width="2"/>',
  clock: '<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 6v6l4 2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  check: '<path d="M22 11.08V12a10 10 0 11-5.93-9.14" fill="none" stroke="currentColor" stroke-width="2"/><path d="M22 4L12 14.01l-3-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  alert: '<path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  doc: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M14 2v6h6M8 13h8M8 17h8M8 9h2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  play: '<polygon points="5,3 19,12 5,21" fill="currentColor"/>',
};

async function makeIconPng(name, color) {
  const svgPath = ICONS[name];
  if (!svgPath) return null;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 24 24" style="color:${color}">${svgPath.replace(/currentColor/g, color)}</svg>`;
  return svgToPng(svg);
}

// ─── SVG Diagram Generators ─────────────────────────────────

async function makeWorkflowDiagram() {
  const W = 880, H = 320;
  const steps = [
    { label: "Scan", sub: "Camera", color: "#0891B2" },
    { label: "OCR", sub: "AI Extract", color: "#0891B2" },
    { label: "Classify", sub: "AI Detect", color: "#0891B2" },
    { label: "Route", sub: "Auto-assign", color: "#059669" },
    { label: "Review", sub: "Multi-dept", color: "#059669" },
    { label: "Complete", sub: "Notify", color: "#059669" },
  ];
  const boxW = 110, boxH = 70, gap = 25;
  const totalW = steps.length * boxW + (steps.length - 1) * gap;
  const startX = (W - totalW) / 2;
  const startY = (H - boxH) / 2 - 20;

  let boxes = "";
  steps.forEach((s, i) => {
    const x = startX + i * (boxW + gap);
    const y = startY;
    boxes += `<rect x="${x}" y="${y}" width="${boxW}" height="${boxH}" rx="8" fill="${s.color}" opacity="0.12" stroke="${s.color}" stroke-width="1.5"/>`;
    boxes += `<text x="${x + boxW / 2}" y="${y + 28}" text-anchor="middle" font-size="14" font-weight="bold" fill="${s.color}" font-family="Arial, sans-serif">${esc(s.label)}</text>`;
    boxes += `<text x="${x + boxW / 2}" y="${y + 48}" text-anchor="middle" font-size="11" fill="#64748B" font-family="Arial, sans-serif">${esc(s.sub)}</text>`;
    // Number circle
    boxes += `<circle cx="${x + boxW / 2}" cy="${y - 18}" r="13" fill="${s.color}"/>`;
    boxes += `<text x="${x + boxW / 2}" y="${y - 13}" text-anchor="middle" font-size="12" font-weight="bold" fill="white" font-family="Arial, sans-serif">${i + 1}</text>`;
    // Arrow
    if (i < steps.length - 1) {
      const ax1 = x + boxW + 3, ax2 = x + boxW + gap - 3, ay = y + boxH / 2;
      boxes += `<line x1="${ax1}" y1="${ay}" x2="${ax2}" y2="${ay}" stroke="#94A3B8" stroke-width="2" marker-end="url(#ah)"/>`;
    }
  });

  // Labels row
  const labelY = startY + boxH + 30;
  boxes += `<rect x="${startX}" y="${labelY}" width="${3 * boxW + 2 * gap}" height="24" rx="4" fill="#0891B2" opacity="0.08"/>`;
  boxes += `<text x="${startX + (3 * boxW + 2 * gap) / 2}" y="${labelY + 16}" text-anchor="middle" font-size="11" fill="#0891B2" font-family="Arial, sans-serif" font-weight="bold">AI-Powered</text>`;
  const rx2 = startX + 3 * (boxW + gap);
  boxes += `<rect x="${rx2}" y="${labelY}" width="${3 * boxW + 2 * gap}" height="24" rx="4" fill="#059669" opacity="0.08"/>`;
  boxes += `<text x="${rx2 + (3 * boxW + 2 * gap) / 2}" y="${labelY + 16}" text-anchor="middle" font-size="11" fill="#059669" font-family="Arial, sans-serif" font-weight="bold">Workflow Engine</text>`;

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
    <defs><marker id="ah" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6Z" fill="#94A3B8"/></marker></defs>
    ${boxes}
  </svg>`;
  return svgToPng(svg);
}

async function makeProblemDiagram() {
  const W = 400, H = 300;
  const items = [
    { label: "5-7 days", sub: "avg. processing", y: 40 },
    { label: "High %", sub: "manual effort", y: 115 },
    { label: "Many depts", sub: "fragmented flow", y: 190 },
  ];
  let content = "";
  items.forEach(it => {
    content += `<rect x="30" y="${it.y}" width="${W - 60}" height="60" rx="8" fill="#FEF2F2" stroke="#DC2626" stroke-width="1" opacity="0.8"/>`;
    content += `<circle cx="65" cy="${it.y + 30}" r="16" fill="#DC2626" opacity="0.15"/>`;
    content += `<text x="65" y="${it.y + 35}" text-anchor="middle" font-size="14" fill="#DC2626" font-family="Arial">!</text>`;
    content += `<text x="95" y="${it.y + 24}" font-size="16" font-weight="bold" fill="#1E293B" font-family="Arial, sans-serif">${esc(it.label)}</text>`;
    content += `<text x="95" y="${it.y + 44}" font-size="12" fill="#64748B" font-family="Arial, sans-serif">${esc(it.sub)}</text>`;
  });
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${content}</svg>`;
  return svgToPng(svg);
}

// ─── Main ───────────────────────────────────────────────────

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Public Sector AI Team";
  pres.title = "AI Document Intelligence — Pitch Deck";

  // Pre-render diagrams
  const workflowDiag = await makeWorkflowDiagram();
  const problemDiag = await makeProblemDiagram();

  // ════════════════════════════════════════════════════════════
  // SLIDE 1 — TITLE
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };
    // Subtle decorative bar
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });
    // Title
    s.addText("AI-Assisted Document Intelligence", {
      x: 0.8, y: 1.2, w: 8.4, h: 1.2,
      fontSize: 36, fontFace: "Arial Black", color: C.white, bold: true, margin: 0,
    });
    // Subtitle
    s.addText("Transforming Manual Document Processing\ninto Intelligent, Secure Workflows", {
      x: 0.8, y: 2.5, w: 8, h: 0.9,
      fontSize: 16, fontFace: "Calibri", color: "94A3B8", lineSpacingMultiple: 1.3, margin: 0,
    });
    // Accent line
    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 3.6, w: 1.5, h: 0.05, fill: { color: C.teal } });
    // Bottom info
    s.addText("Public Sector Innovation Challenge", {
      x: 0.8, y: 4.6, w: 5, h: 0.5,
      fontSize: 12, fontFace: "Calibri", color: "64748B", margin: 0,
    });
    s.addText("April 2026", {
      x: 7, y: 4.6, w: 2.5, h: 0.5,
      fontSize: 12, fontFace: "Calibri", color: "64748B", align: "right", margin: 0,
    });
  }

  // ════════════════════════════════════════════════════════════
  // SLIDE 2 — THE PROBLEM
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.offWhite };
    // Top bar
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });
    // Title
    s.addText("The Challenge Today", {
      x: 0.7, y: 0.35, w: 9, h: 0.6,
      fontSize: 28, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
    });

    // Left column — 3 pain cards
    const pains = [
      { title: "Processing Delays", desc: "Manual classification, routing,\nand review across 5-7 days", icon: "clock" },
      { title: "Fragmented Flow", desc: "Limited visibility, duplicated\neffort across departments", icon: "alert" },
      { title: "Security Constraints", desc: "4 classification levels require\nstrict access control + audit", icon: "shield" },
    ];

    for (let i = 0; i < pains.length; i++) {
      const p = pains[i];
      const cy = 1.25 + i * 1.35;
      // Card bg
      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.7, y: cy, w: 4.8, h: 1.15,
        fill: { color: C.white }, shadow: mkSoftShadow(),
      });
      // Left accent
      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.7, y: cy, w: 0.06, h: 1.15,
        fill: { color: C.red },
      });
      // Icon circle
      const iconPng = await makeIconPng(p.icon, "#DC2626");
      if (iconPng) {
        s.addShape(pres.shapes.OVAL, { x: 1.05, y: cy + 0.25, w: 0.55, h: 0.55, fill: { color: "FEF2F2" } });
        s.addImage({ data: iconPng, x: 1.15, y: cy + 0.35, w: 0.35, h: 0.35, sizing: { type: "contain", w: 0.35, h: 0.35 } });
      }
      s.addText(p.title, {
        x: 1.8, y: cy + 0.15, w: 3.5, h: 0.35,
        fontSize: 14, fontFace: "Calibri", color: C.text, bold: true, margin: 0,
      });
      s.addText(p.desc, {
        x: 1.8, y: cy + 0.5, w: 3.5, h: 0.55,
        fontSize: 11, fontFace: "Calibri", color: C.muted, margin: 0, lineSpacingMultiple: 1.2,
      });
    }

    // Right column — impact stats
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.9, y: 1.25, w: 3.6, h: 3.8,
      fill: { color: C.white }, shadow: mkSoftShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.9, y: 1.25, w: 3.6, h: 0.06,
      fill: { color: C.navy },
    });
    s.addText("Operational Impact", {
      x: 6.15, y: 1.5, w: 3.1, h: 0.35,
      fontSize: 14, fontFace: "Calibri", color: C.navy, bold: true, margin: 0,
    });

    const stats = [
      { big: "5-7", unit: "days", label: "avg. processing time" },
      { big: "High %", unit: "", label: "manual processing" },
      { big: "Many+", unit: "", label: "departments involved" },
      { big: "4", unit: "levels", label: "security classification" },
    ];
    stats.forEach((st, i) => {
      const sy = 2.05 + i * 0.75;
      s.addText(st.big, {
        x: 6.3, y: sy, w: 1.5, h: 0.35,
        fontSize: 22, fontFace: "Arial Black", color: C.teal, bold: true, margin: 0,
      });
      if (st.unit) {
        s.addText(st.unit, {
          x: 7.6, y: sy + 0.05, w: 1.2, h: 0.3,
          fontSize: 12, fontFace: "Calibri", color: C.muted, margin: 0,
        });
      }
      s.addText(st.label, {
        x: 6.3, y: sy + 0.3, w: 3, h: 0.3,
        fontSize: 11, fontFace: "Calibri", color: C.muted, margin: 0,
      });
      if (i < stats.length - 1) {
        s.addShape(pres.shapes.LINE, {
          x: 6.3, y: sy + 0.65, w: 2.8, h: 0,
          line: { color: "E2E8F0", width: 0.5 },
        });
      }
    });
  }

  // ════════════════════════════════════════════════════════════
  // SLIDE 3 — OUR SOLUTION
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.offWhite };
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });
    s.addText("Our Solution: End-to-End AI Platform", {
      x: 0.7, y: 0.35, w: 9, h: 0.6,
      fontSize: 28, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
    });

    // 3 pillars
    const pillars = [
      { title: "AI Engine", sub: "OCR + Classification\n+ Summarization", color: C.teal, icon: "brain" },
      { title: "Workflow Engine", sub: "Auto-routing + Multi-dept\nsequential approval", color: C.green, icon: "route" },
      { title: "Citizen Portal", sub: "Real-time tracking\n+ Notifications", color: C.medNavy, icon: "track" },
    ];

    for (let i = 0; i < pillars.length; i++) {
      const p = pillars[i];
      const px = 0.7 + i * 3.1;
      // Card
      s.addShape(pres.shapes.RECTANGLE, {
        x: px, y: 1.25, w: 2.8, h: 2.0,
        fill: { color: C.white }, shadow: mkSoftShadow(),
      });
      // Top accent
      s.addShape(pres.shapes.RECTANGLE, {
        x: px, y: 1.25, w: 2.8, h: 0.06,
        fill: { color: p.color },
      });
      // Icon
      const iconPng = await makeIconPng(p.icon, `#${p.color}`);
      if (iconPng) {
        s.addShape(pres.shapes.OVAL, { x: px + 1.0, y: 1.55, w: 0.7, h: 0.7, fill: { color: C.ice } });
        s.addImage({ data: iconPng, x: px + 1.1, y: 1.65, w: 0.5, h: 0.5, sizing: { type: "contain", w: 0.5, h: 0.5 } });
      }
      s.addText(p.title, {
        x: px + 0.15, y: 2.35, w: 2.5, h: 0.35,
        fontSize: 16, fontFace: "Calibri", color: C.text, bold: true, align: "center", margin: 0,
      });
      s.addText(p.sub, {
        x: px + 0.15, y: 2.7, w: 2.5, h: 0.5,
        fontSize: 11, fontFace: "Calibri", color: C.muted, align: "center", margin: 0, lineSpacingMultiple: 1.3,
      });
    }

    // Workflow diagram below
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7, y: 3.55, w: 8.6, h: 1.85,
      fill: { color: C.white }, shadow: mkSoftShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7, y: 3.55, w: 8.6, h: 0.05,
      fill: { color: C.teal },
    });
    s.addText("Digitized Workflow — 6 Steps", {
      x: 0.9, y: 3.62, w: 4, h: 0.3,
      fontSize: 11, fontFace: "Calibri", color: C.teal, bold: true, margin: 0,
    });
    s.addImage({
      data: workflowDiag,
      x: 0.8, y: 3.85, w: 8.4, h: 1.5,
      sizing: { type: "contain", w: 8.4, h: 1.5 },
    });
  }

  // ════════════════════════════════════════════════════════════
  // SLIDE 4 — 8 CAPABILITIES GRID
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.offWhite };
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });
    s.addText("8 Future-State Capabilities — Delivered", {
      x: 0.7, y: 0.35, w: 9, h: 0.6,
      fontSize: 28, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
    });

    const caps = [
      { title: "Automated Ingestion", desc: "Camera scan on any phone.\nAI OCR in 10-30 seconds.", icon: "scan", color: C.teal },
      { title: "Intelligent Classification", desc: "Ensemble AI (text + vision).\n15 document types, 85-95%.", icon: "brain", color: C.teal },
      { title: "Auto-Routing", desc: "Rule-based per case type.\nSLA deadlines per step.", icon: "route", color: C.green },
      { title: "AI Summarization", desc: "Key entity extraction.\nConsolidated dossier summary.", icon: "summary", color: C.green },
      { title: "Cross-Dept Collaboration", desc: "Sequential multi-dept review.\nShared annotations.", icon: "collab", color: C.medNavy },
      { title: "Real-time Tracking", desc: "Citizen App timeline.\nIn-app notifications.", icon: "track", color: C.medNavy },
      { title: "Centralized Indexing", desc: "Full-text search, Vietnamese\ndiacritics, clearance-filtered.", icon: "search", color: C.navy },
      { title: "Access Control", desc: "4 security levels, ABAC,\nRLS, full audit trail.", icon: "shield", color: C.navy },
    ];

    const cols = 4, rows = 2;
    const cardW = 2.05, cardH = 1.55;
    const gapX = 0.2, gapY = 0.2;
    const startX = 0.7, startY = 1.15;

    for (let i = 0; i < caps.length; i++) {
      const c = caps[i];
      const col = i % cols, row = Math.floor(i / cols);
      const cx = startX + col * (cardW + gapX);
      const cy = startY + row * (cardH + gapY);
      // Card
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cardW, h: cardH,
        fill: { color: C.white }, shadow: mkSoftShadow(),
      });
      // Left accent
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: 0.05, h: cardH,
        fill: { color: c.color },
      });
      // Icon
      const iconPng = await makeIconPng(c.icon, `#${c.color}`);
      if (iconPng) {
        s.addImage({ data: iconPng, x: cx + 0.15, y: cy + 0.15, w: 0.32, h: 0.32, sizing: { type: "contain", w: 0.32, h: 0.32 } });
      }
      // Check mark
      const checkPng = await makeIconPng("check", "#059669");
      if (checkPng) {
        s.addImage({ data: checkPng, x: cx + cardW - 0.4, y: cy + 0.12, w: 0.22, h: 0.22, sizing: { type: "contain", w: 0.22, h: 0.22 } });
      }
      s.addText(c.title, {
        x: cx + 0.12, y: cy + 0.52, w: cardW - 0.24, h: 0.3,
        fontSize: 11, fontFace: "Calibri", color: C.text, bold: true, margin: 0,
      });
      s.addText(c.desc, {
        x: cx + 0.12, y: cy + 0.82, w: cardW - 0.24, h: 0.6,
        fontSize: 9, fontFace: "Calibri", color: C.muted, margin: 0, lineSpacingMultiple: 1.2,
      });
    }

    // Bottom note
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7, y: 4.6, w: 8.6, h: 0.55,
      fill: { color: C.lightTeal },
    });
    s.addText("All 8 capabilities are fully implemented and demo-ready on live AI models (Alibaba Cloud DashScope)", {
      x: 0.9, y: 4.65, w: 8.2, h: 0.45,
      fontSize: 11, fontFace: "Calibri", color: C.teal, bold: true, align: "center", margin: 0,
    });
  }

  // ════════════════════════════════════════════════════════════
  // SLIDE 5 — CHALLENGE SOLVED + KEY RESULTS
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.offWhite };
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });
    s.addText("Challenges Solved", {
      x: 0.7, y: 0.35, w: 9, h: 0.6,
      fontSize: 28, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
    });

    // Three challenge -> solution cards
    const solved = [
      {
        challenge: "Manual Identification",
        before: "5-10 min per document",
        after: "Under 1 minute",
        how: "AI OCR + ensemble classification with officer confirmation",
        color: C.teal,
      },
      {
        challenge: "Cross-Dept Consolidation",
        before: "Duplicated reviews, paper memos",
        after: "Single shared dossier",
        how: "One scan, one index — every department sees the same data",
        color: C.green,
      },
      {
        challenge: "Extended Approval Cycles",
        before: "No visibility, physical transfer",
        after: "Instant routing + SLA tracking",
        how: "Auto-routing with deadlines; citizen tracks in real-time",
        color: C.medNavy,
      },
    ];

    for (let i = 0; i < solved.length; i++) {
      const sol = solved[i];
      const cy = 1.15 + i * 1.4;
      // Card
      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.7, y: cy, w: 8.6, h: 1.2,
        fill: { color: C.white }, shadow: mkSoftShadow(),
      });
      // Left accent
      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.7, y: cy, w: 0.06, h: 1.2,
        fill: { color: sol.color },
      });
      // Challenge name
      s.addText(sol.challenge, {
        x: 1.0, y: cy + 0.1, w: 2.5, h: 0.3,
        fontSize: 14, fontFace: "Calibri", color: C.text, bold: true, margin: 0,
      });
      s.addText(sol.how, {
        x: 1.0, y: cy + 0.42, w: 3.5, h: 0.6,
        fontSize: 10, fontFace: "Calibri", color: C.muted, margin: 0, lineSpacingMultiple: 1.2,
      });

      // Before → After comparison
      // Before
      s.addShape(pres.shapes.RECTANGLE, {
        x: 5.3, y: cy + 0.15, w: 1.8, h: 0.8,
        fill: { color: "FEF2F2" },
      });
      s.addText("BEFORE", {
        x: 5.35, y: cy + 0.15, w: 1.7, h: 0.2,
        fontSize: 8, fontFace: "Calibri", color: C.red, bold: true, margin: 0,
      });
      s.addText(sol.before, {
        x: 5.35, y: cy + 0.38, w: 1.7, h: 0.5,
        fontSize: 10, fontFace: "Calibri", color: C.text, margin: 0,
      });

      // Arrow
      s.addText("\u2192", {
        x: 7.15, y: cy + 0.3, w: 0.4, h: 0.4,
        fontSize: 20, fontFace: "Arial", color: C.muted, align: "center", margin: 0,
      });

      // After
      s.addShape(pres.shapes.RECTANGLE, {
        x: 7.5, y: cy + 0.15, w: 1.65, h: 0.8,
        fill: { color: "ECFDF5" },
      });
      s.addText("AFTER", {
        x: 7.55, y: cy + 0.15, w: 1.55, h: 0.2,
        fontSize: 8, fontFace: "Calibri", color: C.green, bold: true, margin: 0,
      });
      s.addText(sol.after, {
        x: 7.55, y: cy + 0.38, w: 1.55, h: 0.5,
        fontSize: 10, fontFace: "Calibri", color: C.text, margin: 0,
      });
    }
  }

  // ════════════════════════════════════════════════════════════
  // SLIDE 6 — DEMO VIDEO + LIVE NUMBERS
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.offWhite };
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });
    s.addText("See It in Action", {
      x: 0.7, y: 0.35, w: 9, h: 0.6,
      fontSize: 28, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
    });

    // Video placeholder (large, left)
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7, y: 1.2, w: 5.5, h: 3.6,
      fill: { color: C.navy }, shadow: mkShadow(),
    });
    // Play button
    s.addShape(pres.shapes.OVAL, {
      x: 2.95, y: 2.5, w: 1.0, h: 1.0,
      fill: { color: C.teal, transparency: 20 },
    });
    const playIcon = await makeIconPng("play", "#FFFFFF");
    if (playIcon) {
      s.addImage({ data: playIcon, x: 3.15, y: 2.7, w: 0.6, h: 0.6, sizing: { type: "contain", w: 0.6, h: 0.6 } });
    }
    s.addText("1-Minute Demo Video", {
      x: 1.2, y: 4.0, w: 4.5, h: 0.35,
      fontSize: 12, fontFace: "Calibri", color: "94A3B8", align: "center", margin: 0,
    });
    s.addText("Quick Scan + Dossier Workflow + Citizen Tracking", {
      x: 1.2, y: 4.3, w: 4.5, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: "64748B", align: "center", margin: 0,
    });

    // Right side — key metrics
    const metrics = [
      { value: "10-30s", label: "AI processing per document", color: C.teal },
      { value: "15", label: "document types supported", color: C.green },
      { value: "85-95%", label: "classification accuracy", color: C.medNavy },
      { value: "100%", label: "audit trail coverage", color: C.navy },
    ];
    for (let i = 0; i < metrics.length; i++) {
      const m = metrics[i];
      const my = 1.2 + i * 0.9;
      s.addShape(pres.shapes.RECTANGLE, {
        x: 6.6, y: my, w: 2.9, h: 0.75,
        fill: { color: C.white }, shadow: mkSoftShadow(),
      });
      s.addShape(pres.shapes.RECTANGLE, {
        x: 6.6, y: my, w: 0.05, h: 0.75,
        fill: { color: m.color },
      });
      s.addText(m.value, {
        x: 6.85, y: my + 0.08, w: 2.5, h: 0.32,
        fontSize: 18, fontFace: "Arial Black", color: m.color, bold: true, margin: 0,
      });
      s.addText(m.label, {
        x: 6.85, y: my + 0.42, w: 2.5, h: 0.25,
        fontSize: 10, fontFace: "Calibri", color: C.muted, margin: 0,
      });
    }
  }

  // ════════════════════════════════════════════════════════════
  // SLIDE 7 — CALL TO ACTION / Q&A
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

    s.addText("Thank You", {
      x: 0.8, y: 1.0, w: 8.4, h: 0.9,
      fontSize: 40, fontFace: "Arial Black", color: C.white, bold: true, margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 2.0, w: 1.5, h: 0.05, fill: { color: C.teal } });

    s.addText("We answered the Innovation Challenge:", {
      x: 0.8, y: 2.3, w: 8, h: 0.4,
      fontSize: 14, fontFace: "Calibri", color: "94A3B8", margin: 0,
    });
    s.addText([
      { text: "Classify", options: { bold: true, color: C.teal } },
      { text: "  documents with ensemble AI\n", options: { color: "CBD5E1" } },
      { text: "Summarize", options: { bold: true, color: C.teal } },
      { text: "  with key entity extraction\n", options: { color: "CBD5E1" } },
      { text: "Route", options: { bold: true, color: C.teal } },
      { text: "  automatically across departments\n", options: { color: "CBD5E1" } },
      { text: "Track", options: { bold: true, color: C.teal } },
      { text: "  in real-time from the citizen's phone\n", options: { color: "CBD5E1" } },
      { text: "Secure", options: { bold: true, color: C.teal } },
      { text: "  with 4-level classification + full audit trail", options: { color: "CBD5E1" } },
    ], {
      x: 0.8, y: 2.8, w: 8, h: 2.0,
      fontSize: 14, fontFace: "Calibri", lineSpacingMultiple: 1.6, margin: 0,
    });

    s.addText("Questions?", {
      x: 0.8, y: 4.8, w: 4, h: 0.4,
      fontSize: 16, fontFace: "Calibri", color: C.teal, bold: true, margin: 0,
    });
  }

  // ─── Write file ─────────────────────────────────────────────
  const outDir = path.join(__dirname);
  const outFile = path.join(outDir, "AI-Document-Intelligence-Pitch.pptx");
  await pres.writeFile({ fileName: outFile });
  console.log(`Created: ${outFile}`);
}

main().catch(err => { console.error(err); process.exit(1); });
