# F2 PWA — Performance Baseline & Budget

Reference baseline for the F2 PWA (HCW survey + Admin Portal) measured on production. Use this to detect regressions in future releases.

**First measurement:** 2026-05-12 (PR #274 + slate 2 — closes [#192](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/192) E6-PWA-010)
**Re-measurement:** 2026-05-12 PM after slate 4 bundle-split — closes [#275](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/275). See "Bundle-split delta" section below.
**Method:** Lighthouse 11.7.1, headless Chromium, mobile profile (default), single sample, run from operator workstation against `https://f2-pwa.pages.dev/`.

> Single-sample Lighthouse numbers fluctuate ±5% run-to-run. Treat ±10pt swings on any individual metric as noise; persistent shifts of >10pt or any score dropping below the **AA budget** below as a regression.

## Baseline (2026-05-12)

### HCW survey root (`/`)

| Metric | Value | LH score | Budget |
|---|---|---|---|
| **Performance** | — | **0.91** | ≥ 0.85 |
| First Contentful Paint | 2.5 s | 0.68 | ≤ 3.0 s |
| Largest Contentful Paint | 2.8 s | 0.83 | ≤ 4.0 s |
| Cumulative Layout Shift | 0 | 1.0 | ≤ 0.1 |
| Total Blocking Time | 10 ms | 1.0 | ≤ 200 ms |
| Speed Index | 3.5 s | 0.88 | ≤ 5.8 s |
| Time to Interactive | 2.6 s | 0.98 | ≤ 5.0 s |

### Admin Portal login (`/admin/login`)

| Metric | Value | LH score | Budget |
|---|---|---|---|
| **Performance** | — | **0.93** | ≥ 0.85 |
| First Contentful Paint | 2.3 s | 0.75 | ≤ 3.0 s |
| Largest Contentful Paint | 2.3 s | 0.93 | ≤ 4.0 s |
| Cumulative Layout Shift | 0 | 1.0 | ≤ 0.1 |
| Total Blocking Time | 190 ms | 0.91 | ≤ 200 ms |
| Speed Index | 2.3 s | 0.99 | ≤ 5.8 s |
| Time to Interactive | 2.6 s | 0.98 | ≤ 5.0 s |

## Resource Composition

HCW root first-paint network footprint (cold cache):

| Resource | Requests | Transfer (gzipped) |
|---|---|---|
| Total | 12 | 394 KB |
| Script (`index-*.js`) | 2 | 250 KB |
| Font (`/fonts/*.woff2`) | 4 of 22 | 76 KB |
| Stylesheet (`index-*.css`) | 2 | 13 KB |
| Other (icons, vite.svg, fonts.css, sw.js) | 4 | 55 KB |

Notes:
- The font runtime cache is doing what it should — only 4 woff2 (Newsreader 500, JBMono 400, Public Sans 400+500) get fetched at first paint, not all 22. The remaining 18 weights are pulled lazily as the user encounters surfaces that use them, then cached for offline use.
- The `index-*.js` bundle is currently 930 KB raw / 250 KB gzipped. Vite emits a chunk-size warning at the 500 KB raw threshold ([build log](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/275)) — this is a known suboptimal that doesn't currently trip the perf budget but is worth route-splitting at v2.0.2.

## Budget

| Surface | Perf score floor | LCP floor | TBT ceiling | CLS ceiling |
|---|---|---|---|---|
| HCW survey | 0.85 | ≤ 4.0 s | ≤ 200 ms | ≤ 0.1 |
| Admin Portal | 0.85 | ≤ 4.0 s | ≤ 200 ms | ≤ 0.1 |
| Bundle size (gzipped, single chunk) | — | — | ≤ 350 KB | — |

Floor values are intentionally below current baseline — they're regression triggers, not aspirational targets. If a future release drops below any floor, a perf-regression issue gets filed automatically (TODO: wire to CI in #275 follow-up).

## Re-measurement

To re-run the baseline:

```sh
cd deliverables/F2/PWA/app
npx lighthouse https://f2-pwa.pages.dev --only-categories=performance \
  --chrome-flags="--headless=new --no-sandbox" \
  --output=json --output-path=./lh-perf-hcw.json --quiet

npx lighthouse https://f2-pwa.pages.dev/admin/login --only-categories=performance \
  --chrome-flags="--headless=new --no-sandbox" \
  --output=json --output-path=./lh-perf-admin.json --quiet
```

Run 3 times and average; single samples are noisy.

## Bundle-split delta (PR #281 / closes #275)

Slate 4 (2026-05-12 PM) split the `index-*.js` monolithic chunk into three by adding `manualChunks` + `lazy(() => import('@/admin/App'))`:

| Chunk | Pre-split | Post-split | Notes |
|---|---|---|---|
| HCW first-paint JS (entry + vendor) | 930 KB raw / 250 KB gzip | **608 KB raw / 188 KB gzip** | 35% raw / 25% gzip reduction; admin chunk no longer downloaded |
| `index-*.js` (HCW shell) | 930 KB | **26 KB raw / 8 KB gzip** | App.tsx + survey components only |
| `vendor-*.js` (React + deps) | (in index) | 582 KB raw / 179 KB gzip | All node_modules; eagerly loaded for app boot |
| `admin-*.js` (Admin portal) | (in index) | 329 KB raw / 61 KB gzip | **Lazy** — only fetched on /admin/* navigation |

`build.modulePreload.resolveDependencies` filters the admin chunk out of `<link rel="modulepreload">` for the HCW entry, so the browser doesn't eager-fetch admin even though it's reachable from the entry's module graph.

Re-measured Lighthouse perf (single sample, post-split, local preview build):

| Surface | Pre-split perf | Post-split perf | LCP delta |
|---|---|---|---|
| HCW root | 0.91 | **0.90** | 2.8s → 3.0s (within ±5% sample noise) |
| Admin login | 0.93 | **0.87** | 2.3s → 3.6s (one-time lazy-fetch cost) |

Trade-off accepted: HCW respondents (dominant traffic class) get a smaller first-paint payload; Admin users (ASPSI ops staff, low traffic, typically on fixed connections) pay a one-time ~1s lazy-load cost on first admin-portal navigation, then everything is cached. For a survey app where 99%+ of traffic is HCW, this is the right shape. Both surfaces remain above the 0.85 perf floor.

A11y unaffected — both surfaces still score 1.0 / 100.

## Known regressions / follow-ups

- **CI perf gate** (deferred): no automated regression detection today. Adding a Lighthouse CI step against staging on every PR would catch perf drops at the PR level instead of post-deploy.
- **Authenticated-state perf** (deferred): same as the a11y audit limitation — Lighthouse against post-login dashboards needs cookie-injection setup. Tracked alongside [#273](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/273) (E6-PWA-009b).
- **Vendor chunk split** (deferred): the `vendor-*.js` chunk at 582 KB raw still trips Vite's chunkSizeWarningLimit (500 KB). Could be sub-split into `vendor-react`, `vendor-forms`, etc., but diminishing returns once the admin lazy-load is in place. Re-evaluate if HCW LCP regresses below 0.85 in a future measurement.
