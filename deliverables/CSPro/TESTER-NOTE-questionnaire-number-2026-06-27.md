# Tester note — entering the Questionnaire Number (F1 / F3 / F4)

*For ASPSI to relay to CAPI testers before the pre-test. CSEntry, all three instruments.*

## What changed
The very first field of every interview is the **12-digit Questionnaire Number**, and the app now **checks it against the official PSGC list before the interview can start**. If the number's geographic part isn't a real region / province / city, you'll see:

> **"Geo prefix … not found in PSGC. Check the Questionnaire Number."**

…and you **won't be able to move past the first screen.** This is intentional — it stops cases from being saved against an invalid location.

## What you need to do
**Enter the real, assigned Questionnaire Number for your facility — not a made-up or placeholder number** (no `000000000000`, `123…`, etc.). Use the number provided for your assigned pre-test facility.

The 12 digits are read as:

```
R R  P P  M M M  F F  S S S
└┬┘  └┬┘  └─┬─┘  └┬┘  └─┬─┘
region prov  city  facility  sequence
```

## Valid example for the pre-test (Laguna test facility)
- **`040340002001`** → resolves on screen to **Region IV-A (CALABARZON) / Laguna / Cabuyao City Hospital**.
  - The app fills in the Region / Province / City names automatically — **check they match the facility you're at.** If they don't, the number was typed wrong.

(F1 also checks the facility code against the facility list; F3/F4 only need the region/province/city to be valid.)

## If you get the error
1. Don't restart the app — just **re-type the Questionnaire Number** correctly.
2. Confirm the auto-filled Region / Province / City names match your facility.
3. If a number you believe is correct is still rejected, report it (with the exact number) — the facility may be missing from the PSGC/facility reference and we'll add it.

---
*Prepared 2026-06-27 from desktop CSEntry verification of the deployed F1/F3/F4 builds.*
