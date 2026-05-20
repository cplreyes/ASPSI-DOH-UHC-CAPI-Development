# Email draft — R3 design-decision questions (via Shan)

**To:** Shan _(R3 tester + coordinator — please raise to Kidd and the survey-design team)_
**Cc:** Kidd _(for visibility — Shan to route to Mam Merlyne / Dr Myra as needed)_
**Subject:** F2 PWA UAT R3 — 9 questionnaire design questions, need survey-design confirmation

---

Hi Shan,

UAT Round 3 surfaced 9 observations from Marriz that are **questionnaire-content / validation-policy calls**, not CAPI bugs — they need a survey-design ruling before I can close them or implement. Could you please raise these to Kidd and the team (Mam Merlyne / Dr Myra as relevant) and come back with the confirmations?

I've drafted a recommendation per item below. For each, the team can mark **Yes** (approve my recommendation) or **No** (do something else — note what in Remarks). A remark on a Yes is welcome too.

Once confirmed, I'll close the GitHub issues with the disposition recorded and slot any approved changes into the build.

| # | GH | Section / Item | Marriz's observation (short) | My recommendation | Confirm (Yes / No) | Remarks |
|---|---|---|---|---|---|---|
| 1 | [#303](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/303) | A · Q11 work hours | Allow decimal hours (e.g., 3.5h for part-time)? | **Keep integer** (1–24, per spec). | | |
| 2 | [#304](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/304) | E · Q52 | "No significant impact" can be ticked with other options → contradicts. | **Make "No significant impact" exclusive** (standard sentinel pattern). | | |
| 3a | [#305](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/305) | A · Q9 tenure | "0 years AND 0 months" should not be allowed. | **Block 0+0**. | | |
| 3b | #305 | A · Q9 vs Q34 | Q9 years should be < Q34 age (cross-field). | **Defer** (need a separate call on the failure UX — block? warn? require comment?). | | |
| 4 | [#306](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/306) | C · Q35 date | Respondent may not remember the exact date. | **Add a "Don't Know / Can't Recall" code** (value `9999`, project F-series convention). | | |
| 5a | [#307](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/307) | C · Q36 | Should Q36 allow multiple responses (like Q39)? | _Survey-design call — no default._ | | |
| 5b | #307 | C · Q36 stem | When Q34 = "already accredited", current stem reads future-tense ("…applying…"). Re-word to past-tense ("…apply…")? | _Survey-design call — no default. Marriz already flagged to Mam Merlyne._ | | |
| 6 | [#309](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/309) | C · Q39 | Remove "Not a physician/dentist" option, OR fix it being selectable alongside others. | **Keep the option, make it exclusive.** | | |
| 7 | [#310](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/310) | D · Q47 ZBB challenges | No "None" option if respondent had no challenges. | **Add "None"** (exclusive). | | |
| 8 | [#311](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/311) | J · Q110 resources | No "None" option if no additional resources needed. | **Add "None"** (exclusive). | | |
| 9 | [#312](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/312) | J · Q125 future plans | Multi-select allows contradictions ("Retire" + "Transfer"). | **Convert to single-select.** | | |

**Notes on a couple of items where context helps:**

- **#305 (3b)** — adding a Q9 < Q34 cross-field check is straightforward; what's not obvious is the failure UX (hard-block vs. soft-warn vs. require a comment). Easier to disposition once we see real respondent behaviour. Hence "defer".
- **#307** — both sub-decisions are questionnaire-content. I don't paraphrase item wording on my own; needs the survey-design team's call.
- **#312** — single-select is the simplest fix and eliminates the contradiction class. If the team wants to keep multi-select with specific exclusivity rules between options, just list which pairs are exclusive and I'll implement.

Thanks Shan — let me know if anything is unclear before you raise it.

Carl
