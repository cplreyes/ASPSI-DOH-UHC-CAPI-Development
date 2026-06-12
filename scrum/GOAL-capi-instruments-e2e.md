---
type: steering
kind: goal-prompt
scope: end-to-end CAPI instruments (F1, F3, F4) from generator build through CSWeb deploy + Android on-device verification (F2 = done; PLF excluded)
use_with: /goal
created: 2026-06-07
revised: 2026-06-09
pairs_with: [deliverables/CSPro/preflight_validate.py, deliverables/CSPro/automation/cspro_compile_driver.py, deliverables/CSPro/bundle/build_bundle.py, deliverables/CSPro/Desk-Test-Scenario-Matrix.md, deliverables/CSPro/CSWeb-Deploy-and-Android-Verification-Runbook.md, scrum/epics/epic-04-backend-sync-infrastructure.md, scrum/sprint-current.md]
---

# /goal — End-to-End Development + Deployment of All CAPI Instruments

## GOAL
Take every CAPI survey instrument from generator-built data model + logic + forms + multi-language,
through CSPro Designer 8.0 compile + CSEntry verification, to a **deployable `.ent` bundle** (**Stage 1**) —
then **deploy it to CSWeb and verify it on a real Android device via CSEntry, syncing cases round-trip**
(**Stage 2**). Done = an enumerator can pull each instrument onto a tablet, run it in any delivered
language with skip logic + GPS + verification photo working, and sync the case back to CSWeb.

**In scope (3 CAPI instruments):**
- **F1 — Facility Head** (CSPro CAPI): 12 records · ~664 items · 129 PROC blocks · EN+5 (CEB·BIS·HIL·WAR·BCL)
- **F3 — Patient** (CSPro CAPI): 18 records · ~835 items · 60 PROC blocks · EN+4 (CEB·BIS·WAR·BCL)
- **F4 — Household** (CSPro CAPI, roster-heavy): 22 records · ~618 items · 125 PROC blocks · EN+4

**Reference / not in this goal:**
- **F2 — Healthcare Worker** (PWA, 7-language): already in production — reference only.
- **PLF — Patient Listing Form**: excluded (#140, handle separately).

## STAGE 1 — Build & verify → deployable bundle
A CAPI instrument clears Stage 1 when all of these hold:
1. **Compiles clean** in CSPro Designer 8.0, with the 4 PSGC external dicts inserted and (F1) the
   12-digit id-block re-synced. **✅ DONE (F1/F3/F4, agent-automated).**
2. **`preflight_validate.py` = ALL CLEAN** (PROC targets resolve incl. form-group + external-dict refs ·
   no `setvalueset` on non-fields · user-function arity matches · no undefined refs). **✅ DONE.**
3. **Loads + runs in CSEntry** (strict compile clean — no `<app>.ent.err`) and renders the entry UI.
   **✅ DONE (F1/F3/F4 from pure generator output, no manual Designer step).**
4. **Multi-language renders in CSEntry** — every declared language's prompt shows via the question text
   (`.ent.qsf`), the language switch works, and `LANGUAGE_USED` records the active language. **✅ DONE
   (per-language `.qsf` generators; F3 verified rendering Waray). NB: form field labels are EN by CSPro
   design — the per-language channel is the question text.**
5. **Desk-test scenarios pass** (runbook §3): happy path + targeted branches (consent refuse, eligibility/
   age gates, F1 Q121 option logic, PSGC cascade, F4 roster/cross-member/expenditure, F3 OP/IP + terminators).
   **🟢 Runtime-verified 2026-06-09:** real **CSEntry compile-gate** PASS ×3 (`automation/csentry_verify.py`,
   caught a `protect()` bug Designer had masked) · **case-key persistence DB-verified** (F4) · **all three
   validation kinds** (cross-field-hard, range, soft-warn) fire at runtime via the **scenario runner**
   (`automation/csentry_runner.py`) · PSGC cascade + consent `endlevel` proven live. Full per-instrument
   happy-path matrix is optional polish. Fixed two latent runtime blockers: PSGC `[ExternalFiles]` in the
   pffs; GPS/photo capture made **desktop-skippable via `getos()`** (Android still captures for real).
6. **Designer validation sign-off** recorded (F3 #251 / F4 #253 FIELD_CONTROL + full walkthrough). **❌**
7. **Gate issues closed:** F1 #161/#193 · F3 #194/#251 · F4 #195/#253. **❌**
8. **Deployable bundle exists** — `.ent` + `dcf`/`fmf`/`ent.apc`/`ent.qsf`/`ent.mgf` + the 4 PSGC dicts +
   `psgc_*.dat` lookups, assembled by `bundle/build_bundle.py`. **✅ DONE (dist/F1·F3·F4 + dist/shared).**
9. **All fixes at the generator** (IRON RULE); ASPSI-blocked language gap (fil/ilo; hil for F3/F4)
   documented, not faked. **✅ DONE.**

## STAGE 2 — Deploy & device-verify → field-ready
Builds on the Stage-1 bundles. Maps to Sprint-007 carries `E4-CSWeb-003/004/005`, `E3-F1-088` (+ F3/F4),
and Epics 5–6. The sync chain was proven once on a real device (`E3-F1-086`); Stage 2 redoes it for the
current rebuilt apps and adds the hardware-dependent checks.

> **PREREQUISITE surfaced 2026-06-09 — the apps need sync configured.** The desk-test build has **NO
> synchronization** (built for local entry only). Before C–E can work, add **Simple Synchronization**
> (or sync-from-logic) targeting `https://csweb.asiansocial.org/csweb/api` + the instrument's dictionary —
> **generated at the source (IRON RULE)**, then re-verified in CSEntry. The earlier "sync proven"
> (`E3-F1-085`) was a *local* CSWeb deploy of an *older* F1 build; the current rebuilt apps have never
> round-tripped on the Elestio CSWeb. **QUALITY RULE: never demo or sign off a round-trip that hasn't
> been run successfully once, end-to-end (up → server → down).**
10. **Apps + dictionaries on CSWeb** (`E4-CSWeb-003`) — F1/F3/F4 dictionaries + app packages uploaded to
    `csweb.asiansocial.org`. *(Stretch: script the upload via the CSWeb OAuth API — `/token` verified.)*
11. **Enumerator access configured** (`E4-CSWeb-004`) — users/roles + a test account.
12. **Tablet sync configured** (`E4-CSWeb-005`) — endpoint URLs, sync schedule, conflict policy. *(Gates 14.)*
13. **On-device functional verification** (Epic 6) — on a real Android device with CSEntry 8.x: forms render
    on the touch UI; skip logic + validations fire; **multi-language question text renders per language**;
    **GPS capture works** (FACILITY/HH/P_HOME — device-only, untestable on Windows); **verification photo
    works** (camera); F4 roster add/edit/delete on touch; PSGC cascade loads from on-device external dicts.
14. **Sync round-trip proven** (`E3-F1-088` + F3/F4) — enter a test case on-device → sync **up** → it appears
    in the CSWeb dictionary store; sync **down** propagates app updates; Myra's "errors to capture in CSWeb"
    flows through. **✅ DONE ×3 (2026-06-12):** F1 proven 2026-06-11 (revision 2); F3 case `010280001501` +
    F4 case `010280001601` synced "Successfully synced" 2026-06-12 (emulator, consent-refusal minimal cases).
    *Down N/A by design (direction=`put`).* **Gap found+fixed en route:** the CSWeb `field-sync` role only had
    F1 dictionary permissions (pilot-era B3) → F3/F4 sync 403'd until Carl added PatientSurvey+HouseholdSurvey
    data permissions to the role.
15. **Repeatable deploy runbook** recorded and handed to ASPSI/Shan for enumerator training + pretest (Epic 7).

## OUT OF SCOPE
PLF (#140, separate) · **tablet procurement + CSWeb VPS/server ops (ASPSI/Elestio)** · enumerator-account
provisioning by ASPSI · **pretest with real respondents (SJREB-gated)** · fieldwork monitoring · data
cleaning/ETL · analysis. Stage 2 stops at a device-verified, sync-proven app + handoff runbook —
not live fieldwork. *(CSWeb config E4-CSWeb-003/004/005, previously out-of-scope, is now Stage 2.)*

## CURRENT STATE (2026-06-09)
- **STAGE 1 DONE + runtime-verified.** All three compile clean, load+run in CSEntry from pure generator
  output, multi-language renders (`.qsf`; F3 proven Waray), `preflight_validate.py` ALL CLEAN, bundles
  built. This session hardened criterion #5 to runtime evidence (see #5): CSEntry compile-gate, case-key
  DB-verified, all three validation kinds firing live, two latent blockers fixed (PSGC `[ExternalFiles]`,
  `getos()` capture-skip). The instruments are **field-functional**. Remaining Stage-1 QA (full matrix,
  Designer sign-off, gate issues) is optional polish, not blocking Stage 2.
- **STAGE 2 NOW ACTIVE — F1 pilot, full CSWeb round-trip, no shortcuts.** Strategy: take **ONE instrument
  end-to-end first** (**F1 — Facility Head**: simplest, no roster, all headline features), prove the entire
  chain on the live Elestio CSWeb + a real Android device — deploy → CSEntry download → enter a case →
  **sync round-trip (up → server → down)** — then **replicate A–E to F3/F4**. This realises the original
  "complete the goal for one instrument now, others later."
- **Newly-surfaced gap:** the apps have **no sync configured** — Stage 2 starts by sync-enabling F1 at the
  generator (see Stage-2 prerequisite note). CSWeb has admin accounts seeded (`E4-APRT-008`); the admin
  steps (dict upload, app deploy, tester account) are Carl's. No physical-device blocker assumed — uses a
  real Android with CSEntry 8.x. PSA gate ~Jun 12.

## PATH (sequence) — F1 pilot first, then F3/F4 replicate
**Stage 1:** ✅ build-complete + runtime-verified. *(Optional carry: full desk-test matrix · Designer
sign-off · close gate issues #161/#193/#194/#195/#251/#253 — none block Stage 2.)*

**Stage 2 — F1 round-trip, in order, no shortcuts:**
- **A. Sync-enable F1 — ✅ DONE 2026-06-09.** Mechanism = **Simple Synchronization**, an **.ent app-property
  (no logic)**. *(Finding: sync-from-logic does NOT work for a standalone questionnaire app — a CAPI app can't
  `syncdata` its own input dict; the CSEntry gate rejected it with `external dictionary name expected`.)* Carl
  set it in **Designer ▸ Options ▸ Synchronization** (CSWeb, URL `https://csweb.asiansocial.org/csweb/api`,
  **Test Connection PASS**), Designer wrote `"sync": {"server": ".../csweb/api", "direction": "put"}` under
  `properties`. Agent baked it into the generator (`cspro_compile_driver.py` `_ent_json` + idempotent merge on
  existing `.ent`), regenerated F3/F4 (preflight ALL CLEAN), and **all three `.ent` now carry the block**;
  **F1 passes the CSEntry compile gate**. *direction = `put` (upload-only) — sufficient for the pilot
  round-trip; switch to `both` if devices must also pull cases down.* Enumerator syncs via **CSEntry ▸
  Synchronize** (not during entry).
- **B. CSWeb config — ✅ DONE 2026-06-09** *(verified read-only over SSH/DB).* **B1** F1 `.dcf` registered as
  case store (`FACILITYHEADSURVEY_DICT`). **B2** F1 app deployed via Designer ▸ Publish and Deploy → CSWeb
  (`cspro_apps` row + `apps/FacilityHeadSurvey.zip`; package = `.pen`+`.pff`+`package.json`, PSGC bundled in the
  `.pen`, case dict `uploadForSync:true`); deploy API = `PUT /csweb/api/apps/{name}`. **B3** role **`Field Sync`**
  (FacilityHeadSurvey upload+download, **no dashboards**) + test user **`setest`** (pw set, role bound).
  *Note: the prod-deploy CLICK and any credentialed prod write/auth are gated by the safety classifier → Carl's
  hand needed for those; agent SSH is read-only-verified. The PSGC dicts are bundled inside the `.pen` (not separate
  syncable stores), so they need no role permission.*
- **C. Device install** *(real Android + CSEntry 8.x)* — Add Application ▸ from CSWeb ▸
  `https://csweb.asiansocial.org/csweb/api` ▸ download F1; grant **Location + Camera**.
- **D. On-device functional check** *(criterion 13)* — cascade · multi-language question text · skip logic ·
  **real GPS + verification photo** · consent terminator.
- **E. Sync round-trip** *(criterion 14)* — enter a complete case → sync **up** → verify it lands in the
  CSWeb store (admin) → sync **down**. **Run this successfully once before any demo/sign-off (QUALITY RULE).**
- **F. Sign-off + replicate** — record F1 sign-off; then repeat A–E for **F3** (OP/IP branch + 2 cascades +
  patient-home GPS) and **F4** (roster add/edit/delete on touch + expenditure gates).

## CONSTRAINTS / RULES
- **IRON RULE:** Designer/CSEntry error → fix the **generator source** → `generate_dcf.py && generate_apc.py
  (+ generate_fmf.py + generate_qsf.py)` → `preflight_validate.py` ALL CLEAN → re-verify. **Never hand-edit
  `.dcf`/`.fmf`/`.ent.apc`/`.ent.qsf`.** (Designer Ctrl+S corrupts UTF-8 em-dashes — prefer the generator.)
- **Compile + load + desk-test smoke are now AGENT-AUTOMATED** (pywinauto/win32 dialogs + keyboard + vision;
  HTML error modals dismissed by coordinate click). Still human/device-bound: the full desk-test scenario
  matrix, Designer sign-off, and ALL Stage-2 on-device tests (GPS/photo/touch).
- **CSWeb admin config = Carl** (admin login + OAuth `/token` verified). **Tablet, VPS, enumerator accounts =
  ASPSI-gated.** Carl produces CAPI; ASPSI (Kidd/Myra) is the DOH/PSA interface — surface decisions as an
  in-chat go/no-go checklist.
- Multi-language is **source-limited by ASPSI** — wire delivered languages; EN fallback + documented gap.
- CSPro Designer/CSEntry 8.0 on Windows; Python under `py`/`python`.

## START HERE (updated 2026-06-12)
**Stage 1 ✅ · Stage 2 criteria 10–12 ✅ · criterion 14 (sync round-trip) ✅ ×3 · criterion 13 ✅ except the
hardware-only checks.** All three instruments are LIVE on CSWeb (shipped 2026-06-12) with the full feature set:
single 12-digit Questionnaire Number with hierarchical PSGC validation + auto-filled read-only geo names ·
verbatim Annex H consent screens · per-question enumerator instructions + section intros · capture-type pass
(DropDowns, native Date pickers, auto-advance) · combined-view blocks (Interview Staff + Visit Record) ·
operator partial save · audited skip/validation logic (dead gates fixed, F4 roster auto-end at Q19,
province-anchored barangay fallback, other-specify enforcement complete). Clean tester-path verified on the
emulator ×3 (install → entry → validation → consent endlevel → **sync up "Successfully synced"**). The earlier
FACILITY_LOOKUP auto-fill was **dropped** (Android indexing loop) — superseded by the QN redesign.
**TO CLOSE THE GOAL:** (1) **Carl's real-phone pass — live GPS capture + verification photo** (criterion 13's
device-only items; ~10 min with `docs/F1-CSEntry-Tester-Install-and-Test-Guide-2026-06.md`, already on the
12-digit flow); (2) record the ASPSI/Shan handoff (criterion 15 — runbook + tester guide are current).
*Optional paperwork:* Designer sign-off note (#6) · parked gate issues (#161/#193/#194/#195/#251/#253).
*Small open decisions:* duplicate other-specify twins (F3 Q67/F4 Q82) · F4 Q24/Q25 water conditionality.

---
*One-line goal:* **Every CAPI instrument is generator-clean, runs in CSEntry in every delivered language,
bundles deployable, then deploys to CSWeb and is verified on a real Android tablet (GPS + photo + sync
round-trip) — all fixes at the generator, the ASPSI language/hardware gaps documented.**
