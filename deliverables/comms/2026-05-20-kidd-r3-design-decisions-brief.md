# Email draft — R3 questionnaire decisions (via Shan, Marriz looped in)

**To:** Shan _(R3 tester + coordinator — please raise to Kidd and the survey-design team)_
**Cc:** Kidd _(for visibility — Shan to route to Mam Merlyne / Dr Myra as needed)_, Marriz _(originator — looped in to see how her observations get resolved)_
**Subject:** HCW Survey Round 3 — 9 questionnaire items needing the team's decision

---

Hi Shan,

Looping Marriz in directly — during HCW Survey Round 3 testing, she noticed 9 items that involve **questionnaire wording, answer options, or answer rules** rather than anything wrong with the app itself. Those are decisions for the survey-design team to make. Marriz, thank you for the detail in each note — it made it easy to sort them.

Shan, could you please walk these 9 items below with Kidd and the team (Mam Merlyne and Dr Myra as relevant) and come back with their decisions?

**A note on process:** changes to questionnaire wording and answer rules ideally get settled *before* testing begins, since making those changes after a round opens means re-doing the build and re-running the testing. That's a process point for the next round to tighten on — it isn't a comment on Marriz's input, which is exactly the kind of careful feedback we want on these items. Whatever the team decides for each (change it now / hold it for the next questionnaire revision / leave as-is with a reason), Marriz will see the outcome on this thread.

For each item below, I've suggested what I think makes sense. The team can mark **Yes** to approve, or **No** with a remark on what to do instead. Notes are welcome on a Yes too.

Once the team confirms, I'll update the build for anything approved and close out the tracking notes.

| # | Section / Item | What Marriz noticed | Suggested decision | Confirm (Yes / No) | Remarks | Tracker |
|---|---|---|---|---|---|---|
| 1 | A · Q11 — work hours | Should respondents be able to enter half-hours (e.g., 3.5 hours) for part-time workers? | Keep it as whole hours only (1–24) for now. If half-hours come up often in the field, we can revisit. | | | [#303](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/303) |
| 2 | E · Q52 | "No significant impact" can currently be ticked together with other options, which contradicts itself. | Make "No significant impact" a stand-alone choice — if the respondent picks it, the other options auto-clear. | | | [#304](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/304) |
| 3a | A · Q9 — tenure | A respondent could currently enter "0 years AND 0 months", which doesn't make sense. | Block 0 years + 0 months. | | | [#305](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/305) |
| 3b | A · Q9 vs Q34 | Years in current job (Q9) shouldn't be greater than the respondent's age (Q34). | Hold for now — first we need the team's call on what should happen when the answers don't match (block? warn the respondent? require a note?). | | | #305 |
| 4 | C · Q35 — date | Respondent may not remember the exact date. | Add a "Don't Know / Can't Recall" option. | | | [#306](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/306) |
| 5a | C · Q36 — accreditation reason | Should Q36 accept multiple answers (like Q39 does), or stay single-answer? | The team's call — no suggestion from my side. | | | [#307](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/307) |
| 5b | C · Q36 — wording | When Q34 = "already accredited", the current Q36 wording asks "why is your facility applying…" — should it be re-worded to past tense ("why did your facility apply for…")? | The team's call. Marriz already flagged this to Mam Merlyne. | | | #307 |
| 6 | C · Q39 | The "Not a physician/dentist" option can currently be picked alongside other options. Marriz also asked if the option should be removed (since Q38 already captures the same fact). | Keep the option, but make it a stand-alone choice — if picked, others auto-clear. | | | [#309](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/309) |
| 7 | D · Q47 — challenges with ZBB patients | No option for respondents who had no challenges. | Add a "None" option (stand-alone — auto-clears the others). | | | [#310](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/310) |
| 8 | J · Q110 — additional resources | No option for respondents who don't need any additional resources. | Add a "None" option (stand-alone — auto-clears the others). | | | [#311](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/311) |
| 9 | J · Q125 — HCW future plans | Multiple answers are allowed, which can produce contradictions (e.g., "Retire" + "Transfer to new facility"). | Allow only one answer. If the team would rather keep multiple answers but block specific contradictions (e.g., "Retire" can't go with "Transfer"), please list which combinations to block and I'll set that up. | | | [#312](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/312) |

**A few notes where context might help:**

- **Item 3b (Q9 vs Q34):** Comparing one answer against another is straightforward to set up. The harder call is what the questionnaire should *do* when the answers don't match — block the respondent until they fix it, show a warning, or ask them to add a note. Easier to decide once we see how often it actually happens.
- **Item 5 (Q36):** Both parts are pure questionnaire-content calls. I don't change the wording of any item on my own — it's the survey-design team's call.
- **Item 9 (Q125):** Allowing only one answer is the simplest fix and removes the contradiction problem Marriz flagged. If the team prefers to keep multiple answers, just list which combinations shouldn't be allowed together and I'll set up the rule.

Thanks Shan — let me know if anything is unclear before you raise it.
Marriz — you'll see the decisions land in this thread; thanks again for the careful R3 work.

Carl
