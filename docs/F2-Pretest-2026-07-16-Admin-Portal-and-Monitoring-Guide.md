# F2 Admin Portal & Monitoring — Pretest Guide (LPH-Bay)

**Round:** F2 Pretest · **Facility:** LPH-Bay District Hospital (`040340210`) · **Dates:** 2026-07-16 → 17
**Portal:** `https://uhc-hcw.asiansocial.org/admin` · **Build:** production `v2.1.0`
**Companion:** `F2-Pretest-2026-07-16-Facilitator-Guide-HCW-Survey.md`

> This is the monitoring + operations side. You'll log in, watch the 25 HCW slots fill in, reprint a lost link, and (if needed) encode a paper response. You do **not** touch the survey questions here — that's the HCW's phone.

---

## 1. Log in

Go to `https://uhc-hcw.asiansocial.org/admin`.

| Who | Username | Password |
|---|---|---|
| Field team (7) | `se_001` … `se_007` | **their shared field password** — the SAME one they use for CSWeb + hub login. Sheet: `deliverables/F2/pretest-2026-07-16/f2-admin-credentials.md` → points to `pretest-credentials.md`. |
| Carl | `carl_admin` | (Carl's) |
| Marriz | `marriz_admin` | (Marriz's) |

All 9 accounts are **Administrator** (full access). One password per person across CSWeb, hub, and this portal.

> Keep the credentials sheets confidential; they're git-ignored and never committed.

---

## 2. The portal at a glance

Top nav (Administrators see all):

- **Data** — the working area during the pretest: `Responses`, **`HCWs`**, `Audit`, `DLQ` tabs.
- **Reports** — `Sync Report` + `Map Report` (roll-ups; light during a one-facility pretest).
- **Apps** — build version, broadcast banner, **kill switch**, files, breakout settings.
- **Users / Roles** — account + RBAC management (leave as-is unless adding people).

---

## 3. Monitor completion — Data → HCWs (your main screen)

1. **Data → HCWs.**
2. In **Facility ID**, type `040340210` (LPH-Bay). You'll see the 25 slots `LPHBAY-HCW-01…25` (QN `…101…125`).
3. Watch the **status** of each slot — the status pills are your live tracker:

| Status | Means |
|---|---|
| **enrolled** | slot is ready / link claimed, HCW hasn't submitted yet |
| **submitted** | HCW completed and submitted the survey ✅ |
| **refusal** | HCW declined (recorded as data — also a valid outcome) |
| **revoked** | slot disabled (not used in this pretest) |

Filter by the status pills to see who's **submitted** vs still **enrolled**. **Goal: all 25 accounted for (submitted or refusal) by end of D2.** Each row's **View responses** jumps to that HCW's submission.

> The list is a snapshot — refresh the page to pull the latest. A just-submitted survey can take a few seconds to appear after the phone syncs.

---

## 4. See the actual answers — Data → Responses

- **Data → Responses**, filter **Facility ID** = `040340210`.
- Each row = one submission. Click a row for the full **response detail** (every answer, the QN, consent, submit time, GPS if captured).
- Use this to spot-check that answers look sane and that the QN matches the HCW you handed the card to.

---

## 5. Generate / reprint the HCW links — HCWs → "Facility links"

The 25 links are already generated and printed (facilitator guide). Use this only to **reprint** (e.g., a lost card):

1. **Data → HCWs → "Facility links"** (button next to *+ Create HCW*).
2. Facility ID `040340210`, short code `LPHBAY` → **Generate links**.
3. You get the 25 links + **Copy all** / **Print**.

> ⚠️ **Regenerating rotates every secret** — all previously printed cards stop working. Only do a full regenerate if you're reprinting the whole set; then redistribute. For the pretest the set is already generated, so avoid regenerating unless necessary.

---

## 6. Encode a paper response (fallback)

If an HCW answered on paper:

1. **Data → HCWs**, find their slot (e.g., `LPHBAY-HCW-07`).
2. Row action **Encode** → opens the encoder for that HCW's number.
3. Enter the answers from the paper form → submit. It lands as a `paper_encoded` response against that QN.

---

## 7. Things to leave alone (unless you mean it)

- **Apps → Kill switch:** turns OFF all submissions system-wide. Leave it **off** (submissions enabled). Only flip it in an emergency, and turn it back.
- **Apps → Broadcast:** shows a banner to every HCW device. Fine for a "survey open until 5pm" note; keep it short.
- **Users / Roles:** don't delete/rename roles mid-pretest — accounts depend on them.
- **Reissue token** (per-row): the old per-HCW token flow — not needed for Model C links; ignore it this round.

---

## 8. Daily monitoring rhythm

- **Morning:** confirm portal loads, 25 slots present at `040340210`, kill switch off.
- **Through the day:** keep **Data → HCWs** open; watch `enrolled → submitted/refusal`.
- **End of day:** count submitted + refusal vs 25; note any still `enrolled` (not yet done) and follow up. Post a short tally + any issues to `#f2-pwa-uat`.
