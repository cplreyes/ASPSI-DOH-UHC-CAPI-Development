# R3 questionnaire-design decisions — GH issue update staging

> Prepared 2026-05-25 from Dr. Myra Silva-Javier's 2026-05-21 decisions in the [Healthcare Worker CAPI_Comments Google Doc](https://docs.google.com/document/d/1IFT6QY8JvPih2xYAui5k-4M7U0JqqE6zhsXzarmgzUI/edit). Source ingest: `wiki/sources/Source - HCW CAPI Comments Matrix (Myra answers 2026-05-21).md`. Action plan: `wiki/analyses/Analysis - 2026-05-21 HCW R3 Myra Decisions to Build Actions.md`.

**Repo:** `cplreyes/ASPSI-DOH-UHC-CAPI-Development`
**Labels current on all 9:** `severity:medium` · `status:blocked` · `round:3` · `from-uat-round-3-2026-05` · `design-decision`
**Suggested label moves below:** remove `status:blocked` from items Myra fully resolved; keep it on items still gated on a follow-up clarification.

---

## Apply order

Block A — close + clean wins (6 issues, no upstream questions):
- `#303` close as no-op
- `#310`, `#311`, `#304`, `#309` (Q39 half), `#305` (Q9-vs-Q4 half), `#306` — comment + unblock

Block B — partially resolved, still gated on clarification (3 issues):
- `#305` (Q9 year floor sub-item), `#307` (Q36 wording sub-item), `#309` (Q38 wording sub-item), `#312` (new option translation)

Comments are ready to paste into the GH web UI or shipped via `gh issue comment` / `gh issue close`. Each comment is in a fenced block exactly as it should land on GH.

---

## #303 — Section A · Q11 work hours → CLOSE as no-op

**State change:** `OPEN` → `CLOSED (completed)`
**Label change:** remove `status:blocked`

```
gh issue close 303 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --reason completed --comment-file C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/_issue-bodies/303.md
gh issue edit 303 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --remove-label "status:blocked"
```

Comment body:

```
Decision: keep current design (whole hours only, range 1–24).

Source: Dr. Myra Silva-Javier, 2026-05-21 — Healthcare Worker CAPI_Comments matrix, MESJ column for Item 1: "Just stick to whole numbers. It is easier."

No code change required. Closing as completed.
```

---

## #304 — Section E · Q52 "No significant impact" → BUILD

**State change:** stays `OPEN` until shipped
**Label change:** remove `status:blocked`, add `type:validation`

```
gh issue edit 304 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --remove-label "status:blocked" --add-label "type:validation"
gh issue comment 304 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --body-file C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/_issue-bodies/304.md
```

Comment body:

```
Decision (Dr. Myra Silva-Javier, 2026-05-21):

> "Allow multiple answers to the first 3. Then 'no significant impact' as a standalone choice. But cannot be chosen if any of the top 3 are chosen."

Build:
- Top 3 options: multi-select allowed (unchanged behaviour).
- "No significant impact": mutually exclusive with the top 3. Selecting it clears the top 3 and disables them; selecting any of the top 3 disables "No significant impact".

Net effect matches the standalone-None pattern used in Q47 / Q110 / Q112. Source: Healthcare Worker CAPI_Comments matrix, MESJ column for Item 2.
```

---

## #305 — Section A · Q9 tenure → BUILD (3b) + PARTIAL CLARIFY (3a)

**State change:** stays `OPEN` (3a sub-item still gated)
**Label change:** add `type:validation`; keep `status:blocked`

```
gh issue edit 305 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --add-label "type:validation"
gh issue comment 305 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --body-file C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/_issue-bodies/305.md
```

Comment body:

```
Two sub-items here. Both decided by Dr. Myra Silva-Javier on 2026-05-21 in the Healthcare Worker CAPI_Comments matrix; one needs one short follow-up before it ships.

**3a — Q9 0+0 problem.** Myra wrote: "Year 1 to 60 / Month 0 to 11."
  - Reads cleanly as `years ∈ [1, 60]`, but the F2 HCW sampling frame includes HCWs with <1 year tenure (a 6-month hire is a valid respondent).
  - Open question: does Myra intend (a) `years ≥ 1` strict, excluding sub-1-year HCWs entirely, or (b) phrasing of "block only the 0-years-0-months combination" while still allowing `years = 0, months ≥ 1`?
  - Build path: bundling the question into one short follow-up to the team this week. Keeping this sub-item `status:blocked` until clarification lands.

**3b — Q9 vs Q4 tenure-vs-age cross-check.** Myra wrote (top of doc): "Depends on the system, CAPI would not accept. **[# OF SERVICE < AGE minus 20 (not 15)]**."
  - Promotes the prior post-survey review flag to an in-survey hard block.
  - Threshold tightened from `age − 15` to `age − 20`.
  - Build: hard block on `Q9_years ≥ Q4_age − 20`. Error text: "Years of service must be less than age minus 20."
  - Buildable today; not waiting on 3a.

Will land 3b in the F2 v1.3.x patch; 3a follows once clarified.
```

---

## #306 — Section C · Q35 date → BUILD (engineering pick)

**State change:** stays `OPEN` until shipped
**Label change:** remove `status:blocked`, add `type:ux`

```
gh issue edit 306 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --remove-label "status:blocked" --add-label "type:ux"
gh issue comment 306 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --body-file C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/_issue-bodies/306.md
```

Comment body:

```
Decision (Dr. Myra Silva-Javier, 2026-05-21):

> "Year is important. Month and day can be optional."

Per-component "Don't Know" pattern: `Q35_YEAR` required, `Q35_MONTH` + `Q35_DAY` each independently allowed to be empty / "Don't Know". Replaces the originally-suggested whole-date "Don't Know / Can't Recall" option.

Build shape: either split into three numeric fields (year required + month/day optional) or keep the composite date with per-component DK codes. Engineering pick — both satisfy the design call. Will document the chosen approach in the F2 v1.3.x patch.

Source: Healthcare Worker CAPI_Comments matrix, MESJ column for Item 4.
```

---

## #307 — Section C · Q36 → BUILD (5a) + CLARIFY (5b wording)

**State change:** stays `OPEN` (5b sub-item still gated)
**Label change:** add `type:skip-logic`, `type:validation`; keep `status:blocked`

```
gh issue edit 307 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --add-label "type:skip-logic" --add-label "type:validation"
gh issue comment 307 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --body-file C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/_issue-bodies/307.md
```

Comment body:

```
Two sub-items. 5a decided; 5b still pending.

**5a — Q36 cardinality.** Dr. Myra Silva-Javier, 2026-05-21: "Allow for multiple answers."
  - Overrides the original single-answer spec. Switch Q36 to multi-select.
  - Build dependency: the Q36 → Q39 skip rule was derived assuming single-answer. With multi-select, the routing needs re-derivation — "if Q36 contains any applying-reason → go to Q39; if Q36 = {Not-applying} only → skip Q39." Will validate against the current skip table before flipping the cardinality.

**5b — Q36 wording for the "already accredited" Q34 branch.** No answer in Myra's column.
  - Original ask: when Q34 = "already accredited", should the Q36 prompt be past-tense ("why did your facility apply for…") instead of the current present-tense ("why is your facility applying…")?
  - Routing this to @merlyne (Marriz had previously flagged this to her). Keeping the wording sub-item `status:blocked` until her answer lands.

Will land 5a in the F2 v1.3.x patch; 5b follows once Merlyne weighs in.

Source: Healthcare Worker CAPI_Comments matrix, MESJ column for Items 5a/5b.
```

---

## #309 — Section C · Q39 option → BUILD (Q39 part) + CLARIFY (Q38 wording)

**State change:** stays `OPEN` (Q38 wording sub-item still gated)
**Label change:** add `type:validation`; keep `status:blocked`

```
gh issue edit 309 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --add-label "type:validation"
gh issue comment 309 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --body-file C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/_issue-bodies/309.md
```

Comment body:

```
Compound decision (Dr. Myra Silva-Javier, 2026-05-21, top of Healthcare Worker CAPI_Comments matrix):

> "First, in #38, what does 'not a physician/dentist' mean? Does it refer to the fact that the head of facility is not a physician or dentist? If so, then change the wording."
>
> "I agree with the feedback. Remove the 'not a physician/dentist' option in #39."

**Part (i) — Q39 option removal: BUILD.** Remove the "Not a physician/dentist" option from Q39's value set. This option is structurally unreachable in the current spec (Q39 is only shown when Q38 = Yes; selecting "Not a physician/dentist" at Q38 routes past Q39 entirely), so removing it has no downstream impact. Will land in the F2 v1.3.x patch.

**Part (ii) — Q38 wording reinterpretation: PENDING.** Myra reads the Q38 "Not a physician/dentist" option as a statement about the *head of facility*. The current build reads it as a statement about the *respondent HCW* (gatekeeping Q39's MD-specific questions). Two valid rewordings depending on intent. Need a one-line confirmation before changing Q38 text. Bundling into the one short follow-up to the team this week. Sub-item stays `status:blocked` until clarified.
```

---

## #310 — Section D · Q47 "None" option → BUILD

**State change:** stays `OPEN` until shipped
**Label change:** remove `status:blocked`, add `type:validation`

```
gh issue edit 310 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --remove-label "status:blocked" --add-label "type:validation"
gh issue comment 310 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --body-file C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/_issue-bodies/310.md
```

Comment body:

```
Decision (Dr. Myra Silva-Javier, 2026-05-21):

> "Add a 'None' option (stand-alone — auto-clears the others)."

Build: add `None` as a stand-alone option to Q47's multi-select; selecting it auto-clears the other selections. Mirrors the pattern already in place for Q112.

Source: Healthcare Worker CAPI_Comments matrix, MESJ column for Item 7.
```

---

## #311 — Section J · Q110 "None" option → BUILD

**State change:** stays `OPEN` until shipped
**Label change:** remove `status:blocked`, add `type:validation`

```
gh issue edit 311 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --remove-label "status:blocked" --add-label "type:validation"
gh issue comment 311 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --body-file C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/_issue-bodies/311.md
```

Comment body:

```
Decision (Dr. Myra Silva-Javier, 2026-05-21):

> "Allow for multiple answers. [Add a 'None' option (stand-alone — auto-clears the others), consistent with Q112.]"

Build: add `None` as a stand-alone option to Q110's multi-select; selecting it auto-clears the other selections. Consistent with the Q112 pattern. Multi-select on the other options is retained.

Source: Healthcare Worker CAPI_Comments matrix, MESJ column for Item 8.
```

---

## #312 — Section J · Q125 HCW future plans → BUILD (Retire standalone) + CLARIFY (new option translation)

**State change:** stays `OPEN` (new option text needs translation queue slot)
**Label change:** add `type:validation`, `type:i18n`; keep `status:blocked`

```
gh issue edit 312 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --add-label "type:validation" --add-label "type:i18n"
gh issue comment 312 --repo cplreyes/ASPSI-DOH-UHC-CAPI-Development --body-file C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/_issue-bodies/312.md
```

Comment body:

```
Decision (Dr. Myra Silva-Javier, 2026-05-21):

> "Add 'transfer to a new facility (in the Philippines) with the same role'."
>
> "If they choose 'retire', it is a stand alone choice."

Two changes to Q125:

**(i) Add new answer option.** Text: "Transfer to a new facility (in the Philippines) with the same role." Assign next free option code in `Q125_FUTURE_PLANS` value set per project convention. This option text needs to enter the 7-language translation queue before the 2026-06-12 PSA submission; staging this as `status:blocked` until the translation slot opens.

**(ii) Retire becomes standalone.** Selecting "Retire" auto-clears the other selections; multi-select retained for the remaining options. This sub-item is build-ready independent of the translation queue.

Overrides the originally-suggested switch to single-answer.

Source: Healthcare Worker CAPI_Comments matrix, MESJ column for Item 9.
```

---

## Files referenced by the gh commands above

The comments are extracted as individual `.md` files under `_issue-bodies/` so the `gh issue comment --body-file` invocations are exact and reproducible. The file paths in this staging doc assume Carl runs the gh commands from the project root.

If you'd rather paste each comment manually into the GH UI, the bodies are also in the fenced code blocks above — copy from the opening triple-backtick to the closing one.

## After all 9 land

Open `#271` (R3 close-out, S006 carry to S007) and add a closing comment referencing this slate:

```
Questionnaire-design half of R3 close-out is complete (Dr. Myra Silva-Javier's 2026-05-21 decisions in the Healthcare Worker CAPI_Comments matrix). Per-issue actions tracked in #303 through #312. Of those: #303 closed as no-op (current design retained), #304/#306/#310/#311 fully buildable, #305/#307/#309/#312 buildable in part with sub-items pending a one-line clarification each.

Engineering-bug half (#314 matrix rehydrate) is independent and pending tester re-verify on PR #335.
```
