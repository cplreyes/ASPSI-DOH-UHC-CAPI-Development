# Aug-21 translations — F4 fix evidence (wave 3, v3.2.1)

**Driver:** ASPSI Aug-21 revised instruments (raw/Survey-Instruments-2026-08-21).
**Ships as:** Household Survey (F4) v3.2.1 (2026-08-26) — DEV channel, not the PSA submission set
(that stays frozen at tag `capi-psa-2026-08-20`).

**What changed in this wave:** English aligned to the Aug-21 paper; printed gates rendered as
on-screen instruction notes; 7-locale Aug-21 translation import. v3.2.1 is the patch on top of
v3.2.0 that fixes the extractor defect which had prefixed 154 WARAY values with the paper's
question number (7 of them with the wrong number).

**Package proven:** the emulator ran the **deployed** package, not a local build.
`/opt/app/lamp/www/csweb/files/apps/HouseholdSurvey.zip` md5 `843b5beb2880428ebecf64e3c59eca4a`;
the `HouseholdSurvey.pen` pushed to the device md5 `3deff890aa14ece6ddaf995db466543d`, verified
equal to the one inside that served zip.

## Files

| file | what it shows |
|---|---|
| `00-deploy-result.png` | CSWeb deploy dialog, v3.2.0 |
| `00-deploy-result-3.2.1.png` | CSWeb deploy dialog, v3.2.1 (Task 32b re-publish) |
| `00-app-list-f4-3.2.1.png` | CSEntry app list with the `Household Survey (F4) - v3.2.1 (2026-08-26) [DEV]` stamp |
| `f4_q2_1_age_en.png` | Q2.1 + Q3 in English (baseline for the two locale shots) |
| `f4_q2_1_age_fil.png` | Q2.1 **and** the Q3 option list in Filipino |
| `f4_q2_1_age_ceb.png` | Q2.1 **and** the Q3 option list in Cebuano |
| `byte-verify.txt` | v3.2.0 byte-verify (utf-16-le `bytes.find`, `aug17-tools/byte_verify_aug21.py`) |
| `byte-verify-3.2.1.txt` | v3.2.1 byte-verify with `--baseline` + wave-changed probes |

## What the locale shots prove

Every string below was read off the device and matches the written map value exactly.

| key | wave status | FIL on screen | CEB on screen |
|---|---|---|---|
| `item:Q2_1_AGE` | wave-changed in **both** locales | `Para makumpirma, ilang taon ka na batay sa iyong huling kaarawan (sa taon)?` | `Para ma-confirm lang, pila na imong edad base sa imong miaging birthday (sa tuig)?` |
| `item:Q3_SEX` / `vs:Q3_SEX_VS1` | wave-changed in FIL | `[Ano po ang inyong kasarian nang ipinanganak?]` | `Unsa ang imong sex sa pagkahimugso?` (unchanged since baseline) |
| `val:Q3_SEX_VS1:1` | wave-changed in FIL | `[Lalaki]` | `Lalaki` |
| `val:Q3_SEX_VS1:2` | wave-changed in FIL | `[Babae]` | `Babae` |

The square brackets in the FIL cells are the paper's own brackets, carried through verbatim — they
are in the map, not a rendering artefact. The `2. Month` / `2. Year` headings above stay English:
that is the cleared source printing English, not an untranslated defect.

## Substitutions (why these keys and not Q40 / Q67 / Q131)

The task named Q40, Q67 and Q131 FIL. All three were substituted, under the controller's
post-Task-20 ruling (30-minute navigation cap; shots must come from wave-changed keys reachable
early). Reasons:

- **Q67_TRAVEL_HH** — has **no map value in either FIL or CEB** (English fallback in both; see the
  `SKIP ... (no map value - English fallback)` lines in `byte-verify-3.2.1.txt`). A shot of it would
  show English in every locale and would prove nothing about the import.
- **Q40_EDUCATION** — **no FIL map value** (English fallback). CEB does carry a wave-changed value
  (`Naabot nga edukasyon`), but Q40 sits on form `FORM015`, behind the whole of Section B plus ten
  repeating Section-C roster forms, well past the 30-minute budget.
- **Q131_NBB_OOP** — no map value in FIL or CEB, and it is far past Q130 in Section H.

Substituted with the earliest wave-changed question (`Q2_1_AGE`, changed in both FIL and CEB) plus
one wave-changed option list (`Q3_SEX_VS1`, changed in FIL) — both visible in a single frame per
locale, so the three shots are pixel-comparable.

## Capture method (accepted divergences)

- Tier-2 evidence on the **`capi_tablet` AVD** (`emulator-5554`) — there is no physical tablet.
- Raw `adb shell screencap -p /sdcard/cap.png` + `adb pull` (never a PowerShell `>` redirect, which
  corrupts PNG bytes). This is an accepted divergence from `capture-csentry-screenshots.ps1`.
- CSEntry was force-stopped before the deployed `.pen`/`.pff`/`psgc_*` were pushed, and a **new**
  case was started afterwards.
- Language switched by hand through CSEntry's ⋮ → Change Language menu.
- Throwaway case: F4 questionnaire number **`010280001901`**, respondent `TESTER,TEST,T,NA`.
  It was **never synced** and must not be. The pre-existing F1 throwaway case with the same number
  must likewise never be synced.
- The emulator was already running before this task and was **left running** — this task started no
  emulator process, and the standing rule is to kill only PIDs you started.
