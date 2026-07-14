---
type: deliverable
kind: training-deck
audience: Survey Enumerators (SEs) — CAPI field staff for F1 / F3 / F4
prepared_by: Carl Patrick L. Reyes
date_drafted: 2026-06-02
status: draft-for-review
related_task: E7-TRAIN-001
companion_to:
  - Survey-Manual/CSPro-Section-Draft_2026-04-29.md
  - Survey-Manual/CAPI-PWA-Stakeholder-Section_2026-05-02.md
tags: [training, capi, cspro, csentry, enumerator, e7]
---

# CAPI Enumerator Training Deck — F1 / F3 / F4 Walkthrough

> **How to use this file.** Each `---`-separated block is one slide. The **Slide** line is the on-screen title; bullets are the on-screen content; the *Facilitator notes* are spoken guidance / activity cues, not projected. Render to slides with Marp, `pandoc -t pptx`, or Google Slides. `[Screenshot slot: …]` markers are filled with real CSEntry captures once the F1/F3/F4 apps reach Designer-validated state (same convention as the Survey Manual CSPro-section draft).
>
> **Duration:** ~half-day session (≈3 hrs incl. hands-on). **Prerequisite:** each SE has a charged training tablet with the three apps installed.

---

### Slide 1 — Title

**UHC Survey Year 2 — CAPI Enumerator Training**
Facility Head (F1) · Patient (F3) · Household (F4)

ASPSI CAPI Team · DOH UHC Survey Year 2

*Facilitator notes:* Welcome. Confirm every SE has a tablet in hand before starting. State the goal: by the end you can run a complete interview on CSEntry, capture GPS + photo, and sync correctly.

---

### Slide 2 — What you'll be able to do by the end

- Open CSEntry and pick the right instrument for the interview in front of you.
- Run a case start-to-finish: consent → eligibility → questions → photo → GPS → accept.
- Recognise what the tablet is checking for you (skip-logic, range, consistency) and why you can't "force" a bad value.
- Sync your day's work to the server **before 10 PM** and confirm it landed.
- Know exactly what to do — and what *not* to touch — when something goes wrong.

*Facilitator notes:* Set expectations: the tablet does a lot of the error-checking that paper left to encoders. Your job is accurate capture + protocol, not fighting the device.

---

### Slide 3 — Why CAPI (and why it helps you)

- **CAPI** = Computer-Assisted Personal Interviewing. You read the question, the respondent answers, you tap the response.
- Built on **CSPro / CSEntry** — the US Census Bureau platform used in 160+ countries (DHS, MICS, WHO surveys).
- The questionnaire logic is built in: it skips the questions that don't apply, blocks impossible entries, and saves your work automatically.
- No paper to lose, no double-encoding, no transcription errors. Cleaner data, less rework for you.

*Facilitator notes:* Frame the validations as help, not obstacles — they stop the On-Hold returns that would otherwise come back to the SE days later.

---

### Slide 4 — The three CAPI instruments

| App on the tablet | Form | Who it's for | Mode |
|---|---|---|---|
| **FacilityHeadSurvey** | F1 | The facility head / officer-in-charge | On-site, you administer |
| **PatientSurvey** | F3 | A patient (or proxy) exiting the facility | On-site, you administer |
| **HouseholdSurvey** | F4 | A sampled household + every member | On-site, you administer |

- The **Healthcare Worker survey (F2)** is **not** on your tablet — HCWs complete it themselves on a web link. (Covered in a separate one-pager.)

*Facilitator notes:* Make sure SEs can name which app maps to which respondent. Common early mistake: opening the wrong app.

---

### Slide 5 — Your tablet is ready-to-use

- The ASPSI CAPI team **pre-configures every tablet** before it leaves Los Baños: CSEntry + the three apps + the sync endpoint are all set.
- You receive the tablet from your **STL**. You do **not** install, update, or delete apps yourself.
- Confirm the **lock-screen ID matches the device assigned to you**. If unsure — ask your STL before you start.
- Keep it charged (**≥ 50%** before heading out) and keep **Location** turned on.

*Facilitator notes:* Reinforce device hygiene: one SE, one assigned tablet, signed for. Lost/damaged = tell STL immediately.

---

### Slide 6 — The interview in 9 steps (the map)

1. Open CSEntry → pick the instrument.
2. Tap **'+'** → enter the case ID your STL gave you.
3. Read **consent**; record accept / refuse.
4. Pass the **eligibility** screen.
5. Work through the questions (**→** forward, **←** back).
6. Capture the **verification photo** when prompted.
7. **GPS** captures automatically — Location ON.
8. Reach the end → **"Accept this case?" → Yes**.
9. End of day → **sync before 10 PM** → confirm "Sync successful".

*Facilitator notes:* This is the spine of the whole session. We now expand each step. Tell them we'll do it together on the tablet right after.

---

### Slide 7 — Step 1–2: Start a case

- From the CSEntry main menu, tap the instrument you're about to run.
- Tap **'+'** (top of the case list) to start a new case.
- Enter the **case identifier (questionnaire number)** assigned to you by your STL — not one you make up.
- Case IDs are pre-assigned in ranges per enumerator so two SEs never collide.

[Screenshot slot: CSEntry main menu with the three instruments]
[Screenshot slot: case list with the '+' icon highlighted]

*Facilitator notes:* Stress: the STL owns the number ranges. If you run out or are unsure of your range — ask, don't improvise.

---

### Slide 8 — Step 3: Informed consent

- Read the **informed-consent script aloud** from the **printed consent sheet** (SJREB-approved wording, Annex H), in the language the respondent understands.
- Consent is **read from paper, not from the tablet.** There is no "I accept / I refuse" button in the app — do not go looking for one.
- The **outcome** of consent is what you record in the app, on the **Interview status** screen (next slide).
- Consent is voluntary and can be withdrawn at any point without affecting the respondent's care.

*Facilitator notes:* Corrected 2026-07-14. Earlier versions of this deck described an in-app consent screen with Accept/Refuse buttons. **That screen does not exist** and never did in the built instruments — the consent script lives on the printed sheet, and the outcome is captured through Interview status. Practice reading the consent aloud from the sheet.

---

### Slide 8b — Step 3b: Interview status — **and what to do when there is no interview**  ⭐ NEW

**This is the most commonly missed step. Read it twice.**

Every case opens on an **Interview status** screen, on the very first form, right after you enter the Questionnaire Number.

- If the interview is going ahead → leave it on **Continue interview**. That is the default; you do nothing.
- If the interview **cannot happen at all**, you still **open the case** and pick the reason:

| Choose | When |
|---|---|
| **Not interviewed — refused** | They declined at the door / declined consent. |
| **Not interviewed — not found** | Nobody there, vacant, could not be located after your call-backs. |
| **Not interviewed — ineligible** | They do not qualify for this survey. |

The app then jumps straight to the closing screen, records the visit as **Replaced**, and ends the case. You do **not** walk through the questionnaire.

> ### ⛔ Do NOT just skip the unit and move on.
> If you never open a case, that unit is **invisible** — head office cannot see that you went, cannot see why it failed, and cannot account for the replacement. **A unit you could not interview is still work you did.** Open the case, mark the reason, move on to the substitute.

**Postponed is different.** If you are coming back later, choose **Postponed / reschedule** — not one of the "Not interviewed" options. Postponed means *revisit*; the three "Not interviewed" options mean *this unit is being replaced by a substitute*.

*Facilitator notes:* Drill this with a role-play — a locked gate and a flat refusal. The instinct is to walk away and start the next household; that instinct loses the record. Expect the "why bother, there is no interview?" question and answer it head-on: the replacement count is how ASPSI proves the sample was worked properly, and a missing record looks the same as an unworked one. Explain plainly that replacements are monitored per enumerator — not as a threat, but because it is exactly why an honest record protects them: a hard area with many replacements is fine and expected, an area that *silently* produces no records is not.

---

### Slide 9 — Step 4: Eligibility (and F3's branch)

- Section A confirms **who you are talking to** — F3: *are you the patient?* (if not, their relationship to the patient, i.e. a proxy); F4: *are you the household head?*
- Answering "No" does **not** end the case — it routes you down the proxy-respondent path. It is an identification question, not a gate.
- If the respondent is genuinely **ineligible for the survey**, that is not handled here — go back to **Interview status** and choose *Not interviewed — ineligible* (Slide 8b).
- **F3 (Patient) specifically:** **outpatient vs inpatient** is selected on the case-start screen — this sets which path through the questionnaire the app follows. Pick carefully; it changes the questions asked.

*Facilitator notes:* Corrected 2026-07-14 — an earlier version claimed an eligibility screen "routes to the correct disposition". It does not: Section A is respondent identification and falls through to the proxy path. Ineligibility is recorded on Interview status. For F3, drill the outpatient/inpatient choice — it is the single most consequential branch.

---

### Slide 10 — Step 5: Moving through the questions

- **→** advances to the next item; **←** goes back to correct a prior answer.
- **Save & resume is automatic.** You can pause a case and reopen it from the case list later — nothing is lost.
- The app shows the item, the response field, and the navigation arrows. Tap the response, then **→**.

[Screenshot slot: data-entry screen — item, response field, nav arrows]

*Facilitator notes:* Demonstrate going back with ← to fix an answer — SEs panic when they mistap. Show that the case survives a pause.

---

### Slide 11 — What the tablet checks for you

| The app will… | Meaning |
|---|---|
| **Skip** questions that don't apply | Based on earlier answers — that's normal, not a bug |
| **Block** an impossible value (**hard**) | e.g. age below the eligible minimum — fix it to continue |
| **Warn + ask to confirm** (**soft**) | Unusual but possible value — confirm or correct |
| **End the interview** (**gate**) | A critical eligibility criterion failed |
| Flag a **cross-field contradiction** | e.g. tenure longer than age — one of them is wrong |
| Enforce the **PSGC geography cascade** | Region → Province → City/Mun → Barangay must match (PSA 1Q 2026) |

- You **cannot** type past a hard block. If a value is correct but blocked, **flag your STL** — don't fabricate a value to get past it.

*Facilitator notes:* This is the heart of data quality. Soft vs hard is a common confusion — soft = confirm, hard = must fix.

---

### Slide 12 — Step 6: Verification photo

- Where prompted, capture **one verification photograph** per case with the rear camera.
- Photo content per SOP (e.g. facility signage / setting) — it documents your **visit**, not the respondent's identity.
- **Re-take** if it's blurry or the subject isn't clearly visible. The new photo replaces the old.

[Screenshot slot: photo-capture prompt with camera icon]

*Facilitator notes:* Remind them the photo is audit evidence of presence — a missing/garbage photo can put the whole case On-Hold.

---

### Slide 13 — Step 7: GPS capture

- GPS is captured **automatically** at a set point in the questionnaire.
- **Before you start**, check the **Location** icon is ON in the notification bar (swipe down → tap Location if off).
- If GPS doesn't lock within **1 minute**, step **outside or near a window** and try again.

[Screenshot slot: notification bar with Location enabled]

*Facilitator notes:* Most GPS failures are Location-off or indoors. Make them practise enabling Location now.

---

### Slide 14 — Instrument notes: F1 Facility Head

- Respondent is the **facility head / OIC**.
- Captures facility identity + the facility's UHC implementation answers.
- PSGC cascade + facility GPS + one verification photo.
- **Result of Visit** recorded on the Field Control form — F1: Completed / Postponed / Refused / Incomplete / **Replaced** (first visit and final visit are recorded separately), plus the case disposition (In progress / Completed / Partial). **Replaced** is set for you by the app when you choose one of the *Not interviewed* options on Interview status (Slide 8b) — you never pick it by hand.

*Facilitator notes:* F1 is usually the first interview at a site and anchors the facility code that F3 links to.

---

### Slide 15 — Instrument notes: F3 Patient

- Respondent is a **patient or proxy** exiting the facility.
- **Outpatient vs inpatient branch** set at eligibility (Slide 9).
- Collects patient profile + health-seeking + PhilHealth use; **sensitive data** — handle with care and privacy.
- Links to the **F1 facility** via the facility code; patient-home location captured.

*Facilitator notes:* Emphasise sensitivity and privacy — patient health data. Confirm the proxy relationship is recorded when it's not the patient answering.

---

### Slide 16 — Instrument notes: F4 Household

- Respondent + a **full household roster** — add, edit, remove, and reorder members.
- Each member gets profile questions; some questions loop **per member**.
- **Section N expenditure grid** + bill-recall chain — work the batteries carefully.
- Watch the **roster size**: the app warns on unusual sizes; only one household head.

*Facilitator notes:* F4 is the most complex — the roster loop trips people up. We'll spend extra hands-on time here. Show add/edit/remove on the training app.

---

### Slide 17 — Step 8–9: Finish the case

- Answer through to the last item → the app prompts **"Accept this case?"**
- Tap **Yes** → the case moves from **in-progress** to **completed**.
- If it's still in the in-progress list when you expected it done → open it, **→** to the end, accept at the prompt.

[Screenshot slot: "Accept this case?" prompt]

*Facilitator notes:* "Accepted" is what makes a case eligible to sync. An un-accepted case sits on the tablet and never reaches the server.

---

### Slide 18 — End of day: Synchronize

- When you have reliable **Wi-Fi or mobile data**, tap the **synchronize** icon (**↻**, two arrows in a circle).
- **Wait for "Sync successful."** Do **not** close the app during sync.
- **Sync every day before 10 PM** — ASPSI checks the next-morning dashboard.
- If sync **fails**: confirm connectivity, retry **once**. Still failing → **flag your STL**. Your completed cases stay safe on the tablet and will sync once it's resolved.

[Screenshot slot: sync icon + "Sync successful" message]

*Facilitator notes:* Drill the 10 PM rule and "data is never lost on a failed sync." This calms the panic that makes people delete cases.

---

### Slide 19 — Do's and Don'ts (security)

**Do**
- Keep your assigned tablet charged, locked, and with you.
- Sync daily before 10 PM; hand the tablet to your STL for end-of-day review.
- Report a lost / damaged / stolen tablet to your STL **immediately**.

**Don't**
- ❌ Share your tablet or login outside your survey team.
- ❌ Delete cases or apps — ever — without explicit instruction.
- ❌ Tap a prompt you don't understand — photograph the screen and escalate.
- ❌ Copy respondent data anywhere off the tablet.

*Facilitator notes:* Tie to the NDU everyone signs and ASPSI's NPC registration (PIC-000-358-2021). Confidentiality is a contractual obligation.

---

### Slide 20 — Troubleshooting quick table

| Issue | What to do |
|---|---|
| GPS won't lock in 1 min | Location ON; step outside/near a window; wait |
| Photo blurry | Re-take; it replaces the old one |
| Tapped wrong answer | **←** back; tap the correct response |
| Case stuck in in-progress | Open → **→** to end → accept |
| Sync error | Check data; retry once; still failing → **[Escalate STL]** |
| Case disappeared | Don't restart it — **[Escalate STL]**, it may be on the server |
| App freezes | Close & reopen — cases are auto-saved |
| Unknown message | Photograph screen → **[Escalate]**; don't tap blindly |
| Tablet lost/damaged | **[Escalate STL] immediately** |

*Facilitator notes:* This mirrors the Troubleshooting appendix in the Survey Manual draft. Print it as the field card (see QRC).

---

### Slide 21 — Hands-on practice (activity)

1. Open each app, start a dummy case with a practice ID.
2. Walk a consent → eligibility → a few items → photo → GPS → accept.
3. Deliberately trigger a **hard block** and a **soft warning**; see the difference.
4. F4: build a 4-member roster, edit one, remove one.
5. Sync the practice cases; confirm "Sync successful."

*Facilitator notes:* Circulate. Watch for: wrong app, made-up case IDs, Location off, closing during sync. Pair stronger SEs with those struggling.

---

### Slide 22 — Wrap-up & checkout

- You can run a full case on all three instruments.
- You know the tablet is **helping** you with the checks.
- You will **sync before 10 PM** and confirm it landed.
- You know your **escalation path: STL first.**
- Field kit: tablet, charger, **Quick Reference Card**, STL contact card.

*Facilitator notes:* Quick verbal/check checkout: each SE demonstrates one full case before being cleared for field. Hand out the laminated QRC.

---

### Appendix A — Facilitator checklist (not projected)

- [ ] Every SE had a charged tablet with all three apps.
- [ ] Each SE completed ≥1 full case per instrument with GPS + photo.
- [ ] Each SE saw a hard block, a soft warning, and a skip in action.
- [ ] Each SE synced successfully at least once.
- [ ] QRC distributed; STL contact card filled in.
- [ ] Open questions logged for the CAPI team.

### Appendix B — Pending before main fieldwork

- Real **screenshots** replace the `[Screenshot slot]` markers once F1/F3/F4 are Designer-validated.
- **Case-ID scheme** and **CSWeb server name/URL** confirmed (Survey Manual open questions #1 / #5).
- Final **instrument list per tablet** confirmed from the validated `.dcf`.
