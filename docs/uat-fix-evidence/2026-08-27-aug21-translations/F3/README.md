# Aug-21 translations — F3 fix evidence (wave 4, v6.1.0 → v6.1.2)

**Driver:** ASPSI Aug-21 revised instruments (`raw/Survey-Instruments-2026-08-21`).
**Ships as:** Patient Survey (F3) **v6.1.2** — DEV channel, not the PSA submission set
(that stays frozen at tag `capi-psa-2026-08-20`).
**Deployed:** v6.1.0 at 2026-08-27 00:47 +08, v6.1.1 at 2026-08-27 08:38 +08,
**v6.1.2 at 2026-08-27 09:28 +08**, all to `capi.asiansocial.org/csweb/api`.

> **v6.1.2 is the shipped build** (v6.1.1 was superseded 50 minutes later — same words on
> the tablet, written instead of inherited; see the last section).
> **v6.1.1** repaired the row-inheritance defect class Task 48 traced
> to the papers' two-column option grids: 29 option labels across six locales that carried a
> NEIGHBOURING row's translation. The v6.1.0 material below is kept as the wave record; read
> the **v6.1.1 patch** and then the **v6.1.2 patch** section at the end first, and prefer the
> `-6.1.2` files (the `-6.1.1` ones stand where v6.1.2 did not re-measure them).

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
| `automation/scenarios/f3_aug21_bill_detail_hil.txt` **(new)** | `F3/PatientSurvey_desktest_HIL.pff` **(new)** — moved to `automation/scenarios/` in v6.1.1, paths rewired | HIL | ICF screen 1, Q66, 97.1 / 97.2 |

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

## Tablet pass — the DEPLOYED package on the `capi_tablet` AVD (Task 43)

The frames above are **desk** frames from the locally compiled build. The frames below come
from the package CSWeb actually serves: `PatientSurvey.zip` was pulled from
`/opt/app/lamp/www/csweb/files/apps/` (the same 1 720 407 bytes `byte-verify.txt` probed),
expanded, and `adb push`ed into
`/storage/emulated/0/Android/data/gov.census.cspro.csentry/files/csentry/PatientSurvey/`.

| | |
|---|---|
| served `.pen` md5 (from the pulled zip) | `2bf5dfdec6f104229afabce2c57d390e` |
| on-device `.pen` md5 (`adb shell md5sum`) | `2bf5dfdec6f104229afabce2c57d390e` — **identical**, so these frames are the deployed bytes |
| served `.pff` Description | `Patient Survey (F3) - v6.1.0 (2026-08-27) [DEV]` |
| case | a NEW throwaway case (`040340302001`, `RHU BINAN`, Outpatient) started after `am force-stop gov.census.cspro.csentry`; **never saved, never synced** — the emulator was killed with the case still open |

| file | what it shows |
|---|---|
| `00-app-list-f3-6.1.0.png` | CSEntry's app list on the AVD showing `Patient Survey (F3) - v6.1.0 (2026-08-27) [DEV]` beside the old `v3.1.11 (2026-08-17)` install — sideloaded from the DEPLOYED `PatientSurvey.zip` |
| `f3_q8_hil_tablet.png` | Q8 (`Q8_LGBTQIA`) in **Hiligaynon**: `Huo` / `Wala` / **`Not Comfortable to Answer` — English fallback, code 3** / `Wala kabalo` / `Nagbalibad sa pagsabat`. Four of the five options render Hiligaynon; code 3 is the one code the HIL write set did not carry, so the build correctly prints the English source (write-set table below) |
| `f3_q8_war_tablet.png` | Q8 in **Waray**: full stem `Nag-iidentify ba an pasyente komo parte han LGBTQIA+ community? …`, the directive `BASAHA HA MAKUSOG AN MGA OPSYON. PILI MA USA LA NA BATON`, and `Oo / Waray / Dire Komportable ha Pagbaton / Dire ako maaram / Pagdumiri pagbaton` |
| `f3_icf_hil_tablet.png` | ICF screen 1 (`ICF_PART1`) in **Hiligaynon** on the tablet — the consent prose *and* the `Translated Questionnaire ver. 08/21/2026` stamp in one frame (the tablet pane is tall enough, so the desk pass's two-frame split is not needed here) |
| `f3_icf_war_tablet.png` | the same screen in **Waray** — `Kumusta, an akon ngaran amo hi …`, same 08/21/2026 stamp |

### Why Q8 and not Q47 / 97.2 — substitution, stated

The tablet plan asked for Q47 and 97.2 in HIL and WAR. Both sit deep in the questionnaire
(Q47 ≈ 50 fields in, 97.2 ≈ 110). CSEntry on Android takes **no keyboard input on coded
fields** — every one needs a screenshot-guided tap on its radio row — and CSPro refuses a
**forward** jump in the case tree: tapping `38.` while sitting on Q10 returns
`WARNING: Out of range! Please enter a valid value for Q10_CIVIL_STATUS`. At the 30-minute
navigation cap (05:26 → 05:58 device clock) the walk had reached Q10, so the shots were taken
from the wave-changed keys that *were* reachable, per the standing rule. Backward tree jumps
**are** allowed, which is how Q8 and the ICF screens were revisited in each language.

The substitute is not arbitrary: `Q8_LGBTQIA`'s value set is wave-changed in **both** locales
in this wave's own applied write set,
`.superpowers/sdd/2026-08-25-aug21-translations/task-40/evidence/aug21_apply_diff_F3_applied.json`:

| locale | codes written this wave | what the frame shows |
|---|---|---|
| HIL | `val:Q8_LGBTQIA_VS1:` **1, 2, 4, 5** (not 3) | the four written options render Hiligaynon; code 3 correctly still prints the English `Not Comfortable to Answer` — the frame is a live confirmation of the write set, gap included |
| WAR | `val:Q8_LGBTQIA_VS1:` **2, 3, 4, 5** | all five options render Waray |

The two ICF frames are **supplementary**, not substitutes: `ICF_PART1` came from the ICF
import of Tasks 25/26 and is not in this wave's write set. They are kept because they are the
cheapest on-device proof that the deployed package carries per-language consent text and the
`08/21/2026` questionnaire stamp.

Q47's stem and 97.2 in both locales stay covered by this folder's **desk** frames
(`f3_q971_*.png`, `f3_q972_*.png`) and by `byte-verify.txt`, which probes the deployed `.pen`
byte-for-byte. `f3_q972_hil` was always going to render English anyway — see the gap table
above: `item:Q972_SOURCES` has no HIL value, an accepted hold.

#### Spec device-evidence item — status, for the controller

The plan's Verification item 3 (*device evidence from the deployed package*) is satisfied

- for the **package**: the app-list frame plus on-device `.pen` md5 == served, above; and
- for **two wave-changed keys per locale**: `val:Q8_LGBTQIA_VS1:*` in HIL and WAR.

It is **not** satisfied for the two keys the task named. **Q47 and 97.2 have no tablet frame
in any locale**; for those two keys the proof is the desk frames plus `byte-verify.txt`.
Standing rule (8) permits the substitution and it is recorded here, in the patch note
(`### Tablet pass (Task 43) — substitution deviation record`) and in `log.md`; **ratifying it,
or ordering a re-shoot, is the controller's call — this task does not close it.**

Cost of closing it: one AVD session of roughly 60–90 minutes of screenshot-guided tapping.
Q47 sits ~50 coded fields in and 97.2 ~110, and every coded field needs its own tap because
CSEntry on Android ignores hardware-keyboard input on them (text and numeric fields do accept
`adb shell input text`). The one idea that might have been cheaper — push a saved deep case to
the device, reopen it, and use the case tree, since the forward jump was refused only because
the intervening fields were unanswered — has **no starting material in-tree**: Task 41's
`F3/desktest_hil.csdb` and `F3/desktest_war.csdb` both hold **0 cases**
(`select count(*) from cases` = 0 on each), because those runs were killed before save.
Producing one means re-running the desk walk to a partial save first, and whether CSEntry then
allows the jump is itself untested.

### Rendering defects the tablet pass surfaced (pre-existing — no wave-4 write touched either key)

Both are **map-content** problems (not paper-side): the extract carried neighbouring text into
the value. They are visible on the tablet because it renders the same bytes as the desk build.
Both predate v6.1.0, on two independent checks:

- `aug21_apply_diff_F3_applied.json` has **no** `PATIENT_TYPE` / `Q7_SEX` key in any bucket
  (`writes`, `replaced`, `overridden`, `unmatched`, `flagged_skipped`, `already_same`) of any
  of the seven locale blocks; and
- the values are byte-identical to the pre-wave maps in
  `.superpowers/sdd/2026-08-25-aug21-translations/task-40/before/deliverables/CSPro/F3/translations/`.

**`PATIENT_TYPE` is not a Hiligaynon-only problem.** The HIL pair is what made it visible — it
was seen on the AVD during the Task-43 walk, at the case's Outpatient selection; **no committed
frame in this folder shows that screen**, so the table below is read off the build, not off a
picture. The per-locale check that followed the sighting found the same class in **six of the
seven** locales. Every string below is in the DEPLOYED package: read out of
`F3/PatientSurvey.dcf` and confirmed present in the served `.pen` (bz2-decompressed, UTF-16LE
`bytes.find`, the same 1 720 407-byte zip `byte-verify.txt` probed):

| locale | code 1 (English `Outpatient`) | code 2 (English `Inpatient`) |
|---|---|---|
| FIL | `mentioned facility)` | `visit ng pasyente` |
| BCL | `mentioned facility)` | English fallback (`Inpatient`) |
| BIS | `mentioned facility)` | `visit sa pasyente` |
| CEB | `mentioned facility)` | English fallback (`Inpatient`) |
| WAR | English fallback (`Outpatient`) | English fallback (`Inpatient`) |
| **HIL** | **`nga serbisyo`** | **`kag`** |
| ILO | `mentioned facility)` | `This section is for respondents in` |

Why this one is the serious one: `PATIENT_TYPE` **routes the whole case** — Outpatient sends it
through Section G, Inpatient through Section H — so an enumerator working in any language but
Waray is choosing between two fragments on a field that decides the rest of the interview. No
data is corrupted (the stored codes are 1 / 2 and the routing logic is untouched; the field label
itself, `item:PATIENT_TYPE`, is English everywhere except WAR), but it is the most user-visible
string defect in the build, so it is called out in the patch note's Slack block as well as in its
findings list.

`item:Q7_SEX` is HIL-only: it renders `your Ano ang sekswalidad sang pasiente sang pagkabata?` —
an English anchor head (`your`) left on the front of the value. The other six locales are clean.

Remediation is deliberately **not** a Task-43 change (this task writes evidence, and the wave's
apply is closed — wave rule 2 forbids a `remediate_scan --write` after an apply). The sanctioned
route is a locale-scoped `keep: null` in `data/translations-official/aug21-overrides.json` for
`val:PATIENT_TYPE_VS1:1` / `:2` in the six locales and for `item:Q7_SEX` in HIL — `keep:null`
never writes, so the build falls back to the English `Outpatient` / `Inpatient`, which is strictly
better than a fragment — plus an extractor rule so the next extract cannot re-introduce them.
Neither key is in the Q47 / 97.x / 115.x set this wave was about; both are recorded here, in the
patch note and in `log.md` for Task 45's worklist.


---

# v6.1.1 patch — the row-inheritance repair (2026-08-27 08:38 +08)

**What it is.** Task 48 measured that several Aug-21 papers lay an option grid out in two
columns, so `pdf_text()` returns both boxed ENGLISH rows first and both translations after
them as one block. The first row's span is then box-to-box and therefore empty, and the whole
block falls to the second row — one option ends up carrying its neighbour's translation. The
extractor now HOLDS those rows (`sibling-run` / `duplicate-label`) and `apply_aug21.py` carries
a permanent gate, but neither repairs what is already on a tablet. This build does.

The seven Cebuano `*_SOURCE_VS1` questions are the headline case: `F3_CEB.txt` prints

```
☐ Legislation
☐ LGU/ Barangay
Balaod
LGU/Barangay
```

`LGU/ Barangay` is a proper noun the paper leaves untranslated, so the anchor matches its own
echo, the span for code 06 is bounded to code 02's `Balaod`, and **v6.1.0 shipped `Balaod`
("Legislation") on the LGU/Barangay option of all seven questions**.

## The 29 rows, by locale

| locale | rows | keys |
|---|---|---|
| CEB | 8 | `val:Q{36_UHC,75_KON,100_BUCAS,117_NBB,120_ZBB,125_MAIFIP,153_GAMOT}_SOURCE_VS1:06` (was `Balaod`) + `val:Q10_CIVIL_STATUS_VS1:6` (was `Bulag sa kapikas` = Separated's text) |
| BCL | 9 + 1 | `Q2_RELATIONSHIP_VS1:02,03` (`Aki`), `:08,09` (`Apo`), `:16,17` (`Pamangkin`), `Q10_CIVIL_STATUS_VS1:6` (`Hiwalay`), `Q98_PAY_SRC_VS1:15` / `Q113_PAY_SRC_VS1:13` (`Iba pa (ispecify)`); **and `Q10_CIVIL_STATUS_VS1:5` CORRECTED** `Diborsyado` → `Live-in` |
| HIL | 5 | `Q34_WHO_DECIDES_VS1:08,09,10` (all read `Tatay sang Pasyente` = the patient's FATHER), `Q10_CIVIL_STATUS_VS1:2` (`Kasado`), `:4` (`Balo`) |
| WAR | 2 | `Q10_CIVIL_STATUS_VS1:2` (`Minyo`), `:6` (`Nagbulag`) |
| FIL | 2 | `Q38_2_WHY_NOT_REG_VS1:02,03` (both `[Mahirap magparehistro]` = code 01's text) |
| BIS | 1 | `Q10_CIVIL_STATUS_VS1:6` (`Separada/Separado`) |
| ILO | 1 | `Q38_2_WHY_NOT_REG_VS1:08` (`Awan ti oras nga agparehistro` = code 07's text) |

28 of the 29 are **deletions**: the Aug-21 paper carries no distinct translation for the row,
so the key is removed from the map and CSEntry renders the **English** option label. An English
option beats a wrong one, and a wrong one here means two options a respondent cannot tell apart.
The 29th is the Bikol `Common law / Live-in` correction — `F3_BCL.txt` line 377 prints
`☐ Common law / Live-in Live-in`, and the hold that had suppressed it was the direct cause of
two duplicate rows.

**Superseded by v6.1.2 — see the last section of this file.** The seven CEB `:06` rows were
deleted rather than written with the paper's own `LGU/Barangay`, for a measured reason: that string **is** the English label, so writing it grows the
poisoned-key scan's `SELF_ECHO` reason by 6 (and `IS_OTHER_EN` by 1 — Q36's English carries a
stray space, `LGU/ Barangay`) and `run_aug21_gates.ps1` gate 1 fails. Deleting renders the same
text from the dictionary and leaves the gap honestly on the translator worklist.

## Proof

| | |
|---|---|
| package | `PatientSurvey.zip` 1 720 432 bytes, md5 `ea467e2bf1e14306c751745f52a0087a`, server mtime 2026-08-27 00:38:03 UTC = **08:38:03 +08** |
| served `.pff` Description | `Patient Survey (F3) - v6.1.1 (2026-08-27) [DEV]` |
| deploy dialog | `Application Deployed Successfully` — `00-deploy-result-6.1.1.png` |
| byte-verify | `byte-verify-6.1.1.txt` — **RESULT: ALL PASS**, exit 0 |
| per-code proof | `dcf-removal-proof-6.1.1.txt` — **BUILT-DICTIONARY RESULT: ALL PASS** |
| device | `01-app-list-v6.1.1.png`; on-device `.pen` md5 `0b1826681b4a2f00dbe19fa48816abea` == the `.pen` inside the served zip == `package.json`'s signature. No case opened, nothing synced |

### Why there is a second proof file

The `.pen`'s string table is **pooled**, so a `--count` is a per-LANGUAGE fact, not a per-code
one: 14 map keys still carry `Balaod` (7 BIS + 7 CEB, all on code 02, where it is correct) and
the pen holds **2**. A `--count "Balaod" 0` would therefore be a lie, and a `7` would be a
different lie. `dcf-removal-proof-6.1.1.txt` gives the per-CODE evidence instead, over the
`PatientSurvey.dcf` Designer compiled this `.pen` from: every removed row's locale label **is**
the English label, every kept sibling still carries its own translation, and **no value set, in
any of the eight languages, has two codes with the same label** (213 value sets × 8).

`byte-verify-6.1.1.txt` carries `--baseline` against the **pre-wave** maps
(`git show HEAD:F3/translations/*.json`), not against v6.1.0: the tool fails unless every locale
has ≥1 wave-changed probe **present**, and 28 of this patch's 29 rows are deletions, which cannot
be present. Its four counts are all measured off this served pen —
`Balaod` 2×, `LGU/Barangay` 7×, `[Mahirap magparehistro]` **0×** (the one true discriminator:
v6.1.0 shipped it, this build does not) and `Live-in` 3×. The two `--probe` rows on the CEB
`*_SOURCE_VS1:06` keys come back `SKIP … (no map value - English fallback)`, which is precisely
the intended post-removal state.

## Coverage (v6.1.0 → v6.1.1)

Translated labels in the built `.dcf` (a label that equals its English is not counted):

| locale | v6.1.0 | v6.1.1 | delta |
|---|---|---|---|
| FIL | 1310 | 1308 | −2 |
| BCL | 1166 | 1157 | −9 |
| BIS | 1198 | 1197 | −1 |
| CEB | 1255 | 1247 | −8 |
| WAR | 1265 | 1263 | −2 |
| HIL | 1015 | 1010 | −5 |
| ILO | 1215 | 1214 | −1 |
| **total** | **8424** | **8396** | **−28** |

Exactly the 28 deleted rows and nothing else — coverage falls **on purpose**, because those
rows were rendering another option's words.

## Known, and on the translator worklist

* **Bikol `Aki` / `Apo` / `Pamangkin`** are the correct Bikol words for *child*, *grandchild*
  and *nephew-or-niece*; Bikol has no gendered term, so the paper prints one string against
  both rows. Both rows now render English until a translator supplies `Aki (lalaki)` /
  `Aki (babae)`.
* **Cebuano `Annulled` has a real span the schema could not take.** `F3_CEB.txt:428` prints
  `Annulled / gipa-walay bisa ang kasal`, but `val:Q10_CIVIL_STATUS_VS1:6` needs a REMOVAL in
  BCL/BIS/WAR and a KEEP in CEB, and `aug21-overrides.json` allows one entry per key. CEB is
  removed with the other three; the span is a worklist item.
* **`PATIENT_TYPE` and HIL `item:Q7_SEX`** (the v6.1.0 section above) are a different class —
  dangling tails, not row inheritance — and are **not** fixed here.


---

# v6.1.2 patch — the seven Cebuano `LGU/Barangay` rows are WRITTEN (2026-08-27 09:28 +08)

**Why.** Controller ruling 2026-08-27 06:30 (b) said those seven rows must **write** the paper's
`LGU/Barangay`. v6.1.1 deleted the keys instead, so the English label rendered the same words —
the right text by an unauthorised mechanism, and the review flagged it. The blocker was real:
writing a value that equals an English label grows `scan_poisoned_keys.py`'s `SELF_ECHO` (and
`IS_OTHER_EN` on Q36, whose English carries a stray space, `LGU/ Barangay`), and gate 1 of
`run_aug21_gates.ps1` refuses the wave when a reason grows.

**What changed in the tooling.** `scan_poisoned_keys.py` gained a reasoned, per-key,
**value-pinned** waiver file — `data/translations-official/scan_waivers.json` — restricted by its
validator to `SELF_ECHO` / `IS_OTHER_EN`; every other detector (`DOUBLED`, `EN_FRAGMENT`,
`WRONG_Q_CLEARED`, `GLUED_CLEARED`, `STALE_KEY`) is a corruption class and can never be waived.
Each entry names the map value it covers and cites the paper line, so a value that drifts off the
paper is flagged again. Waived rows print under `--- waived ---` on every scan (the gate script
echoes them), and a waiver that covers nothing prints as `STALE WAIVER`. The file ships with
**exactly seven** entries, all F3/ceb.

**What changed in the build.** The whole F3 wave was re-applied from the proven pre-wave baseline
with the seven overrides flipped from `remove: true` back to `keep: "LGU/Barangay"`. The delta
against the live v6.1.1 maps is **7 rows in one locale and nothing else**.

| | |
|---|---|
| package | `PatientSurvey.zip` 1 720 219 bytes, md5 `21fb4b31528c5dee09e76362926999d3`, server mtime 2026-08-27 01:28:28 UTC = **09:28:28 +08** |
| served `.pff` Description | `Patient Survey (F3) - v6.1.2 (2026-08-27) [DEV]` |
| compile | `Compile Successful at 09:25:52` — `02-compile-successful-6.1.2.png` |
| deploy dialog | `Application Deployed Successfully` — `00-deploy-result-6.1.2.png` |
| byte-verify | `byte-verify-6.1.2.txt` — **RESULT: ALL PASS**, exit 0. The two CEB probes now read `OK CEB val:Q36_UHC_SOURCE_VS1:06 [wave-changed]: 'LGU/Barangay'` (they were `SKIP … English fallback` in v6.1.1) |
| per-code proof | `dcf-label-proof-6.1.2.txt` — **BUILT-DICTIONARY RESULT: ALL PASS**: the 21 removed rows still render English, the seven written rows carry `LGU/Barangay`, every kept sibling keeps its translation, and no value set in any of the eight languages has two codes with the same label (213 × 8) |
| device | `01-app-list-v6.1.2.png` — `Patient Survey (F3) - v6.1.2 (2026-08-27) [DEV]`; on-device `.pen` md5 `44c59760fcc86d6dbec815524ceed55e` == the `.pen` inside the served zip == `package.json`'s signature. No case opened, nothing synced |

**Coverage** (built `.dcf`, a label equal to its English is not counted): CEB **1247 → 1248**,
every other locale unchanged, total **8396 → 8397**. Only Q36 moves the number, because on the
other six questions the paper's Cebuano and the English are the same string — which is the whole
reason this row needed a waiver rather than an ordinary import.

**A `--count` note that is easy to misread.** `LGU/Barangay` occurs **1×** in the v6.1.2 `.pen`
and occurred 7× in v6.1.1's. Nothing was lost: the `.pen` pools its string table, and the count
is a per-LANGUAGE/pool fact, not a per-code one. The distinct-string set of the two pens is
identical (4 256 strings each) apart from the cover-image blob that carries the version stamp;
the seven per-code labels are proven in `dcf-label-proof-6.1.2.txt`, over the very `.dcf`
Designer compiled this `.pen` from.
