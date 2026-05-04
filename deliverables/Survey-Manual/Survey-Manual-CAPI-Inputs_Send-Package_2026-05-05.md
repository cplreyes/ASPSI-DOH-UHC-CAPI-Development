# Survey Manual CAPI Inputs — Send Package

**From:** Carl Patrick L. Reyes, Data Programmer
**Date:** 2026-05-05
**Package contents:** 12 documents covering Survey Manual edits, methodology clarifications, and supporting annexes for the UHC Year 2 CAPI build.

---

## Reading order (suggested)

1. **Cover note** — this document.
2. **Inputs to Survey Manual** — clean-add form of the proposed edits, organized by Survey Manual section.
3. **Survey-Manual-Apr28_with-CAPI-edits** — track-changes view of the affected Apr 28 sections, for direct review in Word/Google Docs.
4. **Methodology Clarification Requests** — six items needing methodology-team decision before some Manual sections can be finalized.
5. **Annexes A through I** — referenced by the Manual edits; provide the operational and technical detail behind each high-level section.

---

## Document inventory

### Primary documents

| # | Document | File | Purpose |
|---|---|---|---|
| 1 | Inputs to Survey Manual | `Inputs-to-Survey-Manual_2026-05-05.md` | Clean-add edits organized by Manual section |
| 2 | Survey Manual (Apr 28) with CAPI edits | `Survey-Manual-Apr28_with-CAPI-edits_2026-05-05.md` | Track-changes view of affected sections |
| 3 | Methodology Clarification Requests | `Methodology-Clarification-Requests_2026-05-05.md` | Six items for methodology-team decision |

### Annexes

| Annex | Title | File | Status |
|---|---|---|---|
| A | CAPI Tablet Specifications | `annexes/Annex-A_CAPI-Tablet-Specifications_2026-05-05.md` | Sent to ASPSI procurement on 2026-04-29; this is the Manual-version reformat |
| B | CAPI Field Troubleshooting Guide | `annexes/Annex-B_CAPI-Field-Troubleshooting-Guide_2026-05-05.md` | New |
| C | F2 PWA Field Operations Guide | `annexes/Annex-C_F2-PWA-Field-Operations-Guide_2026-05-05.md` | New (F2 PWA already in production) |
| D | F0 Field Supervisor App Operations Guide | `annexes/Annex-D_F0-Field-Supervisor-App-Operations-Guide_2026-05-05.md` | New (F0 build queued in Epic 2) |
| E | Data Transmission and Storage | `annexes/Annex-E_Data-Transmission-and-Storage_2026-05-05.md` | New (CSWeb on VPS architecture) |
| F | Bench Testing Protocol | `annexes/Annex-F_Bench-Testing-Protocol_2026-05-05.md` | New |
| G | CAPI Versioning and Amendment Log | `annexes/Annex-G_CAPI-Versioning-and-Amendment-Log_2026-05-05.md` | New |
| H | Refusal and Replacement Logging | `annexes/Annex-H_Refusal-and-Replacement-Logging_2026-05-05.md` | New |
| I | CAPI Application Architecture Reference | `annexes/Annex-I_CAPI-Application-Architecture-Reference_2026-05-05.md` | New |

---

## Summary of what this package proposes

### Survey Manual edits (Documents 1 and 2)

Seven edits across the Apr 28 draft, all within Data Programmer scope:

1. Replace §"Guidelines on installing/using of CSPro" — swap the Year 1 Dropbox-based steps for a CSWeb-based flow.
2. Insert a new §"Guidelines on the F2 Healthcare Worker Survey" — F2 PWA, paper fallback, offline-on-device.
3. Append a paragraph to §"Initial Health Facility Visit" — F0a documentation of all courtesy-call activities.
4. Add CAPI/Supervisor App reminders to §"Field Logistic and Procedure".
5. Replace §"Data transfer and extraction" — name CSWeb-on-VPS as the sync target; keep Data Extraction paragraph nearly verbatim.
6. Insert §"Bench Testing of CAPI Applications" under §QUALITY CONTROL — operationalizes Protocol §XI.
7. Insert paragraph at start of §"Survey Team Leaders" — names F0 as the supervisor's primary tool.

### Methodology clarifications (Document 3)

Six items where CAPI implementation surfaced questions that need the methodology team's decision. The most consequential is **M1 — Patient intercept procedure** (Protocol §IX), which proposes adopting the Year 1 IDinsight list-everyone-in-window pattern in place of the random-time-interval procedure (which is not implementable natively in CSPro).

Decisions on M1, M2, and M4 are needed before F3a bench testing begins.

### Annexes (A through I)

Operational and technical references the Manual points to. None of the annexes propose methodology changes; they describe how the Manual's high-level instructions are implemented in CAPI.

---

## What this package does **not** include

- **Pre-test sites and pilot training mechanics** — already specified in Protocol §XI; nothing to add from the CAPI side.
- **Translation logistics** — outside Data Programmer scope.
- **Tokens and incentives** — protocol-owned.
- **Specific CSWeb URL and access credentials** — provisioned at training; placeholders in the documents.
- **Screenshots** — 18 screenshot placeholders in the Manual edits; the Data Programmer will capture from the production CSWeb instance once stood up.

---

## Cross-document alignment with DOH requirements

DOH requires that the Protocol, Survey Manual, Annexes, ICFs, training materials, and SOPs remain consistent. The Methodology Clarification Requests document includes an alignment matrix mapping each open item to the documents it touches, so the team can update them in a single coordinated cycle once decisions are made.

---

## Recommended next step

A 30-minute methodology-team discussion (Myra, Doc Paulyn, Daisy, Carl) to walk through M1–M4 from the Methodology Clarification Requests document. M5 and M6 can be resolved asynchronously by email. Once decisions are recorded, the Survey Manual edits in Documents 1 and 2 can be finalized and the corresponding annexes can be locked.

The Data Programmer is available for any technical context the team needs during that discussion.
