---
type: steering
kind: goal-prompt
scope: end-to-end development of the CAPI survey instruments (F1, F3, F4; F2 = done; PLF excluded)
use_with: /goal
created: 2026-06-07
pairs_with: [deliverables/CSPro/CSPro-Compile-and-Desk-Test-Runbook.md, deliverables/CSPro/TRANSLATION-STATUS-2026-06-03.md, deliverables/CSPro/preflight_validate.py, scrum/sprint-current.md]
---

# /goal — End-to-End Development of All CAPI Instruments

## GOAL
Take every CAPI survey instrument through its **complete development lifecycle** — from
generator-built data model + logic + forms, through **multi-language**, **CSPro Designer 8.0 compile**,
**CSEntry desk-test**, and **Designer validation sign-off** — to **verified, deployable `.ent`
application bundles** ready to hand to CSWeb upload + tablet sync and to QA (Shan).

**In scope (3 CAPI instruments):**
- **F1 — Facility Head** (CSPro CAPI): 12 records · ~664 items · 129 PROC blocks · EN+5 (CEB·BIS·HIL·WAR·BCL)
- **F3 — Patient** (CSPro CAPI): 18 records · ~835 items · 60 PROC blocks · EN+4 (CEB·BIS·WAR·BCL)
- **F4 — Household** (CSPro CAPI, roster-heavy): 22 records · ~618 items · 125 PROC blocks · EN+4

**Reference / not in this goal:**
- **F2 — Healthcare Worker** (PWA, 7-language): already in production (v2.1.0) — reference only.
- **PLF — Patient Listing Form**: **excluded from this goal** (handle separately; #140 not in scope here).

## SUCCESS CRITERIA (definition of done)
A CAPI instrument is **DONE** when all of these hold:
1. **Compiles clean** in CSPro Designer 8.0 (Build ▸ Compile, zero errors), with the 4 PSGC external
   dicts inserted and (F1) the 12-digit id-block re-synced.
2. **`preflight_validate.py` = ALL CLEAN** (PROC targets resolve · no `setvalueset` on non-fields ·
   user-function arity matches · no undefined dictionary refs).
3. **Multi-language verified in CSEntry** — every *declared* language loads, forms render translated
   labels, the language switch works, and **skip logic + validations fire identically across languages**;
   `LANGUAGE_USED` records the active language.
4. **Desk-test scenarios pass** (runbook §3): happy path + targeted branches (consent refuse, eligibility
   gates, age blocks, F1 Q121 option logic, PSGC cascade, F4 roster/cross-member/expenditure grid, F3
   OP/IP branching + terminators), screenshots captured to the gate issue.
5. **Designer validation sign-off** recorded (F3 #251 / F4 #253 FIELD_CONTROL + full walkthrough).
6. **Gate issues closed:** F1 smoke #161 + desk #193 · F3 desk #194 · F4 desk #195 · F3 #251 · F4 #253.
7. **Deployable bundle exists** — Designer-bound `.ent` (dcf + fmf + ent.apc + the 4 PSGC dicts) + the
   `psgc_*.dat` lookups, ready for CSWeb dictionary upload + tablet deploy.
8. **All fixes were made at the generator** (IRON RULE) and the artifacts regenerate cleanly; the
   ASPSI-blocked language gap (fil/ilo for F1/F3/F4; hil for F3/F4 — no source) is documented, not faked.

## OUT OF SCOPE (consume the instruments, but not instrument development)
**PLF (Patient Listing Form) — excluded from this goal** (handle in a separate pass) · CSWeb server
provisioning/config (E4-CSWeb-003/-004/-005) · tablet procurement (ASPSI) · pretest with real
respondents (SJREB-gated) · fieldwork monitoring · data cleaning/ETL · analysis · handover. Stop at the
deployable, signed-off `.ent`.

## CURRENT STATE (2026-06-07)
- **Stages 1–5 DONE for F1/F3/F4:** DCF + skip/validation spec + generators + multi-language overlay
  (self-applied in `generate_dcf.py`, QC'd 2026-06-03) + **preflight GREEN** + **language-parity GREEN**
  (F1 2463 / F3 2831 / F4 2232 label arrays, 0 off-parity). CSPro **8.0** installed.
- **Stage 6–8 IN PROGRESS:** the Designer compile → CSEntry desk-test → sign-off is the live work
  (**S009 Goal A**, `E3-F1-001 / -F3-001 / -F4-001` = in-progress). Worksheet:
  `deliverables/CSPro/2026-06-07-multilang-verify-worksheet.md`.

## PATH (sequence)
**F1 first** (reference instrument, largest, exercises the full pattern range) → **F3** (reuses F1
interviewer patterns) → **F4** (roster engine, highest complexity). Per instrument:
GUI setup (F1 id-block re-sync; all: insert 4 PSGC dicts) → compile (fix-loop) → CSEntry desk-test all
declared languages → record sign-off + close gate issues.

## CONSTRAINTS / RULES
- **IRON RULE:** Designer error → fix the **generator source table** → `python generate_dcf.py &&
  generate_apc.py` (+ `generate_fmf.py` for F3/F4) → `preflight_validate.py` ALL CLEAN → reload Designer.
  **Never hand-edit `.dcf`/`.fmf`/`.ent.apc`.**
- **The compile/desk-test is GUI-only** — no honest headless entry compile exists (verified). The agent
  prepares/fixes; **Carl drives Designer + CSEntry** and pastes errors back into the fix-loop.
- Multi-language is **source-limited by ASPSI** — verify/bundle delivered languages; English-fallback +
  documented gap for the rest.
- CSPro Designer 8.0 on Windows; preflight runs under `py`/`python`.

## START HERE
Run `preflight_validate.py` (confirm ALL CLEAN) → open F1 in Designer per the worksheet (id-block
re-sync + 4 PSGC dicts) → compile → desk-test the 6 declared languages → close #161/#193 → repeat F3
(#194/#251) → F4 (#195/#253). Paste any Designer compile error verbatim for the generator fix-loop.

---
*One-line goal:* **Every CAPI instrument compiles clean, desk-tests pass in all delivered languages with
skip logic intact, sign-offs recorded, and a deployable `.ent` bundle exists — all fixes made at the
generator, the ASPSI language gap documented.**
