# Fix evidence — F1 v4.1.4 (2026-08-27): #1323 Ilocano Q37 stem

Deployed 2026-08-27 14:44 MNL to `capi.asiansocial.org/csweb/api`. Logic (`.apc`) byte-identical to v4.1.1–4.1.3; two Ilocano
labels added to the dictionary (Q37 item label + value-set label).

| file | what it proves |
|---|---|
| `01-compile-successful-4.1.4.png` | fresh Designer compile, `Compile Successful at 14:40:28` |
| `02-deploy-dialog-files-4.1.4.png` | deploy dialog with the 8 PSGC files + `FacilityHeadSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-4.1.4.png` | `Application Deployed Successfully` |
| `served-package-4.1.4.txt` | served zip md5 `b311ce8cb1c4cf740d77d778cccbae20` (1 636 361 bytes), pff `v4.1.4 (2026-08-27) [DEV]`, apc unchanged |
| `byte-verify-4.1.4.txt` | served `.pen` bz2-decoded: `item:Q37_ACCESS_CHALL` and `vs:Q37_ACCESS_CHALL_VS1` ILO present (*Ania dagiti kangrunaan a karit …*), option 01 present; footer v4.1.4 — `RESULT: ALL PASS` |
| `dcf-label-proof-1323.txt` | the whole `.dcf` diff vs 4.1.3 = the two Ilocano Q37 labels |
| `1323-desk-q37-stem-ILO.png` | Windows CSEntry, Ilocano desk pff (`f1_1323_q37_ilo.txt`): the Q37 screen — question banner and popup title in Ilocano, options in Ilocano |
| `f1_1323_q37_ilo.txt` | the desk scenario (copy of `automation/scenarios/`), driven on the new `F1/FacilityHeadSurvey_desktest_ILO.pff` |

Desk frames are the Windows CSEntry engine (same logic and dictionary, not tablet chrome); Q37 is the last field of
Section C, past Sections A–B and the whole Section C battery, beyond the tablet-navigation cap, so the proof is
desk-engine + the served-package byte-verify.
Patch note: `deliverables/CSPro/patch-notes/2026-08-27-f1-v4.1.4-uat-1323.md`.
