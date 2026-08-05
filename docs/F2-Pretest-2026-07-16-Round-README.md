# F2 HCW Survey — Pretest Round (LPH-Bay) — READ ME FIRST

**Instrument:** F2 — DOH UHC Survey Year 2, Healthcare Worker Survey (self-administered PWA)
**Facility:** LPH-Bay District Hospital · facility `040340210` · EA **D2** · **2026-07-16 → 17**
**Enrollment model:** **Model C — numbered self-register links** (HCW answers on their own phone; no app, no token)
**Status:** ✅ **OPEN — production, verified, provisioned**
**Coordinator:** Carl Patrick L. Reyes · **Slack:** `#f2-pwa-uat`

---

## Readiness (verified 2026-07-16)

- **Deployed to production** (`uhc-hcw.asiansocial.org`): Model C backend + DDL + frontend. Health green, kill switch off.
- **Device-verified end-to-end** on a real phone: scan link → claim questionnaire number → consent → survey → submit → lands in the server DB → refusal tag works.
- **Provisioned:** 25 pre-numbered HCW slots + links at LPH-Bay; 9 admin accounts.
- Full test suite green (528 app / 80 server), production build clean.

---

## The package (this round's artifacts)

| Artifact | Path | For |
|---|---|---|
| **Facilitator guide** (run the HCW survey) | `docs/F2-Pretest-2026-07-16-Facilitator-Guide-HCW-Survey.md` | Field team |
| **Admin portal & monitoring guide** | `docs/F2-Pretest-2026-07-16-Admin-Portal-and-Monitoring-Guide.md` | Coordinator / monitors |
| **HCW QR cards** (25, printable) | `deliverables/F2/pretest-2026-07-16/lph-bay-hcw-links.html` 🔒 | Hand-out |
| **HCW links (CSV)** | `deliverables/F2/pretest-2026-07-16/lph-bay-hcw-links.csv` 🔒 | Reference |
| **Admin account credentials** | `deliverables/F2/pretest-2026-07-16/f2-admin-credentials.md` 🔒 | Login |
| **Slack announcement** (paste) | `docs/F2-Pretest-2026-07-16-Slack-Announcement.md` | Coordinator |

🔒 = git-ignored (contains live secrets — never commit or post publicly).

---

## Accounts (F2 Admin portal · `uhc-hcw.asiansocial.org/admin`)

- **Field team:** `se_001`…`se_007` — **same password as their CSWeb + hub login** (one password everywhere).
- **Carl:** `carl_admin` · **Marriz:** `marriz_admin`.
- All 9 are **Administrator**. Passwords in the credentials sheet above.

## Links (HCW self-register · `uhc-hcw.asiansocial.org/e/…`)

- **25 pre-numbered slots:** `LPHBAY-HCW-01`…`HCW-25` → QN `040340210101`…`125`.
- Each is a personal `…/e/LPHBAY-HCW-NN?k=<secret>` link; the QR sheet is the print-and-hand-out form.
- **Reprint** a lost card via Admin → HCWs → **Facility links** (regenerating rotates all secrets — see admin guide §5).

---

## How the round runs

1. **Print** the QR card sheet. **Confirm** in the admin portal that 25 slots show at `040340210`.
2. **Facilitators** hand each HCW their card → HCW scans → self-answers → submits. One card per HCW.
3. **Coordinator** monitors **Data → HCWs** (facility `040340210`): each slot flips `enrolled → submitted/refusal`. Target: all 25 accounted for by end of D2.
4. **Issues** → `#f2-pwa-uat` (Slack is this round's reporting channel — not GitHub; the repo is public). Criticals (can't open link / can't submit) → flag immediately.
5. **Close:** coordinator tallies submitted/refusal vs 25, dispositions any issues.

---

## Confidentiality

The QR/links (`?k=`) and admin passwords are live credentials. Distribute person-to-person; never post them in group chats or commit them. All secret-bearing files here are git-ignored by policy.
