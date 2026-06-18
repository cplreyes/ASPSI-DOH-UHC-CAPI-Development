#!/usr/bin/env node
/**
 * Bundle-size budget gate (E6-PWA-010 — the #275 "wire to CI" follow-up).
 *
 * Runs as the last step of `npm run build` (after check-bundle-secrets), so CI
 * and Cloudflare Pages refuse to ship a bundle that regresses past the perf
 * budget documented in PERFORMANCE.md. Catches the case where a dependency bump
 * or a feature balloons the gzipped JS that field tablets must download at
 * first paint — the build only *warns* on raw chunk size today (>500 KB), which
 * is easy to miss in CI logs and doesn't fail anything.
 *
 * Chunks (vite manualChunks): `index` (HCW survey shell) + `vendor`
 * (node_modules) load eagerly at HCW first paint; `admin` is lazy (fetched only
 * on /admin/* navigation). Budgets carry ~30-45% headroom over the current
 * (2026-06-16) gzip sizes — eager first-paint 185 KB, vendor 176 KB, admin
 * 105 KB — so ordinary feature growth doesn't trip the gate; these are
 * regression triggers, not targets. The eager budget is the tight, important
 * one (it's what HCW field tablets download); the lazy admin budget is looser
 * because admin growth never touches the respondent path.
 */
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const here = dirname(fileURLToPath(import.meta.url));
const bundleDir = resolve(here, '..', 'dist', 'assets');

if (!existsSync(bundleDir)) {
  console.error(`check-bundle-budget: ${bundleDir} not found. Did vite build run?`);
  process.exit(2);
}

const KB = 1024;
// Budgets in gzipped bytes. See PERFORMANCE.md "Budget".
const EAGER_FIRST_PAINT_BUDGET = 250 * KB; // index + vendor — the HCW download (~35% over 185 KB)
const ADMIN_BUDGET = 150 * KB; // lazy admin chunk (~43% over 105 KB; looser — never on the respondent path)
const SINGLE_CHUNK_BUDGET = 350 * KB; // documented per-chunk ceiling

function role(name) {
  if (name.startsWith('admin-')) return 'admin';
  if (name.startsWith('vendor-')) return 'vendor';
  if (name.startsWith('index-')) return 'index';
  return 'other';
}

const chunks = readdirSync(bundleDir)
  .filter((f) => f.endsWith('.js'))
  .map((f) => ({ name: f, role: role(f), gz: gzipSync(readFileSync(join(bundleDir, f))).length }));

if (chunks.length === 0) {
  console.error('check-bundle-budget: no .js chunks found in dist/assets.');
  process.exit(2);
}

const fmt = (b) => `${(b / KB).toFixed(1)} KB`;
const total = chunks.reduce((s, c) => s + c.gz, 0);
const adminTotal = chunks.filter((c) => c.role === 'admin').reduce((s, c) => s + c.gz, 0);
// Everything that isn't the lazy admin chunk is downloaded at HCW first paint.
const eagerFirstPaint = total - adminTotal;
const maxChunk = chunks.reduce((m, c) => Math.max(m, c.gz), 0);

console.log('check-bundle-budget — gzipped JS chunks:');
for (const c of [...chunks].sort((a, b) => b.gz - a.gz)) {
  console.log(`  ${c.role.padEnd(7)} ${fmt(c.gz).padStart(10)}  ${c.name}`);
}
console.log('  ---');
console.log(`  eager first-paint (non-admin): ${fmt(eagerFirstPaint)} / ${fmt(EAGER_FIRST_PAINT_BUDGET)}`);
console.log(`  admin (lazy):                  ${fmt(adminTotal)} / ${fmt(ADMIN_BUDGET)}`);
console.log(`  largest single chunk:          ${fmt(maxChunk)} / ${fmt(SINGLE_CHUNK_BUDGET)}`);

const failures = [];
if (eagerFirstPaint > EAGER_FIRST_PAINT_BUDGET) {
  failures.push(
    `eager first-paint JS ${fmt(eagerFirstPaint)} exceeds budget ${fmt(EAGER_FIRST_PAINT_BUDGET)}`,
  );
}
if (adminTotal > ADMIN_BUDGET) {
  failures.push(`admin chunk ${fmt(adminTotal)} exceeds budget ${fmt(ADMIN_BUDGET)}`);
}
if (maxChunk > SINGLE_CHUNK_BUDGET) {
  failures.push(`largest chunk ${fmt(maxChunk)} exceeds single-chunk budget ${fmt(SINGLE_CHUNK_BUDGET)}`);
}

if (failures.length > 0) {
  console.error('\ncheck-bundle-budget: FAIL');
  for (const f of failures) console.error(`  x ${f}`);
  console.error(
    '\nIf the increase is intentional and justified, raise the budget in' +
      '\nscripts/check-bundle-budget.mjs and record the new baseline in PERFORMANCE.md.',
  );
  process.exit(1);
}

console.log('check-bundle-budget: OK');
