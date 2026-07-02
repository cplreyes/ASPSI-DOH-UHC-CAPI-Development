---
title: "CSWeb Landing Page — UI/UX Audit & Refresh"
category: deliverable
tags: [csweb, landing, ui-ux, design, accessibility, ph-doh]
last_updated: 2026-06-29
status: live
---

# CSWeb Landing Page — UI/UX Audit & Refresh

Audit + refresh of `https://csweb.asiansocial.org/` (the front-door `index.html`,
served from `/opt/app/lamp/www/index.html`). Done 2026-06-15 with the
`ui-ux-pro-max` skill. Source of truth for the page now lives here
(`landing/index.html`); deploy copy is on the box. Pre-refresh page backed up at
`/root/www-stock-backup/index.html.pre-refresh-2026-06-15`.

## Design-system target (ui-ux-pro-max)
Government health ops portal → **"Accessible & Ethical" style + "Enterprise
Gateway" pattern**: WCAG-grade contrast, path-selection ("choose your system")
layout, trust signals prominent; **avoid** ornate/gradient/low-contrast.
Kept **system fonts** (not the suggested Lora/Raleway) — self-contained, zero
external requests is the right call for an internal gov tool; the suggested pair
skews wellness-consumer, not ops.

## Audit findings (against the prior build)
The prior build was already solid: self-contained, DOH "Verde Vision" green
matched to F2 tokens, semantic HTML, `focus-visible`, `noindex`, AA contrast
(muted ~5.6:1 on paper). Real gaps fixed:

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | "Open CSWeb" (fill) vs "HCW Admin" (outline) read as primary/secondary, but they're **two different systems for two user groups** | UX (high) | Restructured to a **two equal "doors"** gateway (Enterprise Gateway pattern), each a full-card link with tag (F1·F3·F4 / F2), description, CTA |
| 2 | No skip-link | A11y | Added keyboard skip-to-content |
| 3 | No favicon / `theme-color` | Polish | Inline SVG-data-URI monogram favicon + DOH-green `theme-color` (still zero external assets) |
| 4 | No `prefers-reduced-motion` | A11y | Added; disables all transitions/animation/lift |
| 5 | Single breakpoint (3-up cards → 1-up, no tablet stage) | Responsive | Info cards now `auto-fit minmax(220px,1fr)` — reflow 3→2→1 by width, no orphan; doors 2-up → 1-up at 640px |
| 6 | Flat hero | Polish | CSS-only ambient motif (soft green glow + faint survey dot-grid), **masked to fade out so it never touches text contrast**; added trust band (ASPSI × DOH) above hero |
| 7 | `rel="noopener"` no-op (no `target=_blank`) | Minor | HCW link now `target="_blank" rel="noopener"` (correct), labelled "opens in a new tab" |

## Added: live status pill
A "CSWeb reachable" pill, revealed **only** by a successful same-origin
`HEAD /csweb/` (progressive enhancement). Never shows a false "online" — stays
hidden on failure or with JS off. Pulse animation gated behind reduced-motion.

## Brand integrity
No official DOH/ASPSI logo art was fabricated (ui-ux-pro-max "Correct Brand
Logos" rule). Kept the existing neutral green/gold monogram + a **typographic**
trust band. If ASPSI provides official marks, swap them into the `.trust` block.

## Verified
HTTP 200, `text/html`, 21.7 KB, fully self-contained (no external requests).
Structural elements confirmed live: skip-link, two `.door` cards, status pill,
favicon, `theme-color`, `prefers-reduced-motion`. Contrast re-checked: muted
`#51604f` ≥5.8:1 on paper/white; green CTA `#006b3f` 6.6:1 on white; no gold used
as text (accent fills only).

## Help & documentation page (2026-06-16)
Added `help.html` (source: `landing/help.html`; deployed to `/opt/app/lamp/www/help.html`)
— a self-contained, same-design user-facing help page, linked from the landing
page (access-note + footer). Sections: the two systems · signing in · using CSWeb
(Data / Sync Report / Map Report / Apps) · collecting on a tablet (CSEntry) ·
syncing · troubleshooting · support. Content curated from the F1 tester +
enumerator guides but **public-safe**: the site is internet-reachable, so the page
carries operational guidance only — **no credentials, usernames, server IPs/paths,
DB/breakout details, patch internals, GitHub/Slack links, or runbooks**. Verified
live (HTTP 200) and a content scan confirmed zero leaked internals. `noindex` set.
If ASPSI wants the full internal runbooks reachable, that belongs behind CSWeb auth,
not on the public front door.

## Published guides (2026-06-16)
Added the existing user-facing instrument guides to the live site as a small
docs hub, linked from the Help page ("Step-by-step guides" section). New files:
- `assets/docs.css` — shared same-origin stylesheet for the guide pages (same DOH tokens).
- `docs/enumerator-guide.html` — from `deliverables/training/2026-06-07-CSEntry-Enumerator-App-Guide.md` (F1/F3/F4 CSEntry tablet walkthrough). The 2 captured screenshots embedded (`docs/img/01-…`, `02-…`); remaining steps text-only with a banner noting illustrated screenshots are being added (capture is the deferred follow-up).
- `docs/hcw-guide.html` — from `deliverables/training/2026-06-02-f2-hcw-self-admin-one-pager.md` (F2 self-admin).

**Sanitized for the public front door** (the site is internet-reachable): stripped
the enumerator guide's build-status note + "Screenshot plan (internal — remove
before field release)" section; stripped the F2 one-pager's "Notes for the focal
person" + per-facility `[link]` placeholders (reframed as "use the link your
facility shares"); replaced emoji section headers (no-emoji-as-icons rule). A
content scan of all three published pages returned **0 internal-marker hits** (no
IPs, usernames, rosters, internal repo/Slack links, or internal-only sections).

**Deliberately NOT published** (internal / wrong audience for a public site): the
UAT tester guides (rosters, usernames, test-QN assignments), the ASPSI-internal F2
demo guides, the STL/enumerator training decks, and the CSWeb monitoring companion.
Those stay in the vault; if any are needed online they belong behind CSWeb auth.

**Deferred (next):** capture the per-instrument F1/F3/F4 screenshots (emulator
pipeline proven; app now deployed) and drop them into the enumerator guide's
remaining slots.

## Docs-hub expansion + R6 alignment (2026-06-29)
Since the 2026-06-16 publish, the docs hub grew and was realigned to the
**deployed Supervisor & Enumerator Hub (UAT Round 6)**.

**Added to the live docs hub** (linked from help.html → "Step-by-step guides"):
- `docs/hub-guide.html` — Supervisor & Enumerator Hub training guide: role-based
  sign-in, the Supervisor/Enumerator menus, Bluetooth assign/collect/send/receive,
  Collect → Relay, coverage report + offline EA map. Public-safe (operational only;
  no credentials/usernames/internal links).
- `docs/f1-crosswalk.html` … `docs/f4-crosswalk.html` — paper ↔ CAPI/web crosswalks
  per instrument (shared `assets/docs.css`).

**Alignment pass (this update)** — brought help.html and the guides in line with the
deployed R6 build and made them consistent with each other (single source of truth on
the shared facts: sync endpoint, menu labels, update path, Bluetooth message):
- **hub-guide.html** — menu label "Receive Assigned Data **(Patient)**" → "Receive
  Assigned Data"; the Bluetooth connect-failure text now matches the build's actual
  message ("Couldn't connect over Bluetooth. Check: (1) Bluetooth is ON on BOTH
  tablets, and (2) the supervisor has started '…' — then retry.") in §5 + troubleshooting.
- **enumerator-guide.html** — corrected the CSEntry sync endpoint to
  `https://csweb.asiansocial.org/csweb/api` (was the bare `…/csweb` web-console URL);
  replaced the generic "☰ Sync → Add server / Get Application / Send data" wording with
  the real CSEntry UI (**Add Application → from CSWeb → Connect → Install**;
  **Synchronize** circular-arrows icon); added a reciprocal link to the hub guide;
  added remove + re-add update guidance and a 12-digit-key / PSGC-gate note; dropped the
  stale "screenshots being added" banner.
- **help.html** — led the update guidance with the reliable **remove + re-add** path and
  demoted "⋮ → Update Installed Applications" (it can miss CSWeb redeploys); aligned the
  hub guide-list entry to the **"recommended way"** framing; added a hub pointer in the
  tablet section.

All five live pages (index, help, hub-guide, enumerator-guide, hcw-guide) pass an HTML
tag-balance check. hcw-guide.html (F2 self-admin) needed no change. **Deploy:** `scp`
the changed files to `/opt/app/lamp/www/` (help.html → web root; the guides → `docs/`).

## CAPI Manual published to the docs hub (2026-06-29)
Published the **CAPI Manual** (the Epic-7/D5 deliverable at `deliverables/CAPI-Manual/`,
17 sections) to the live help hub as **`docs/capi-manual.html`**, linked as the lead
item in help.html's "Step-by-step guides" (the comprehensive manual; the focused guides
follow). **Reproducible build:** `bash build/build-csweb-help.sh` from `CAPI-Manual/` —
assembles `sections/*.md` → strips the per-section author-note HTML comments → renders the
7 mermaid diagrams to **SVG** in a DOH-green theme (`build/mermaid-green.json`, via
mermaid-cli) → pandoc with `build/csweb-help-template.html` (same `/assets/docs.css`
chrome as the other guides) → strips any residual HTML comments. Output is **self-contained
(no client-side JS)** — diagrams are static SVG, screenshots are the 24 real app captures.
Images land under `docs/img/capi-manual/` (24 PNG + 7 SVG). **Public-safe:** the manual was
written operational-only; a scan found no credentials/IPs/internal paths/repo or Slack links
— only example role usernames (`se-004`/`fs-01`, no passwords, shown in screenshots) and the
fill-in support-contact table (§XVII·H), both fine for the audience. Verified live: page +
all 34 image refs + CSS HTTP 200, 0 broken images, diagrams render green, screenshots cap at
320px, TOC lists all 17 sections. Deployed via `scp -i ~/.ssh/aspsi-csweb` to
`/opt/app/lamp/www/docs/` (+ `docs/img/capi-manual/`).

## To revert
- CAPI Manual: `rm /opt/app/lamp/www/docs/capi-manual.html` + `rm -rf /opt/app/lamp/www/docs/img/capi-manual` (and remove the manual `<li>` from help.html's guide list)
- Landing: `cp /root/www-stock-backup/index.html.pre-refresh-2026-06-15 /opt/app/lamp/www/index.html`
- Help page: `rm /opt/app/lamp/www/help.html` (and remove the two `/help.html` links from index.html)
- Guides: the prior copies are in git history (`git log -- deliverables/CSWeb/landing/docs/`).
