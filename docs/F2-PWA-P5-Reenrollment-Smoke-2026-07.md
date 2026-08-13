# F2 PWA — P5 Re-enrollment Smoke Round (new origin: uhc-hcw.asiansocial.org)

| | |
|---|---|
| **Round** | P5 re-enrollment smoke (serving-migration gate, NOT a full UAT round) |
| **Window** | Opens **Fri 2026-07-10** · Closes **Tue 2026-07-14** (0.5–1 day of tester time) |
| **Surface under test** | `https://uhc-hcw.asiansocial.org` — F2 PWA + Admin Portal served by f2-api, store = csweb_f2 MySQL |
| **App / spec** | header shows `v… · spec 2026-07-02-r6` (verify on device) |
| **Plan of record** | `deliverables/F2/F2-Prod-Migration-Plan.md` §3 P5 · sprint lane E4-F2-ELESTIO (S013 Goal A) |
| **Gate** | **Zero P1-severity findings** → P6 retirement proceeds |

> **Why this round:** P4 flipped authority — csweb_f2 MySQL on our own server is now
> F2's store of record; the Cloudflare/Google stack is frozen (kill_switch) and retires
> at P6. The JWT signing key changed at migration, so **every device must re-enroll**
> at the new origin with a fresh token. This smoke round proves the four legs of the
> plan's checklist on the production origin: self-admin submit · refusal path (#825) ·
> admin dashboards · offline queue — plus the 12-digit QN assigning end-to-end.

> **⚠️ STOP using `f2-pwa.pages.dev`.** The old origin still LOOKS enrolled (the app
> only checks the token's expiry client-side) but every sync now fails — a
> working-looking form whose submissions never land. All testing happens at
> `uhc-hcw.asiansocial.org`. The old admin portal is read-only by policy.

---

## ⚠️ Coordinator pre-flight (Carl — do BEFORE opening the round)

1. **Log in at `https://uhc-hcw.asiansocial.org/admin`** with your existing admin
   credentials (all 10 admin users migrated with their passwords intact). If the
   portal forces a password change on first login, that's the migrated
   `password_must_change` flag — complete it; there is no skip.
2. **Old-queue drain check** (one-time): ask each R5 tester to open the OLD origin's
   Sync page and confirm **0 pending** rows. Old-origin pending rows are stuck (they
   can never sync anywhere) — anything pending must be re-entered at the new origin
   by hand. (P4's counts gate matched 41=41, so queues should already be empty.)
3. **Reissue tokens** for each roster row below: Admin → Data → **HCWs** tab → find
   the HCW → amber **Reissue** → confirm → the modal shows a **QR code + enrollment
   URL + raw token + expiry** (30-day default). Copy each URL into §3. If you get
   "token already reissued by another admin; refresh and retry", refresh the row and
   redo — that's the concurrency guard working.
4. **QN leg — create ONE new HCW on a real 9-digit facility**: HCWs → **Create** →
   HCW ID `p5-qn-check`, Facility ID `040340002` (Laguna UAT facility). The QN
   auto-assigns (expect `040340002001` if this is the first 9-digit enrollment on the
   new store). Reissue its token too — one tester walks it end-to-end (§5, leg E).
5. **Tracking issue + label**: ✅ done — label `from-p5-reenroll-2026-07`, tracking
   issue [#836](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/836).
   (This is a smoke round; it does not consume a UAT round number.)
6. **Announce in `#f2-pwa-uat`** with the kickoff draft at the bottom of this doc.

*Until steps 1–6 are done this guide is a draft — don't send it with empty token cells.*

---

## 1. Quick Reference

| What | Where |
|---|---|
| Survey app (new origin) | `https://uhc-hcw.asiansocial.org` |
| Admin Portal | `https://uhc-hcw.asiansocial.org/admin` (existing usernames + passwords) |
| Unified monitoring dashboard | csweb dashboard — F2 section now reads the live store |
| Bug repo | `cplreyes/ASPSI-DOH-UHC-CAPI-Development` · label `from-p5-reenroll-2026-07` |
| Slack | `#f2-pwa-uat` |
| Old origin (do NOT test) | `f2-pwa.pages.dev` — frozen; admin read-only by policy |

## 2. Roster + token assignments

| Tester | HCW ID | Facility | Fresh enrollment URL (30-day token) |
|---|---|---|---|
| Shan | DEMO-HCW-004 | DEMO-FAC-RHU-QC-1 | *pinned post in #f2-pwa-uat* |
| Kidd | DEMO-HCW-007 | DEMO-FAC-DH-INFANTA | *pinned post in #f2-pwa-uat* |
| Marriz | DEMO-HCW-002 | DEMO-FAC-RHU-QC-1 | *pinned post in #f2-pwa-uat* |
| Aly | DEMO-HCW-005 | DEMO-FAC-RHU-QC-1 | *pinned post in #f2-pwa-uat* |
| (QN leg — one volunteer) | p5-qn-check | 040340002 | *pinned post in #f2-pwa-uat* |

> **Live enrollment URLs are never written into this document** (the repo is public).
> They're distributed via the pinned post in `#f2-pwa-uat` (R6 credential policy) —
> personal per tester; a leak is fixed by reissuing (which revokes the leaked token).
> No password is needed on the survey side; the token in your URL is your
> authentication. Admin-side: your existing R5 username/password works at the new
> origin.

## 3. Per-tester smoke checklist (~30–40 min)

**A. Re-enroll (cold)**
1. Open YOUR enrollment URL from §2 in your device's browser (or scan the QR).
   Expect the enrollment screen with the token pre-filled.
2. Tap **Verify token** → "Token accepted for facility …".
3. Step 2 asks for your HCW ID — **type it exactly** as in §2 (it's a text box, not a
   picker; the "pick yourself from the roster" wording is a known copy quirk).
4. Tap **Enroll** → the consent screen appears (per-case SJREB gate, #808).
5. ✅ File a bug if: token rejected ("Token malformed…" = coordinator must reissue),
   facility name wrong, or you land anywhere other than consent.

**B. Self-admin submit (online)**
1. Agree on the consent screen → complete the questionnaire normally → Submit.
2. Expect the thank-you screen and NO pending badge in the header.
3. ✅ Header must read `spec 2026-07-02-r6`.
4. The **language switcher is live** (English-only mode was reverted 2026-06-27, #774) —
   English + the 7 PSA-target languages. Untranslated strings still fall back to English;
   that's expected, not a bug. Test in English unless you're specifically checking a locale.

**C. Refusal path (#825) — new since R5, first time in a tester script**
1. Tap **Start over** (fresh case) → on the consent screen choose
   **"I do not wish to participate."** → **Continue**.
2. Expect the "Thank you for your time" declined screen — no location prompt, no
   further questions.
3. The refusal is DATA: it queues and syncs like a submission (verify in leg D/F).

**D. Offline queue**
1. **Start over** → airplane mode ON → complete a survey → Submit.
2. Expect: thank-you screen says the response is saved on-device, header shows the
   amber **"1 pending"** badge; Sync page lists it under Pending.
3. Airplane mode OFF → within ~30 s (or tap **Sync now**) the row moves to Synced and
   the badge clears.
4. ✅ File a bug if the row lands in "retry" with an error while online, or the badge
   never clears.

**E. QN end-to-end (the volunteer with `p5-qn-check` only)**
1. Enroll with the `p5-qn-check` URL — facility `040340002` is a real 9-digit PSGC
   code, so the enrollment carries an auto-assigned 12-digit QN.
2. Submit one survey. In the Admin Portal → Data → Responses, the row must show
   QN `040340002001` (12 digits, leading zero intact).

**F. Admin dashboards (Marriz leads, everyone spot-checks)**
1. Log in at `/admin` (existing credentials; complete the forced password change if
   prompted — one-time, migrated flag).
2. Data → **Responses**: today's submissions from legs B–E all present; the refusal
   rows show status **refusal**.
3. Data → **HCWs**: your row shows status **Enrolled** (or **Refusal** after leg C —
   the tag is forward-only and expected); `p5-qn-check` shows its QN.
4. **Sync Report / Map**: today's counts move.
5. The unified csweb monitoring dashboard's F2 tile reflects the new totals within
   ~2 minutes (it reads the live store directly now).

## 4. Bug filing

One GitHub issue per finding, label `from-p5-reenroll-2026-07`, linked to the round's
tracking issue. Use the R5 template fields (step, tester, device, HCW, expected vs
actual, severity, screenshot). **Severity P1** = a leg above cannot complete at all on
the production origin — P1s stop the P6 retirement clock.

## 5. Triage + close

Daily 09:00 PHT check in `#f2-pwa-uat` while the window is open. Round closes with a
disposition per finding (fix-now / next-sprint / survey-team / won't-fix). **Gate:
zero open P1s → Carl calls P5 PASSED and P6 (CF/Google retirement + rotations) is
unblocked.**

---

## 📣 Kickoff draft (coordinator posts to #f2-pwa-uat)

> 📣 **F2 re-enrollment smoke is open — new production home** (Fri Jul 10 – Tue Jul 14)
> F2 has moved off Cloudflare/Google onto our own production server. Everything now
> lives at **https://uhc-hcw.asiansocial.org** — same app, same spec (2026-07-02-r6),
> new address and a fresh security key, so **everyone re-enrolls once**.
> • Your personal enrollment link is in the guide (§2) — old links/bookmarks are dead
> • ~30–40 min: re-enroll → submit → refusal path → offline test → admin spot-check
> • Admin portal: **uhc-hcw.asiansocial.org/admin** — your existing username/password
> • ⚠️ Do NOT use f2-pwa.pages.dev anymore (it looks alive but can't sync)
> • Bugs: label `from-p5-reenroll-2026-07` — P1 = a step you cannot complete at all
> Guide: `docs/F2-PWA-P5-Reenrollment-Smoke-2026-07.md`
