---
purpose: Short cover note to paste into Slack / email when sending the ASPSI open-items doc to Juvy / Dr Claro / Dr Paunlagui
related: open-items-for-aspsi.md, codebook.md
---

# Slack / email draft

Subject suggestion: **UHC Survey Y2 — six small decisions for cross-instrument data alignment**

---

Hi Juvy / Dr Claro / Dr Paunlagui,

Quick heads-up — as I was lining up the data-harmonization spec for the four instruments (F1 / F2 / F3 / F4), I surfaced **six small decisions that need ASPSI's call** before production fieldwork. None block the current sprint; all block clean cross-instrument data delivery later.

I've put them in a single doc with context, options, and a recommended default for each, so the discussion has a starting point:

📄 **`deliverables/data-harmonization/open-items-for-aspsi.md`** (in the GitHub repo: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/blob/main/deliverables/data-harmonization/open-items-for-aspsi.md)

The six items, by urgency:

**Worth resolving in the next 1–2 weeks (touches instrument design still in flight):**
1. F4 respondent sex allows 'Other' — how do we encode that across instruments?
2. F2 PWA — should we capture explicit consent as a data field? (F1/F3/F4 already do via `CONSENT_GIVEN`)
3. Add `LANGUAGE_USED` to FIELD_CONTROL across F1/F3/F4? (F2 already has the locale at runtime.)

**Operational, can be answered any time before main fieldwork:**
4. Facility master list — when can ASPSI publish the canonical version? (F2 PWA currently uses a placeholder.)
5. Pin one PSGC vintage for the engagement (recommend PSA 2023Q4).
6. Confirm F1's `QUESTIONNAIRE_NO` scheme reconciles with the facility master list's `facility_id` scheme.

**How to respond**: even a one-line "OK to recommendation" on each is enough where you're happy with the defaults. The full doc has context + options for the items where you'd want to push back.

Goal is to lock these before F1 enters production fieldwork so the data pipeline runs clean the first time.

Thanks,
Carl

---

# Tone notes

- This is for Juvy + the senior ASPSI / DOH stakeholders. Should read as "small operational asks" not "engineering deep-dive".
- Items 4–6 are gentle — ASPSI may already be working on them; the doc just formalises the request.
- Items 1–3 are the ones where their answer materially shapes my work.
