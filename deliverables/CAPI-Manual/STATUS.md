# CAPI Manual — Build Status (what's done / what's missing)

_Last updated 2026-06-28. Manual lives in `sections/01`–`17.md` + `README.md`; images in `img/`; combined reader `CAPI-Manual.md`; styled output `CAPI-Manual.html` + **`CAPI-Manual.pdf`** (build assets in `build/`)._

## ✅ Done — the manual is complete

| Area | Status |
|---|---|
| **All 17 sections** | I Introduction · II Device · III System Overview · IV Logging in · V Dashboard · VI Assignments · VII Listing · VIII Mapping/GPS · IX Starting · X Navigating · XI Entering/Reviewing · XII Completing · XIII Syncing · XIV Supervisor · XV Troubleshooting · XVI Security · XVII Annexes |
| **House style** | Myra's "Digital PDF / task-based" — every procedure as Task → User → When → Steps → Expected → Common problem → What to do; troubleshooting table per function |
| **Real-system grounding** | Written to the deployed CSEntry + Supervisor/Enumerator hub + CSWeb; on-device labels verified |
| **Complete workflows** | Sign-in · get assignment · navigate · enter/review · complete · sync · supervisor Assign→Collect→Relay — all end-to-end, with flow diagrams |
| **Real app screenshots (24)** | captured live on the Samsung A23 + embedded in their sections (see table below) |
| **Diagrams (8)** | system architecture, day workflow, role hierarchy (§III); sign-in flow (§IV); case lifecycle (§XII); supervisor sequence (§XIV); troubleshooting decision tree (§XV); + ASCII tree (§XVII·G) |
| **Code-list annexes B/C/D** | filled from the live F1/F3/F4 value sets — case/disposition status (B), per-instrument Result-of-Visit + BREAKOFF codes (C), real error-message examples by type (D) |
| **`[VERIFY]` flags** | resolved from the system: §VI documents both distribution paths (protocol picks); §III settled — one production CSWeb, training via practice cases, no separate training server |
| **Styled PDF export** | `CAPI-Manual.pdf` — A4, purple Style-Guide-3 cover/headers/callouts, **123-entry bookmark outline**, mermaid diagrams rendered in purple, all 24 screenshots embedded with captions. Reproducible via `build/build-pdf.sh` (pandoc + Chrome). |

### Screenshots embedded ✅ (24)
| File | Section | Shows |
|---|---|---|
| `04-01-loginapp-start.png` · `04-02-username.png` · `04-03-password.png` | §IV | LoginApp start + username + password |
| `04-04-enumerator-menu.png` | §IV · §V · §IX | Enumerator role menu (se-004) |
| `04-csentry-app-list.png` | §IV·7 | CSEntry Entry Applications list |
| `04-login-error.png` | §IV·4 | "Unknown username." error dialog |
| `05-coverage-report.png` | §V · §XIV | MY INTERVIEW COVERAGE report |
| `07-f3-case-list.png` | §VII · §XIII | PatientSurvey case list + sync icon |
| `08-gps-values.png` | §VIII·1 | Auto-captured Facility GPS (lat/lon/accuracy/satellites) |
| `09-consent-q1.png` | §IX·3 | Consent / eligibility gate (Q1 are-you-the-patient) |
| `09-f3-casekey.png` · `09-f3-casekey-numpad.png` | §IX·4 | 12-digit Questionnaire Number entry |
| `10-question-single-select.png` | §X·1 | Single-select radio question (Type of Patient) |
| `10-nav-tree.png` | §X·1 | Case section navigation tree |
| `10-question-checkbox.png` | §X·3 | Multi-select checkbox question (Q87) |
| `10-question-select-list.png` | §X·3 | Long single-select list (Barangay) |
| `11-consistency-warning.png` | §XI·6 | Soft consistency-check warning dialog |
| `12-interview-status-breakoff.png` | §XII·2 | Closing Interview-status / Result-of-Visit radio |
| `13-sync-login.png` · `13-sync-success.png` | §XIII·2 | CSWeb sync sign-in + "Successfully synced" |
| `14-supervisor-menu.png` · `14-supervisor-menu-full.png` | §XIV | Supervisor role menu (fs-01) |
| `14-assign-ea-bluetooth.png` · `14-assign-waiting.png` | §VI·2 · §XIV·1 | Assign EA Bluetooth host + "Waiting for connections…" |

## 🟡 Remaining — both ASPSI-side, neither blocks release
| Item | Why it's outstanding |
|---|---|
| **Support contacts §XVII·H** | Names + numbers are roster-specific — ASPSI fills the (clearly marked) form at training. The only blank field in the manual. |
| **§2.A tablet hardware photo** *(optional)* | A posed front/back photo of the issued tablet is best taken with a camera during kit prep; flagged as optional, add before printing. Everything else is captured on-device. |

## ⚙️ Notes
- **On-page TOC links:** the PDF's navigation is the **bookmark outline** (123 entries, shows in any reader's sidebar). Chrome's headless print-to-pdf does not convert in-page `#anchor` links to click-through links; the markdown source (`CAPI-Manual.md`) remains fully hyperlinked in Obsidian. The two engines that keep anchor links can't render the mermaid diagrams, so the diagram-faithful Chrome render was chosen.
- **Rebuild after edits:** `bash build/build-pdf.sh` from the `CAPI-Manual/` directory regenerates `CAPI-Manual.md` → `.html` → `.pdf`.

## Coverage at a glance
- **Workflows:** 17/17 sections complete, all illustrated.
- **Diagrams:** 8 (system, day-flow, roles, sign-in, lifecycle, supervisor, troubleshooting + ASCII tree).
- **Screenshots:** 24 real app screens embedded; no in-app placeholders remain (only the optional posed tablet photo).
- **Code lists:** B/C/D filled from the live instruments; H awaits ASPSI's contact roster.
- **Output:** styled 93-page purple PDF with bookmark navigation.
- **Release-readiness: ~98%** — content, visuals, code lists, and packaging done; only ASPSI's support-contact names and an optional device photo remain.
