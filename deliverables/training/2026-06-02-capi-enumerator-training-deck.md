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

- Every interview opens with the **informed-consent screen** (SJREB-approved wording, Annex H).
- Read it to the respondent in the language they understand.
- Record their choice:
  - **Accept** → the questionnaire unlocks and you proceed.
  - **Refuse** → the app records the refusal, sets the disposition, and **ends the interview** — do not continue.
- Consent is voluntary and can be withdrawn at any point without affecting the respondent's care.

*Facilitator notes:* This is non-negotiable and audited. No consent screen completed = no interview. Practice reading the consent aloud.

---

### Slide 9 — Step 4: Eligibility (and F3's branch)

- After consent, an **eligibility screen** must pass before the main questionnaire loads.
- If the respondent fails eligibility, the app routes to the correct disposition — you do not force entry.
- **F3 (Patient) specifically:** at eligibility you select **outpatient vs inpatient** — this sets which path through the questionnaire the app follows. Pick carefully; it changes the questions asked.

*Facilitator notes:* For F3, drill the outpatient/inpatient choice — it's the single most consequential branch. For F1/F4, eligibility is the gate to the main form.

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
- Disposition + AAPOR codes recorded (completed / partial / refused / ineligible / contact attempt).

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
