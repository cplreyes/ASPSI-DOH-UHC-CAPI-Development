---
type: concept
tags: [capi, survey-design, papi-vs-capi, review-criteria, doh-comments, quality]
source_count: 2
---

# PAPI-to-CAPI Translation Review Criteria

The recurring checklist a DOH/PSA reviewer applies when judging whether a **paper (PAPI)** instrument
was faithfully and well translated to a **computer-assisted (CAPI)** one. Distilled from
[[Xylee Javier (XJ)|XJ]]'s two 2026-07 PAPI-vs-CAPI reviews
([[Source - PAPI vs CAPI Household Review (XJ 2026-07)|Household]] +
[[Source - PAPI vs CAPI HCW Review (XJ 2026-07)|HCW]]), where the same criteria appear near-verbatim
across both instruments — so they read as a general rubric, not instrument-specific quibbles. Useful
both as a **response framework** for the parked comments and as a **design self-check** for any future
CAPI build.

## The two structural constraints behind every comment

1. **No test-environment access.** The reviewer sees only **screenshots**, not the running app. So
   skip logic, validations, and cross-question rules are *unverifiable* from their side — which is why
   the single most-repeated ask is for a **skip-pattern matrix, programming specifications, or access
   to a test environment.** Supplying one collapses a large fraction of the comments at once.
2. **Screenshots lag the build.** The reviewed screens are the **April submission** set; the live
   instruments have moved on. Many "not observed / missing" items are presentation gaps in old
   screenshots, not absent features — so the response is often "already implemented; here is the
   current screen," not a change.

## The rubric (what a reviewer checks)

**A. Section fidelity & sequencing** — every PAPI section (Consent, Field Control, Geographic ID,
sub-headers like BUCAS/GAMOT) should be present, titled, and in order; section intros and overarching
questions should not be dropped so items stop reading as standalone.

**B. One question, once** — question text should display a single time; repeated prompt-and-text is a
readability defect. (The HCW/PWA instrument is XJ's positive exemplar here.)

**C. Skip logic is programmed, not printed** — PAPI skip/filter instructions ("Only answer if…",
"Ask if…", "Ask all questions unless a skip applies") should be **automated as display logic/skip
rules and removed from the enumerator view**, not left in the question text where they can be misread
as part of the question. If a note is kept as guidance, style it distinctly (e.g., blue enumerator
font) and keep its section context.

**D. Validation checks** — the reviewer explicitly watches for:
- exclusive options ("None of the above" / "Refuse" / "Not applicable" / "Don't know") that must be
  **blocked when a real option or "Other" is chosen**, and must not be selectable simultaneously;
- **single-vs-multi** mismatches (a one-answer item that allows multi-select, or vice versa);
- range/consistency/required/cross-question checks generally.

**E. Other (specify) needs a "specify" field** — every "Other" option must expose a free-text capture;
a bare option with no data field is flagged (both reviews list dozens of items).

**F. Codes harmonized & justified** — disposition codes and their **order** should match across
instruments (F1/F2/F4) unless a deviation is documented; any code change (e.g. "Refused" →
"Withdraw Participation/Consent") needs a rationale.

**G. CAPI-appropriate wording & affordances** — replace paper verbs ("tick" → "select"); add input
labels/units ("Year(s)", "Day(s)", "Hour(s)"); provide a legend for markers (the red-asterisk
required-field mark); surface option **definitions** (help text/tooltips) that paper printed inline;
give a required-field/"select one only" cue.

**H. Cascading geography** — administrative geo should be a **Region → Province/HUC →
City/Municipality → Barangay** cascade (narrows the barangay list, cuts mis-selection), plus GPS
lat/long capture with a stated capture/record/validate method.

**I. Roster integrity** — member-level loops must keep a **visible member identifier throughout**,
prevent cross-member mixing/duplication, and auto-populate already-collected respondent data for
confirmation rather than re-entry.

**J. Realistic ranges** — numeric limits should fit the field (e.g. travel duration must allow >1 day
/ >1440 min for GIDA households, a Year-1 SurveyCTO failure mode called out explicitly).

**K. System robustness disclosures** — navigation controls (Next/Back/Go-To/navigator), **autosave**
on interruption, **resume from last save**, and **session timeout** handling should be documented; for
a self-administered tool, online-vs-offline parity should be stated.

## Why it matters

Several of these criteria are **CAPI-native strengths** the build already delivers (programmed skips,
exclusivity blocking, GPS, the PSGC cascade, autosave/resume) — the gap is usually **evidence**, not
implementation. That reframes the parked-comment response from "rework the instruments" to "document
what exists + supply a skip/validation matrix + a test login." See
[[Analysis - XJ PAPI-vs-CAPI Reviews vs Current CAPI Build]].

## Related

- [[Source - PAPI vs CAPI Household Review (XJ 2026-07)]] · [[Source - PAPI vs CAPI HCW Review (XJ 2026-07)]]
- [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]] — the governing parked posture
- [[Questionnaire Numbering Convention]] · [[PSGC Value Sets]] · [[GPS and Photo Capture]]
