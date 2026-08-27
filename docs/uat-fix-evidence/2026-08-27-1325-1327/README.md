# Fix evidence — F1 v4.1.5 (2026-08-27): #1325 #1326 #1327 Ilocano Section D stems

Deployed 2026-08-27 14:59 MNL to `capi.asiansocial.org/csweb/api`. Logic (`.apc`) byte-identical to v4.1.1–4.1.4; five Ilocano
labels added to the dictionary (Q39 month + year, Q44 stem, Q45 stem item + value-set label).

| file | what it proves |
|---|---|
| `01-compile-successful-4.1.5.png` | fresh Designer compile, `Compile Successful at 14:56:07` |
| `02-deploy-dialog-files-4.1.5.png` | deploy dialog with the 8 PSGC files + `FacilityHeadSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-4.1.5.png` | `Application Deployed Successfully` |
| `served-package-4.1.5.txt` | served zip md5 `ececd8094e20573cb1d1fe69034c0c5d` (1 635 522 bytes), pff `v4.1.5 (2026-08-27) [DEV]`, apc unchanged |
| `byte-verify-4.1.5.txt` | served `.pen` bz2-decoded: all five ILO keys present; footer v4.1.5 — `RESULT: ALL PASS` |
| `dcf-label-proof-1325-1327.txt` | the whole `.dcf` diff vs 4.1.4 = the five Ilocano labels |
| `1325-desk-q39-month-ILO.png` / `1325-desk-q39-year-ILO.png` | Windows CSEntry, Ilocano desk pff: Q39 Month banner *No wen, manipud kaano? Bulan*, Year banner *… Tawen* |
| `1326-desk-q44-capitation-ILO.png` | Q44 banner *Maibatay iti ammom, ania ti capitation amount ti YAKAP/Konsulta package?* (`Field = Q44_CAPITATION_AMT`) |
| `1327-desk-q45-perf-indicators-ILO.png` | Q45 banner and popup title *Ania dagiti performance indicators a kasapulam a matungpal tapno maawatmo ti maikadua a tranche payment?*, options in Ilocano |
| `f1_1325_sectionD_ilo.txt` | the desk scenario (copy of `automation/scenarios/`), driven on `F1/FacilityHeadSurvey_desktest_ILO.pff` |

Desk frames are the Windows CSEntry engine (same logic and dictionary, not tablet chrome); Section D sits past Sections A–C
(~100 fields), beyond the tablet-navigation cap, so the proof is desk-engine + the served-package byte-verify.
Patch note: `deliverables/CSPro/patch-notes/2026-08-27-f1-v4.1.5-uat-1325-1327.md`.
