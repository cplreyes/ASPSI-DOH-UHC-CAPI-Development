# Fix evidence — F3 v6.1.4 (2026-08-27): #1315 + #1316

Deployed 2026-08-27 13:12 MNL to `capi.asiansocial.org/csweb/api`. v6.1.3 (13:02 MNL) carried the same
two fixes; its byte-verify found one residual Hiligaynon fragment (`vs:Q7_SEX_VS1`, the value-set-label twin
of the removed item label), so v6.1.4 removed that too and superseded 6.1.3 within the hour.

| file | what it proves |
|---|---|
| `01-compile-successful-6.1.4.png` | fresh Designer compile, `Compile Successful at 13:09:09` |
| `02-deploy-dialog-files-6.1.4.png` | deploy dialog with the 8 PSGC files + `PatientSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-6.1.4.png` | `Application Deployed Successfully` |
| `served-package-6.1.4.txt` | served zip md5 `018e40a90eb491f84c1f3ee7a4bc7866` (1 720 059 bytes), pff `v6.1.4 (2026-08-27) [DEV]`, generated md5s, F1/F4 untouched |
| `byte-verify-6.1.4.txt` | served `.pen` bz2-decoded: `mentioned facility)` 0×, `your Ano ang sekswalidad` 0×, footer v6.1.4 — `RESULT: ALL PASS` |
| `apc-diff-1315.txt` | the whole `.apc` diff vs the 6.1.2 build = the two `Q1141_1 → Q1141_6` lines, plus the regenerated PROC |
| `dcf-label-proof-1316.txt` | the whole `.dcf` diff vs 6.1.2 = 12 labels: 6× `Outpatient`, 4× `Inpatient`, HIL Q7 item + value-set label back to English |
| `1315-deskA-row1-yes-rows2-6-no_lands-on-Q1141_NONE.png` | Windows CSEntry, WAR Inpatient walk (`f3_1315_row1_only.txt`): row 1 = Yes + 250, rows 2–6 = No → status bar `Field = Q1141_NONE`, the 115.1 (specify) box skipped. Before the fix this is where errmsg 1177 blocked. |
| `1315-deskA-after-none_lands-on-Q1142_HAS_OTHER.png` | …and on to `Q1142_HAS_OTHER` |
| `1315-deskB-row6-yes_specify-box-opens.png` | `f3_1315_row6_other.txt`: rows 1–5 = No, row 6 *Other expenses* = Yes + 300 → status bar `Field = Q1141_OTHER_TXT`, banner "115.1 Other expenses — specify text". Before the fix this box was skipped and cleared. |
| `1315-deskB-after-specify_lands-on-Q1141_NONE.png` | text entered → `Q1141_NONE` |
| `f3_1315_row1_only.txt`, `f3_1315_row6_other.txt` | the two desk scenarios (copies of `automation/scenarios/`) |
| `1316-tablet-type-of-patient-HIL.png` | **tablet** (`capi_tablet` AVD, CSEntry 8, sideloaded **served** v6.1.4 `.pen`, md5 `0391f917…` == served): Type of Patient in the Hiligaynon session reads `Outpatient / Inpatient` (was `nga serbisyo` / `kag`) |
| `1316-tablet-consent-HIL-same-session.png` | the same session two screens earlier — consent in Hiligaynon, proving the language in force |
| `1316-tablet-build-banner-6.1.4.png` | the case-start banner of that session: `Build: F3 v6.1.4 (2026-08-27)` |

Desk frames are the Windows CSEntry engine (same logic, not tablet chrome); 115.1 sits ~150 fields into an
Inpatient walk, beyond the tablet-navigation cap, so the gate proof is desk-engine. The tablet frame is the
respondent-facing label fix. The pilot case on the AVD is labelled `DO NOT SYNC` and was never synced.

Patch note: `deliverables/CSPro/patch-notes/2026-08-27-f3-v6.1.4-uat-1315-1316.md`.
