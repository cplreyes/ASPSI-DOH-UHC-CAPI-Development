# Tester tickets vs the DOH-cleared questionnaire — counter-check

**Date:** 2026-08-14 · Each open F1 Bicolano ticket (#1216–#1233) checked against two
sources: what the **deployed CAPI** actually shows, and what the **DOH/SJREB-cleared
June-5 questionnaire** says. Rule applied throughout: **the cleared questionnaire is
authoritative.** A tester can be right that the tablet is wrong and still request wording
that does not match the cleared tool — separating those two things is the point.

Evidence tool: `python lookup.py --instrument F1 --locale BCL --q 27` prints
English / deployed / cleared side by side for any question.

## Headline

**Every ticket reports a real on-tablet defect. None is invalid.** But **four** ask for
changes that would move the tool *away* from the cleared questionnaire, and three carry a
wrong diagnosis that must be corrected in the reply.

| verdict | count | tickets |
|---|---|---|
| Tester right, requested wording matches cleared | 10 | #1216, #1218, #1219, #1220, #1223, #1224, #1225, #1227, #1231, #1233 |
| Defect real, but the requested change conflicts with cleared | 4 | #1222, #1228, #1229, #1230 |
| Not a defect | 0 | — |

Separately, the tickets exposed a class my own audit **structurally could not see**, and a
ticket I closed yesterday is only half fixed.

## 1. The ten fixable tickets are three root causes, not ten edits

### (a) `SECTION_INTROS` is an English-only dict — #1216, #1219, #1220

`F1/generate_qsf.py` prepends `<p>{SECTION_INTROS[q]}</p>` to **every** locale block, so all
eight intros spill English into all seven languages. Cleared Bicolano exists for keys
1, 7, 9, 101, 118, 163 — e.g. key 7 → `Masunod mga kahapotan manungod sa health facility.`,
character-for-character what the tester quoted. Keys **51 and 135 stay English**: the
cleared Bicolano file has no translation for them either.

### (b) `INSTRUCTIONS` is an English-only dict — #1223, #1224, #1225

Same mechanism for the enumerator directives. **The notes are not interchangeable** — each
question has its own cleared wording, so store per question, and **keep the cleared source's
own typos** (`Bago p` in Q14, `PLION` in Q15) rather than silently correcting a cleared
instrument.

### (c) Translation-table key defects — #1218, #1227, #1231, #1233

- **#1218** — four fields drop the stem. *The tester's diagnosis is wrong*: missing numbering
  is not the cause (Q3/Q4 are numbered identically and translate fine). Same stem-dropping
  appears in BIS/CEB/WAR, with the inverse label-dropping in FIL/HIL.
- **#1227** — `Q18_HPU_ROLE_VS1` options 1–4 are byte-identical English copies; cleared
  Bicolano exists for all four. The ticket's attached image turned out to be a screenshot of
  the cleared questionnaire itself, matching `F1_BCL.txt` exactly.
- **#1231** — *the option is not missing.* Code 06 exists; `translations/bcl.json` holds a
  poisoned **unscoped** key that makes the tablet show two consecutive NBB rows:

  ```
  "YAKAP/Konsulta utilization reports"  ->  "NBB compliance NBB compliance"
  ```

  Verified directly in `bcl.json`. **Do not add a 13th code** — that would break the 12-code
  cleared value set and data comparability. This is the same corruption class as the 25
  values repaired on 2026-08-13, so **that sweep did not catch everything.**
- **#1233** — Q49 stem and options 01–08 render English because `bcl.json` keys them on
  *short* display labels that never match the long value-set labels in the `.dcf`, so the
  merge silently no-ops. Source the Bicolano from cleared `F1_BCL.txt`, **not** from the
  ticket's PNG (unread, non-authoritative). Sweep Q50 for the same mismatch.

## 2. The four that must NOT be actioned as written

### #1222 — "change all Bikol *No* to DAE" would fix 10 and break 26

`bcl.json` holds exactly **one** bare key `"No": "Dai"` shared by all 36 yes/no value sets,
so the literal request is a one-character flip.

- **Tester is right on 10** — cleared says `Dae`: Q9, Q10, Q16, Q35, Q138, Q139, Q141,
  Q145, Q148, Q150.
- **Tester is wrong on 26** — cleared says `Dai` and the tablet already matches: Q13, Q37,
  Q51, Q54, Q55, Q56, Q59, Q61, Q77, Q81, Q88, Q89, Q90, Q93, Q97, Q101, Q102, Q107, Q108,
  Q109, Q112, Q116, Q118, Q135, Q136, Q157.

The cleared F1 Bicolano corpus is itself mixed — **139 `Dai` / 65 `Dae`**. *The
inconsistency originates in the cleared source, not in the CAPI.* Fix per question on the
ten; reject the blanket.

### #1228 — the ticket supplies the wrong question's translation

Defect is real (Q27 renders English). But the Bicolano in the ticket is the cleared
translation of **item 25**, already live and correct there. Cause: the cleared Bicolano file
**duplicates item 25 at item 27** — so there is *no* cleared Bicolano stem anywhere for
"Has the increase in equipment been implemented…". **Leave Q27 on English fallback and ask
ASPSI for approved wording.** Inventing a stem or reusing Q25's is out of bounds.

### #1229 / #1230 — "DO THIS IN ALL QUESTIONS" cannot be honoured

The cleared source is not uniform across the Section-C option sets.

- **#1229** — apply to **20** questions (Q14, Q19, Q21, Q23, Q25, Q27, Q29, Q31, Q36,
  Q38–Q48). **Exclude Q12** (cleared already equals what the tablet shows) and **Q17**
  (cleared is a third variant matching neither side).
- **#1230** — apply to **19**. **Exclude Q12**, **Q17** (cleared differs only by a trailing
  period) and **Q21** (cleared drops `may` and `mga`).

Root cause: the build propagated **Q12's** wording to the other 21 questions instead of each
question's own cleared wording.

## 3. The blind spot the testers found — 299 screens my audit could not see

**#1216, #1219, #1220, #1223, #1224 and #1225 are not dictionary labels at all.** They are
hardcoded English constants in each `generate_qsf.py`, injected into the `.qsf` identically
for every language. They never enter the `.dcf`, which is what the verbatim audit compared —
so the audit reported them as fine.

| | section intros | screens with an instruction note | note identical in all 7 locales |
|---|---|---|---|
| F1 | 8 | 91 | **91** |
| F3 | 30 | 100 | **100** |
| F4 | 18 | 108 | **108** |

**299 question screens show an English-only note regardless of language — 2,093
respondent-facing renderings.** Generator work, not a translation-file change. The spill
affects FIL/BIS/CEB/WAR/HIL/ILO identically, so fixing F1 Bicolano alone closes only a
fraction.

## 4. A ticket I closed yesterday is only half fixed

**#1213 — F1 Q57 capitation.** Closed 2026-08-13. Bikol is correct and matches cleared.
**Filipino still renders English**, because its stored value was a corrupt fragment and I
dropped it to English fallback, flagging it for translators. The cleared June-5
questionnaire had the proper Filipino all along —
`Batay sa iyong kaalaman, Ano ang halaga ng capitation para sa YAKAP/Konsulta Package?…` —
I had simply not ingested the cleared source yet. It is now in `safe_to_apply.json`.
**Reopen, or file a follow-up.**

**#1182 — F3 Q45 capped labels.** Also half fixed. Filipino renders correctly now, but
**Hiligaynon is still truncated mid-sentence** at the 255-character dictionary cap:
`Ano nga kategorya sang myembro ikaw? READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY. ASKED ONLY FOR`
Keep open.

## 5. Defects found that no tester has reported

Testers are sweeping Bicolano F1, so these are unseen. All verified in the deployed build:

- **F3 Waray Q2 — HIGH.** `Q2_RELATIONSHIP` asks *"What is your relationship to the
  patient?"*, but Waray respondents are read *"Mayda ka ba ginbaydan nga iba pa nga gastos
  durante han imo kaconfine…"* — *"Did you pay any other expenses during your confinement
  not included in the hospital bill?"* **A different question entirely**, with the answer
  recorded against a relationship code.
- **F3 Bikol Q141 and Q142.** The Bikol slot holds an English *example* sentence
  (`For example, they did not disclose any of your private medical information…`) instead of
  the question. Cleared Bikol exists for both.
- **F3 Cebuano Q147.** Cebuano respondents see raw English
  (`PLEASE LIST DOWN ALL MEDICINES THAT YOU TOOK…`); cleared Cebuano exists.

### The #1231 corruption class is not confined to #1231 — HIGH severity

Re-scanning every locale file for the #1231 pattern (`scan_poisoned_keys.py`) found **39
suspect entries**. Five are the dangerous `DOUBLED` kind — a value that is *another
option's* label, repeated — and two are confirmed live and worse than #1231 because they
create a **duplicate visible row that silently records the wrong code**:

| instrument | item | option | renders as | consequence |
|---|---|---|---|---|
| F3 CEB | `Q52_PLANS` | `Pag-ibig` | **`SSS SSS`** | two identical "SSS" rows; picking the second records **Pag-ibig** |
| F4 BCL | `Q94_TRANSPORT` | `Public Bus` | **`Taxi Taxi`** | two identical "Taxi" rows; picking the first records **Public Bus** |

Both were verified in the deployed `.dcf`. Neither has been reported by a tester. The
remaining entries are milder: `IS_OTHER_KEY` (30) is mostly English stored explicitly as
its own "translation", `SELF_ECHO` (4) is case-only. Full list in `poisoned_keys.json`.

A vocabulary-overlap scan separately flagged **22** strings sharing almost no words with the
cleared text for the same question. Roughly half are genuine deployed defects like these; the
F4/Waray ones are my own positional-pairing artifact on the single monolingual source file,
already flagged `option_confidence: "positional"`.

## 6. For ASPSI — inconsistencies in the cleared source itself

- **#1228:** item 25 duplicated at item 27 in the cleared Bicolano; no approved wording
  exists for Q27. **Blocking.**
- The `Dai`/`Dae` split (#1222) and the three- and four-way Section-C option variants
  (#1229/#1230). Coding these per question is defensible and is the recommendation — but
  ASPSI should know **the tool will ship internally inconsistent Bicolano because the
  cleared questionnaire is.**

## Recommended disposition

1. **Generator fix (closes 6 tickets + 299 screens):** make `SECTION_INTROS` and
   `INSTRUCTIONS` locale-keyed in all three instruments.
2. **Translation-table fixes:** #1218, #1227, #1231 (delete the poisoned key), #1233.
3. **Per-question, not blanket:** #1222 (10 questions), #1229 (20), #1230 (19).
4. **Blocked on ASPSI:** #1228.
5. **Reopen #1213** (Filipino half); **keep #1182 open** (Hiligaynon truncation).
6. **File new — highest severity first:** F3 CEB `Q52_PLANS` and F4 BCL `Q94_TRANSPORT`
   (duplicate rows recording the wrong code), F3 WAR Q2 (wrong question shown),
   F3 BCL Q141/Q142, F3 CEB Q147.
7. **Re-scan done** — `scan_poisoned_keys.py`, 39 suspect entries in `poisoned_keys.json`.
   The 2026-08-13 sweep was incomplete; keep this scan in the release checks.

Every fix goes in the generator or the translation JSON — never by hand-editing
`.qsf` / `.dcf`.
