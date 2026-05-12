# F2 PWA — Performance Baseline & Budget

Reference baseline for the F2 PWA (HCW survey + Admin Portal) measured on production. Use this to detect regressions in future releases.

**First measurement:** 2026-05-12 (PR #274 + slate 2 — closes [#192](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/192) E6-PWA-010)
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

## Known regressions / follow-ups

- **Bundle splitting** ([#275](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/275) — to file): the `index-*.js` chunk is 930 KB raw. Route-level code-splitting on `/admin/*` would let the HCW survey ship with a smaller initial JS payload (most HCWs never load admin code).
- **CI perf gate** (deferred): no automated regression detection today. Adding a Lighthouse CI step against staging on every PR would catch perf drops at the PR level instead of post-deploy.
- **Authenticated-state perf** (deferred): same as the a11y audit limitation — Lighthouse against post-login dashboards needs cookie-injection setup. Tracked alongside [#273](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/273) (E6-PWA-009b).
