# Fix evidence — F1 v4.1.8 (2026-08-27): #1348–#1354 Cebuano compliance batteries (batched + proactive)

Deployed 2026-08-27 17:29 MNL to `capi.asiansocial.org/csweb/api`. Logic (`.apc`) byte-identical to v4.1.1–4.1.7
(md5 `f548f8e81b4defd3897f559f419a31fe`); 45 Cebuano dictionary labels changed: Section F Q109–Q121 stems (item + value-set label,
#1348–#1354 filed for Q109–Q115, Q116–Q121 fixed in the same pass), Q107 *No. of Days*, and the Section D Q53–Q61 stems.

| file | what it proves |
|---|---|
| `01-compile-successful-4.1.8.png` | fresh Designer compile, `Compile Successful at 17:26:48` |
| `02-deploy-dialog-files-4.1.8.png` | deploy dialog with the 8 PSGC files + `FacilityHeadSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-4.1.8.png` | `Application Deployed Successfully` |
| `served-package-4.1.8.txt` | served zip md5, pff `v4.1.8 (2026-08-27) [DEV]`, apc unchanged |
| `byte-verify-4.1.8.txt` | served `.pen` bz2-decoded: CEB Q107-NUM, Q109, Q115, Q121, Q53, Q61 probes present, 26× `Nganong lisud ang pagsunod sa mga mosunod: `, 18× `Nganong lisod tumanon: `, footer v4.1.8 — `RESULT: ALL PASS` |
| `dcf-label-proof-1348-1354.txt` | the whole `.dcf` label diff vs v4.1.7 = the 45 Cebuano stems |
| `1348-desk-q107-num-CEB.png` | Windows CSEntry, Cebuano desk pff (pilot-jump build): Q107 *No. of Days* banner *Pila ka adlaw ang imong giabot sa pagkuha sa lisensya? — No. of Days* |
| `1348-desk-q109-stem-CEB.png` | Q109 banner + popup title *Nganong lisud ang pagsunod sa mga mosunod: Mga katungod sa pasyente ug organization ethics?* (Q110–Q121 carry the same shape; dcf diff + byte-verify) |
| `f1_1348_sectionF_pilot_ceb.txt` | the scenario — **pilot-jump build**: `F1_PILOT_JUMP=Q88_HEARD_BUCAS` desk-only apc (a Q1 postproc `skip to Q88`), regenerated clean and md5-checked after the capture; the labels these frames show are the ones in the served package (byte-verify) |

Section D Q53–Q61 (Cebuano) were fixed in the same build and are covered by the dcf diff + byte-verify; they sit on the sequential
Section D walk (`f1_1335_sectionD_ceb.txt` in the v4.1.7 folder) after Q52.
Desk frames are the Windows CSEntry engine (same logic and dictionary, not tablet chrome); Section F sits ~170 fields in, beyond the
tablet-navigation cap, so the proof is desk-engine + the served-package byte-verify.
Patch note: `deliverables/CSPro/patch-notes/2026-08-27-f1-v4.1.8-uat-1348-1354.md`.
