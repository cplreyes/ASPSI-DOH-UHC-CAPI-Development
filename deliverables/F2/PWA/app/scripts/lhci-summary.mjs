#!/usr/bin/env node
/**
 * Print the Lighthouse scores + Core Web Vitals the CI gate just measured,
 * per public surface (median of the run set).
 *
 * Why this exists: lhci is SILENT on passing assertions, so when the gate is
 * green you can't see the actual CI-runner numbers — which is exactly what you
 * need to decide whether a `warn`-tier assertion (perf / LCP / TBT, see
 * lighthouserc.cjs) has enough margin over its budget to promote to a hard
 * `error`. This prints them every run so the margin is observable.
 *
 * Reads ./.lighthouseci (the filesystem upload target). No-op + exit 0 if the
 * manifest is absent, so it never fails the build — pair it with `if: always()`
 * in CI so it still prints when an assertion failed.
 */
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const dir = '.lighthouseci';
const manifestPath = resolve(dir, 'manifest.json');
if (!existsSync(manifestPath)) {
  console.log('lhci-summary: no .lighthouseci/manifest.json — nothing to summarize');
  process.exit(0);
}

const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const byUrl = {};
for (const run of manifest) (byUrl[run.url] ??= []).push(run);

const pct = (n) => (n == null ? '—' : Math.round(n * 100).toString().padStart(3));

console.log('Lighthouse CI — observed scores this run (representative of the run set):');
console.log('(thresholds in lighthouserc.cjs — a11y/CLS are hard `error`; perf/LCP/TBT are `warn`)');
for (const url of Object.keys(byUrl)) {
  const runs = byUrl[url];
  const rep = runs.find((r) => r.isRepresentativeRun) ?? runs[0];
  const s = rep.summary ?? {};
  let lcp = '—';
  let cls = '—';
  let tbt = '—';
  try {
    const audits = JSON.parse(readFileSync(rep.jsonPath, 'utf8')).audits;
    lcp = `${Math.round(audits['largest-contentful-paint'].numericValue)}ms`;
    cls = audits['cumulative-layout-shift'].numericValue.toFixed(3);
    tbt = `${Math.round(audits['total-blocking-time'].numericValue)}ms`;
  } catch {
    /* metrics are best-effort; category scores below always print */
  }
  console.log(`  ${url}`);
  console.log(
    `    a11y ${pct(s.accessibility)}   perf ${pct(s.performance)}   best-practices ${pct(s['best-practices'])}`,
  );
  console.log(`    LCP ${lcp}   CLS ${cls}   TBT ${tbt}   (budgets: LCP≤4000ms · CLS≤0.1 · TBT≤300ms)`);
}
