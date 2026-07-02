---
type: source-summary
source: "Email — Myra (mcsilva@up.edu.ph) → Carl, 2026-06-17 'for the CAPI MANUAL'; 4 attachments in raw/capi-manual-materials/"
date_ingested: 2026-06-28
tags: [capi, capi-manual, documentation, epic-7, d5, training, style-guide]
---

# Source - CAPI Manual Materials (Myra 2026-06-17)

**Four files Myra sent Carl 2026-06-17 ("for the CAPI MANUAL")** — the structure + style + reference models for authoring the **CAPI Manual** (a Carl/Epic-7/D5 deliverable). Downloaded + filed at `raw/capi-manual-materials/` (gitignored). These are the spec inputs; the manual itself will be authored in `deliverables/CAPI-Manual/`.

## 1. Topic outline (`CAPI_topic outline.docx`) — the manual's TOC

**Primary users:** enumerators, field supervisors, data manager, CAPI/IT support. **Purpose:** device + application use, assignment management, data entry, upload, troubleshooting. 17 sections + annexes:

- **I. Introduction** — purpose · intended users · relationship to Enumerator's/Supervisor's manuals · support contacts · device/data-security basics
- **II. Tablet / Device Overview** — components · charging · connectivity · date/time/location · care/storage · prohibited uses
- **III. CAPI System Overview** — workflow · user roles & access (enumerator/supervisor/data-manager) · environments (training/testing/live) · sync & data-transfer logic
- **IV. Logging into CAPI** — opening the app · username/password · login options/errors · password reset · logout · offline version
- **V. CAPI Dashboard** — navigating · viewing assignments · training materials · notifications · sync status · pending/completed cases
- **VI. Downloading Assignments** — when · facility-based · household · confirming · errors · missing assignments
- **VII. Assignment Listing** — list overview · top/side menu · grid · operation-info icon · comments · callouts · new records · filter/search · status categories
- **VIII. Mapping and Navigation** — open maps · directions · radius search · best route · map all · GPS capture · address/site verification · map errors
- **IX. Starting a Questionnaire** — select assignment · select tool (Facility Head / HCW / Patient / Household) · confirm eligibility · record consent · start interview
- **X. Navigating a Questionnaire** — moving between screens · required questions · question types (single/multiple/numeric/text/date/roster/skip/validation) · help · comments · operator info · facility verification · return to listing
- **XI. Entering & Reviewing Data** — entering correctly · editing · "Other specify" · "Don't Know/Refused/Missing" · interviewer comments · error messages · consistency checks · saving progress
- **XII. Completing a Questionnaire** — review before completion · conclusion screen · final result codes · save/submit · partial/interrupted · reopening cases
- **XIII. Uploading & Syncing** — when · manual/automatic sync · upload status · sync errors · no-internet · confirm upload · report problems
- **XIV. Supervisor-Only Features** — switch enumerators · view assignments · reassign cases · map-all team · review completed · monitor pending · return-for-correction · close site/batch · supervisor sync review
- **XV. Troubleshooting** — login · password · missing/duplicate assignments · frozen app · date/time · GPS/mapping · sync failure · incomplete upload · battery · lost/damaged device · escalation
- **XVI. Data Security & Confidentiality** — passwords · device locking · secure storage · no account sharing · no copy/export · lost/stolen devices · electronic-record confidentiality
- **XVII. Annexes** — login quick guide · assignment status codes · final result codes · common errors · daily sync checklist · supervisor checklist · troubleshooting decision tree · support contacts

> **Build note:** this outline maps cleanly onto OUR system — CSEntry app, CSWeb sync, the Map Report, and especially the **Supervisor hub** (XIV = exactly the login→role-menu→assignment→review→map features the hub already does). Write the manual to CSEntry + supervisor-hub + CSWeb reality, not generic CAPI.

## 2. Style guide (`CAPI_style guide.docx`) — "Style Guide 3: Digital PDF / Clickable Modular"

- **Distribution:** electronic PDF on tablets/laptops/Drive/LMS — "function almost like a mini-website."
- **Per-procedure format (use this for every task):** **Task title → User role → When to use → Steps → Expected result → Common problem → What to do → Related section.**
- **Formatting:** A4 or 16:9 landscape (tablet); body 11–12pt; large readable screenshots; functional color; generous white space; simple narrow tables; avoid long paragraphs; each major procedure starts on a new page.
- **Accent color: purple** (cover, dividers, headers, callouts) — never color alone, always pair with text labels (grayscale-safe).
- **Digital navigation:** clickable TOC + section tabs + PDF bookmarks + hyperlinked cross-refs/annexes + "Return to Manual Map" / "Go to Troubleshooting" buttons + searchable keywords + QR/short-link to latest version.
- **Screenshots:** one per step/key screen; numbered callouts on the image; instruction immediately below; avoid crowding; consistent labels ("Tap," "Select," "Enter," "Review," "Sync"); a troubleshooting table after each major function.
- **Sample tone:** *"Tap the assignment only after confirming that the respondent type matches the assigned tool. If the wrong tool opens, stop and inform the supervisor before proceeding."*
- Reference models cited: CDC Quick Reference Guide (4-page tablet-friendly task guide), INSTRKTIV user-manual template, Visme manual templates.

## 3. Reference models (PDFs, in raw/)

- **`CAPI_Manual (for CAPI).pdf`** — UN/Malawi NSO **"Survey on Aging in sub-Saharan Africa – CAPI Users' Manual" (2017)**, 20pp. A real **CSPro/CSEntry** CAPI manual (our exact toolchain) — strong structural model: intro to CAPI/CSPro, tablet basics, enumerator vs team-leader vs field-supervisor flows, navigation, field notes, interrupt/save, upload to team-leader. Borrow its role-separated structure.
- **`Filling out Forms with ODK Collect (for CAPI manual).pdf`** — 16pp generic CAPI form-filling guide (ODK Collect). Model for the "navigating/entering data" sections — but **adapt to CSEntry**, not ODK.

## Cross-references

- [[Source - Survey Manual Set Architecture (Myra brainstorm 2026-06-08)]] — the CAPI Manual is one of the 4 separate manuals Myra recommends; this is its outline + style.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro CAPI Strategies]] · the supervisor hub ([[project_aspsi_supervisor_app]]) · the live enumerator guide + crosswalks (`deliverables/CSWeb/landing/docs/`) — existing assets to feed the manual.
