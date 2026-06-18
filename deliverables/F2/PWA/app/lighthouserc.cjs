/**
 * Lighthouse CI gate — full-page a11y + performance scores on the public
 * surfaces (E6-PWA-009 / E6-PWA-010).
 *
 * Complements the two existing build-chain gates:
 *   - scripts/check-contrast.mjs      — token-level WCAG AA contrast (parses index.css)
 *   - scripts/check-bundle-budget.mjs — gzipped bundle-size budget
 * Those run inside `npm run build` (no browser needed). This one needs a real
 * rendered page, so it runs as a dedicated CI job (`lighthouse` in
 * .github/workflows/ci.yml): build → serve the static `dist/` with `vite
 * preview` → audit with headless Chrome. It closes the *score-level* blind spot
 * the unit gates can't see (the axe component tests disable `color-contrast`,
 * and neither unit gate measures LCP/CLS/TBT on a real render).
 *
 * Scope: the two surfaces reachable WITHOUT auth — HCW enrollment (`/`) and the
 * admin login (`/admin/login`). Deep authed surfaces need a live session token
 * (blocked on #543/#528) and stay deferred — see PERFORMANCE.md / A11Y.md.
 *
 * Assertion tiers (rationale + promotion path in PERFORMANCE.md "CI perf gate"):
 *   error — host-independent signals we already hold and never want to silently
 *           regress: perfect accessibility (100/100, also backed by the axe
 *           component tests + the contrast gate) and zero layout shift. These
 *           don't depend on the runner's CPU, so a failure is a real finding.
 *   warn  — throughput metrics (perf score, LCP, TBT) that vary with the CI
 *           runner's CPU under Lighthouse's simulated mobile throttling. Admin
 *           login's baseline TBT (190ms) already sits a hair under the 200ms
 *           budget, so a hard gate would flake. They surface in the run but
 *           don't block; promote to `error` once a few green runs establish the
 *           real CI baseline.
 */
module.exports = {
  ci: {
    collect: {
      // Serve the already-built static dist. --strictPort so the URL below is
      // deterministic (preview won't silently hop to 4174 if 4173 is taken).
      startServerCommand: 'npm run preview -- --port 4173 --strictPort',
      // vite preview prints "  ➜  Local:   http://localhost:4173/" — the default
      // ready-pattern ("listen") never matches. Match the banner's "Local" label,
      // NOT "Local:": vite colorizes the label, so ANSI reset codes sit between
      // "Local" and the colon and a "Local:" pattern silently never matches
      // (lhci then burns the full ready-timeout before proceeding).
      startServerReadyPattern: 'Local',
      startServerReadyTimeout: 30000,
      url: ['http://localhost:4173/', 'http://localhost:4173/admin/login'],
      // Median of 3 — single-sample Lighthouse swings ±5% run-to-run.
      numberOfRuns: 3,
      settings: {
        // headless=new = the modern headless mode; --no-sandbox is required in
        // CI containers (ubuntu-latest runs Chrome without a sandbox-capable uid).
        chromeFlags: '--headless=new --no-sandbox',
      },
    },
    assert: {
      // Only the audits listed here are evaluated (no preset), so nothing fails
      // implicitly. Both URLs are held to the same assertions.
      assertions: {
        // --- hard gates: host-independent, we already hold these ---
        'categories:accessibility': ['error', { minScore: 1 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        // --- visible-but-non-blocking: CI-runner-variable throughput ---
        'categories:performance': ['warn', { minScore: 0.85 }],
        'categories:best-practices': ['warn', { minScore: 0.9 }],
        'largest-contentful-paint': ['warn', { maxNumericValue: 4000 }],
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
      },
    },
    upload: {
      // Keep reports as a CI artifact path; no LHCI server to talk to.
      target: 'filesystem',
      outputDir: './.lighthouseci',
    },
  },
};
