---
type: source-summary
source: "Gmail thread 19edec8589bb5cd5 — Kidd fwd to clreyes6@up.edu.ph, 2026-06-19 (embeds Myra↔Kidd↔DOH chain Jun 11–19 + linked comment matrix 'XJ_Comments_F1-F3')"
date_ingested: 2026-06-28
tags: [capi, survey-design, doh-comments, parked-decision, f1-facility, f2-hcw, f3-patient, f4-household, build-posture]
---

# Source - DOH June Questionnaire Comments (PARKED) 2026-06-19

**Email chain, forwarded by Kidd (`aspsi.doh.uhc.survey2@gmail.com`) → Carl (`clreyes6@up.edu.ph`), 2026-06-19**, embedding the Jun 11–19 Myra↔Kidd↔DOH exchange + the linked Google Doc comment matrix **"XJ_Comments_F1-F3"** (DOH reviewer **Xylee "XJ" Javier** / OAAED / HCFinancing / WHO-PHL / ADB comments on the **April 8** tools). Fetched + analyzed 2026-06-28 via the UP-account connector.

## The decision that governs the build: PARK EVERYTHING

> [!important] Build posture — do NOT implement the June comments now
> Dr. Myra Silva-Javier's 2026-06-12 ruling is the governing decision: **"We will hold off on responding to the comments at this time… they have already accepted the tools… submitted to SJREB and PSA. However, the comments given will be parked. We will wait for the SJREB and PSA comments as well as the results of the pre-testing. If the concerns raised in this set of comments surface during the reviews and the pre-testing, then we will address it then."**
>
> - The **accepted baseline is the April 20 version** (it folded in only the April 17 typo/skip fixes; HH-tool changes were **not** incorporated).
> - **None of the June comments are approved for adoption.** They are deferred to whatever surfaces in **SJREB review · PSA review · pre-testing**.
> - **There is no instruction to Carl** in the thread — it is an informational forward. **Keep building to the April 20 baseline.** These become build work only if they resurface downstream.

This is distinct from, and the opposite posture to, the [[Source - PhilHealth Reinstatement Email (Kidd 2026-06-09)|PhilHealth reinstatement]] (which **is** an approved, DOH-agreed change to build). The June comment batch is **parked**.

## What's parked (high level — full per-item matrix in the thread/Google Doc)

The comment legend: **light-red = substantial revisions / new questions**; **yellow = minor (skip patterns, wording, editorial)**. The big still-open ("please confirm" / "not observed") items:

- **F1 (Facility Head):** convert ~18 single Yes/No "…changed since 2019 / result of UHC Act?" items into **two-step** questions (Q19/21/23/25/27/29/31/39–48 + EMR, MoU, NBB, ZBB, no-copay, ward-allocation, CPG, licensing, accreditation, protocols, quality). *Largest potential F1 rework.* Plus Q91 filter note; justify old Q96/Q97 OOP removal.
- **F2 (HCW, PWA in prod):** ADB-WHO disposition codes; two-step preliminaries (equipment/supplies/EMR); specify standards domains. All "not observed."
- **F3 (Patient):** **new expenditure block after Q18** (food 7-day; utilities; non-food) + **FIES assets replacing Q24–Q28** (substantial); disposition-code clarification ("Completed/Withdraw"); education to all HH members; skip after Q65; BUCAS LGU-functional instruction; option definitions; MAIFIP understanding; **billed-vs-paid separation (#168–171, "no response from ASPSI")**.
- **F4 (Household):** ❓**CONTESTED** — DOH asks to adopt their **April 15 PIDS/DHS-format Household Questionnaire** (a "major revision"), but the UP/ASPSI team was **instructed not to follow Xylee's HH suggestions** and the April 20 submission deliberately excluded them. **No F4 comment matrix exists** in these sources — Myra: *"I did not see the comments for the household survey… Pahabol in a separate document"* (still pending). **Do not build to an F4 restructure.**

## Forward-looking CAPI-native checklist (mostly already done)

Many comments were CAPI-layer logic ASPSI answered "Will apply in the CAPI version" — and most are already built into our generators: **numeric response codes** (1=Yes, 2=No, −5=DK, −999=Refused), **exclusive-option blocking** (None/Refused vs others), **"Other specify" routing to a box**, **GPS/geocodes**, **auto-age-from-birthdate**, **Patient Listing Form generation**, **travel-time >1440-min validation** (GIDA), **single/multi-select enforcement** (Q69/97/99/100/102/132/167/170), and numerous skip-rule fixes. Treat as a confirmation checklist, not new work.

## Timing / relationship context

DOH's comments came in waves on the **April 8** tools, the latest forwarded **June 10** — *after* ASPSI had already submitted to SJREB and PSA. Myra: *"This kind of behavior on their part is unacceptable… they could have given these comments earlier."* Hence the park-and-wait posture: let SJREB/PSA/pre-test be the filter; answer with finality afterward. This ties the comment batch's fate to the **pretest** (ASPSI-scheduled) and the SJREB/PSA reviews — all ASPSI/DOH lane ([[feedback_external_gates_not_carls_concern]]).

## Attachments not readable (connector can't download)

- `Survey Tools_Comment Matrix_XJ_June9 (MESJ).docx` — Myra-annotated matrix (the red/yellow highlight coding + her per-item dispositions live here; plain-text/Doc extraction can't show highlight classes).
- The linked Google Doc "XJ_Comments_F1-F3" is **screenshot-heavy** (`[image]` rows) — exact wording for image-only rows isn't in the text layer.
- **F4 "pahabol" HH comments** — a separate document, not yet provided as of Jun 19.

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix]] — the earlier (Apr 20) change-rationale matrix this batch follows on from.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ADB]] — Xylee Javier ("XJ"), the DOH/ADB reviewer whose comments these are.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD]] · [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Myra Silva-Javier]] — the park decision is Myra's.
- [[Source - PhilHealth Reinstatement Email (Kidd 2026-06-09)]] — the **approved** change (contrast: build it); this batch is **parked**.
