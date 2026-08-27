# Fix evidence — F1 v4.1.2 (2026-08-27): #1317 Ilocano Q5/Q6 (+ #1318–#1321 already-in-build probe)

Deployed 2026-08-27 13:52 MNL to `capi.asiansocial.org/csweb/api`. Logic (`.apc`) byte-identical to v4.1.1;
four Ilocano labels added to the dictionary.

| file | what it proves |
|---|---|
| `01-compile-successful-4.1.2.png` | fresh Designer compile, `Compile Successful at 13:49:54` |
| `02-deploy-dialog-files-4.1.2.png` | deploy dialog with the 8 PSGC files + `FacilityHeadSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-4.1.2.png` | `Application Deployed Successfully` |
| `served-package-4.1.2.txt` | served zip md5 `43094b35a702469e8ef11f8e04282c28` (1 635 465 bytes), pff `v4.1.2 (2026-08-27) [DEV]`, apc md5 unchanged |
| `byte-verify-4.1.2.txt` | served `.pen` bz2-decoded: the four ILO keys present; `Bilang ti Tawen` / `Bilang ti Bulan` 4× each (dcf label + qsf question text, ×2 rows); footer v4.1.2 — `RESULT: ALL PASS` |
| `dcf-label-proof-1317.txt` | the whole `.dcf` diff vs 4.1.1 = exactly the four Ilocano labels |
| `byte-verify-4.1.1-served-probe-Q10_1-Q13_1-already-present.txt` | the **v4.1.1** served package probed for the #1318–#1321 strings (Q10.1, Q11/11.1, Q12/12.1/12.2, Q13/13.1): all 8 ILO keys present → those tickets were a stale tablet build, not a defect (the count lines in that file were guesses and are not the finding; the `OK ILO item:…` lines are) |
| `1317-tablet-q5-q6-ILO.png` | **tablet** (`capi_tablet` AVD, CSEntry 8, sideloaded **served** v4.1.2 `.pen`, md5 `7b90460b…` == served), Ilocano session: Q5 *Number of Years* and *Number of Months* read *Iti agdama a posisionmo, mano a bulan/tawen ti panagtrabahom iti daytoy a pasilidad ti salun-at? Bilang ti Tawen / Bilang ti Bulan*, Q6 *Number of Years* reads *Mano a tawen a nagtrabahoka iti posision a mainaig iti salun-at? Bilang ti Tawen* |
| `1317-tablet-q3-q4-q5-ILO.png` | same session one scroll up: Q3, Q4 (already Ilocano) and Q5 Number of Years |
| `1317-tablet-consent-ILO-same-session.png` | the same session's consent screen in Ilocano — the language in force |

The pilot case on the AVD is labelled `DO NOT SYNC` and was never synced.
Patch note: `deliverables/CSPro/patch-notes/2026-08-27-f1-v4.1.2-uat-1317.md`.
