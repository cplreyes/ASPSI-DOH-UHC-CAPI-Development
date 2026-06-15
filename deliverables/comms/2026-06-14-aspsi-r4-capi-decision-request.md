---
type: deliverable
kind: decision-request
audience: ASPSI survey-design (Dr. Myra Silva-Javier · Merlyne) · routed via Kidd
prepared_by: Carl Patrick L. Reyes
reporter: Marriz (F3 Patient Survey UAT tester) — Round 4 sweep, 2026-06-13/14
date_drafted: 2026-06-14
status: draft-for-Carl-review-before-sending
tags: [comms, decision-request, aspsi, f3, uat-round-4]
---

# F3 Patient Survey — UAT Round 4 Items for Confirmation

During Round 4, **Marriz** walked the F3 Patient Survey cover-to-close and flagged the items below, each with her own suggestion. Everything that was a build issue has been fixed and deployed. The rest are points where we'd like a quick **confirm** from ASPSI — for almost all of them we can handle the concern on the CAPI side or the current behaviour already works, so **no change to the approved questionnaire is needed**. The table shows Marriz's suggestion alongside our recommendation; in most cases a "confirm" is all we need.

> Reporter for every item: **Marriz** (F3 tester). One sweep, one tester — field observations, not yet design positions.

---

## A. Interview flow — making sure it never gets "stuck"

| # | Observation | Raised by | Marriz's suggestion | Our recommendation (confirm / amend) | Issue |
|---|---|---|---|---|---|
| 1 | A respondent who withdraws partway can't be recorded as "not completed" — the result screen isn't reachable. | Marriz | A way to jump to the Result screen and record the interview as not completed. | We'll add a quiet "not completed" exit **on the CAPI side** — no questionnaire change. Just confirm the result label to record. | #515 |
| 2 | **Q86** ("Which of the following happened during the patient's most recent visit?") and **Q128** ("Which items did you have to pay for out-of-pocket?") — if none of the listed items applied, the interviewer can't move on. | Marriz | Add an "Other (Specify)" / "None" option. | We can **relax the CAPI requirement** so it never blocks — no new option on the questionnaire. Confirm. | #438, #481 |
| 3 | **Q18** ("In the past 6 months, what is the patient's average monthly household income?") — nothing to enter if the respondent doesn't know even an estimate. | Marriz | Add a "Don't know" code for income. | Interviewer records the closest bracket; the CAPI won't block. No new code needed unless preferred in a future version. | #398 |

## B. Skips that depend on area-level programs

| # | Observation | Raised by | Marriz's suggestion | Our recommendation (confirm / amend) | Issue |
|---|---|---|---|---|---|
| 4 | The GAMOT block (**Q152** "Have you heard of … GAMOT?" → Q159) and BUCAS block (**Q99** "Have you heard about … BUCAS center?" → Q103) should only be asked where those programs operate, but the area isn't recorded. | Marriz | Add a question on whether the area has GAMOT / BUCAS so the skip is automatic. | **Keep as-is** — the existing awareness question already acts as the entry point, and interviewers can be briefed to skip in non-program areas. No new question. | #495, #464 |

## C. Answer options & wording

| # | Observation | Raised by | Marriz's suggestion | Our recommendation (confirm / amend) | Issue |
|---|---|---|---|---|---|
| 5 | **Q54** ("Who is your main primary care provider?") has a "None" option, and **Q77** ("Are you registered with a YAKAP/Konsulta package provider?") has "I've never heard of it" — both look inconsistent with the earlier filter answers. | Marriz | Remove those options. | Harmless to leave as printed; we can quietly **not display** them in the CAPI if preferred — either way, no change to the paper instrument. | #412, #430 |
| 6 | **Q157** ("Where did you get the rest of the medicines?") has no "got all from GAMOT" choice; **Q178** ("Overall, how would you rate your experience with the referral process?") has a "Not applicable" that may not apply. | Marriz | Add a "got all from GAMOT" option (Q157); remove "Not applicable" (Q178). | The existing choices are workable — interviewers use the closest fit. No change needed. | #500, #514 |
| 7 | **Q47** ("Awareness of PhilHealth package"), **Q150** ("Travel time from home to nearest pharmacy") and **Q131–Q134** ("Satisfaction with cleanliness and comfort") show a short label rather than the full paper wording. | Marriz | Show the exact paper-questionnaire wording. | The current labels read fine on-device and carry the same meaning; we'd **keep them**. A full-text refresh can ride a future questionnaire version — not blocking. | #404, #493, #486 |

## D. Interviewer notes, field labels & layout (CAPI-side, not questionnaire content)

| # | Observation | Raised by | Marriz's suggestion | Our recommendation (confirm / amend) | Issue |
|---|---|---|---|---|---|
| 8 | The note on **Q97** ("What was the final amount you paid in cash for your outpatient care?") sits on the wrong sub-question; the **Q124** ("Have you heard of … MAIFIP?") skip note is redundant; **Q135** ("Were you satisfied with the overall time spent from registration to exiting the facility?") is marked "for inpatients only". | Marriz | Move the Q97 note to Q97.1; remove the Q124 note; remove the "inpatients only" note on Q135. | These are **CAPI notes, not questionnaire content** — we adjust/move/remove them on our end. (Q135 is already asked of everyone.) Confirm. | #455, #477, #487 |
| 9 | **Q148** ("What are the medical conditions that you take the medicines for?") has a medicines field that reads like a duplicate of **Q147** ("What are the medications that you usually take?"). | Marriz | Clarify the difference — it looks redundant. | We can **relabel the CAPI field** to remove the duplicate impression — no questionnaire change. Confirm what it should read. | #491 |
| 10 | **Q94** ("Cost of laboratory test/s") should repeat per lab test; the payment grids **Q92** ("Cost of consultation"), **Q94** and **Q96** ("Amount spent for prescribed medicines") allow contradictory entries. | Marriz | Repeat Q94 per lab test (from Q93); make the grids select-one with the amount box appearing only on the paid option. | The amount-vs-"No" check is **already tightened**. The rest we'd apply as **CAPI-side presentation refinements** within the existing questions — keep for this round, no paper change. | #450, #446, #451, #453 |

---

*Draft for Carl's review before sending. All items raised by Marriz (F3 tester). Net: nearly everything can be handled on our side or left as-is — the only thing we genuinely need from ASPSI is the **result label for the "not completed" exit (#1)**; the rest are quick confirms.*
