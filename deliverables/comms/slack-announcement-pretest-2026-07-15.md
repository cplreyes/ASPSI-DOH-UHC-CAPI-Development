# Slack announcement — CAPI Pretest (post in `#capi-scrum`)

> **Draft for Carl to post.** Not sent. Credentials are deliberately absent — send those privately.
> Pin this message after posting.

---

:rotating_light: **CAPI PRETEST — tomorrow, 15 July, 08:00** · Brgy. Mayondon, Los Baños

**Full guide (read this first): https://csweb.asiansocial.org/docs/pretest-guide.html**
**Findings tracker: #839** — label every finding `from-pretest-2026-07`

---

**:warning: Everyone — BEFORE 08:00: remove the app and add it again.**
New builds went out today. CSEntry's *"Update Installed Applications"* does **not** reliably pick up a
CSWeb redeploy — tap Update only, and the tablet silently keeps yesterday's build, everything looks
normal, and none of today's changes are there.

CSEntry → remove the app → **Add Application → CSWeb server** → download again → **check the version**:
• Facility Head (F1) **v1.1.0**  • Patient (F3) **v1.1.0**  • Household (F4) **v1.4.0**
If it doesn't match — **stop**, don't interview on an old build.

---

**:new: New this round — "Interview status" (replacements)**
Every case now opens on an **Interview status** screen with **seven** options (was four).
• Interview going ahead → leave it on **Continue interview**.
• Interview **can't happen at all** → **still open the case**, pick the reason: *Not interviewed — refused / not found / ineligible*. The app jumps to the closing screen, records **Replaced**, and ends the case.

:no_entry: **Don't just skip the unit and move on.** No case = that unit is invisible to us. We can't see that you went, why it failed, or account for the replacement. **A unit you couldn't interview is still work you did.**
*Postponed / reschedule is NOT a replacement — that's for when you're coming back.*

---

**By role**
• **Enumerators** — QNs from your assignment sheet, full 12 digits (the app rejects made-up numbers). Consent is read aloud from the printed SJREB sheet; there's no consent screen in the app.
• **Supervisors / STLs** — confirm *every* tablet re-added the app and shows the right version. End of day: everyone syncs. Then reconcile assigned vs synced **including replacements**.
• **Data Manager (CSWeb)** — Sync Dashboard: https://csweb.asiansocial.org/docs/dashboard.html (refreshes ~2 min). New **Replacements** tile + per-enumerator **Replaced** column. It reads 0 until the first sync lands — that's "no data yet", not "no replacements".
• **F2 Admin** — portal https://uhc-hcw.asiansocial.org/admin. F2 was reset to a clean state on 14 July: recreate users + HCWs, reissue enrolment links.

---

**:memo: This is a PRETEST, not a UAT round.**
We're not asking *"does the app work?"* — we're asking **"does the questionnaire work on a real respondent?"** The findings we most want are the ones only a pretest can catch: a question the respondent didn't understand, one you had to explain twice, a skip that felt wrong, how long an interview really takes, a translation that didn't land. **If a respondent was confused, quote them.** That's worth more than a cosmetic bug.

File on **#839** → *New issue → "CAPI UAT feedback"* → label **`from-pretest-2026-07`** + a severity.

**Credentials are sent to each of you privately.** If you don't have yours by 07:30, message me directly.

Good luck tomorrow :muscle:
