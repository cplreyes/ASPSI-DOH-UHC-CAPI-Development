<!--
RELEASE NOTES TEMPLATE — v2.0.0 onward

PURPOSE: Stakeholder-readable release notes for the F2 PWA + Admin Portal.
Audience: DOH program managers, ASPSI operations, UAT testers, healthcare workers,
plus engineers who maintain the system.

USAGE:
  1. After tagging a release, the auto-pipeline at `.github/workflows/uat-release-notes.yml`
     generates the conventional-commits changelog into the GH Release body.
  2. BEFORE publishing the Release publicly, copy this template into the Release body
     (replacing the auto-generated content), fill in the stakeholder sections, and paste
     the auto-generated changelog into the `<details>` collapsible at the bottom.
  3. Save manually via `gh release edit <tag> --notes-file <path>` or via the GH web UI.

WRITING GUIDANCE:
  - Lead with what users see, not what engineers built. "Real-time submission dashboard"
    not "ResponseDetail page at /admin/data/responses/:id".
  - Plain language: avoid `inline_code`, conventional-commit prefixes (feat: / fix:),
    file paths, and project IDs in the stakeholder sections. Save those for the technical
    changelog at the bottom.
  - Be honest: if a soak gate was waived, say so. If browsers were deferred, say which.
    Stakeholders trust honest releases more than gleaming ones.
  - Skip sections that don't apply (e.g., "UAT Round N — open now" only on UAT-cycle releases).
  - Keep the technical changelog in `<details>` — engineers expand, stakeholders ignore.

DELETE THIS COMMENT BLOCK before publishing.
-->

**Released to production:** YYYY-MM-DD
**Production URL:** https://f2-pwa.pages.dev

---

## What's new for users

<!--
Split by audience if multiple groups are affected. Examples:
  - For healthcare workers taking the survey
  - For ASPSI operations staff
  - For DOH and project leadership
  - For UAT testers

If a group sees no change, say so explicitly: "Nothing changed for you." This
prevents alarm.

Translate technical features into business outcomes. Examples of the right level:
  ✅ "See submissions in real time — dashboard with filters by date / facility / role"
  ❌ "ResponseDetail page at /admin/data/responses/:id"
-->

### For [audience 1]
[plain-language summary of what they'll see, do, or need to know]

### For [audience 2 — only if different]
[etc.]

---

## What's tested vs what's coming

<!--
Honest QA disclosure. Three categories typically:
  ✅ what shipped + passed QA
  ⏳ what was deferred (and to which sprint)
  ⚠️ any gates that were waived (soak, cross-browser, etc.) — ALWAYS disclose

This section builds trust. Don't hide deferrals.
-->

- ✅ [thing that passed QA, e.g., "Cross-platform QA on Chrome desktop + tablet"]
- ⏳ [thing deferred, e.g., "Firefox + Edge cross-engine pass deferred to Sprint NNN — visual / accessibility refinements, not architectural"]
- ⚠️ [any waived gate, e.g., "Soak gate waived to align with UAT Round 2 demo timing"]

---

## UAT Round N — open now

<!--
DELETE this section if not a UAT-cycle release.

Otherwise: who's testing, what they have, how to file feedback.
-->

- **[Tester 1 name]** — [what they're testing]
- **[Tester 2 name]** — [what they're testing]

**How to file feedback:**
- GitHub Issues with the `from-uat-round-N-YYYY-MM` label
- Or post in `#f2-pwa-uat` Slack — automated daily digest fires at 9 AM PHT during the round

**Tester guides:**
- `docs/F2-PWA-UAT-Round-N-[Surface]-Tester-Guide-YYYY-MM-DD.md`

---

## What's coming next (Sprint NNN+1)

<!--
Backlog preview in plain terms. Group by:
  - Higher priority (HIGH security findings, accessibility regressions, half-built features)
  - Medium priority (visual polish, UX consistency, MEDIUM security)
  - New features

Avoid raw task IDs (E4-APRT-NNN) in the human-facing description; mention them parenthetically
or in the technical changelog only.

Stakeholders care about WHAT and WHY. Engineers can map back to ticket IDs from the
GitHub Project link.
-->

**Higher priority:**
- [user-visible bug fix or critical regression]
- [accessibility / security item]

**Medium priority:**
- [polish, consistency, UX]

**New features:**
- [larger increment shipping next sprint]

---

## Production endpoints

| Surface | URL | Audience |
|---|---|---|
| HCW Survey | `f2-pwa.pages.dev` | Healthcare workers (public link) |
| Admin Portal | `f2-pwa.pages.dev/admin` | ASPSI ops + designated testers |
| Worker API | `f2-pwa-worker.hcw.workers.dev` | Internal — backend traffic only |
| Apps Script backend | `F2-PWA-Backend` (Google) | Internal — data persistence |

---

## Rollback (for engineers, in case of emergency)

<!--
Concrete commands, not handwaving. Include:
  - Worker rollback (wrangler deploy from previous tag)
  - Pages rollback (wrangler pages deploy with previous SHA)
  - Apps Script rollback (which dist/Code.gs version to redeploy)
  - Database / migration notes (additive vs destructive)

This is the difference between a 5-minute and 50-minute incident response.
-->

If a critical issue surfaces:

1. **Worker:** `wrangler deploy --env production` from the v[PREVIOUS] tag
2. **Pages:** `wrangler pages deploy --branch=main --commit-hash=<v[PREVIOUS] SHA>`
3. **Apps Script:** redeploy `dist/Code.gs` from the v[PREVIOUS] tag (Manage Deployments → New Version)
4. **Database:** [migration rollback notes — "additive only, no rollback needed" OR "run reverse migration X"]

Contact: Carl (`carlpatricklreyes@gmail.com` / `clreyes6@up.edu.ph`)

---

<details>
<summary><strong>Technical changelog</strong> — for engineers (click to expand)</summary>

<!--
PASTE THE AUTO-GENERATED CONVENTIONAL-COMMITS CHANGELOG HERE.

Source: the matching `## [vX.Y.Z]` section from `deliverables/F2/PWA/app/CHANGELOG.md`,
or the body produced by `.github/workflows/uat-release-notes.yml` before manual edit.

Keep the original ### Added / ### Fixed / ### Changed / ### Deprecated / ### Removed
sections. Optionally add an ### Architecture subsection if the release shifts the system
shape.
-->

### Added

- [auto-generated bullets]

### Fixed

- [auto-generated bullets]

### Changed

- [auto-generated bullets]

### Architecture (optional)

[short summary if the release changes the system shape]

</details>
