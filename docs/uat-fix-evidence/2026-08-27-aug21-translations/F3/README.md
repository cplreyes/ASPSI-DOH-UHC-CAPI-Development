# Aug-21 translations — F3 fix evidence (wave 4, v6.1.0)

**Driver:** ASPSI Aug-21 revised instruments (`raw/Survey-Instruments-2026-08-21`).
**Ships as:** Patient Survey (F3) v6.1.0 — DEV channel, not the PSA submission set
(that stays frozen at tag `capi-psa-2026-08-20`).
**Deployed:** 2026-08-27 00:47 +08 to `capi.asiansocial.org/csweb/api`.

> The desk frames below were taken 2026-08-26 23:28–23:54 +08, four minutes before
> midnight; the deploy landed after it. The folder is dated from `versions.json` `F3.date`,
> which is the deploy date — hence desk frames dated the 26th inside a folder dated the 27th.

**What changed:** Q47/Q69/Q94/Q96/Q98 stems and the 97.2 / 115.1 / 115.2 labels aligned to
the Aug-21 paper (**no answer code changed** — MINOR, not a data-shape break); the
Hiligaynon/Ilocano facility-name dialect phrase; the Aug-21 translations imported for all
seven locales; consent screens and section intros per language.

## Deploy record

| | |
|---|---|
| package | `PatientSurvey.zip` → `/opt/app/lamp/www/csweb/files/apps/` (1 720 407 bytes) |
| members | `PatientSurvey.pen`, `PatientSurvey.pff`, `package.csds`, `package.json`, and all **8** `psgc_*.{dcf,dat}` |
| served `.pff` Description | `Patient Survey (F3) - v6.1.0 (2026-08-27) [DEV]` |
| deploy dialog | `Application Deployed Successfully` — `00-deploy-result.png` |
| byte-verify | `RESULT: ALL PASS`, exit 0 — `byte-verify.txt` |

The CSDeploy dialog's own Description field is blank **by design**, so it is not version
proof; the served `.pff` line above is, together with the `v6.1.0` footer probe in
`byte-verify.txt`. The CSEntry app-list shot and the on-device `.pen` md5 come from the
tablet pass (task 43).

### How to read `byte-verify.txt`

The run carried `--baseline` (the pre-wave maps from task 40) so every probe is labelled
`[wave-changed]` or `[unchanged-since-baseline]`, and it fails unless **every** locale has at
least one wave-changed probe present in the served package — all seven do. Two probes were
added on top of `PROBE_KEYS['F3']` because the fix-round-1 holds left `item:Q972_SOURCES`
absent in CEB and HIL: `item:Q98_SOURCES` and `val:Q107_SOURCES_VS1:05`, both wave-changed in
all seven.

Rows marked `[dcf-rendered]` are probed through the instrument's own #714 pass: those map
values hold the source-side `[facility_name_input]` token, which `generate_dcf.py` rewrites to
a per-language neutral noun-phrase before the label reaches the package, so the literal map
bytes are never in the `.pen`. `SKIP` means the map has no value for that locale — the build
prints the English source, which is the accepted hold described further down, not a miss.

## What the desk frames are, and what they are NOT

These are **desk frames from Windows CSEntry 8.0**, driven by `automation/csentry_runner.py`
against the local `PatientSurvey.ent`. They prove that the Aug-21 maps and the per-language
consent block **render** in the rebuilt application. They are **not** device evidence and
they are **not** version proof: the build was not published when they were taken. Version
proof is the **Deploy record** above; device proof is task 43's.

## How the walk was driven

| scenario | pff | locale | reaches |
|---|---|---|---|
| `automation/scenarios/f3_aug21_bill_detail_war.txt` | `F3/PatientSurvey_WAR.pff` | WAR | Outpatient walk → 97.1 / 97.2 |
| `automation/scenarios/f3_aug21_bill_detail_war_ip.txt` | `F3/PatientSurvey_WAR.pff` | WAR | Inpatient walk → 115.1 / 115.2 |
| `automation/scenarios/f3_aug21_bill_detail_hil.txt` **(new)** | `F3/PatientSurvey_desktest_HIL.pff` **(new)** | HIL | ICF screen 1, Q66, 97.1 / 97.2 |

97.x and 115.x cannot share one walk: `Q88_OUTPATIENT_GATE` sends an Inpatient case past the
whole of Section G, and `Q105_REASON` sends an Outpatient case past the whole of Section H.
HIL was chosen because it is the locale with the **lowest** coverage — the hardest case.

## Files

| file | what it shows |
|---|---|
| `00-deploy-result.png` | the CSDeploy dialog for package `PatientSurvey` on `capi.asiansocial.org/csweb/api`, showing `Application Deployed Successfully` and the added PSGC files |
| `byte-verify.txt` | the deployed `.pen` probed for map values (utf-16-le `bytes.find`, `aug17-tools/byte_verify_aug21.py`), the `v6.1.0` footer, an English/dialect-phrase probe, and the served `.pff` Description |
| `f3_q971_war.png` | 97.1 stem **and** its option list in Waray. Field `Q971_SOURCES` |
| `f3_q972_war.png` | 97.2 stem **and** options 01–06 in Waray. Field `Q972_SOURCES` |
| `f3_q1151_war.png` | 115.1 row 1 (`Q1141_1`) — **stem still English**, Yes/No value set in Waray (`Oo` / `Waray`) |
| `f3_q1152_war.png` | 115.2 stem in Waray (`Q1142_HAS_OTHER`), Yes/No value set in Waray |
| `f3_q971_hil.png` | 97.1 stem **and** options in Hiligaynon. Field `Q971_SOURCES` |
| `f3_q972_hil.png` | 97.2 in Hiligaynon **— stem falls back to English** (see the gap table). Kept because it is the honest picture of HIL, the lowest-coverage locale |
| `f3_q66_hil.png` | Q66 in Hiligaynon with the `~~FACILITY_NAME~~` fill resolved to the typed facility (`RHU BINAN`). Field `Q66_SAME_AS_USUAL` |
| `f3_icf_hil.png` | Informed-consent screen 1 (`ICF_PART1`) — the Hiligaynon consent prose |
| `f3_icf_hil_stamp.png` | the same screen scrolled to its footer: `SJREB: ICF ver. 07/25/2026 · Translated Questionnaire ver. 08/21/2026` |

Two ICF frames, not one: CSEntry's question-text pane is two lines tall and **opens on the DOH
banner image** that heads the consent HTML, so the prose and the version stamp cannot be in the
same frame. The scenario scrolls the pane (4 clicks → prose, 6 more → stamp) and then clicks the
entry box to hand keyboard focus back to data entry before typing.

## What the frames prove, string by string

| key | locale | on screen | source |
|---|---|---|---|
| `item:Q971_SOURCES` | WAR | `Labot la han mga gastos ha igbaw (e.g. konsultasyon, …)` | Aug-21 Waray paper |
| `val:Q971_SOURCES_VS1:01` | WAR | `Bayad han Doktor` | Aug-21 Waray paper |
| `val:Q971_SOURCES_VS1:90` | WAR | `Waray` (= "none") | Aug-21 Waray paper |
| `item:Q972_SOURCES` | WAR | `May iba pa ba kamo nga ginbaydan han iyo pagbisita ha OPD …` | Aug-21 Waray paper |
| `item:Q1142_HAS_OTHER` | WAR | `Mayda ka ba ginbaydan nga iba pa nga gastos durante han imo kaconfine …` | Aug-21 Waray paper |
| `val:Q1141_*_VS1:1/2` | WAR | `Oo` / `Waray` | Aug-21 Waray paper |
| `item:Q971_SOURCES` | HIL | `Luwas sa mga gastusin nga nalista sa ibabaw (e.g. konsulta, …)` | Aug-21 Hiligaynon paper |
| `val:Q971_SOURCES_VS1:01` | HIL | `Propesyonal nga Bayad sang Doktor` | Aug-21 Hiligaynon paper |
| `item:Q66_SAME_AS_USUAL` | HIL | `Ang RHU BINAN bala ang pasilidad nga ginakadtuan mo kasagaran para sa pangkalahatan nga kahimsog?` | Aug-21 Hiligaynon paper + `_pipe_fills` |
| `icf.json` HIL | HIL | `Maayong adlaw. Ako si (ngalan sang data collector), kag nagaubra sa Asian Social Project Services, Inc. (ASPSI)…` | Aug-21 Hiligaynon ICF |

The Q66 frame is the one to look at twice: the **question text** (`.qsf`) carries the full
Hiligaynon stem *with* the facility name piped in, while the **field label** (`.dcf`, shown in the
small popup) reads `Ang ini nga pasilidad bala ang pasilidad n…` — the neutralised
`_FACILITY_NEUTRAL` phrase. Both are Hiligaynon; they differ by design, not by defect.

## Coverage, measured before and after with the generator's own counts

`generate_dcf.py` / `generate_qsf.py` print `{CODE}: {matched}/{total} labels translated ({pct}%)`.

| locale | before (pre-wave tree) | after (this build) | delta |
|---|---|---|---|
| FIL | 1064/1749 (60%) | 1307/1749 (74%) | +243 |
| BCL | 942/1749 (53%) | 1163/1749 (66%) | +221 |
| BIS | 963/1749 (55%) | 1195/1749 (68%) | +232 |
| CEB | 1030/1749 (58%) | 1253/1749 (71%) | +223 |
| WAR | 1004/1749 (57%) | 1262/1749 (72%) | +258 |
| **HIL** | **757/1749 (43%)** | **1012/1749 (57%)** | **+255** |
| ILO | 925/1749 (52%) | 1212/1749 (69%) | +287 |

## Coverage gaps these frames make visible (paper-side, not build-side)

Every row below is a key with **no value in the map** for that locale, so the build correctly
prints the English source. None is a key mismatch: `aug21_apply_diff.json[F3][war|hil].unmatched`
contains no `Q1141_*` / `Q1142_*` / `Q97x` entry (its only bill-detail row is
`record:Q972_PAY_ROSTER`, a record name that has no paper counterpart by design).

| key | missing in | extractor flag that held it | what renders instead |
|---|---|---|---|
| `item:Q1141_1`…`Q1141_3`, `Q1141_5`, `Q1141_6`, `Q1141_NONE`, `item:Q1142_1`…`Q1142_5`, `Q1142_7` (12 keys) | **all 7 locales** | `not-in-paper` (candidate text: none) | the English 115.x row stems. Only the Yes/No value sets are translated |
| `item:Q1141_4`, `item:Q1142_6` | **all 7 locales** | `label-condensed` | the English 115.x row stems |
| `item:Q1142_HAS_OTHER` | BCL, CEB, HIL (present in FIL/BIS/WAR/ILO) | `contains-other-label` (BCL), `empty` (CEB, HIL) | the English 115.2 gate stem |
| `item:Q972_SOURCES` | HIL (present in WAR) | `empty` | the English 97.2 stem |
| `val:Q972_SOURCES_VS1:03` | HIL | `empty` | the English option, **including its paper letter**: `c) Medical equipment or supplies` |
| `val:Q972_SOURCES_VS1:90` | WAR and HIL | `length-ratio` + `local-directive` | `No, did not pay for any other expenses` |

**These gaps are an accepted hold, decided — not an open question.** v6.1.0 knowingly ships the
115.1/115.2 **row labels** in English in all seven locales (their Yes/No value sets *are*
translated), and the 115.2 gate stem in English in BCL/CEB/HIL. The sanctioned way to close a
flagged key is an `aug21-overrides.json` entry (`keep` = the accepted text), and it was measured
against every one of these keys before the hold was accepted: of the **101 gap cells**, **95 have
no candidate text at all** (the Aug-21 papers print the 115.x matrix rows only in the English
column) and the **6 that do have text carry the wrong string** — `item:Q1141_4`'s candidate is the
matrix's own header with the 115.1-amount question glued on, and BCL's `item:Q1142_HAS_OTHER` says
*outpatient* bill in an inpatient question. Writing a value for any of them would be authoring a
translation, which is Task 45's job. Every key is already in `out-aug21/F3/{loc}_flagged.json`
under the flag named above, which is the corpus Task 45 exports as the translator worklist. The
full reasoning and the measurement are in
`deliverables/CSPro/patch-notes/draft-f3-v6.1.0-aug21-translations.md`, section
`### Coverage hold ACCEPTED`; the invariant "a 115.x gap is never silent" is pinned by
`F3/test_aug21_labels.py::test_115x_row_label_gaps_reach_the_task45_worklist`.

`f3_q1151_war.png` and `f3_q972_hil.png` are in this folder **because** of that hold: they are the
two frames where the accepted English fallback is visible, kept rather than substituted with a
prettier screen.

The `c)` in that one option is the **English** label: the Aug-21 English 97.2 letters its options
`a)`–`f)` and the English alignment kept the letters, so a locale that has no value for one option
shows a lettered line among unlettered translated ones. That is an English-side convention from the
alignment tasks, not something this wave introduced; it is flagged here because the frame shows it.
