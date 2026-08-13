---
title: F2 Model C — Open Self-Register (design)
date: 2026-07-16
status: DRAFT — v-next, post-pretest
author: Carl Patrick Reyes (design session w/ Claude)
related: f2-hcw-self-service-workflow.excalidraw (Model C lane)
---

# F2 Model C — Open Self-Register (design)

## Goal

One facility QR / link that any HCW opens on their own phone **in the browser (no install)** and
answers. The server assigns a unique 12-digit QN behind the scenes so every case is unique, with
**zero pre-provisioning** — no admin has to create slots or mint per-HCW cards first.

## Decisions locked (2026-07-16 session)

| Fork | Choice | Note |
|---|---|---|
| Population | **Pure self-register** | No pre-loaded roster; every case is self-registered. |
| Access | **Fully open** | No access code, no dedup gate. (One near-free device-bind guard flagged below.) |
| Number | **Auto-assign + receipt** | Server assigns the QN on tap; phone/browser remembers it; **no login step**. |
| Entry | **Browser, install optional** | The link/QR opens the survey in the mobile browser; PWA install is never required. |

## The flow

1. HCW scans the facility QR / opens the link → survey opens in their **mobile browser** (no install).
2. Taps **"Start / I'm a healthcare worker here."**
3. Server (`self-register` endpoint) **atomically assigns the next QN** in the facility's F2 block
   (101+) and creates the case record.
4. **"You are respondent 127"** shown as a receipt; the enrollment persists in browser storage.
5. **SJREB consent → survey → submit → sync.** (All inherited unchanged.)
6. Admin sees every case land live in the console.

## What's NEW to build (small, self-contained)

1. **`self-register` endpoint** — given the facility token, atomically assign the next QN + create the
   case record, return it. **Reuses the existing admin-create QN-assignment logic minus the admin
   gate.** This is the only genuinely new server logic.
2. **Facility-token mint** — one durable, long-lived token *per facility* (not per-HCW), encoded as
   the printable QR. Today tokens are minted per-HCW via `reissue-token`; add a facility-level mint (or
   designate a standing facility token).
3. **Enrollment-screen branch** — a **"New respondent / Start"** path that calls `self-register`
   instead of asking for an HCW ID. The existing "I have a code" path stays intact for models A/B.

## What's REUSED unchanged (zero new risk to the survey core)

Facility-scoped token verify · SJREB consent gate · survey engine · submit + idempotency · refusal
(#825) · offline queue + sync · admin monitoring. **None of these change.**

## Endpoint sketch

```
POST /enroll/self-register
  Authorization: Bearer <facility_token>
  → 201 { hcw_id, qn, facility_id }
```

- **Concurrency:** assign inside a transaction (e.g. `SELECT max(seq) in F2 block ... FOR UPDATE`, or
  an atomic insert) so two simultaneous taps never collide. The admin-create path already guarantees
  *"seq never reused"* — `self-register` reuses that guarantee.
- **QN partition:** stays in the F2 block (101–999 ≈ 899 slots/facility) → no collision with F3
  patients (001–099). The shared-QN cross-instrument join model is unchanged.
- **hcw_id:** auto-generated server-side (e.g. equal to the QN, or a uuid) since there is no roster
  identifier to supply.

## Browser / PWA behavior (answers "the link just opens the form in the browser, right?")

- **Yes.** The link opens the survey as a normal web page in the phone's browser. **Install (Add to
  Home Screen) is an optional PWA prompt** the HCW can ignore and just fill the form in the tab. No
  install is ever required.
- **Registering needs a signal** at that moment (the server assigns the number). The survey then works
  **offline**; answers queue and sync later.
- **Enrollment persists in the browser's local storage** (IndexedDB) → the same phone/browser resumes
  automatically. **Cross-device resume is NOT supported** in this model — that is exactly what the
  code-login variant would add, and it is deferred.

## Data-integrity trade-offs of the chosen open model (eyes open)

Pure self-register + fully open is the simplest to build and use, but:

- **No denominator** — you can measure who answered, not who *didn't* (no frame to check against).
  Coverage % needs a headcount from elsewhere (e.g. the facility head reports total HCWs).
- **No dedup** — one person can create multiple cases; a stray/curious scan creates a junk case.
  Cleanup is manual (admin prune in the console).
- **Recommended: keep ONE near-free guard — device-binding.** A phone that just registered won't spawn
  a second case on reload. Zero user friction, kills the most common accidental duplicate. Flagged for
  Carl's call; everything else stays open.

Each dropped guard (name/initials field, access code, pre-loaded roster) is **addable later without
rework** if the real fieldwork shows it's needed.

## Effort

Moderate and self-contained: the `self-register` endpoint (reuses QN assignment) + facility-token mint
+ one UI branch + a receipt screen. Consent/survey/submit untouched. **Post-pretest v-next** — nothing
to build before fieldwork.

## Open questions

1. Keep the device-bind guard even in open mode? (recommended: yes — it's free.)
2. Where does the coverage denominator come from under pure self-register?
3. Facility QR token — TTL / rotation policy for a standing per-facility token?

## Not doing (this iteration) — parked, addable later

- Hybrid pre-loaded roster (chaseable non-response denominator).
- Name/initials field + dedup.
- Access-code gate on the QR.
- Code-login / cross-device resume.
