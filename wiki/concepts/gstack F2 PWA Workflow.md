---
type: concept
tags: [tooling, claude-code, workflow, f2-pwa, working-conventions]
source_count: 1
---

# gstack F2 PWA Workflow

Adopted subset of [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - gstack Claude Code Skill Pack|gstack]] skills for the F2 PWA workstream. **Decision date: 2026-04-26.** Scope: F2 PWA only (`deliverables/F2/PWA/app/`). The F1/F3/F4 CSPro generator tracks continue under the existing generator-over-hand-edit convention.

## Why F2 PWA, not F-series CSPro

| Track | Build surface | Why gstack fits / doesn't |
|---|---|---|
| **F2 PWA** | Vite + React + TypeScript + Tailwind + shadcn/ui; Playwright E2E; Cloudflare Pages | Standard web app stack — gstack's core target. `/qa` real-browser tests, `/review` PR audit, `/design-review` visual QA all map directly. |
| F1 / F3 / F4 CSPro | Python `generate_dcf.py` → `.dcf` → CSPro Designer → APC | gstack has no CSPro / Designer awareness. Generator-pattern + manual Designer review stays. |

## The adopted loop

```
Investigate ─► Build ─► Review ─► QA ─► Ship branch ─► (workflow auto-releases on merge)
   │           │         │        │        │
/investigate  Claude    /review  /qa    /ship (branch+PR only)
              Code      /codex   /qa-only
```

### Skills mapped to F2 PWA stages

| Stage | Skill(s) | Role |
|---|---|---|
| Bug triage / debugging | `/investigate` | Root-cause UAT issues before patching; iron law no-fix-without-investigation |
| Design polish | `/design-review` | Live audit + atomic-commit fixes (FIL toggle gating, ARIA, spacing, hierarchy). Plan-side use `/plan-design-review`. |
| Pre-merge code audit | `/review`, optionally `/codex` for second opinion | Catches completeness gaps + race conditions before staging→main promotion |
| Browser-driven QA | `/qa` (fix mode) for dev; `/qa-only` (report mode) for UAT pre-checks | Complements ASPSI human UAT — automated regressions for fixed issues |
| Branch → PR | `/ship` (constrained: branch + PR only, see warning below) | Replaces ad-hoc `git push && gh pr create` |
| Safety during prod debug | `/careful`, `/freeze`, `/guard` | Lock edits to `deliverables/F2/PWA/app/` while patching live issues |
| Performance regressions | `/benchmark` | Track Core Web Vitals on the Cloudflare Pages deploy |
| Docs sync | `/document-release` | Catch stale `NEXT.md` / `F2-PWA-UAT-Guide.md` after merges |

### Skills NOT adopted (out of scope for F2 PWA right now)

- `/office-hours`, `/plan-ceo-review` — F2 scope is locked (Apr 20 PDF alignment shipped; Round 3 backlog defined)
- `/design-consultation`, `/design-shotgun`, `/design-html` — F2 PWA design system already shipped (shadcn/ui + Tailwind)
- `/plan-devex-review`, `/devex-review` — F2 is end-user-facing (HCWs), not developer-facing
- `/cso` — useful as a one-off audit before public launch; not in the regular loop
- `/land-and-deploy` — F2 PWA deploys via Cloudflare Pages on push to `main`; the existing milestone-close workflow handles release notes
- `/retro` — separate cadence; may adopt later for weekly project retros
- `/setup-gbrain` — not adopting a separate KB; this Obsidian wiki is the canonical KB

## Constraints and gotchas

### `/ship` must NOT bump version or write CHANGELOG

The F2 PWA repo has `.github/workflows/uat-release-notes.yml` that triggers on **milestone close**, auto-bumps `package.json`, writes `CHANGELOG.md`, creates a GitHub Release, and posts to Slack `#f2-pwa-uat`. Letting `/ship` also do these creates duplicate releases / version drift.

**Rule:** Use `/ship` for *branch → push → PR* only. Do not let it touch `package.json` or `CHANGELOG.md`. The merge → milestone-close path handles versioning.

### Windows: Node.js must be on PATH for `/browse` and `/qa`

Bun's Playwright pipe transport is broken on Windows ([bun#4253](https://github.com/oven-sh/bun/issues/4253)). gstack auto-falls-back to Node.js. Carl's box has Node 22 on PATH (CI bumped to Node 22 in commit `c432887`); local install meets the same bar.

### Real-browser QA shares cookies with browser

Use `/setup-browser-cookies` to import auth cookies from real Chrome before `/qa` hits authenticated routes. F2 PWA staging at `https://5466a539.f2-pwa-staging.pages.dev` is unauthenticated; production at `https://f2-pwa.pages.dev` likewise. **No cookie import needed for F2 PWA QA** unless we add admin auth in a future epic.

### Telemetry stays off

gstack telemetry is opt-in. Carl: keep it off — no remote data leaves the box.

## How this layers with existing F2 PWA conventions

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off]] — gstack `/qa` and `/review` produce evidence (atomic commits + screenshots) that satisfy "drive through to testable artifact." Test bugs found via `/qa` loop back to the source spec (`F2-Spec.md`, skip-logic, validation), per the same convention.
- The existing post-commit Slack notifier (parses task changes → `#capi-scrum`) and the UAT bot automation continue unchanged.
- Lint stack (ESLint + Prettier + tsc + Vitest + Playwright) is what `/review` and `/qa` rely on — already configured.

## How to use gstack on this project

Decided 2026-04-26. Tuned to: solo dev, F2 PWA only, Windows + Git Bash, post-commit Slack notifier, milestone-close release-notes workflow.

### 1. Use it as a pipeline, not à-la-carte

gstack is designed so each skill writes artifacts the next reads. Run `/investigate` → `/review` → `/qa` → `/ship` as a sprint. Skipping straight to `/qa` skips the artifacts that make the rest work.

### 2. Lead with `/investigate` on every UAT bug

Iron-law: no fix without root cause. Stops the "patch first, hope it sticks" loop. The auto-freeze to the module under investigation is a free guardrail.

### 3. Split QA modes by context

- `/qa-only` (report-only) **during** an active UAT round so it doesn't rewrite code while testers are mid-session.
- `/qa` (fix mode) **between** rounds when Carl owns the branch.

Don't mix.

### 4. `/freeze deliverables/F2/PWA/app/` when debugging

Repo has F1/F3/F4 generators and the Obsidian wiki sitting alongside F2 PWA. Freeze prevents Claude from "helpfully" editing the wrong tree mid-debug.

### 5. Run `/benchmark` to baseline at v1.1.1, before Round 3

Round 3 features (#16 exclusive multi-select, #17 auto-select all-of-above, #18 matrix view) can regress LCP/INP. Cheaper to baseline now than to argue from memory later. Then `/benchmark` lives in PR comments going forward.

### 6. `/document-release` after every merged PR

The milestone-close workflow handles `CHANGELOG.md` + `package.json` version bump only. It does **not** sync `deliverables/F2/PWA/app/NEXT.md`, `app/spec/F2-Spec.md`, or `docs/F2-PWA-UAT-Guide.md` — those drift silently. `/document-release` closes that gap.

### 7. `/codex` second opinion only for high-stakes PRs

Costs OpenAI API calls. Worth it for: staging→main promotion, IndexedDB persistence changes, anything touching the Slack webhook or GitHub Actions surface. Skip for label tweaks and copy fixes.

### 8. Hard avoid the planning skills on F2 PWA

`/office-hours`, `/plan-ceo-review`, `/design-consultation`, `/design-shotgun` — F2 scope is locked, design system shipped. Treat as a hard rule, not a nudge.

### 9. `/ship` is branch + push + PR only

Never let it touch `package.json` or `CHANGELOG.md`. The milestone-close workflow (`.github/workflows/uat-release-notes.yml`) owns release semantics.

## Resolved decisions

| Question | Decision | Rationale |
|---|---|---|
| Continuous-checkpoint mode (`gstack-config set checkpoint_mode continuous`)? | **Off** | Post-commit Slack notifier fires on every commit → WIP-prefixed checkpoints would spam `#capi-scrum`. UAT cycles are short; recovery benefit is low. Revisit if Round 3 turns into multi-week build. |
| `/cso` security audit cadence? | **One-off before audience expansion** (e.g., before opening to actual HCWs or DOH demo). **Not** recurring. | Repo went public 2026-04-23; client-side IndexedDB + Slack webhook secret + GitHub Actions surface justify a one-time audit per audience-expansion gate. |
| Adopt `/learn` (gstack cross-session memory)? | **Off** | Already have two memory layers: Obsidian wiki (canonical KB) + auto-memory (`~/.claude/projects/.../memory/`). `/learn` would fragment the truth across three stores. If a gstack skill internally calls `/learn`, fine — but no manual workflow. |
