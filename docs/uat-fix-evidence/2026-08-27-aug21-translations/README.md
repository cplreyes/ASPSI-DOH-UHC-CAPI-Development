# Aug-21 translations — evidence index (all four instruments)

Root index for the Aug-21 revised-Deliverable-2 translation import
(`raw/Survey-Instruments-2026-08-21/`, gitignored). Everything below is **DEV channel**; the
PSA submission set stays frozen at tag `capi-psa-2026-08-20`.

The waves crossed midnight, so the evidence lives in **two** dated folders — F1/F2/F4
deployed on 2026-08-26, F3 at 00:47 on 2026-08-27. Each folder is dated from its
instrument's `versions.json` deploy date. This file is the single index over both.

| instrument | version | deployed | evidence folder | key frames | byte-verify |
|---|---|---|---|---|---|
| **F1** Facility Head | v4.1.0 | 2026-08-26 | [`../2026-08-26-aug21-translations/F1/`](../2026-08-26-aug21-translations/F1/README.md) | `00-deploy-result.png`, `01-app-list-v4.1.0.png`, `02-q20-fil.png`, `03-q20-ilo.png`, `04-q11-1-options-fil.png`, `05-icf-fil.png` | [`byte-verify.txt`](../2026-08-26-aug21-translations/F1/byte-verify.txt) — **ALL PASS** (7 locales probed in the served pen; `sa masunod sa masunod` present 1× as expected) |
| **F2** Healthcare Worker (PWA) | spec `2026-08-26-m4` | 2026-08-26 | [`../2026-08-26-aug21-translations/F2/`](../2026-08-26-aug21-translations/F2/README.md) | `f2_secA_en.png` + `f2_secA_{fil,ceb,bis,ilo,hil,war,bcl}.png`, `f2_consent_fil.png` | n/a — the PWA has no packaged artefact. Proof is the Playwright locale run against the **production build** (`vite preview`), spec stamp `2026-08-26-m4` visible in every shot |
| **F4** Household | v3.2.2 | 2026-08-26 | [`../2026-08-26-aug21-translations/F4/`](../2026-08-26-aug21-translations/F4/README.md) | `00-app-list-f4-3.2.2.png`, `00-deploy-result-3.2.2.png`, `f4_q2_1_age_{en,fil,ceb}.png` | [`byte-verify-3.2.2.txt`](../2026-08-26-aug21-translations/F4/byte-verify-3.2.2.txt) — **ALL PASS** (the v3.2.0 bracket-gloss and v3.2.1 question-number strings are absent, 0× each) |
| **F3** Patient | v6.1.0 | 2026-08-27 | [`F3/`](F3/README.md) | `00-app-list-f3-6.1.0.png`, `00-deploy-result.png`, `f3_q8_{hil,war}_tablet.png`, `f3_icf_{hil,war}_tablet.png`, `f3_q97{1,2}_{hil,war}.png`, `f3_q115{1,2}_war.png`, `f3_q66_hil.png` | [`F3/byte-verify.txt`](F3/byte-verify.txt) — **ALL PASS**, plus a phrase probe on the served `PatientSurvey.zip` (`daytoy a pasilidad`, `ini nga pasilidad` FOUND) |

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

## Where the rest of the record lives

* Status page, with coverage before → after for all 28 instrument × locale cells:
  `deliverables/CSPro/TRANSLATION-STATUS-2026-08-27.md`
* Patch notes: `deliverables/CSPro/patch-notes/2026-08-26-f1-v4.1.0-aug21-translations.md`,
  `…/2026-08-26-f2-m4-aug21-translations.md`, `…/2026-08-26-f4-v3.2.2-aug21-translations.md`,
  `…/2026-08-27-f3-v6.1.0-aug21-translations.md`
* ASPSI-facing summary:
  `deliverables/CSPro/patch-notes/2026-08-27-aug21-translations-status-for-aspsi.md`
* Wiki: `wiki/sources/Source - Revised Deliverable 2 Translated Questionnaires (Aug 21).md`
