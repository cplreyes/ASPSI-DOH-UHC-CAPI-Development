# Viber reply to Aidan — pretest 15 July, 8:00 AM  (paste-ready)

> **Credentials are NOT in this message on purpose.** Send the `se-001…se-007` usernames +
> passwords yourself from `pretest-credentials.md` — ideally not over Viber. Everything below is
> safe to paste.

---

Good evening Aidan — thanks for following up. Three things, and **#1 is the important one.**

**1. IMPORTANT — before 8:00 AM, every tablet must REMOVE and RE-ADD the app.**

We deployed new builds to CSWeb today. CSEntry's *"Update Installed Applications"* does **not**
reliably pick these up — if you only tap Update, the tablet keeps running the OLD build, everything
looks completely normal, and the new options in #3 simply will not be there.

On each tablet:
1. In CSEntry, **remove** the survey application.
2. **Add Application → CSWeb server**, download it again.
3. Check the version in the app list:

| Instrument | Must show |
|---|---|
| Facility Head Survey (F1) | **v1.1.0** |
| Patient Survey (F3) | **v1.1.0** |
| Household Survey (F4) | **v1.4.0** |

If the version does not match, stop and tell me before starting.

**2. Household survey (F4) codes — Brgy. Mayondon, facility 040341101 (20 households):**

| Enumerator | Login | Questionnaire Numbers |
|---|---|---|
| DRamos | se-004 | 040341101001 – 040341101004 |
| SLait | se-006 | 040341101005 – 040341101008 |
| ASalazar | se-003 | 040341101009 – 040341101011 |
| PCrudo | se-007 | 040341101012 – 040341101014 |
| AParaiso | se-002 | 040341101015 – 040341101017 |
| KPura | se-005 | 040341101018 – 040341101020 |

Enter the **full 12 digits**. The app checks them against the PSGC — a made-up number is rejected
at the first field, so please use only the numbers above.

*(Passwords follow separately.)*

**3. NEW — "Interview status" screen: what to do when there is NO interview.**

Every case now opens on an **Interview status** screen with **seven** options (it had four).

- Interview proceeding → leave it on **Continue interview** (the default). Do nothing.
- Interview **cannot happen at all** → still **open the case**, and choose the reason:
  - **Not interviewed — refused** (declined at the door / declined consent)
  - **Not interviewed — not found** (nobody there, vacant, not located after call-backs)
  - **Not interviewed — ineligible** (does not qualify)

The app then jumps straight to the closing screen, records the visit as **Replaced**, and ends the
case. No need to go through the questionnaire.

⛔ **Please do not just skip the household and move on.** If no case is opened, that household is
invisible to us — we cannot see that you went, why it failed, or account for the replacement. **A
household you could not interview is still work you did.** Open the case, mark the reason, then move
to the substitute.

**"Postponed / reschedule" is different** — use that if you are coming back later. The three
"Not interviewed" options mean the household is being **replaced** by a substitute.

Consent is unchanged: read it aloud from the printed SJREB sheet. There is no consent screen in the
app — the outcome is what you record on Interview status.

Good luck tomorrow — message me if anything looks wrong at 8:00.
