# Email — Survey Manual clarifications (Working File + appendices)

**To:** Kidd_ASPSI DOH UHC Survey2 `<aspsi.doh.uhc.survey2@gmail.com>`
**Cc:** *(consider)* Dr Myra Silva-Javier `<mcsilva@up.edu.ph>` for items 1 + 5; otherwise direct to Kidd
**Subject:** Re: Survey Manual — CAPI inputs *(replies in the existing thread)*
**Status:** Draft for Carl's review. Not sent.

---

Hi Kidd,

Good day!

Finished reading through the Survey Manual Working File and the appendices yesterday alongside Myra's Protocol V2 and the Apr 30 diff. The CSEntry install steps and the supervisor-app reminders block landed cleanly — thank you for working those in.

Five items came up where the Working File reads slightly differently from the May 5 CAPI Inputs package, or where two of the May 6 ASPSI artifacts are internally inconsistent. Wanted to flag them now so we're aligned before the F3 patient-listing CAPI app and the bench-testing handoff start (June 12 target per the May 4 meeting).

**1. Patient listing methodology**

The Working File §3.4.1.3 (around L900) keeps the Apr 28 per-patient random-interval procedure — CSPro generates *n* in 1–10, enumerator waits *n* minutes, approaches the next patient, repeats. The May 5 CAPI Inputs (lines 30–32) refined this to continuous listing during the designated window, with the Patient Listing app then designating the first two-thirds of the listed pool as main respondents and the last third as backup, in the order patients were listed — following the IDinsight Year 1 methodology.

Both approaches work; they shape the F3 listing CAPI app differently. Could you confirm which is canonical? If we're keeping the Apr 28 procedure (which aligns with Protocol V2 §VII.B.3 wording, so this may be deliberate), I'll retire the refinement from the CAPI Inputs draft to avoid drift.

**2. Healthcare Worker Survey self-admin guide**

The three-path HCW capture model from Annex 1 §1.2 (online self-admin, offline device fallback, paper-to-portal encoding) plus the Field Supervisor / Data Encoder duties don't appear in the Working File main text yet. Was the intent to keep them as attached annexes for the field teams, or to fold them into the manual?

The Field Supervisors will need the three-path workflow as a desk-reference during the August training, regardless of where it lives.

**3. Bench testing protocol**

The pre-deployment bench testing sign-off (skip patterns, range checks, roster looping, sync verification) from Annex 2 §2.2 isn't in §6 Quality Control yet. Same question — annex or inline? Happy to draft a §6 sub-section with the sign-off checklist if that's useful.

**4. Sync architecture**

Working File §6.1 specifies a single daily sync to the server before 10 PM. The May 5 CAPI Inputs §Quality Control specified three sync points — end-of-interview when network is available, end-of-day at lodging, on-demand by the Field Supervisor — for redundancy.

Practically the difference shows up if a tablet fails between 10 AM and 10 PM: the three-point model recovers the cases via the end-of-interview sync, while a single 10 PM rule loses everything since the previous evening. Defer to whatever the field teams find operationally feasible — just want to make sure the manual and the app behave the same way.

**5. Case-ID format — small internal mismatch between two May 6 artifacts**

There's a small inconsistency between two of the May 6 ASPSI artifacts on the last 5 digits of the 12-digit case ID:

- **Appendix D** (Field Codes section, L1–149) uses `RR-PP-MMM-FF-CCC` — Facility 2 + Sequence 3, with the active / replacement / refused partition (001–699 / 700–899 / 900–999) tied to AAPOR disposition. This matches the May 5 brief I sent earlier.
- **Working File §5** (around L1313) uses `RR-PP-MMM-FF-CC-CCC` — Facility 2 + Respondent Type 2 (doubled-digit codes 11/22/33/44) + Sequence 3 per respondent type per facility. The example `035401-01-22-03` reads as Region III / Pampanga / Magalang / Facility 01 / Respondent Type 22 (HCW) / 3rd HCW respondent.

Both are sensible designs — Appendix D's partition gives explicit ID-level headroom for replacements and refusals; the Working File variant makes cross-instrument deduplication explicit at the ID level. The operational refusal-handling rule (different number outside the designated set, slot filled from the replacement DB) is identical in both versions.

Suggest aligning Working File §5 to Appendix D since the appendix matches the May 5 brief and the partition maps cleanly to the AAPOR disposition stamps F1/F3/F4 already carry. If you'd prefer the respondent-type-embedded layout, no problem — happy to retire the partition and move respondent type into the ID. Just let me know which is canonical.

---

A couple of smaller informational items — no urgent decision needed:

- Tablet hardware specs sent to Tita Juvy on April 29 don't appear in the manual yet. Not sure whether the manual is the right place for them or whether procurement is keeping them separately.
- Appendix F (Patient Listing Form) captures only Contact Number + Family Name; the F3b protocol implies more metadata (randomization sequence, eligibility flag, exit-vs-follow-up tag, listing_id for the F3 join). Probably fine if Appendix F is meant as a paper backup only and CSPro carries the full metadata, but wanted to confirm that's the model.

---

Happy to discuss any of these async on the thread or via a quick call, whichever works. Thanks again for pulling the integration together — the CAPI content reads well in the Working File, and these are the leftover bits to align.

Thanks and regards,
Carl

---

## Drafter notes (not sent)

**Source pages this draft is built from:**
- `wiki/sources/Source - Survey Manual Working File (2026-05-06 Kidd).md` — gaps + divergences callouts
- `wiki/sources/Source - Survey Manual Appendix D — Field Codes.md` — case-ID format spec
- `wiki/sources/Source - DOH Survey Protocol V2 (30 April).md` — Protocol V2 §VII.B.3 patient listing wording
- `deliverables/Survey-Manual/Survey-Manual-CAPI-Inputs_2026-05-05.md` — Carl's May 5 inputs (lines 30–32 patient listing refinement; §QC sync architecture)
- `deliverables/Survey-Manual/Annex-1_Field-Operations_2026-05-05.md` §1.2 — HCW three-path model
- `deliverables/Survey-Manual/Annex-2_Technical-Reference_2026-05-05.md` §2.2 — bench testing sign-off
- `deliverables/Survey-Manual/Case-ID-Convention-Brief_2026-05-05.md` — May 5 case-ID brief (matches Appendix D)

**Cc decision (consider):** Items 1 and 5 reference Protocol V2 + the May 5 brief. If Kidd wants to confirm with Myra on item 1, looping her in saves a round-trip. Items 2–4 are operational decisions Kidd can make directly. Default: send to Kidd only; Kidd can forward to Myra at her discretion. If Carl wants to include Myra, add `mcsilva@up.edu.ph` to Cc.

**Lane discipline check (per `feedback_data_programmer_scope.md`):** All five items are CAPI-technical (data dictionary + CAPI app behaviour + case-ID format + bench testing). In scope for direct Carl→Kidd communication. No PM / coordination / ethics / financial content.

**Tone notes:** Items 1, 4 explicitly defer to Kidd / field teams ("if we're keeping the Apr 28 procedure ... I'll retire the refinement"; "defer to whatever the field teams find operationally feasible"). Items 2, 3 offer to do the work ("happy to draft a §6 sub-section"). Item 5 frames the mismatch as a same-day copy-paste rather than a deliberate scope change. Avoids any framing that implies Kidd dropped Carl's content.

**Next step:** Carl reviews + sends from `clreyes6@up.edu.ph` as a Reply to the existing `Re: Survey Manual — CAPI inputs` thread. If discussion lands by EOD Thursday, the F3 listing CAPI app architecture (Sprint 005 candidate) can be locked in for Sprint 006 build.
