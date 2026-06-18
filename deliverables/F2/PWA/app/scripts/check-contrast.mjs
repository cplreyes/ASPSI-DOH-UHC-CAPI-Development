#!/usr/bin/env node
/**
 * Color-contrast a11y gate (E6-PWA-009).
 *
 * The component axe tests disable axe's `color-contrast` rule because jsdom
 * can't compute CSS (see src/test/axe-helpers.ts: "check in Lighthouse
 * instead"), and Lighthouse only sees whatever page is rendered — the
 * warning-tinted surfaces live behind enrollment/login, so contrast went
 * effectively unchecked. This closes that gap: it parses the real theme tokens
 * from src/index.css and enforces WCAG 2.1 AA (4.5:1 for normal text) for every
 * foreground/background pair that actually renders, in light + dark.
 *
 * Runs in `npm run build` (after check-bundle-budget), so CI fails on a contrast
 * regression. Reading the source tokens keeps it drift-proof. A few DOH-anchored
 * Verde Manual colors don't meet AA today (see EXCEPTIONS + A11Y.md) — changing
 * them is a design decision (DESIGN.md), so those are pinned at a regression
 * FLOOR rather than failing the build.
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(resolve(here, '..', 'src', 'index.css'), 'utf8');

function blockBody(selector) {
  const m = css.match(new RegExp(`${selector}\\s*\\{([^}]*)\\}`));
  if (!m) throw new Error(`check-contrast: theme block not found in index.css: ${selector}`);
  return m[1];
}

function parseTheme(body) {
  const out = {};
  const re = /--([\w-]+):\s*([\d.]+)\s+([\d.]+)%\s+([\d.]+)%/g;
  let m;
  while ((m = re.exec(body)) !== null) {
    out[m[1]] = [Number(m[2]), Number(m[3]), Number(m[4])];
  }
  return out;
}

const THEMES = {
  light: parseTheme(blockBody(':root')),
  dark: parseTheme(blockBody('\\.dark')),
};

function hslToRgb([h, s, l]) {
  const sat = s / 100;
  const lig = l / 100;
  const hue = h / 360;
  if (sat === 0) {
    const v = Math.round(lig * 255);
    return [v, v, v];
  }
  const q = lig < 0.5 ? lig * (1 + sat) : lig + sat - lig * sat;
  const p = 2 * lig - q;
  const channel = (t) => {
    let tt = t;
    if (tt < 0) tt += 1;
    if (tt > 1) tt -= 1;
    if (tt < 1 / 6) return p + (q - p) * 6 * tt;
    if (tt < 1 / 2) return q;
    if (tt < 2 / 3) return p + (q - p) * (2 / 3 - tt) * 6;
    return p;
  };
  return [
    Math.round(channel(hue + 1 / 3) * 255),
    Math.round(channel(hue) * 255),
    Math.round(channel(hue - 1 / 3) * 255),
  ];
}

function relativeLuminance([r, g, b]) {
  const lin = (c) => {
    const cs = c / 255;
    return cs <= 0.03928 ? cs / 12.92 : ((cs + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

function contrastRatio(theme, fg, bg) {
  const f = theme[fg];
  const b = theme[bg];
  if (!f) throw new Error(`check-contrast: token --${fg} not found`);
  if (!b) throw new Error(`check-contrast: token --${bg} not found`);
  const lf = relativeLuminance(hslToRgb(f));
  const lb = relativeLuminance(hslToRgb(b));
  return (Math.max(lf, lb) + 0.05) / (Math.min(lf, lb) + 0.05);
}

const AA_TEXT = 4.5;

// foreground/background pairs that actually render as text or a UI affordance.
const PAIRS = [
  ['foreground', 'background'], // body text
  ['muted-foreground', 'background'], // muted labels (mono uppercase captions)
  ['muted-foreground', 'muted'], // muted text on secondary surfaces
  ['secondary-foreground', 'secondary'],
  ['primary', 'background'], // links / signal text ("Saved", etc.)
  ['destructive', 'background'], // error text (text-error)
  ['primary-foreground', 'primary'], // primary button text
  ['destructive-foreground', 'destructive'], // destructive button text
  ['warning', 'background'], // warn-severity text (lock strip, warn alerts)
  ['warning-foreground', 'warning'], // text on a warning fill
];

// All theme pairs now meet WCAG 2.1 AA (4.5:1 normal text). The former
// sub-AA Verde Manual pairs (light ochre warning-as-text, dark primary/
// destructive CTA text) were raised to AA on 2026-06-17 — see DESIGN.md
// Decisions Log + A11Y.md. Re-add an entry here only with a matching
// DESIGN.md row and sign-off (palette is locked, #163).
const EXCEPTIONS = {
  light: {},
  dark: {},
};

console.log('check-contrast — WCAG 2.1 AA (4.5:1 normal text), theme tokens:');
const failures = [];
for (const themeName of ['light', 'dark']) {
  for (const [fg, bg] of PAIRS) {
    const key = `${fg}/${bg}`;
    const floor = EXCEPTIONS[themeName][key];
    const min = floor ?? AA_TEXT;
    const ratio = contrastRatio(THEMES[themeName], fg, bg);
    const ok = ratio >= min;
    const tag = floor ? `floor ${min}` : `AA ${AA_TEXT}`;
    console.log(`  ${ok ? 'ok  ' : 'FAIL'} [${themeName}] ${key.padEnd(36)} ${ratio.toFixed(2)}:1  (${tag})`);
    if (!ok) failures.push(`[${themeName}] ${key} ${ratio.toFixed(2)}:1 < ${min}:1`);
  }
}

if (failures.length > 0) {
  console.error('\ncheck-contrast: FAIL');
  for (const f of failures) console.error(`  x ${f}`);
  console.error(
    '\nA token regressed below its WCAG floor. Fix the color in src/index.css, or — if' +
      '\nintentional — update the floor here + A11Y.md (palette changes need DESIGN.md sign-off).',
  );
  process.exit(1);
}
console.log('check-contrast: OK');
