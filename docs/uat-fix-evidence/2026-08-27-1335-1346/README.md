# Fix evidence — F1 v4.1.7 (2026-08-27): #1335–#1343, #1345–#1347 Cebuano Section D + Ilocano Sections F–G (batched)

Deployed 2026-08-27 17:11 MNL to `capi.asiansocial.org/csweb/api`. Logic (`.apc`) byte-identical to v4.1.1–4.1.6
(md5 `f548f8e81b4defd3897f559f419a31fe`); 37 dictionary labels changed (36 stems: 5 Cebuano + 31 Ilocano; 1 Cebuano option row) plus
four Cebuano note-layer texts (`const:_READ_ONE`, `def:44`, `def:45`, `def:52`) that live in the `.qsf`.

| file | what it proves |
|---|---|
| `01-compile-successful-4.1.7.png` | fresh Designer compile, `Compile Successful at 17:08:40` |
| `02-deploy-dialog-files-4.1.7.png` | deploy dialog with the 8 PSGC files + `FacilityHeadSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-4.1.7.png` | `Application Deployed Successfully` (the auto_deploy driver lost the dialog handle during the CSWeb progress box after clicking Deploy; the popup was captured and dismissed by a follow-up driver, dialog re-parked) |
| `served-package-4.1.7.txt` | served zip md5, pff `v4.1.7 (2026-08-27) [DEV]`, apc unchanged |
| `byte-verify-4.1.7.txt` | served `.pen` bz2-decoded: CEB Q44/Q45/Q49-NUM/Q101:1 and ILO Q107-NUM/Q109/Q121/Q129/Q134/Q143 probes present, Cebuano note texts present, footer v4.1.7 — `RESULT: ALL PASS` |
| `dcf-label-proof-1335-1346.txt` | the whole `.dcf` label diff vs v4.1.6 = the 37 labels |
| `notes-diff-4.1.7.txt` | `notes.json` rebuild diff = the four Cebuano cells (+ English registration of the `def:` rows in F1/F3/F4, no behaviour change) |
| `1335-desk-q44-capitation-CEB.png` | Windows CSEntry, Cebuano desk pff: Q44 banner *Base sa imong kaugalingon nga kahibalo …* + blue note *Capitation mao ang kantidad …* |
| `1338-desk-q45-perf-indicators-CEB.png` | Q45 banner + popup title *Unsa ang mga performance indicators …* + note in Cebuano |
| `1340-desk-q47-directive-CEB.png` | Q47 banner with the directive *BASAHA UG KUSOG. PILI UG USDA KA TUBAG LAMANG* (same constant on Q90 — #1346) |
| `1343-desk-q49-num-CEB.png` | Q49 *No. of Days* banner *Kasagaran, unsa man kadugay … — No. of Days* |
| `1345-desk-q52-preamble-CEB.png` | Q52 banner + note *Mao kini ang mga requirements … BASAHA UG KUSOG ANG MGA TUBAG. PILIA ANG TANAN NGA MO APPLY* |
| `1336-desk-q107-num-ILO.png` | Ilocano desk pff (pilot-jump build, see below): Q107 *No. of Days* banner *Mano nga aldaw ti kasapulan tapno maawatmo ti lisensia? — No. of Days* |
| `1337-desk-q109-stem-ILO.png` | Q109 banner + popup title *Apay a narigat ti agtungpal kadagiti: Karbengan ti pasiente ken etika ti organisasion?* (Q110–Q121 carry the same shape; dcf diff + byte-verify) |
| `1339-desk-q129-ILO.png` | Q129 banner *Apay nga ipalubos ti pasilidad dagiti gastos ti OOP …* |
| `1341-desk-q134-ILO.png` | Q134 banner + popup title *Apay a saan a mangipapaay ti pasilidad …* |
| `1342-desk-q143-ILO.png` | Q143 banner + popup title *Ania a kita ti referral form …* |
| `f1_1335_sectionD_ceb.txt` | the Cebuano desk scenario (sequential walk, clean apc) |
| `f1_1334_1336_pilot_ilo.txt` | the Ilocano Sections E–G scenario — **pilot-jump build**: `F1_PILOT_JUMP=Q88_HEARD_BUCAS` desk-only apc (a Q1 postproc `skip to Q88`), regenerated clean and md5-checked (`f548f8e8…`) before the publish; the labels these frames show are the ones in the served package (byte-verify) |

Desk frames are the Windows CSEntry engine (same logic and dictionary, not tablet chrome); Sections D–G sit ~100–200 fields
in, beyond the tablet-navigation cap, so the proof is desk-engine + the served-package byte-verify.
#1344 (Q150 *I don't know*) was closed without a build change — the option is not on the Aug-17 English instrument.
Patch note: `deliverables/CSPro/patch-notes/2026-08-27-f1-v4.1.7-uat-1335-1346.md`.
