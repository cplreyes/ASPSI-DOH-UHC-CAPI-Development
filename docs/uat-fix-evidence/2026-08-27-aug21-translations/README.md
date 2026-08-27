# Aug-21 translations — evidence index (all four instruments)

Root index for the Aug-21 revised-Deliverable-2 translation import
(`raw/Survey-Instruments-2026-08-21/`, gitignored). Everything below is **DEV channel**; the
PSA submission set stays frozen at tag `capi-psa-2026-08-20`.

The waves crossed midnight, so the evidence lives in **two** dated folders — F1/F2/F4 first
deployed on 2026-08-26, F3 at 00:47 on 2026-08-27. Each folder is dated from the day its
instrument first deployed, and later same-instrument patches are filed **alongside** their
originals rather than in a new folder, suffixed with the version they prove
(`byte-verify-4.1.1.txt`, `01-app-list-v4.1.1.png`). This file is the single index over both.

| instrument | version | deployed | evidence folder | key frames | byte-verify |
|---|---|---|---|---|---|
| **F1** Facility Head | **v4.1.1** | 2026-08-27 | [`../2026-08-26-aug21-translations/F1/`](../2026-08-26-aug21-translations/F1/README.md) | `00-deploy-result-4.1.1.png`, `01-app-list-v4.1.1.png`, and from v4.1.0: `02-q20-fil.png`, `03-q20-ilo.png`, `04-q11-1-options-fil.png`, `05-icf-fil.png` | [`byte-verify-4.1.1.txt`](../2026-08-26-aug21-translations/F1/byte-verify-4.1.1.txt) — **ALL PASS** (7 locales probed in the served pen, 9 `0×` counts on strings only v4.1.0 carried) + [`dcf-removal-proof-4.1.1.txt`](../2026-08-26-aug21-translations/F1/dcf-removal-proof-4.1.1.txt) for the two removed rows |
| ↳ F1 v4.1.0 (superseded) | v4.1.0 | 2026-08-26 | same folder | `00-deploy-result.png`, `01-app-list-v4.1.0.png` | [`byte-verify.txt`](../2026-08-26-aug21-translations/F1/byte-verify.txt) — **ALL PASS** (7 locales probed in the served pen; `sa masunod sa masunod` present 1× as expected) |
| **F2** Healthcare Worker (PWA) | spec **`2026-08-27-m5`** | 2026-08-27 | [`../2026-08-26-aug21-translations/F2/`](../2026-08-26-aug21-translations/F2/README.md) | `f2_secA_en.png` + `f2_secA_{fil,ceb,bis,ilo,hil,war,bcl}.png`, `f2_consent_fil.png` (all re-shot on m5), `map-delta-m5.txt`, `served-content-m5.txt` | n/a — the PWA has no packaged artefact. Proof is the Playwright locale run against the **production build** (`vite preview`), spec stamp `2026-08-27-m5` visible in every shot, plus a string check on the bundle PROD actually serves and `build-info.json` sha == HEAD (`fb91241a`) |
| ↳ F2 spec `2026-08-26-m4` (superseded) | `2026-08-26-m4` | 2026-08-26 | same folder | the m4 shots are the same files, replaced in place | the m4 record is the §m4 half of that README; the only value m5 changes is Q57 `war` |
| **F4** Household | **v3.2.3** | 2026-08-26 | [`../2026-08-26-aug21-translations/F4/`](../2026-08-26-aug21-translations/F4/README.md) | `00-app-list-f4-3.2.3.png`, `00-deploy-result-3.2.3.png`, and from v3.2.2: `f4_q2_1_age_{en,fil,ceb}.png` | [`byte-verify-3.2.3.txt`](../2026-08-26-aug21-translations/F4/byte-verify-3.2.3.txt) — **ALL PASS** (12 counts, 7 of them 0×) + [`dcf-removal-proof-3.2.3.txt`](../2026-08-26-aug21-translations/F4/dcf-removal-proof-3.2.3.txt) |
| **F3** Patient | **v6.1.2** | 2026-08-27 | [`F3/`](F3/README.md) | `00-deploy-result-6.1.2.png`, `01-app-list-v6.1.2.png`, `02-compile-successful-6.1.2.png`, and from v6.1.0: `f3_q8_{hil,war}_tablet.png`, `f3_icf_{hil,war}_tablet.png`, `f3_q97{1,2}_{hil,war}.png`, `f3_q115{1,2}_war.png`, `f3_q66_hil.png` | [`F3/byte-verify-6.1.2.txt`](F3/byte-verify-6.1.2.txt) — **ALL PASS** (4 measured counts, `[Mahirap magparehistro]` 0×, both CEB `*_SOURCE_VS1:06` probes present) + [`F3/dcf-label-proof-6.1.2.txt`](F3/dcf-label-proof-6.1.2.txt) — per-code proof for the 21 removed **and** the 7 written rows, and no duplicate option label in 213 value sets × 8 languages |
| ↳ F3 v6.1.1 (superseded) | v6.1.1 | 2026-08-27 | same folder | `00-deploy-result-6.1.1.png`, `01-app-list-v6.1.1.png` | [`F3/byte-verify-6.1.1.txt`](F3/byte-verify-6.1.1.txt) — **ALL PASS**. Same rendered text as v6.1.2; the seven Cebuano `LGU/Barangay` rows were DELETED (English label) instead of written |
| ↳ F3 v6.1.0 (superseded) | v6.1.0 | 2026-08-27 | same folder | `00-app-list-f3-6.1.0.png`, `00-deploy-result.png` | [`F3/byte-verify.txt`](F3/byte-verify.txt) — **ALL PASS**, plus a phrase probe on the served `PatientSurvey.zip` (`daytoy a pasilidad`, `ini nga pasilidad` FOUND) |

F4 also carries `byte-verify.txt` (v3.2.0) and `byte-verify-3.2.1.txt` with their app-list and
deploy frames. Both builds were superseded the same day; **v3.2.2 is the shipped one** and its
`-3.2.2` files are the ones to read.

## What each folder proves

* **F1 / F3 / F4** — the artefact actually served by CSWeb was pulled back down, the probe
  strings were byte-verified inside the `.pen`, and the package was sideloaded onto a device
  or emulator so the labels could be read on screen in the language menu. Both halves matter:
  byte-verify proves the right bytes shipped, the frames prove they render.
* **F2** — no package to verify; the check is a render of the production build, one full-page
  screenshot per locale, with the spec version stamped in the header of every shot.

## Known gaps, disclosed

* **F3 Q47 and 97.2 have no *tablet* frame.** The 30-minute navigation cap stopped the walk at
  Q10, so Q8 (Hiligaynon and Waray) and the Hiligaynon ICF were substituted. Their desk frames
  (`f3_q971_*.png`, `f3_q972_*.png`) and the byte-verify probes stand as the proof for those
  two keys. Recorded in the F3 folder's README and in the F3 patch note.
* **English still on screen in some places is not a defect.** Where ASPSI's Aug-21 paper prints
  no translation, the instrument renders English on purpose; the full list is the translator
  worklist (`deliverables/CSPro/translator-worklist-aug21.xlsx`).

## The row-inheritance repair (2026-08-27, Tasks 48-51)

A review of the four v-first builds found option labels carrying a NEIGHBOURING row's
translation. Task 48 traced it to the papers' two-column option grids, fixed the extractor so
the class cannot be re-introduced, and added a permanent duplicate-label gate to
`apply_aug21.py`. The repair of what was already deployed shipped as **F1 v4.1.1**,
**F4 v3.2.3**, **F3 v6.1.1** (re-published as **v6.1.2**, which writes the seven Cebuano
`LGU/Barangay` rows the paper prints untranslated instead of letting the English label render
them — see the F3 folder) and **F2 spec `2026-08-27-m5`**, each with its own per-code proof
file beside its byte-verify. Rows with no distinct translation on the paper are **deleted**
from the map so the English option renders — an English label beats one that repeats another
option's words — and every deleted row is on the translator worklist.

F2 carried exactly one instance (Q57 `war`, the City/LGU referral form row holding the DOH
row's translation glued to its own) and it is repaired the same way: the whole wave re-applied
from the pre-wave baseline with the corrected extractor, not a hand edit. Its remaining
duplicate pair — `fil` `Agree but for clerical tasks only` / `Disagree for both medical and
clerical tasks` — is the **paper's own** repetition, pre-existing since June-5, and is on the
worklist rather than being deleted, because deleting it would have to be argued per row and
this task's scope was the row-inheritance class.

## Where the rest of the record lives

* Status page, with coverage before → after for all 28 instrument × locale cells:
  `deliverables/CSPro/TRANSLATION-STATUS-2026-08-27.md`
* Patch notes: `deliverables/CSPro/patch-notes/2026-08-27-f1-v4.1.1-aug21-translations.md`,
  `…/2026-08-27-f2-m5-aug21-translations.md`, `…/2026-08-27-f4-v3.2.3-aug21-translations.md`,
  `…/2026-08-27-f3-v6.1.2-aug21-translations.md`
* ASPSI-facing summary:
  `deliverables/CSPro/patch-notes/2026-08-27-aug21-translations-status-for-aspsi.md`
* Wiki: `wiki/sources/Source - Revised Deliverable 2 Translated Questionnaires (Aug 21).md`
