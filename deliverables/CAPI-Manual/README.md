# UHC Survey Year 2 — CAPI Manual

The tablet/application user manual for the DOH UHC Year 2 survey CAPI system (CSPro CSEntry + the Supervisor & Enumerator hub + CSWeb). One of the four manuals in the survey documentation set (Operations · Enumerator · Supervisor · **CAPI** · Training) — see `wiki/sources/Source - Survey Manual Set Architecture (Myra brainstorm 2026-06-08).md`. CAPI is kept **separate** from questionnaire content (the paper questionnaire teaches the questions; this manual teaches the app).

- **Primary users:** enumerators, field supervisors, data manager, CAPI/IT support.
- **Spec:** Myra's topic outline + style guide (`wiki/sources/Source - CAPI Manual Materials (Myra 2026-06-17).md`).
- **Status:** **complete.** All 17 sections, written to our real system (CSEntry + hub + CSWeb) with on-device labels verified; **24 real app screenshots** captured live (Samsung A23) + embedded; **8 diagrams** (system architecture, day-flow, role hierarchy, sign-in flow, case lifecycle, supervisor sequence, troubleshooting tree); code-list annexes **B/C/D filled from the live instruments**; both `[VERIFY]` flags resolved. Single combined reader: `CAPI-Manual.md`; styled **`CAPI-Manual.pdf`** (A4, purple, bookmark navigation). **Full done/missing breakdown: `STATUS.md`.**
- **Files:** `README.md` (this) · `STATUS.md` (done/missing) · `CAPI-Manual.md` (combined source) · `CAPI-Manual.html` / `CAPI-Manual.pdf` (styled output) · `sections/01`–`17.md` · `img/` (24 screenshots) · `build/` (PDF build assets + `build-pdf.sh`).
- **Remaining (ASPSI-side, neither blocks release):** support-contact names/numbers in §XVII·H (the one blank field, filled at training); an optional posed tablet photo for §2.A. See `STATUS.md`.

## House style (from Myra's Style Guide 3 — "Digital PDF / Clickable Modular")

- **Every procedure uses the same 8-part block:** **Task → User → When → Steps → Expected result → Common problem → What to do → Related**.
- Digital-first PDF: clickable TOC, bookmarks, hyperlinked cross-references + annexes, "back to map" / "to troubleshooting" links.
- **Accent colour: purple** (cover, dividers, headers, callouts) — always paired with a text label (grayscale-safe).
- One **screenshot per step / key screen**, with numbered callouts on the image and the instruction directly below. Consistent action verbs: **Tap · Select · Enter · Review · Sync**.
- A **troubleshooting table after each major function**. Short paragraphs; each major procedure starts on a new page.
- Tone (per the style guide's sample): direct, imperative, safety-conscious — e.g. *"Tap the assignment only after confirming the respondent type matches the assigned tool. If the wrong tool opens, stop and inform the supervisor."*

## Grounding — document the real system, not generic CAPI

| Outline concept | Our system |
|---|---|
| Logging in | **LoginApp** (hub) — username/password, role-filtered menu (`se-004 — Enumerator` / `fs-01 — Supervisor`) |
| Dashboard / assignments | the role **menu** + CSEntry case list; assignments distributed device-to-device via **Bluetooth** (hub) |
| Survey tools | F1 Facility Head · F3 Patient · F4 Household (CSEntry); F2 HCW is the separate PWA |
| Mapping | CSWeb **Map Report** + on-device GPS capture |
| Sync / upload | CSEntry **Synchronize** ↔ **CSWeb** (`csweb.asiansocial.org`) |
| Supervisor-only | the **Supervisor hub** (review, reassign, coverage reports, map-all) |

## Section plan (Myra's 17-section outline)

**All drafted ✅** — I. Introduction · II. Tablet/Device Overview · III. CAPI System Overview · IV. Logging into CAPI · V. CAPI Dashboard · VI. Downloading Assignments · VII. Assignment Listing · VIII. Mapping & Navigation · IX. Starting a Questionnaire · X. Navigating a Questionnaire · XI. Entering & Reviewing Data · XII. Completing a Questionnaire · XIII. Uploading & Syncing · XIV. Supervisor-Only Features · XV. Troubleshooting · XVI. Data Security & Confidentiality · XVII. Annexes.

## Build / export

- Authored in markdown here (`sections/`); the markdown is the source of truth. Screenshots in `img/` (captured via the adb/CSEntry pipeline on the Samsung A23).
- **Rebuild the PDF:** `bash build/build-pdf.sh` from this directory. It assembles `sections/*.md` → `CAPI-Manual.md` → `CAPI-Manual.html` (pandoc + `build/purple.css` + the `build/mermaid.lua` filter) → `CAPI-Manual.pdf` (Chrome headless: mermaid rendered in purple, 123-entry bookmark outline). Requires pandoc + Google Chrome; `build/mermaid.min.js` is bundled.
- The PDF's navigation is its **bookmark outline** (reader sidebar). Chrome print-to-pdf doesn't carry in-page TOC links through; the markdown stays fully hyperlinked in Obsidian. See `STATUS.md` for the why.
