# F2 PWA — App-level Claude instructions

This CLAUDE.md is scoped to the F2 PWA app workstream only. The vault-level
(`analytiflow/CLAUDE.md`) and LLM Wiki schema (`ASPSI-DOH-CAPI-CSPro-Development/CLAUDE.md`)
still apply higher up the tree. Anything below this directory follows these rules
in addition to the parents.

**gstack scope:** gstack is adopted for the F2 PWA workstream only. Never use
gstack skills (especially `/ship`, `/qa`, `/review`) on F1, F3, or F4 CSPro
work — those live in `deliverables/{F1,F3,F4}/` and follow the CSPro generator
workflow, not the PWA git/PR flow. `/ship` for this app must NOT bump version
or write CHANGELOG (the release-notes workflow owns those).

## Design System

Always read [`DESIGN.md`](./DESIGN.md) before making any visual, UI, color, type,
spacing, or motion decision in this app. Memorable thing anchor:
**"This is real software, not a government form."** Palette: Verde Manual
(DOH-anchored emerald + pale verde paper). Type: Newsreader display + Public Sans
Variable body + JetBrains Mono data. Layout: hairline-divided, no cards,
marginal mono question numbers. Do not deviate without explicit user approval and
without adding a row to the Decisions Log in `DESIGN.md`. In QA mode, flag any code
that doesn't match.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. The
skill has multi-step workflows, checklists, and quality gates that produce better
results than an ad-hoc answer. When in doubt, invoke the skill. A false positive is
cheaper than a false negative.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke /office-hours
- Strategy, scope, "think bigger", "what should we build" → invoke /plan-ceo-review
- Architecture, "does this design make sense" → invoke /plan-eng-review
- Design system, brand, "how should this look" → invoke /design-consultation
- Design review of a plan → invoke /plan-design-review
- Developer experience of a plan → invoke /plan-devex-review
- "Review everything", full review pipeline → invoke /autoplan
- Bugs, errors, "why is this broken", "wtf", "this doesn't work" → invoke /investigate
- Test the site, find bugs, "does this work" → invoke /qa (or /qa-only for report only)
- Code review, check the diff, "look at my changes" → invoke /review
- Visual polish, design audit, "this looks off" → invoke /design-review
- Developer experience audit, try onboarding → invoke /devex-review
- Ship, deploy, create a PR, "send it" → invoke /ship
- Merge + deploy + verify → invoke /land-and-deploy
- Configure deployment → invoke /setup-deploy
- Post-deploy monitoring → invoke /canary
- Update docs after shipping → invoke /document-release
- Weekly retro, "how'd we do" → invoke /retro
- Second opinion, codex review → invoke /codex
- Safety mode, careful mode, lock it down → invoke /careful or /guard
- Restrict edits to a directory → invoke /freeze or /unfreeze
- Upgrade gstack → invoke /gstack-upgrade
- Save progress, "save my work" → invoke /context-save
- Resume, restore, "where was I" → invoke /context-restore
- Security audit, OWASP, "is this secure" → invoke /cso
- Make a PDF, document, publication → invoke /make-pdf
- Launch real browser for QA → invoke /open-gstack-browser
- Import cookies for authenticated testing → invoke /setup-browser-cookies
- Performance regression, page speed, benchmarks → invoke /benchmark
- Review what gstack has learned → invoke /learn
- Tune question sensitivity → invoke /plan-tune
- Code quality dashboard → invoke /health
