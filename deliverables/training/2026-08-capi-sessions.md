# August 2026 CAPI sessions — what Carl teaches from

**Decision (2026-07-31): teach from ASPSI's decks.** The custom decks built 2026-07-29 (`2026-08-capi-decks/`) were scrapped when [FOR DOH ONLY] Deliverable No. 2 revealed ASPSI had already produced and cleared a full deck set for these exact modules. Don't rebuild them.

## The decks

They live in `raw/DOH-Deliverable-2-2026-07-31/Training materials/` and are **source documents — do not edit them in place.** Any change is a request to ASPSI.

**Five decks, and they are the same for both cohorts.** The FS and SE copies are byte-identical for decks 1–4; the Household pair differs only in PDF binary metadata (text verified character-for-character identical). So there is **one teaching set**, not two:

| # | Deck | Pages | FS filename | SE filename |
|---|---|---|---|---|
| 1 | CAPI Tool | 33 | `fs_MODULE 6_1CAPI TOOL.pdf` | `se_MODULE 9_1CAPI TOOL.pdf` |
| 2 | Facility Head (F1) | 24 | `fs_MODULE 6_2…` | `se_MODULE 9_2…` |
| 3 | Healthcare Worker (F2) | 26 | `fs_MODULE 6_3…` | `se_MODULE 9_3…` |
| 4 | Patient (F3) | 49 | `fs_MODULE 6_4…` | `se_MODULE 9_4…` |
| 5 | Household (F4) | 51 | `fs_MODULE 6_5…` | `se_MODULE 9_5…` |

## Slot map

**Field Supervisors — Day 2, Los Baños** (Module 6, "Using CAPI"):

| Time | Deck |
|---|---|
| 08:00 | 1 — CAPI Tool |
| 09:00 | 2 — Facility Head |
| 10:30 | 3 — Healthcare Worker |
| 13:00 | 4 — Patient |
| 14:30 | 5 — Household |

**Survey Enumerators — Day 2** (Module 9, "CAPI Installation"), four venues simultaneously:

| Time | Deck |
|---|---|
| 08:00 | 1 — CAPI Tool |
| 09:00 | 2 — Facility Head |
| 13:00 | 3 — Healthcare Worker *(programme names no in-charge for this slot)* |
| 15:00 | 4 — Patient |
| Day 3, 08:00 | 5 — Household — **led by the UHC Y2 Project Team, not CReyes** |

## Deck 1 content (the CAPI module proper)

Introduction → Getting started with CSEntry (add application → CSWeb Server → credentials → install the five apps → Supervisor Hub sign-in → role menus) → Navigating CSEntry (case key, adding a case) → Completing the Questionnaire (parts, partial save, the six question types, final result codes) → Uploading and Syncing → Troubleshooting.

It defers troubleshooting to **Chapter XI of the C5 CAPI Manual** — have that open alongside.

## Before the day

1. **The server URL in deck 1 is `https://csweb.asiansocial.org/csweb/api`, and that is correct.** The sync API is dual-hosted; the console moved to `capi.asiansocial.org` but `csweb` still answers for sync. Do not "correct" this slide, and do not retire the `csweb` host — cleared DOH material teaches it.
2. **Title-slide defects in ASPSI's decks** (they will be on screen in front of the room):
   - Deck 2 reads **"FACILTY HEAD"** — missing letter.
   - **"(Inpatient and Outpatient Respondents)"** appears on decks 2, 3 and 5 as well as 4. It only belongs on the Patient deck.
   - Numbering: Facility Head "1 of 4", HCW "2 of 4", Patient "3 of 4", **Household also "3 of 4"** — duplicate, and there is no "4 of 4".

   Cosmetic, but they are ASPSI's to fix. Raise before August or present as-is.
3. **F2 monitoring discrepancy** — deck 3 and the manuals describe HCW monitoring through CSWeb; the live system has a separate HCW console. Unreconciled with Myra.
4. **Pretest fixes land first.** Several items in `wiki/analyses/Analysis - Pretest Findings vs the CAPI Build.md` change what trainees will see on the tablet — exclusivity hard validation, F4 Q141, missing options and definitions, date format. Teach the build that will be in the field, not the one that was pretested.

## What was scrapped

`2026-08-capi-decks/` — two .pptx (65 + 62 slides), the pptxgenjs build source, and 70 extracted screenshots. Deleted 2026-07-31, untracked, **not recoverable from git**. Its one idea worth keeping if the sessions need more than slides: each teaching point was a screenshot plus numbered **"YOU DO"** steps and a **CHECK** line, so trainees did every step on their own tablet rather than watching. ASPSI's decks are reference walkthroughs; the do-along framing can be added verbally without rebuilding anything.
