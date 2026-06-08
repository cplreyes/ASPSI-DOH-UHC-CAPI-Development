---
type: steering
kind: goal-prompt
scope: end-to-end CAPI instruments (F1, F3, F4) from generator build through CSWeb deploy + Android on-device verification (F2 = done; PLF excluded)
use_with: /goal
created: 2026-06-07
revised: 2026-06-08
pairs_with: [deliverables/CSPro/preflight_validate.py, deliverables/CSPro/automation/cspro_compile_driver.py, deliverables/CSPro/bundle/build_bundle.py, deliverables/CSPro/CSWeb-Deploy-and-Android-Verification-Runbook.md, scrum/epics/epic-04-backend-sync-infrastructure.md, scrum/sprint-current.md]
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
   age gates, F1 Q121 option logic, PSGC cascade, F4 roster/cross-member/expenditure, F3 OP/IP + terminators),
   screenshots to the gate issue. **🟡 SMOKE PASS done (entry + range validations fire); full matrix pending.**
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
    flows through.
15. **Repeatable deploy runbook** recorded and handed to ASPSI/Shan for enumerator training + pretest (Epic 7).

## OUT OF SCOPE
PLF (#140, separate) · **tablet procurement + CSWeb VPS/server ops (ASPSI/Elestio)** · enumerator-account
provisioning by ASPSI · **pretest with real respondents (SJREB-gated)** · fieldwork monitoring · data
cleaning/ETL · analysis. Stage 2 stops at a device-verified, sync-proven app + handoff runbook —
not live fieldwork. *(CSWeb config E4-CSWeb-003/004/005, previously out-of-scope, is now Stage 2.)*

## CURRENT STATE (2026-06-08)
- **STAGE 1 ~DONE.** All three instruments compile clean AND **load + run in CSEntry from pure generator
  output** — the old "compile/desk-test is GUI-only" assumption is overturned (Designer compile + CSEntry
  load are now agent-automated via pywinauto + screenshot/vision + the `<app>.ent.err` oracle). Multi-language
  wired via per-language `.qsf` question text (F3 proven Waray). `preflight_validate.py` = ALL CLEAN.
  Deployable bundles built (`bundle/dist/`). **Remaining Stage-1 QA:** full desk-test scenario matrix (#5),
  Designer sign-off (#6), close gate issues (#7).
- **STAGE 2 not started.** The `bundle/dist/` packages are the exact input to `E4-CSWeb-003`. Blocked on:
  CSWeb admin config (Carl; admin + OAuth verified) and a physical Android device (ASPSI-gated). PSA gate ~Jun 12.

## PATH (sequence)
**Stage 1 (finish QA):** full desk-test scenario matrix per instrument → record Designer sign-off → close
gate issues (#161/#193/#194/#195/#251/#253).
**Stage 2 (deploy + device):**
- **A. Package** *(agent-doable now)* — CSPro "Deploy" each `.ent` → app package incl. the 4 PSGC external
  dicts + `.dat`; author the sync spec (server = `csweb.asiansocial.org`, conflict policy).
- **B. CSWeb config** *(Carl, admin UI)* — upload dicts + apps (003) · users/roles (004) · tablet sync (005).
- **C. Tablet provisioning** *(ASPSI procures; Carl/agent configure)* — Android + CSEntry 8.x; add each app.
- **D. On-device functional verification** *(needs device)* — the criterion-13 checklist (GPS + photo are the
  headline device-only gaps).
- **E. Sync round-trip** *(blocked on B-005 + device)* — case up → CSWeb → down.
- **F. Sign-off + handoff** — runbook to ASPSI/Shan.

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

## START HERE
Stage 1 is build-complete and bundled. Next: either (a) finish Stage-1 QA — drive the full desk-test
scenario matrix per instrument (the smoke pass is done), then sign-off + close gate issues; or (b) start
Stage 2 — package the apps for deploy (agent-doable now) and run the CSWeb config go/no-go (device +
admin access). Confirm device/admin availability before the Stage-2 device phases.

---
*One-line goal:* **Every CAPI instrument is generator-clean, runs in CSEntry in every delivered language,
bundles deployable, then deploys to CSWeb and is verified on a real Android tablet (GPS + photo + sync
round-trip) — all fixes at the generator, the ASPSI language/hardware gaps documented.**
