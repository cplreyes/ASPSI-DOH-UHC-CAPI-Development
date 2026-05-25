# Email draft — 3 short clarifications on Myra's 2026-05-21 decisions

**Suggested threading:** reply-in-thread on the 2026-05-20 thread (`Re: HCW Survey Testing Round 3 — 9 questionnaire items needing the team's decision`) so the close-out lands in one place. If you'd rather start a fresh thread for cleaner readability, use the alt subject below.

**To:** Shan _(coordinator — please raise to Merlyne and Dr. Myra)_
**Cc:** Marriz _(originator — outcome continues on this thread per the 2026-05-20 promise)_, Kidd _(visibility)_, Dr. Myra Silva-Javier _(Q1 + Q3 are for her)_, Mam Merlyne _(Q2 is for her)_
**Subject (reply-in-thread):** Re: HCW Survey Testing Round 3 — 9 questionnaire items needing the team's decision
**Subject (alt, fresh thread):** HCW R3 — 3 short follow-ups on the Healthcare Worker CAPI_Comments matrix

---

Hi Shan and team,

Thank you Dr Myra for the quick turnaround on the Healthcare Worker CAPI_Comments matrix on Wednesday — the decisions are clear on most items and I've started lining up the build.

Quick status on the 9 items, then **three short follow-ups** at the end:

- **5 items are buildable on Dr Myra's decisions alone** and will land in the next F2 PWA patch: #303 (Q11 — confirmed, no change), #304 (Q52 — top-3 multi-select with "no significant impact" as the exclusive standalone), #306 (Q35 — year required, month + day optional), #310 (Q47 — None standalone), #311 (Q110 — None standalone, multi-select kept).
- **3 items are partly buildable today**, with one sub-item each still needing a one-line clarification — those are Q1, Q2, Q3 below.
- **#305-3b (Q9 vs Q4 age cross-check)** is also clear and ships now: in-survey block at `years of service < age − 20`, per Dr Myra's note that "CAPI would not accept" entries that violate the rule.

**Three short follow-ups, marked for whoever owns each:**

**Q1 — for Dr Myra — Q9 tenure (#305 sub-item 3a).**
Dr Myra wrote "Year 1 to 60 / Month 0 to 11" for the Q9 tenure range. I want to make sure I read this correctly before changing the field:

- **Reading A:** years strictly ≥ 1, which excludes HCWs with under a year of tenure from entering valid answers (a 6-month hire would have no valid combination since months alone don't cover tenure when years must be ≥1).
- **Reading B:** the intended fix is just to block the "0 years and 0 months" combination, while still allowing "0 years and ≥1 months" for sub-1-year hires.

Which one did you mean? Reading B would match what Marriz originally raised; Reading A would also be a deliberate scope choice if HCWs with <1 year tenure aren't in the frame. Happy with either, just want to confirm before the field rules ship.

**Q2 — for Mam Merlyne — Q36 wording when Q34 is "already accredited" (#307 sub-item 5b).**
Marriz had previously flagged this one to you. The current Q36 wording is present-tense ("Why is your facility applying to become an accredited YAKAP/Konsulta provider?"), but when Q34 indicates the facility is already accredited, past tense reads more naturally ("Why did your facility apply for…"). If you have a preferred phrasing, I'll wire it into the build; if you'd rather leave the wording for the next questionnaire revision, that also works — just let me know.

**Q3 — for Dr Myra — Q38 wording at the "Not a physician/dentist" option (#309 sub-item, alongside the Q39 option removal you already approved).**
You wrote *"in #38, what does 'not a physician/dentist' mean? Does it refer to the fact that the head of facility is not a physician or dentist? If so, then change the wording."* I want to flag that in the current build, Q38 is asked of the **respondent HCW about themselves** — it's there to gate the physician/dentist-specific Q39. Two valid rewordings depending on intent:

- If Q38 is meant to ask about the **head of facility** (i.e., what you read it as), the option text and the Q38 prompt both need rewording, and the downstream Q39 gating rule changes shape.
- If Q38 is meant to ask about the **respondent HCW** (current build's reading), the option text just needs a clearer wording — something like "I am not a physician/dentist" — and the Q39 gating rule stays as-is.

Which reading did you have in mind?

---

Once these three land I can close out the questionnaire-design half of R3 in full. The engineering-bug half (the matrix rehydrate fix on #314) is already in the code and waiting for tester re-verify on the next smoke.

Thanks all,
Carl
