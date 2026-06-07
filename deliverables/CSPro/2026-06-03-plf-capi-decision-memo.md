---
type: deliverable
kind: decision-memo
audience: ASPSI data team · Carl · DOH-PMSMD (for the record)
prepared_by: Carl Patrick L. Reyes
date_drafted: 2026-06-03
status: draft-for-review
related_tasks: [E2-PLF-003, E2-PLF-004, E2-PLF-005, E2-PLF-006, E3-PLF-001]
sources:
  - "raw/Project-Deliverable-1_Apr20-submitted/Annex F3b_Patient Listing Protocol_UHC Year 2.pdf"
  - "wiki/sources/Source - Annex F3b Patient Listing Protocol.md"
tags: [plf, patient-listing, f3b, f4-listing, capi, decision, e2]
---

# Patient List Form — Implementation Decision (CAPI vs paper-only)

**Decision: CAPI** — a lightweight CSPro/CSEntry listing app on the tablet, with a paper log sheet as **backup only**. *Not* paper-only.

This memo records the #137 decision, which is **already settled by the protocol and operationalized in built apps** — it is a decision to document, not an open choice.

---

## 1. The decision is mandated by the protocol (not a free choice)

The **F3b Patient Listing Protocol (Apr 20, 2026 Revised Inception Report)** specifies the listing instrument directly:

- *"Listing instrument: **primary capture via CSPro on tablet**; physical log sheet as backup."*
- *"**CSPro-driven randomization**: generates a random interval 1–10 minutes; enumerator waits n minutes, approaches the next patient, lists them, and repeats until facility target + backups are met."*
- *"CSPro integration formalized: CSPro on tablet is the **primary** listing capture (not just a paper log). **Random-interval generation is a CSPro feature requirement.**"*

The **random-interval generator** is the methodological core of unbiased patient selection (systematic time-based sampling at the patient-flow bottleneck). A paper-only listing **cannot deliver it reliably or auditably** — there is no way to enforce, log, or verify the random wait on paper. Paper-only would break the sampling method the protocol is built around. **CAPI is therefore required, not merely preferred.**

---

## 2. The decision is already operationalized (built apps)

The "if CAPI" work (#138–140, #171) is not hypothetical — it is **substantially built**:

| Instrument | State |
|---|---|
| **F3 patient listing** (`111_F3` / `PatientListing`, `PickPatient()`) | random-interval generator + range bookkeeping built; feeds F3 interview selection via EXTERNAL dictionary |
| **F4 household listing** (`113_F4_listing`, `PickHousehold()`) | **build complete 2026-05-12, 97-test smoke pass**; encodes the 8-decision design sign-off; awaits CSPro Designer publish |

(Both currently live in the `uhc-survey-system-build` worktree — see §4 on reconciling that with the generator-based main instruments.)

---

## 3. What the listing app does (scope of "lightweight")

Per the protocol — deliberately minimal, single-purpose:

- **Sizing:** 1–30 patients per facility (to IS + patient load), **+50% oversample** for non-response backup.
- **Stations:** outpatient at registration (PCF) / OPD registration (hospital); inpatient at the **discharge/billing** station (no ward entry — infection control + privacy). Multi-station targets divided evenly.
- **Capture:** random-interval prompt → list the next patient → refusal/exclusion handling (deceased, ICU, pediatric-without-guardian) → repeat to target + backups.
- **Output / handshake:** a patient (or household) **listing ID + contact info** that the F3 (and F4) interview attaches to via an EXTERNAL dictionary. Links to the replacement protocol (Annex D).

---

## 4. What remains (all Carl-owned, none a new decision)

Recording #137 = CAPI does **not** unblock these on its own; they are owned by Carl, not pending an ASPSI decision and **not** surfaced here:

1. **CSPro Designer publish** of the F3LIST / F4LIST instruments on the tablet build machine (the apps are built; this is the publish step).
2. **Architecture reconciliation** — the listing apps were built in the `uhc-survey-system-build` (Plan-2) worktree; the current main instruments (F1/F3/F4) are the generator-based `deliverables/CSPro/{F1,F3,F4}/` structure. Carl to decide how the listing apps fold into the shipping architecture.
3. **The §3a auto-tag rule** (exit-survey vs follow-up-household-survey) is a known downstream gate inside the F3b build. It is **deliberately not addressed here** — per the standing instruction, that is Carl's to time against Myra's active upstream Survey-Manual edit pass; this memo does not surface or pre-empt it.

---

## 5. Recommendation / issue disposition

- **#137 (E2-PLF-003) — DECIDED: CAPI.** Lightweight CSPro listing app + paper backup. Recorded here; closeable.
- **#138 / #139 / #140 / #171 (the "if CAPI" sub-tasks)** — **active, substantially built** (the listing apps above), not stubs. Track them against the built F3/F4 listing apps; remaining work is the §4 Carl-owned gates (Designer publish + architecture reconciliation + §3a timing), not fresh build from zero.

No ASPSI decision is required to record #137 — the protocol already made the call. The §3a clarification (the one item that *does* need ASPSI) stays with Carl to time.
