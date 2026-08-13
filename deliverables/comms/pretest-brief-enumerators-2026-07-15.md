# Pretest brief — enumerators & STLs (pretest starts 2026-07-15)

**Draft for ASPSI (Kidd / Myra) to relay. Two items. The first one will silently break the
pretest if it is not done.**

---

## 1. ⛔ Before you start: REMOVE the app and ADD it again

New builds were deployed to CSWeb on **14 July**:

| Instrument | Version |
|---|---|
| Facility Head Survey (F1) | **v1.1.0** |
| Patient Survey (F3) | **v1.1.0** |
| Household Survey (F4) | **v1.4.0** |

**"Update Installed Applications" does NOT reliably pick these up.** If you only tap Update, you
may keep running the old build, everything will *look* fine, and the new Interview-status options
below simply will not be there.

**Do this instead, on every tablet, before the pretest:**
1. In CSEntry, **remove** the survey application.
2. **Add Application → CSWeb server**, and download it again.
3. Confirm the version in the application list matches the table above.

If the version does not match, stop and tell the STL. Do not start interviewing on an old build.

---

## 2. ⭐ NEW — "Interview status": what to do when there is NO interview

Every case now opens on an **Interview status** screen, right after you enter the Questionnaire
Number. It has **seven** options (it used to have four).

- Interview going ahead → leave it on **Continue interview**. That is the default. Do nothing.
- Interview **cannot happen at all** → still **open the case**, and pick the reason:

| Choose | When |
|---|---|
| **Not interviewed — refused** | They declined at the door / declined consent. |
| **Not interviewed — not found** | Nobody there, vacant, could not be located after your call-backs. |
| **Not interviewed — ineligible** | They do not qualify for this survey. |

The app then jumps straight to the closing screen, records the visit as **Replaced**, and ends the
case. You do **not** walk through the questionnaire.

> ### ⛔ Do NOT just skip the unit and move on.
> If you never open a case, that unit is **invisible** — the office cannot see that you went, cannot
> see why it failed, and cannot account for the replacement. **A unit you could not interview is
> still work you did.** Open the case, mark the reason, move on to the substitute.

**"Postponed" is different.** If you are coming back later, choose **Postponed / reschedule** — not
one of the "Not interviewed" options. Postponed means *revisit*. The three "Not interviewed"
options mean *this unit is being replaced by a substitute*.

---

*Consent is unchanged: read it aloud from the printed SJREB sheet (Annex H). There is no consent
screen in the app — the outcome is what you record on Interview status.*
