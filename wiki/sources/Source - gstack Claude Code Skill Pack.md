---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/garrytan_gstack_ Use Garry Tan's exact Claude Code setup_ 23 opinionated tools that serve as CEO, Designer, Eng Manager, Release Manager, Doc Engineer, and QA]]"
date_ingested: 2026-04-26
tags: [tooling, claude-code, workflow, f2-pwa]
---

# Source - gstack Claude Code Skill Pack

GitHub README for **`garrytan/gstack`** — an opinionated Claude Code skill pack by Garry Tan (YC President & CEO). Ships **23 specialist slash-commands plus power tools** that turn Claude Code into a virtual eng team (CEO, Eng Manager, Designer, Reviewer, QA Lead, CSO, Release Engineer). MIT licensed, no premium tier.

> [!note] Adoption scope (this project)
> Carl is adopting gstack for the **F2 PWA** workstream only (build, QA, review, ship loop). Not adopting for the F1/F3/F4 CSPro generator tracks — those use a different generator-over-hand-edit workflow (see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/gstack F2 PWA Workflow|gstack F2 PWA Workflow]]).
>
> The skills are already installed and visible in this Claude Code session (`gstack-qa`, `gstack-review`, `gstack-ship`, etc.). This ingest documents adoption, not installation.

## Install (already done)

```
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup
```

On Carl's Windows 11 box (`C:\Users\analy\.claude\skills\gstack\`). Auto-update is throttled to once/hour, network-failure-safe. `--team` flag bootstraps the repo so teammates inherit gstack — **not run for ASPSI-DOH repo** (Carl is the sole AI-assisted dev).

## The sprint shape

> Think → Plan → Build → Review → Test → Ship → Reflect

Each skill feeds the next. `/office-hours` writes a design doc that `/plan-ceo-review` reads; `/plan-eng-review` writes a test plan that `/qa` picks up; `/review` catches bugs that `/ship` verifies fixed.

## The 23 skills

### Plan / think
| Skill | Role | Use |
|---|---|---|
| `/office-hours` | YC Office Hours | Six forcing questions; reframes product before code is written |
| `/plan-ceo-review` | CEO / Founder | Rethink scope; Expansion / Selective Expansion / Hold / Reduction modes |
| `/plan-eng-review` | Eng Manager | Lock architecture, data flow, diagrams, edge cases |
| `/plan-design-review` | Senior Designer | Rates design dimensions 0–10; AI-slop detection |
| `/plan-devex-review` | DX Lead | Persona research; benchmarks TTHW; 20–45 forcing questions |
| `/design-consultation` | Design Partner | Builds a design system from scratch; writes `DESIGN.md` |
| `/design-shotgun` | Design Explorer | Generates 4–6 mockup variants; comparison board |
| `/autoplan` | Review Pipeline | Runs CEO → design → eng → DX automatically; surfaces only taste decisions |

### Build / review / debug
| Skill | Role | Use |
|---|---|---|
| `/design-html` | Design Engineer | Mockup → production HTML/CSS via Pretext computed layout (30 KB, zero deps) |
| `/review` | Staff Engineer | Pre-merge bug hunt; auto-fixes obvious issues |
| `/investigate` | Debugger | Root-cause debugging; iron law: no fixes without investigation |
| `/design-review` | Designer Who Codes | Live audit + atomic-commit fixes with before/after screenshots |
| `/devex-review` | DX Tester | Live onboarding test; navigates docs, times TTHW, screenshots errors |
| `/codex` | Second Opinion | Independent review via OpenAI Codex CLI; pass/fail gate, adversarial, consult |
| `/cso` | Chief Security Officer | OWASP Top 10 + STRIDE; 17 false-positive exclusions; 8/10 confidence gate |

### Test / ship / monitor
| Skill | Role | Use |
|---|---|---|
| `/qa` | QA Lead | Real-browser QA; finds bugs, fixes them, generates regression tests |
| `/qa-only` | QA Reporter | Same methodology, report-only (no code changes) |
| `/ship` | Release Engineer | Sync main, run tests, audit coverage, push, open PR |
| `/land-and-deploy` | Release Engineer | Merge PR, wait for CI/deploy, verify production health |
| `/canary` | SRE | Post-deploy monitoring loop |
| `/benchmark` | Performance Engineer | Page load, Core Web Vitals, resource sizes; before/after on every PR |
| `/document-release` | Technical Writer | Re-syncs README / ARCHITECTURE / CONTRIBUTING / CLAUDE.md against the diff |
| `/retro` | Eng Manager | Per-person breakdowns, shipping streaks, test-health trends |

### Browser / power tools
- `/browse`, `/open-gstack-browser`, `/setup-browser-cookies` — real-Chromium QA; ~100 ms per command; anti-bot stealth; sidebar agent (Sonnet for actions, Opus for analysis)
- `/pair-agent` — share browser with another AI agent (OpenClaw, Hermes, Codex, Cursor); scoped tokens, tab isolation
- `/careful`, `/freeze`, `/guard`, `/unfreeze` — destructive-command guardrails + edit scope locks
- `/setup-deploy`, `/setup-gbrain`, `/gstack-upgrade`, `/learn` — config + maintenance

## Windows gotchas (matter for Carl)

> [!warning] Bun + Playwright pipe transport bug on Windows
> Bun has [bun#4253](https://github.com/oven-sh/bun/issues/4253) — Playwright pipe transport breaks on Windows. **`/browse` falls back to Node.js automatically.** Both `bun` and `node` must be on PATH. Carl's setup already has both (F2 PWA Vite/Vitest stack runs on Node 22; see commit `c432887`).

> [!note] Git Bash or WSL required
> gstack works on Windows 11 via Git Bash or WSL. Carl uses Git Bash (the bash shell wired to Claude Code in this project's settings).

## Telemetry

Default **off**. Opt-in sends only: skill name, duration, success/fail, gstack version, OS. Never code, paths, repo names, branches, prompts, or content. Carl: keep off.

## Skills that overlap with existing F2 PWA automation

The F2 PWA already has a release-notes workflow (`.github/workflows/uat-release-notes.yml` — auto-bumps `package.json`, writes `CHANGELOG.md`, creates GitHub Release, posts to Slack on milestone close). Skills that potentially overlap:

- **`/ship`** — would push + open PR + bump version. Conflicts with the milestone-close auto-release. **Use `/ship` only for branch → PR; let the workflow handle CHANGELOG + version bump on merge.**
- **`/document-release`** — re-syncs project docs against the diff. Complements (does not conflict with) the workflow's CHANGELOG generator.

See the working-conventions concept for the adopted F2 PWA loop: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/gstack F2 PWA Workflow|gstack F2 PWA Workflow]].

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/gstack F2 PWA Workflow]] — adopted skill subset for F2 PWA build/QA/ship
- F2 PWA app: `deliverables/F2/PWA/app/`
- Lint stack already in place: ESLint + Prettier + tsc + Vitest + Playwright

## Citation

(Source: README at https://github.com/garrytan/gstack — clipped to `raw/` 2026-04-26)
