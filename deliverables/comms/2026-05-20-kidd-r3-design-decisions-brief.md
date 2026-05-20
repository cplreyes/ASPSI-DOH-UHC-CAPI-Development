# Email draft — R3 questionnaire decisions (via Shan, Marriz looped in)

**To:** Shan _(R3 tester + coordinator — please raise to Kidd and the survey-design team)_
**Cc:** Kidd _(for visibility — Shan to route to Mam Merlyne / Dr Myra as needed)_, Marriz _(originator — looped in to see how her observations get resolved)_
**Subject:** HCW Survey Round 3 — 9 questionnaire items needing the team's decision

---

Hi Shan,

Looping Marriz in directly — during HCW Survey Round 3 testing, she noticed 9 items that involve **questionnaire wording, answer options, or answer rules** rather than anything wrong with the app itself. Those are decisions for the survey-design team to make. Marriz, thank you for the detail in each note — it made it easy to sort them.

Shan, could you please walk these 9 items below with Kidd and the team (Mam Merlyne and Dr Myra as relevant) and come back with their decisions?

**A note on process:** changes to questionnaire wording and answer rules ideally get settled *before* testing begins, since making those changes after a round opens means re-doing the build and re-running the testing. That's a process point for the next round to tighten on — it isn't a comment on Marriz's input, which is exactly the kind of careful feedback we want on these items. Whatever the team decides for each (change it now / hold it for the next questionnaire revision / leave as-is with a reason), Marriz will see the outcome on this thread.

**Cross-check with the current questionnaire design.** Before writing this up I checked each of the 9 items against the current questionnaire spec, skip logic, and validation rules the team has already approved. The "Current questionnaire design" column below shows what the current design says for each item. **For some items the suggested decision simply matches what the team has already approved** — so the question is whether to keep it or change it. For others, the design is silent and a fresh call is needed.

**Two findings worth flagging up front before the table:**

- **Item 3b — likely typo in Marriz's note.** Marriz wrote "Q9 years should be less than Q34 (Age)", but Q34 in the current questionnaire is actually the YAKAP/Konsulta accreditation question — **Q4 is the age item**. The sanity check Marriz is asking for already exists in the current design as a post-survey review flag (currently set to "tenure years > age − 15 → flag for review"). The real call is whether to upgrade that from a post-survey review flag to an in-survey block / warning that the respondent sees while answering.
- **Item 6 — Q39 has an internal inconsistency.** The current questionnaire lists "Not a physician/dentist" as an answer option for Q39, but Q39 is only shown when Q38 = "Yes". Since picking "Not a physician/dentist" at Q38 already routes the respondent straight past Q39, that answer option in Q39 is unreachable in practice. Marriz's instinct to remove it is structurally correct — the team can decide whether to clean that up.

For each item below, I've suggested what I think makes sense. The team can mark **Yes** to approve, or **No** with a remark on what to do instead. Notes are welcome on a Yes too.

Once the team confirms, I'll update the build for anything approved and close out the tracking notes.

| # | Section / Item | What Marriz noticed | Current questionnaire design | Suggested decision | Confirm (Yes / No) | Remarks | Tracker |
|---|---|---|---|---|---|---|---|
| 1 | A · Q11 — work hours | Should respondents be able to enter half-hours (e.g., 3.5 hours) for part-time workers? | Whole hours only, range 1–24 (current spec) | Keep current design (whole hours only). If half-hours come up often in the field, the team can revisit. | | | [#303](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/303) |
| 2 | E · Q52 | "No significant impact" can currently be ticked together with other options, which contradicts itself. | Multi-select; no exclusivity rule specified | Make "No significant impact" a stand-alone choice — if picked, the other options auto-clear. | | | [#304](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/304) |
| 3a | A · Q9 — tenure | A respondent could currently enter "0 years AND 0 months", which doesn't make sense. | Years allowed 0–60; months allowed 0–11; 0+0 not blocked | Block 0 years + 0 months. | | | [#305](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/305) |
| 3b | A · Q9 vs Q4 _(age)_ | Years in current job (Q9) shouldn't be greater than the respondent's age (Q4). _(Marriz's note said "Q34"; reading the questionnaire, Q4 is the age item — almost certainly a typo.)_ | Already specified — "tenure years > Q4 − 15 → flag for review" as a post-survey check (not enforced in-survey) | Keep the existing post-survey flag, **plus** a separate call from the team on whether the respondent should also see this in-survey (block? warn? require a comment?). | | | #305 |
| 4 | C · Q35 — date | Respondent may not remember the exact date. | Date field; no "Don't Know" option | Add a "Don't Know / Can't Recall" option. | | | [#306](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/306) |
| 5a | C · Q36 — accreditation reason | Should Q36 accept multiple answers (like Q39 does), or stay single-answer? | Single answer + Other-specify (current spec) | Keep current design (single answer). | | | [#307](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/307) |
| 5b | C · Q36 — wording | When Q34 = "already accredited", the current Q36 wording asks "why is your facility applying…" — should it be re-worded to past tense ("why did your facility apply for…")? | Current wording: "Why is your facility applying to become an accredited YAKAP/Konsulta provider?" | The team's call. Marriz already flagged this to Mam Merlyne. | | | #307 |
| 6 | C · Q39 — physician/dentist option | The "Not a physician/dentist" option can currently be picked alongside other options. Marriz also asked if the option should be removed (since Q38 already captures the same fact). | Option exists with skip-rule "→ Q41", **but Q39 is only shown if Q38 = Yes — meaning that option is unreachable in practice** (see flagged finding above) | Remove the unreachable "Not a physician/dentist" option from Q39's choice list. | | | [#309](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/309) |
| 7 | D · Q47 — challenges with ZBB patients | No option for respondents who had no challenges. | Multi-select; no "None" option | Add a "None" option (stand-alone — auto-clears the others). | | | [#310](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/310) |
| 8 | J · Q110 — additional resources | No option for respondents who don't need any additional resources. | Multi-select; no "None" option. _(Q112 in the same section already has "None" as a precedent.)_ | Add a "None" option (stand-alone — auto-clears the others), consistent with Q112. | | | [#311](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/311) |
| 9 | J · Q125 — HCW future plans | Multiple answers are allowed, which can produce contradictions (e.g., "Retire" + "Transfer to new facility"). | Multi-select + Other-specify (current spec); no exclusivity rules between options | Change to single-answer (simplest fix; removes the contradiction class). If the team would rather keep multiple answers but block specific contradictions (e.g., "Retire" can't go with "Transfer"), please list which combinations to block and I'll set that up. | | | [#312](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/312) |

**A few notes where context might help:**

- **Item 3b (Q9 vs Q4):** Comparing tenure against age is already in the post-survey review flow (the team approved this earlier). What's still open is whether to *also* surface it in-survey — and if so, what the failure UX should be (block? warn? note?). Easier to decide once we see how often it actually happens in the field.
- **Item 5 (Q36):** Both parts are pure questionnaire-content calls. I don't change the wording or single-vs-multiple-answer setup of any item on my own — those are the survey-design team's calls.
- **Item 9 (Q125):** Single-answer is the simplest fix and removes the contradiction problem Marriz flagged. If the team prefers to keep multiple answers, just list which combinations shouldn't be allowed together and I'll set up the rule.

Thanks Shan — let me know if anything is unclear before you raise it.
Marriz — you'll see the decisions land in this thread; thanks again for the careful R3 work.

Carl
