# F2 HCW Survey — Pretest Facilitator Guide (LPH-Bay)

**Round:** F2 Pretest · **Facility:** LPH-Bay District Hospital (facility `040340210`, EA D2)
**Dates:** 2026-07-16 → 17 · **Build:** production `v2.1.0` (spec `2026-07-14-r7`)
**Enrollment model:** **Model C — numbered self-register links** (no app install, no token, no HCW-ID typing)
**Companion:** `F2-Pretest-2026-07-16-Admin-Portal-and-Monitoring-Guide.md`
**Coordinator:** Carl Patrick L. Reyes

> **What's different from earlier rounds.** Before, an enumerator pasted a tablet token to enroll. **Now the HCW answers on their own phone** by opening a personal pre-numbered link (or scanning its QR). The link claims their questionnaire number automatically and drops them straight into consent → survey. Your job is to hand out the right link and monitor — not to run the survey for them.

---

## 1. Quick reference

| Item | Value |
|---|---|
| Survey (HCW side) | `https://uhc-hcw.asiansocial.org` (opened via each HCW's link) |
| HCW links / QR cards | `deliverables/F2/pretest-2026-07-16/lph-bay-hcw-links.html` — **print this** (25 cards). CSV: `…/lph-bay-hcw-links.csv` |
| Capacity | **25 pre-numbered HCW slots** — `LPHBAY-HCW-01`…`HCW-25` → QN `040340210101`…`125` |
| Admin portal (monitor) | `https://uhc-hcw.asiansocial.org/admin` — see companion guide |
| Slack | `#f2-pwa-uat` on `aspsi-doh-uhc-survey2.slack.com` |

> **The links are confidential.** Each QR encodes a private key (`?k=…`). A leaked card = someone could submit as that HCW. Hand them out person-to-person; don't post them in a group chat.

---

## 2. What each HCW experiences (verified end-to-end on a real device)

1. HCW **scans their card's QR** with their phone camera (or opens the printed link).
2. The phone browser opens the survey — **already numbered** ("Opening your survey…" → straight to consent). No login, no app, no typing a number.
3. HCW reads the **Informed Consent**, taps **I agree** (or **I do not wish to participate**), taps **Continue**.
4. HCW answers the survey **on their own phone**, at their own pace. Progress saves automatically; they can pause and resume.
5. HCW taps **Submit** at the end → "Thank you". The response syncs to the server automatically (even if they were briefly offline).

That's the whole flow. It works offline mid-survey and resumes cleanly.

---

## 3. Your workflow at the facility

**Before you start:** print the QR card sheet (Section 1). Have the coordinator confirm the admin portal shows 25 `enrolled` slots at `040340210` (companion guide §3).

For each healthcare worker:

1. **Introduce the survey** (short script below).
2. **Hand them ONE card** — the next unused HCW number. Cross it off your printed sheet so no card is reused.
3. **Ask them to scan the QR** with their phone camera and follow the prompts. Stay nearby for the first tap in case they need help opening it.
4. **Let them answer privately.** It's self-administered — don't read the questions to them or watch their answers unless they ask for help.
5. **Confirm they reached "Thank you"** (submitted) or that they declined. Then move to the next HCW with the next card.

> **One card = one HCW.** Never give the same card to two people — it's a single questionnaire number.

### Short intro script (adapt to local language)
> "Good day po. The Department of Health, through ASPSI, is running a short survey for healthcare workers about your experience with Universal Health Care. It's voluntary and anonymous — your name is never attached. It takes about 10–15 minutes on your own phone. May I give you your link? You just scan this QR, read the consent, and answer at your own pace."

---

## 4. HCWs without a smartphone / who can't self-answer

The model assumes personal phones, but plan for exceptions:

- **No smartphone / declines to use their own:** lend a facility/enumerator phone, open the HCW's card there, let them answer, then **fully close the browser tab afterward** so the next HCW starts clean (a shared device stays enrolled to the last person otherwise — see §5).
- **Prefers paper:** record on the paper HCW form, then the coordinator **encodes it in the admin portal** later (companion guide §6) against that HCW's number.
- **Refuses entirely:** that's valid data — have them tap **"I do not wish to participate" → Continue** (records a refusal), or the coordinator marks it. Don't leave the slot blank if you can capture the refusal.

---

## 5. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| QR won't scan | Use the phone's **camera app** (not a random scanner); or type the link from the card. Ensure the phone has data/wifi for the first open. |
| "Invalid or expired link" | Wrong/rotated card. Get a fresh card from the coordinator (reprint rotates that HCW's link — companion guide §5). |
| "This link's survey is already completed" | That HCW already submitted or refused. Correct — don't re-issue the same card. |
| Shows someone else's half-finished survey (shared phone) | The phone is still enrolled to a previous HCW. On that phone: **Sync → Change enrollment → OK**, then open the new HCW's card. (On personal phones this never happens.) |
| Loses signal mid-survey | Fine — it keeps working offline and saves locally; it syncs when signal returns. Don't restart. |
| Phone died / closed before submit | Reopening the **same card** on the **same phone** resumes the draft. On a different phone the draft doesn't carry over. |

---

## 6. Monitoring during the day

The coordinator (or any `se_00x` / admin account) watches **Admin → Data → HCWs** filtered to facility `040340210`: each slot flips `enrolled → submitted` (done) or `refusal`. That's your live completion tracker — see the companion guide. Aim to account for all 25 (submitted or refusal) by end of D2.

---

## 7. Reporting issues

Anything that slows, confuses, or blocks an HCW → post to `#f2-pwa-uat` (Slack is the reporting channel for this round). Include: what the HCW was doing, the HCW number, the phone (model/OS), what you expected vs. what happened, and a screenshot if visual. Criticals (can't open links, can't submit) → flag immediately, don't wait.

> Keep reporting in Slack, not on GitHub — the GitHub repo is public, and HCW numbers / facility IDs / device details shouldn't be posted there.
