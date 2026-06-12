# CSWeb Deploy + Android Verification Runbook (Stage 2)

**Scope:** take the Stage-1 deployable bundles (F1/F3/F4) from `bundle/dist/` onto a real
Android device via CSEntry, verify them on-device (incl. the hardware-only features), and prove
the case sync round-trip to CSWeb. Maps to goal Stage 2 (criteria 10–15) and epics
`E4-CSWeb-003/004/005`, `E3-F1-088` (+F3/F4), Epics 5–6.

**Status:** prep authored 2026-06-08. Phases A–F below; the on-device checklist (§D) is the
deliverable that makes the tablet session productive.

> Pairs with: `bundle/build_bundle.py` (produces `dist/`), `CSPro-Compile-and-Desk-Test-Runbook.md`
> (Stage-1 desktop verification), `automation/cspro_compile_driver.py`.

---

## Prerequisites / gate check
| Need | State | Owner |
|---|---|---|
| Deployable bundles (`dist/F1·F3·F4` + `dist/shared`) | ✅ built | agent (`build_bundle.py --assemble`) |
| CSWeb 8.0.1 live (`csweb.asiansocial.org`, admin + OAuth `/token`) | ✅ live | ASPSI/Elestio |
| CSWeb **admin credentials** (to drive §B) | ⛔ needed | Carl |
| **Android device** + CSEntry **8.x** (must match CSPro 8.0 apps) | ⛔ needed | ASPSI (procurement) |
| Test enumerator account on CSWeb | ⛔ needed | Carl/ASPSI |

> **Two hard gates** before the device phases (§C–E): (1) an Android device with CSEntry, and
> (2) CSWeb admin access. §A and this runbook are doable now; §B onward need the gates.

---

## §A — Package each app for deployment  *(agent/Carl, no device)*
Each `dist/<I>/` already holds the runtime-complete file set (`.ent` + `.dcf` + `.fmf` +
`.ent.apc` + `.ent.qsf` + `.ent.mgf`) beside `dist/shared/` (helpers + 4 PSGC `.dcf`/`.dat`).
Two ways to get this onto CSEntry:

1. **CSWeb-hosted (preferred for fielding):** in CSPro Designer, open each `.ent` →
   **File ▸ Deploy Application ▸ to CSWeb** (server `csweb.asiansocial.org`, the admin creds).
   Designer packages the `.ent` + all referenced files (incl. the 4 PSGC externals) and pushes it.
   CSEntry then installs via **Add Application ▸ from CSWeb**.
2. **Sideload (fast for a one-device smoke test):** Designer **File ▸ Deploy Application ▸ to
   package file** → a `.zip`; copy to the device; CSEntry **Add Application ▸ from file**.

**Packaging checklist (per instrument):**
- [ ] Package includes the 4 PSGC external dicts **and** their `.dat` lookups (the cascade `loadcase`
      reads the `.dat`; without them region→barangay is empty on-device).
- [ ] Package includes `.ent.qsf` (multi-language question text) and `.ent.mgf`.
- [ ] `version: CSPro 8.0` in the `.ent` matches the device CSEntry major version.

> The `.ent.apc` has the shared helpers **inlined**, so the helper `.apc`s are source-only — the
> PSGC `.dcf`/`.dat` are the only `shared/` files actually needed at runtime.

---

## §B — CSWeb server config  *(Carl, admin UI — `E4-CSWeb-003/004/005`)*
> **PATH-B checklist — F1 PILOT FIRST.** Do top-to-bottom on `https://csweb.asiansocial.org/csweb/`,
> logged in as built-in `admin` (the `<csweb-admin-password>` from the setup runbook / password manager).
> Each box is one admin action. F3/F4 repeat B1/B2 with their own `.dcf` + `.pen` once F1 round-trips.
> **State carried in:** F1/F3/F4 **dictionaries already registered** (Jun-4, 12-digit `RR-PP-MMM-FF-CCC`
> key) — so **B1 is likely already done**; **verify** rather than re-upload. The real open item is **B2
> (app deploy, #235)** — the canonical F1 `.pen` was never pushed.

**B0 — Pre-flight (no admin login needed)**
- [ ] F1 `.ent` carries the sync block (`properties.sync` → `…/csweb/api`, `put`) — ✅ done 2026-06-09,
      baked into the generator; verify with: `grep -A2 '"sync"' deliverables/CSPro/F1/FacilityHeadSurvey.ent`.
- [ ] F1 passes the CSEntry compile gate — ✅ `py automation/csentry_verify.py F1` → PASS.
- [ ] Produce the F1 **deploy package** (the `.pen` + PSGC `.dcf`/`.dat`): CSPro Designer ▸ open
      `F1/FacilityHeadSurvey.ent` ▸ **File ▸ Deploy Application ▸ To Package File** → `FacilityHeadSurvey.pen`.
      *(Agent-automatable via pywinauto — see §G; no prod access needed for this step.)*

**B1 — Case store / dictionary  (`E4-CSWeb-003`, part 1)** — *verify, likely already present*
- [ ] **Data dashboard** → confirm `FACILITYHEADSURVEY_DICT` exists with the **12-digit** key and **0 cases**.
- [ ] If missing/old: **Add dictionary** → upload `F1/FacilityHeadSurvey.dcf`.

**B2 — App deploy  (`E4-CSWeb-003`, part 2 — the #235 residual, the real gap)**
- [ ] **Apps dashboard** → host the F1 app so CSEntry can pull it. Two routes:
  - **Designer push (preferred):** Designer ▸ `FacilityHeadSurvey.ent` ▸ **File ▸ Deploy Application ▸
    To CSWeb** → server `https://csweb.asiansocial.org/csweb/api`, **admin creds** → deploy. Designer
    packages the `.ent` + 4 PSGC externals **+ their `.dat`** automatically.
  - **Manual upload:** Apps dashboard ▸ upload the B0 `.pen`.
- [ ] Confirm the F1 app appears under **Apps** and lists the 4 PSGC externals.

**B3 — Roles + one test account  (`E4-CSWeb-004`)** — *minimum for the pilot*
- [ ] **Roles dashboard** → create role **`field-sync`** (no dashboards; tick **F1 dictionary up/down sync**).
      *(Full 5-role matrix is in `CSWeb/CSWeb-User-Management-and-RBAC-Provisioning-Pack.md` — not needed
      for the pilot; one role + one user is enough.)*
- [ ] **Users dashboard** → add **one** test enumerator, username `se-test` (or `se-001`), role `field-sync`,
      a strong password (≥8, store it). First/last name **letters only**.
- [ ] Spot-check: `se-test` **cannot** log into the web UI (no dashboard) — sync-only, by design.

**B4 — Sync config / conflict policy  (`E4-CSWeb-005`, gates §E)**
- [ ] Confirm the F1 dictionary's sync is enabled for `field-sync` (set in B3).
- [ ] **Conflict policy decision** (server-wins vs last-write-wins for a re-synced edited case) —
      ⟨go/no-go⟩, recorded for §E. Default suggestion: **last-write-wins** for a single-tablet pilot.
- [ ] Endpoint sanity: `https://csweb.asiansocial.org/csweb/api/token` returns **405** to a GET
      (exists, POST-only) — ✅ verified 2026-06-09.

> *Scripting B1/B2/B3:* the OAuth `/token` works — see §G. App deploy + user create are **production,
> ASPSI-gated, credentialed** writes → do with Carl's explicit go-ahead + admin creds, not speculatively.

---

## §C — Tablet provisioning  *(ASPSI procures; Carl/agent configure — Epic 5)*
- [ ] Android device, **CSEntry 8.x** installed (Play Store). Confirm version ≥ the app's CSPro 8.0.
- [ ] Grant CSEntry **Location** + **Camera** permissions (required for §D GPS/photo tests).
- [ ] Add each app (CSWeb download or sideload, per §A). Confirm all 3 appear in CSEntry.
- [ ] First-open sanity: each app opens to its FC-metadata form without a load/reconcile error.

---

## §D — On-device functional verification  *(needs device — Epic 6, criterion 13)*
The headline of Stage 2: the things **impossible to test on desktop CSEntry**. Run per instrument;
capture a screenshot per check to the gate issue. Mark ✅/❌/N-A.

### D1 — Common to F1/F3/F4
| Check | How | Result |
|---|---|---|
| App opens, FC-metadata renders on touch | launch from CSEntry | |
| Field entry + range validation fires | enter an out-of-range value (e.g. INTERVIEWER_ID) → expect warning | |
| **Multi-language question text** | switch language in CSEntry (EN→WAR); the question-text bar shows the translated prompt | |
| **GPS capture (device-only)** | trigger the GPS field (below); expect a real lat/long fix + accuracy | |
| **Verification photo (device-only)** | trigger `CAPTURE_VERIFICATION_PHOTO`; camera opens; JPG saved as `case-<id>-verification.jpg` | |
| **PSGC cascade** | REGION→PROVINCE_HUC→CITY_MUNICIPALITY→BARANGAY each filters to children of the parent (loads from on-device PSGC `.dat`) | |
| Consent terminator | `CONSENT_GIVEN = No(2)` ends the interview / sets disposition | |

**Per-instrument specifics:**
- **F1 Facility Head** — GPS trigger `FACILITY_CAPTURE_GPS` → fields `FACILITY_GPS_LATITUDE/LONGITUDE/
  ALTITUDE/ACCURACY/SATELLITES/READTIME`. Multi-language probe: `SURVEY_TEAM_LEADER_S_NAME`
  (WAR = "Ngaran han Survey Team Leader"). Languages EN+5 (BCL·BIS·CEB·WAR·HIL). Q121 DOH-licensing
  option logic (hospital-only O10–12, primary-care-only O13, None O14→skip). Why-difficult gates Q66–74 / Q122–134.
- **F3 Patient** — GPS triggers `FACILITY_CAPTURE_GPS` **and** `P_HOME_CAPTURE_GPS` (patient home →
  `P_HOME_GPS_*`). Patient-home PSGC cascade `P_REGION→P_PROVINCE_HUC→P_CITY_MUNICIPALITY→P_BARANGAY`.
  Multi-language probe: `PATIENT_TYPE` (WAR = "Klase hin Pasyente"). **OP/IP branch:** `PATIENT_TYPE`
  1=Outpatient→Section G, 2=Inpatient→Section H, both→I. Languages EN+4.
- **F4 Household** — GPS trigger `CAPTURE_HH_GPS` → `LATITUDE/LONGITUDE/HH_GPS_*`. **Roster** test
  (the riskiest): add several `C_HOUSEHOLD_ROSTER` members on touch (max 20); first member Self/Head
  soft-confirm; per-member skips (Q35/Q37 disability, Q49 private-ins→advance); roster-count vs
  `Q19_HH_SIZE_TOTAL` warns on mismatch; Section N expenditure consumed-gate (`*_CONSUMED=No`→zero+skip).
  Languages EN+4.

### D2 — Multi-language depth (any one instrument)
- [ ] Switch through **every declared language**; confirm the question bar changes where a translation
      exists and falls back to EN where it doesn't (coverage is partial — WAR ~84% on F3).
- [ ] Confirm `LANGUAGE_USED` records the language actually used (visible on the FC-metadata form).
- [ ] Confirm **skip logic + validations fire identically** regardless of language (logic is
      language-independent — same `.ent.apc` — so this should hold; verify once).

---

## §E — Sync round-trip  *(blocked on §B-005 + device — `E3-F1-088` +F3/F4, criterion 14)*
| Step | Expect | Result |
|---|---|---|
| Log in to CSEntry with the test enumerator account | auth against CSWeb succeeds | |
| Enter + save a complete test case (per instrument) | case stored locally (`.csdb`) | |
| **Sync up** | case uploads; appears in the CSWeb dictionary store (verify in CSWeb admin) | |
| **Sync down** | an app update / new case pulls to the device | |
| Re-sync an edited case | conflict policy (from §B-005) behaves as configured | |
| **Verification-photo binary sync** | photo taken via `CAPTURE_VERIFICATION_PHOTO` syncs up: file appears in `files/binary-items/<dict>/` on the server (named by MD5 signature), one matching row in `csweb_uhc_y2.<DICT>_case_binary_data` for the case GUID, and `verification_photo_filename` populated in the breakout record. Server check: `ls /opt/app/lamp/www/csweb/files/binary-items/facilityheadsurvey_dict/` + `SELECT COUNT(*) FROM csweb_uhc_y2.FACILITYHEADSURVEY_DICT_case_binary_data;` (CSWeb UI doesn't render photos — view via CSPro Data Viewer or the file itself) | |
| "Errors to capture in CSWeb" (Myra's open item) | edit/error data is present in the synced case | |

---

## §F — Sign-off + handoff  *(Epic 7)*
- [ ] Record on-device sign-off (the §D/§E result tables) to the gate issues.
- [ ] Finalize this runbook as the repeatable deploy procedure.
- [ ] Hand to ASPSI/Shan for enumerator training + pretest (SJREB-gated — out of this goal).

---

## §G — Stretch: script the CSWeb dictionary/app upload (`E4-CSWeb-003`)
The CSWeb OAuth `/token` is verified, so the REST API is reachable. **Before building automation,
confirm with Carl + check the live API** whether CSWeb exposes admin endpoints for dictionary/app
creation (its documented API centres on case *sync*, not admin — dictionary upload may be UI-only).
If endpoints exist, a `automation/csweb_upload.py` could: `POST /token` (creds via env, never
committed) → upload each `.dcf` + app package. **Not built yet** — it needs (a) Carl's creds and
(b) a read-only probe of the live API, both outward-facing/credentialed steps to do with Carl, not
speculatively. Until then §B is the manual admin-UI path.

---

## Go/no-go to start the device phases
1. Is an **Android device with CSEntry 8.x** available now, or ASPSI-gated?
2. Do **you** hold CSWeb admin creds for §B, or does that route through ASPSI (Kidd/Myra)?
3. Conflict policy for §B-005: server-wins or last-write-wins?
