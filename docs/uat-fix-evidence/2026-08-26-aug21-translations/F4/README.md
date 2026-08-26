# Aug-21 translations — F4 fix evidence (wave 3, v3.2.3)

**Driver:** ASPSI Aug-21 revised instruments (raw/Survey-Instruments-2026-08-21).
**Ships as:** Household Survey (F4) v3.2.3 (2026-08-27) — DEV channel, not the PSA submission set
(that stays frozen at tag `capi-psa-2026-08-20`).

**What changed in this wave:** English aligned to the Aug-21 paper; printed gates rendered as
on-screen instruction notes; 7-locale Aug-21 translation import. Two extractor defects were then
patched on top of v3.2.0, each with its own re-publish:

* **v3.2.1** (Task 32b) — 154 WARAY values had been prefixed with the paper's question number
  (7 of them with the *wrong* number).
* **v3.2.2** (Task 33b) — 459 FILIPINO values had been wrapped in the Tagalog paper's square-bracket
  gloss delimiter (`[Lalaki]`). Fixed at the extractor; the folder's earlier "OPEN QUESTION" section
  is now the **Resolved** section below.
* **v3.2.3** (Task 49) — 13 option rows had silently inherited a NEIGHBOURING row's translation, so
  two codes of one value set read identically on the tablet. See *The row-inheritance repair* below.

**Package proven (v3.2.3):** `/opt/app/lamp/www/csweb/files/apps/HouseholdSurvey.zip` md5
`a56f24ab7d797dc005b3322765bd5e23`, 1,672,171 bytes, server mtime 2026-08-26 23:10:37 UTC =
2026-08-27 07:10:37 +08. The `HouseholdSurvey.pen` **on the device** md5
`2533a62a2ec1efe1f14638ea5395a014` — byte-identical to the `.pen` inside that served zip — and the
on-device `.pff` reads `Description=Household Survey (F4) - v3.2.3 (2026-08-27) [DEV]`. So the app
list below is the deployed package, not a local build.

**Package proven (v3.2.2, superseded):** served zip md5 `cc7da0badd868e4f24505899104b3df0`
(server mtime 2026-08-26 10:17:36 UTC = 18:17:36 +08); device pen md5
`ceb1133667e861f03e556443167f4ac4`, equal to the one inside that zip.

## Files

| file | what it shows |
|---|---|
| `00-deploy-result.png`, `00-deploy-result-3.2.1.png`, `00-deploy-result-3.2.2.png` | CSPro **Deploy Application** dialog — `Application Deployed Successfully` — from the v3.2.0, v3.2.1 and v3.2.2 publish runs respectively. **All three are byte-identical** (md5 `4fc57525a8d70801955919f0d924d2dc`) because the dialog's `Description` field is empty: nothing on screen names a version. They prove *a* deploy succeeded, nothing more. What proves **v3.2.2** is `00-app-list-f4-3.2.2.png` (the on-device version stamp) plus `byte-verify-3.2.2.txt` (the served package) |
| `00-app-list-f4-3.2.2.png` | CSEntry app list with the `Household Survey (F4) - v3.2.2 (2026-08-26) [DEV]` stamp |
| `00-app-list-f4-3.2.1.png` | the same list on the superseded v3.2.1 build (kept as the Task-33 record) |
| `f4_q2_1_age_fil.png` | **v3.2.2 capture.** Q2.1 **and** the Q3 option list in Filipino — the bracket fix on screen |
| `f4_q2_1_age_en.png` | Q2.1 + Q3 in English (baseline for the locale shots) — **v3.2.1 capture**, still valid: neither the English labels nor `ceb.json` changed between 3.2.1 and 3.2.2 |
| `f4_q2_1_age_ceb.png` | the same frame in Cebuano — **v3.2.1 capture**, valid for the same reason (`ceb.json` is byte-identical in both builds) |
| `byte-verify.txt` | v3.2.0 byte-verify (utf-16-le `bytes.find`, `aug17-tools/byte_verify_aug21.py`) |
| `byte-verify-3.2.1.txt` | v3.2.1 byte-verify with `--baseline` + wave-changed probes |
| `byte-verify-3.2.2.txt` | v3.2.2 byte-verify — `RESULT: ALL PASS`, exit 0 |
| `00-app-list-f4-3.2.3.png` | CSEntry app list with the `Household Survey (F4) - v3.2.3 (2026-08-27) [DEV]` stamp |
| `00-deploy-result-3.2.3.png` | the v3.2.3 publish run's `Application Deployed Successfully` dialog — **byte-identical to the three before it** (md5 `4fc57525a8d70801955919f0d924d2dc`), for the same reason: the dialog names no version |
| `byte-verify-3.2.3.txt` | v3.2.3 byte-verify — `RESULT: ALL PASS`, exit 0, including 12 `--count` assertions |
| `dcf-removal-proof-3.2.3.txt` | the half a byte count cannot do: every removed row's WAR/FIL/ILO label in the built dictionary IS the English label, every kept sibling still carries its translation, and no value set in any of the seven languages has two codes with the same label |

## The row-inheritance repair (v3.2.3, Task 49)

The whole-branch review found a defect the per-task reviews structurally could not see: an option
row that silently carries a NEIGHBOURING row's translation is well-formed and in the right language,
so no flag fires — but two codes of one value set then read **identically on the tablet**, and the
analyst cannot tell the two answers apart afterwards.

Two mechanisms, both read off the papers (`task-48-report.md` §2): the paper lays an option grid out
in two columns, so one row's span comes back empty and the block falls to its neighbour; and the
paper itself repeats one translation against two or three English rows.

`anchor_extract.py` now holds such a row instead of writing it, and `apply_aug21.py` carries a
permanent `duplicate-label` gate over the map an apply WOULD leave behind (the only place both sides
of a collision are visible). That stops the class coming back — it cannot repair what is already on
disk, and for these 13 rows the paper carries no distinct translation at all. The honest outcome is
therefore to leave the row **untranslated**: a new `remove: true` override deletes the map entry and
the English label renders. An English option label beats a wrong one.

| locale | row | read on v3.2.2 | reads on v3.2.3 |
|---|---|---|---|
| FIL | `val:Q45_2_WHY_NOT_REG_VS1:02/:03` | `Mahirap magparehistro` (code 01's text) | English `Don't see value in registering` / `Don't know how to register` |
| ILO | `val:Q45_2_WHY_NOT_REG_VS1:08` | `Awan ti oras nga agparehistro` (code 07's text) | English `No valid ID to register` |
| WAR | `val:Q128_NBB_UNDERSTAND_VS1:05`, `val:Q134_ZBB_UNDERSTAND_VS1:05` | `Mababayaran han PhilHealth an gastos han pagtambal` (code 03's text) | English `Medicine and service are already included` |
| WAR | `val:Q13_INCOME_SOURCE_VS1:02` | `Pagtrabaho ha gobyerno` = *working for government* (code 03's text) | English `Working for private household` |
| WAR | `val:Q{52,55,58,70,127,133,137}_*_SOURCE_VS1:06` (7 rows) | `Balaud` = *legislation* (code 02's text) | English `LGU/Barangay` — which is what the Waray paper itself prints |

The code whose English the text actually translates **keeps** it: FIL `:01` `Mahirap magparehistro`,
ILO `:07` `Awan ti oras nga agparehistro`, WAR `:03` `Mababayaran han PhilHealth an gastos han
pagtambal`, WAR `Q13:03` `Pagtrabaho ha gobyerno`, WAR `*_SOURCE_VS1:02` `Balaud`. Each is expressed
as a `keep` override on the flagged span, never as a hand edit of a map.

**Why the byte-verify counts read `1x` and not `7x`.** The `.pen`'s string table is pooled: `Balaud`
sits on seven WAR value sets and occurs **once** in the served pen. A row-inheritance repair is
therefore invisible to a substring count whenever the wrong string was a neighbour's correct one —
which is every row above. `dcf-removal-proof-3.2.3.txt` is the structural half of the proof, and the
seven `0x` counts in `byte-verify-3.2.3.txt` are the discriminators: five are v3.2.2 values that
this build removes or reverts, and two are the superseded version stamps.

**No case was opened on v3.2.3.** The app-list shot plus the on-device `.pen` md5 (equal to the
served one) and the `.pff` Description are the device evidence; the per-row proof is the built
dictionary, which is what the `.pen` is compiled from. The v3.2.2 locale shots below stay valid for
every screen they show — none of the 13 repaired rows appears in them.

## What the locale shots prove

Every string below was read off the device and matches the written map value exactly.

| key | wave status | FIL on screen (v3.2.2) | CEB on screen |
|---|---|---|---|
| `item:Q2_1_AGE` | wave-changed in **both** locales | `Para makumpirma, ilang taon ka na batay sa iyong huling kaarawan (sa taon)?` | `Para ma-confirm lang, pila na imong edad base sa imong miaging birthday (sa tuig)?` |
| `item:Q3_SEX` / `vs:Q3_SEX_VS1` | wave-changed in FIL | `Ano po ang inyong kasarian nang ipinanganak?` — **was** `[Ano po …]` in v3.2.1 | `Unsa ang imong sex sa pagkahimugso?` (unchanged since baseline) |
| `val:Q3_SEX_VS1:1` | restored to the pre-wave value | `Lalaki` — **was** `[Lalaki]` in v3.2.1 | `Lalaki` |
| `val:Q3_SEX_VS1:2` | restored to the pre-wave value | `Babae` — **was** `[Babae]` in v3.2.1 | `Babae` |

The `2. Month` / `2. Year` headings above stay English: that is the cleared source printing English,
not an untranslated defect.

## RESOLVED in v3.2.2 — the square brackets on the FIL strings

Task 33 raised this as an open question against v3.2.1 and referred it to the controller. The ruling
was that it is a defect of the same class as the Waray question-number prefix, and Task 33b fixed it
the same way: at the extractor, then a full re-apply, rebuild and re-publish.

**The paper's convention.** The Aug-21 **Tagalog** F4 paper is a *bilingual* layout — it prints the
English line and puts the Filipino gloss in square brackets after it (`☐ Male [Lalaki]`,
`☐ Female [Babae]`). The other six translated F4 papers are monolingual. The extractor kept the
delimiter as if it were sentence text.

**The rule** (`data/translations-official/anchor_extract.py`, `strip_wrapping_brackets()`): a value
whose *whole* content is enclosed in ONE matching pair of square brackets loses that pair. Internal
brackets are content and stay (`Kung oo, [tukuyin]`); two side-by-side groups are not one wrap;
a double wrap loses exactly one pair, and an unbalanced value is left visibly wrong for the worklist.
Parentheses are untouched — the Ilocano layout and the ILO directive constants need theirs.

| fact | v3.2.1 | v3.2.2 |
|---|---|---|
| F4 `fil.json` values wholly wrapped in `[ … ]` | **459 of 949** (~48%) | **0** |
| F4 `ceb/war/ilo/bcl/bis/hil` wrapped values | 0 each | 0 each |
| F1 `fil.json` (same Aug-21 import) | 0 of 1256 | 0 (F1 extract re-run: **0 rows changed** in all seven locales) |
| Q3 options | `[Lalaki]` / `[Babae]` | `Lalaki` / `Babae` |
| `[Lalaki]` in the served package | present | **0×** (`byte-verify-3.2.2.txt`) |

Bracketed lines in the Aug-21 Tagalog papers: **F1 0, F2 0, F3 503, F4 455** — so the same rule is a
prerequisite for the F3 Wave-4 import, which would otherwise reproduce the defect at 503 lines.

## Substitutions (why these keys and not Q40 / Q67 / Q131)

The Task-33 brief named Q40, Q67 and Q131 FIL. All three were substituted, under the controller's
post-Task-20 ruling (navigation cap; shots must come from wave-changed keys reachable early):

- **Q67_TRAVEL_HH** — has **no map value in either FIL or CEB** (English fallback in both; see the
  `SKIP ... (no map value - English fallback)` lines in the byte-verify files). A shot of it would
  show English in every locale and would prove nothing about the import.
- **Q40_EDUCATION** — **no FIL map value** (English fallback). CEB does carry a wave-changed value
  (`Naabot nga edukasyon`), but Q40 sits on form `FORM015`, behind the whole of Section B plus ten
  repeating Section-C roster forms, well past the budget.
- **Q131_NBB_OOP** — no map value in FIL or CEB, and it is far past Q130 in Section H.

Substituted with the earliest wave-changed question (`Q2_1_AGE`, changed in both FIL and CEB) plus
one wave-changed option list (`Q3_SEX_VS1`), both visible in a single frame per locale, so the shots
are pixel-comparable.

## Capture method (accepted divergences)

- Tier-2 evidence on the **`capi_tablet` AVD** (`emulator-5554`) — there is no physical tablet.
- Raw `adb shell screencap -p /sdcard/s.png` + `adb pull` (never a PowerShell `>` redirect, which
  corrupts PNG bytes). This is an accepted divergence from `capture-csentry-screenshots.ps1`.
- CSEntry was force-stopped before the deployed `.pen`/`.pff`/`psgc_*` were pushed, ownership was
  restored (`chown -R u0_a192:ext_data_rw`, `chmod -R 770`), and a **new** case was started
  afterwards. The v3.2.1 case Task 33 left open was unsaved and is gone.
- Language switched by hand through CSEntry's ⋮ → Change Language menu, before the first field.
- Throwaway case: F4 questionnaire number **`010280001901`**, respondent `TESTER,TEST,T,NA`.
  It was **never synced** and must not be. The pre-existing F1 throwaway case with the same number
  must likewise never be synced.
- The emulator was already running before this task and was **left running** — this task started no
  emulator process, and the standing rule is to kill only PIDs you started.
