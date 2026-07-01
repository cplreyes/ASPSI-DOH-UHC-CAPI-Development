# Crosswalk Native-Capture Shot-List (device session)

> ## ✅ 2026-06-30 STATUS — F3 + F4 fully native (wired)
>
> Captured on the **itel P10001L** (the original 800×1280 device that produced the existing native shots), by navigating live CSEntry cases via the nav tree.
>
> - **F3 — DONE.** Added `f3-capi-yesno` (Q35), `f3-capi-single-select` (Q84), `f3-capi-long-select` (Q44), `f3-capi-number` (questionnaire pad). `f3-crosswalk.html` repointed: **56 borrowed-F1 refs → 0**, banner updated, 0 broken images.
> - **F4 — DONE.** Added `f4-capi-yesno` (Q1), `f4-capi-single-select` (Q4), `f4-capi-long-select` (Q11 education), `f4-capi-number` (questionnaire pad), `f4-capi-freetext` (Q-name). `f4-crosswalk.html` repointed: **61 → 0**, banner updated, 0 broken images.
> - **F2 — complete** (unchanged).
> - **F1 — RESOLVED on accepted borrow (Carl's call 2026-06-30):** keeps `f4-capi-checkbox` ×7 by design. A native `f1-capi-checkbox.png` would need a filled F1 case at the Q34 checkbox, but Q34 is conditionally hidden by F1's skip logic and ~40 fields deep; since CSEntry renders check-boxes identically, the borrow is a deliberate, honest exception (only the title bar / option text differ).
> - **Deferred F3 enhancements:** dedicated `f3-capi-amount-matrix` / `f3-capi-rating-scale` / `f3-capi-roster` shots (the Q98/Q107/Q113 + Q131–140 + Q92 rows now use native F3 single-select/number — native, just not the bespoke matrix/rating shot). Needs a hole-free F3 case to capture cleanly.



**Companion to** `crosswalk-capture-punchlist.md`. **Generated 2026-06-30** from an exact `<img src>`
audit of the four crosswalk HTMLs (counts are deterministic, not estimates).

**Purpose:** turn the remaining "borrowed-F1 screen" gaps into a tight, do-once device checklist.
Capture each shot below, drop it in `docs/img/`, then run the repoint map at the bottom.

---

## State as audited (2026-06-30)

- **No broken `<img>` paths** — every referenced image exists. **No paper-only / "pending screen" rows** —
  every detailed section already has a screen panel; the only gap is *borrowed vs native*.
- **F2 — complete.** 10 real web shots, correctly paired. No captures. (One desk confirm only: I/J numbering, below.)
- **F1 — reference instrument, 14 native standard-control shots**, BUT it borrows `f4-capi-checkbox.png` ×7 for its
  own check-box rows. Needs **1 native shot** (own checkbox). P2 polish optional.
- **F3 — 56 borrowed-F1 refs remain** (only the checkbox is native, ×9). Biggest gap. Needs **7 native shots**.
- **F4 — 61 borrowed-F1 refs remain** (native: checkbox ×12, expenditure-grid ×6, roster ×2). Needs **5 native shots**.

**Total required native captures: 13** (F1 ×1 + F3 ×7 + F4 ×5). F1 P2 polish = 3 optional extras.

---

## Borrowed → native map (the gap, exactly)

### F3 (56 borrowed refs → 7 native shots)
| Borrowed slug (now) | Refs | Control it stands in for | → Capture (native) |
|---|---|---|---|
| `f1-capi-c-uhc-entry.png` | 19 | Yes/No single-select | `f3-capi-yesno.png` |
| `f1-capi-b-facility-profile.png` | 19 | short single-select *(incl. rating-scale rows — see note)* | `f3-capi-single-select.png` |
| `f1-capi-c-attribution.png` | 9 | long single-select | `f3-capi-long-select.png` |
| `f1-capi-q3-q4-demographics.png` | 9 | number-pad *(incl. amount-matrix rows — see note)* | `f3-capi-number.png` |
| — (weak proxy, subset of the above) | — | 5-pt **rating scale** → Q131–Q135, Q136–Q140, Q178 | `f3-capi-rating-scale.png` |
| — (weak proxy, subset of the above) | — | payment **amount matrix** → Q98, Q107, Q113 | `f3-capi-amount-matrix.png` |
| `f3-capi-checkbox.png` (done ✓) | 9 | check-box tick-all (Q92 etc.) | — |
| optional | — | Q92 payment **roster** view | `f3-capi-roster.png` |

### F4 (61 borrowed refs → 5 native shots)
| Borrowed slug (now) | Refs | Control it stands in for | → Capture (native) |
|---|---|---|---|
| `f1-capi-c-uhc-entry.png` | 25 | Yes/No single-select | `f4-capi-yesno.png` |
| `f1-capi-c-attribution.png` | 17 | long single-select / rating | `f4-capi-long-select.png` |
| `f1-capi-b-facility-profile.png` | 13 | short single-select | `f4-capi-single-select.png` |
| `f1-capi-q3-q4-demographics.png` | 5 | number-pad | `f4-capi-number.png` |
| `f1-capi-q1-name.png` | 1 | free-text + keyboard | `f4-capi-freetext.png` |
| `f4-capi-checkbox.png` (done ✓) | 12 | check-box tick-all | — |
| `f4-capi-expenditure-grid.png` (done ✓) | 6 | expenditure grid | — |
| `f4-capi-roster.png` (done ✓) | 2 | household roster (loop) | — |

### F1 (7 borrowed refs → 1 native shot)
| Borrowed slug (now) | Refs | Control it stands in for | → Capture (native) |
|---|---|---|---|
| `f4-capi-checkbox.png` | 7 | check-box tick-all (Q34, Q49–Q50, Q104–Q105, Q117, Q121 battery, Q165–Q166) | `f1-capi-checkbox.png` |
| optional P2 | — | Q1 re-shot (main panel), Informed-Consent flow, Section-D opening | `f1-capi-q1-name.png` (re-shoot), consent + Section-D screens |

---

## Capture cards (what to do on the device)

Mechanism (per `reference_csentry_screen_capture` + CAPI-manual capture convention):
`adb shell screencap` → pull → crop to the panel → scale ×1.20. WebView screens have **no uiautomator**;
**dropdowns need DPAD** to open. Reach each control by navigating the live instrument to a representative question.

**F1 — 1 shot**
- [ ] `f1-capi-checkbox.png` — open **FacilityHeadSurvey**, go to Q34 (or any tick-all), capture the check-box multi-select. Replaces the 7 borrowed `f4-capi-checkbox.png`.

**F3 — 7 shots** (open the **F3 Patient** instrument; title bar must read F3, not "FacilityHeadSurvey")
- [ ] `f3-capi-yesno.png` — any Yes/No (e.g. Q3 respondent-is-patient).
- [ ] `f3-capi-single-select.png` — any short single-select (e.g. Q1/Q2).
- [ ] `f3-capi-long-select.png` — a long single-select list (e.g. Q114 reasons / a long radio set).
- [ ] `f3-capi-number.png` — a peso/number-pad entry (e.g. Q97 final amount).
- [ ] `f3-capi-rating-scale.png` — a 5-point rating screen (Q131–Q140 / Q178). *Currently mis-shown as a plain list.*
- [ ] `f3-capi-amount-matrix.png` — a per-source Yes/No + Amount matrix (Q98 / Q107 / Q113). *Currently mis-shown as a single number-pad.*
- [ ] `f3-capi-roster.png` *(optional)* — the Q92 payment roster (one row per ticked source).

**F4 — 5 shots** (open the **F4 Household** instrument)
- [ ] `f4-capi-yesno.png` — any Yes/No (e.g. a Section O battery item).
- [ ] `f4-capi-long-select.png` — a long single-select / rating (e.g. Q201 worry scale).
- [ ] `f4-capi-single-select.png` — a short single-select.
- [ ] `f4-capi-number.png` — a number-pad entry.
- [ ] `f4-capi-freetext.png` — a free-text + keyboard screen.

---

## Repoint map (run AFTER the PNGs land)

> **Order matters.** Do the **weak-proxy** rows first (by question badge), then blanket-replace the remainder.
> A blanket slug swap is safe for the standard controls but would wrongly catch the rating/amount rows.

**Step 1 — F3 targeted (find the rows by `qbadge`, repoint only those):**
- Q131–Q135, Q136–Q140, Q178 → `f3-capi-rating-scale.png` (these currently use `f1-capi-b-facility-profile.png`).
- Q98, Q107, Q113 → `f3-capi-amount-matrix.png` (these currently use `f1-capi-q3-q4-demographics.png`).

**Step 2 — F3 blanket (remaining refs):**
```
f1-capi-c-uhc-entry.png        -> f3-capi-yesno.png
f1-capi-b-facility-profile.png -> f3-capi-single-select.png
f1-capi-c-attribution.png      -> f3-capi-long-select.png
f1-capi-q3-q4-demographics.png -> f3-capi-number.png
```

**Step 3 — F4 blanket (no weak-proxy exceptions):**
```
f1-capi-c-uhc-entry.png        -> f4-capi-yesno.png
f1-capi-c-attribution.png      -> f4-capi-long-select.png
f1-capi-b-facility-profile.png -> f4-capi-single-select.png
f1-capi-q3-q4-demographics.png -> f4-capi-number.png
f1-capi-q1-name.png            -> f4-capi-freetext.png
```

**Step 4 — F1 blanket:**
```
f4-capi-checkbox.png           -> f1-capi-checkbox.png
```

**Step 5 — prose cleanup (do not skip):** each repointed row's `alt=` / `capi-cap` still says the screen is
"shown from the F1 instrument." After repointing, drop that disclaimer and update the top `banner` paragraph in
`f3-crosswalk.html` / `f4-crosswalk.html` (and the F1 checkbox alt) so it no longer says the controls are F1 stand-ins.

**Step 6 — verify:** re-run the img-ref audit — expect **0** `f1-capi-*` refs in F3/F4 and **0** `f4-capi-checkbox` in F1,
every `<img>` resolving to an existing file.

---

## F2 — desk confirm only (no capture)
- [ ] **I/J question-number drift** (`f2-crosswalk.html`, the "I. Facility Support · J. Job Satisfaction" page-pair):
  on paper Section I = Q86/Q87 and Section J = Q88–Q100+, but the web PWA shows Section I's satisfaction item as
  Q96 while Section J's battery starts at Q86. Pairing + content are correct — **confirm the renumbering is
  intentional** (Carl's call, it's the PWA's own numbering), then note "confirmed intentional" here.

---

## Prerequisite to start (what to launch)
1. A tablet **or** the `capi_tablet` AVD running, visible to `adb devices` (adb must be on PATH or invoked by full path).
2. Current builds of **F3 Patient**, **F4 Household**, and **F1 FacilityHeadSurvey** installed (title bars must read the
   right instrument — borrowed shots got flagged precisely because they read "FacilityHeadSurvey").
3. Then run the device session against the 13 capture cards above; the repoint map makes the wiring a single pass.
