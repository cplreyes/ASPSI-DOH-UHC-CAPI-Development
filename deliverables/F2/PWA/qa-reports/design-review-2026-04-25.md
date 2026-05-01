# F2 PWA — Visual Design Review (Local Dev)

**Date:** 2026-04-25
**Target:** F2 HCW Survey PWA, local dev (`npm run dev` → http://localhost:5173/)
**Build:** v1.1.1 · spec 2026-04-17-m1
**Mode:** Designer's-eye audit, report-only — no source edits, no commits
**Companion to:** [`qa-report-2026-04-25.md`](./qa-report-2026-04-25.md) (functional QA)
**Health score (visual):** **89 / 100**

---

## Top 3 things to fix

1. **Inverted heading hierarchy.** H1 (page title) is 18px, H2 (section heading) is 24px. The page title should be the most prominent text on the page, not visually demoted. Bump H1 to at least 28-32px or restructure so the section heading carries the H1.
2. **Disabled button contrast fails WCAG AA.** Disabled buttons use `opacity: 0.5` against the teal background. White text on the resulting washed-out teal computes to ~2:1 contrast — well below the 4.5:1 AA threshold. Affects every disabled state in the app (Enroll before form-fill, etc.).
3. **No visible focus ring.** Tabbing through the form leaves no visual indicator of where focus is. The `--ring` CSS variable is defined as the primary teal but `:focus-visible` box-shadow is not being applied. Keyboard users and screen-reader users cannot orient themselves.

---

## Design tokens audit

Pulled directly from `getComputedStyle(documentElement)`:

| Token | Value | Notes |
|-------|-------|-------|
| `--primary` | `hsl(173 80% 26%)` → ~`#0d776b` | Dark teal. Reads as clinical/healthcare. Good. |
| `--background` | `hsl(0 0% 100%)` → `#fff` | Pure white. |
| `--foreground` | `hsl(222 84% 4.9%)` → ~`#020817` | Near-black with hint of blue. |
| `--muted` | `hsl(210 40% 96.1%)` → ~`#f1f5f9` | Pale blue-gray. |
| `--destructive` | `hsl(0 84.2% 60.2%)` → ~`#ef4444` | Red-500 for errors. |
| `--border` | `hsl(214.3 31.8% 91.4%)` → ~`#e2e8f0` | Pale gray border. |
| `--ring` | `hsl(173 80% 26%)` | Same as primary. **Defined but not applied on focus.** |
| Body font | `ui-sans-serif, system-ui, sans-serif, …emoji` | Tailwind default. No custom typeface. |
| Body size | 16px | Standard. |
| H1 size | **18px / 600 / 28px lh** | Too small for an H1. |
| H2 size | **24px / 600** | Larger than H1. Inverted. |
| Label size | 14px / 400 | Reasonable. |
| Button | 12px / 32px tall / 12px padX / 0px padY | **Below 44px touch-target minimum.** |

The palette and spacing tokens read as **shadcn/ui defaults** with the primary swapped to teal. That is fine — it gives a coherent base — but the project hasn't yet personalized typography or layout density for tablet-first field use.

---

## Issues

### ISSUE-D01 [HIGH] Inverted heading hierarchy: H1 < H2

**Category:** Typography / Hierarchy
**Pages:** Every page (header sits above section content)
**Observation:**

- `<h1>UHC Survey Y2 — Healthcare Worker Survey Questionnaire</h1>` renders at **18px / 600 weight**.
- `<h2>Section A — Healthcare Worker Profile</h2>` renders at **24px / 600 weight**.

The page title is the highest-level heading in the document, but it visually reads as **smaller and less important** than the section heading. A first-time enumerator's eye will land on "Section A" and miss the project context. This also breaks heading-only navigation for screen reader users — the "main heading" they jump to is the smaller one.

**Recommendation:**
- Bump H1 to ~28-32px (Tailwind `text-2xl` or `text-3xl`) and either keep weight at 600 or step up to 700.
- Keep H2 at 24px or step it down to 20px for a clearer step-down.
- Verify the heading order in DOM matches the visual hierarchy.

**Evidence:** `screenshots/initial.png` (header at top), `screenshots/section-a-loaded.png` (Section A heading visually larger than page title).

---

### ISSUE-D02 [HIGH] Wide-desktop layout pushes form off-center

**Category:** Layout / Responsive
**Pages:** Enrollment screen at viewports ≥ ~1600px
**Observation:** At 1280px the enrollment form is centered. At 1920px it shifts dramatically to the right with a large empty band on the left of the viewport. Looks broken on field-deployed laptops connected to external monitors (a common pattern for ASPSI supervisors / data managers reviewing tablet uploads).

The likely cause is a fixed-width sidebar slot reserved by the layout grid even when the sidebar is empty (enrollment screen has no sidebar; survey screens do). The content panel then centers within the remaining right-hand column instead of the full viewport.

**Recommendation:**
- Either remove the sidebar reservation on pre-enrollment screens (so content centers in the full viewport), or wrap the entire app in a `max-w-screen-xl mx-auto` so the layout never spreads beyond ~1280px regardless of viewport.

**Evidence:** `screenshots/desktop-wide.png` (1920×1080) vs `screenshots/initial.png` (1280×720).

---

### ISSUE-D03 [HIGH] Disabled button contrast below WCAG AA

**Category:** Accessibility / Color
**Pages:** Everywhere there's a disabled button (Enroll before form-fill, Refresh while loading, etc.)
**Observation:** Disabled state is implemented with `opacity: 0.5` on the entire button. Active button is `rgb(13, 119, 107)` with white text — contrast ~5.5:1 (passes AA). Disabled at 0.5 opacity blends with the white page background to an effective `rgb(134, 187, 181)`, dropping white-text contrast to **~2.06:1**. WCAG AA requires 4.5:1 for normal text and 3:1 for UI components. **Fails on both counts.**

This affects perceived button state: the disabled Enroll looks "muddy" and the label is hard to read at distance or in bright field lighting.

**Recommendation:**
- Replace blanket `opacity: 0.5` with explicit disabled styling: lighter background (e.g. `--muted`) with `--muted-foreground` text. Keeps the disabled signal but maintains contrast.
- If you keep opacity, also change the text color to a dark foreground at full opacity so it remains readable.

**Evidence:** `screenshots/initial.png` (disabled "Enroll" button looks washed out next to the active "Refresh facility list").

---

### ISSUE-D04 [MEDIUM] Buttons below 44px touch-target minimum

**Category:** Accessibility / Tablet ergonomics
**Pages:** All buttons (32px tall)
**Observation:** Button height is 32px with 12px font and 0px vertical padding. Apple HIG recommends a 44×44px minimum tappable area; Material recommends 48×48px. ASPSI's primary use case is enumerators on tablets in the field — sometimes with gloves, sometimes one-handed while writing notes. 32px tall buttons are mistap-prone in those conditions.

**Recommendation:**
- Bump default button height to 44px (Tailwind `h-11`) for tablet builds.
- Bump font size to 14px so the label has room to breathe.
- Optionally add a `compact` variant for desktop UAT/admin tooling.

**Evidence:** `screenshots/initial.png` (Enroll + Refresh buttons), `screenshots/sync-page.png` (Sync now + Change enrollment).

---

### ISSUE-D05 [MEDIUM] No visible focus indicator on Tab navigation

**Category:** Accessibility / Keyboard
**Pages:** All interactive elements
**Observation:** Active element after 4 Tabs is the "Refresh facility list" button. Computed styles:
- `outline: rgba(0,0,0,0) solid 2px` — outline color is transparent.
- `boxShadow` is the button's resting 1px teal border + a faint drop shadow — no focus-specific change.
- `--tw-ring-color: hsl(173 80% 26%)` is set but no `ring` utility is applied on `:focus-visible`.

A keyboard user pressing Tab cannot tell which element is focused. Same problem for switch users and any screen reader user who relies on visual focus tracking.

**Recommendation:**
- Add `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` (or equivalent) to the base button + input + radio styles.
- Verify the ring is visible against both white and teal backgrounds (offset helps).

**Evidence:** `screenshots/focus-state.png` — Refresh button is focused but visually identical to its resting state.

---

### ISSUE-D06 [MEDIUM] Generic system font stack — no typographic identity

**Category:** Typography / Brand
**Pages:** All
**Observation:** The font stack is Tailwind's default (`ui-sans-serif, system-ui, sans-serif, …`). This means the same page renders as San Francisco on iPad, Segoe UI on Windows tablets, Roboto on Android, and DejaVu on some Linux kiosks. For a government-adjacent clinical survey instrument, a defined typeface (Inter, Source Sans Pro, IBM Plex Sans) reads more "official" and behaves consistently across the device fleet.

**Recommendation:**
- Pick one variable font, self-host it, declare it in `index.html` with `font-display: swap`, and set it as the default in `tailwind.config.js`.
- Inter or IBM Plex Sans are both strong fits — high x-height, good legibility at 14-16px, free.
- Keep the system fallback for offline / low-bandwidth.

**Evidence:** Font stack pulled from `getComputedStyle(body).fontFamily`.

---

### ISSUE-D07 [LOW] Header subtitle low-contrast

**Category:** Color / Hierarchy
**Pages:** Header (every page)
**Observation:** "v1.1.1 · spec 2026-04-17-m1" subtitle below the page title appears in a very light gray, ~12px. Useful for QA / build verification, but at this contrast it is borderline AA-fail and visually noisy beneath an already-too-small H1.

**Recommendation:**
- If retained for production: bump contrast (Tailwind `text-muted-foreground` rather than `text-muted`).
- If for QA only: gate behind a build flag so prod doesn't show it.

---

### ISSUE-D08 [LOW] Monochromatic palette limits state signaling

**Category:** Color / Information design
**Pages:** All
**Observation:** The palette is teal + grays + a single red for errors. Saved-success, info, warning, and error all currently rely on copy + position rather than color. Fine for a clinical tool that wants to look restrained, but limits the visual vocabulary if you later want to differentiate "draft saved" from "synced" from "needs attention" at a glance.

**Recommendation:** Add a secondary accent (e.g. amber for "warning / needs attention") and a success green. Don't use them as decoration — reserve them for state.

---

### ISSUE-D09 [LOW] Sidebar lacks per-section progress affordance

**Category:** Information design / Wayfinding
**Pages:** Survey sidebar (B-9)
**Observation:** The sidebar shows section names with lock icons for the locked sections and a teal pill for the active one. There's no indicator of *progress within a section* (e.g. "5 of 11 questions answered") or *completion* (e.g. checkmark on Section A once it's submitted). Users completing a 9-section survey will need to mentally track where they are.

**Recommendation:**
- Add a per-section progress dot (filled / empty / partial) next to each label.
- Replace lock icons on completed sections with checkmarks.

---

## What is working well

- **Avoids common AI-slop visual patterns.** No gratuitous gradients, no glassmorphism, no over-rounded "modern dashboard" corners, no generic stock icons. The aesthetic reads as restrained and government-appropriate, which is the right choice for ASPSI-DOH.
- **Required-field error pattern** (red label below the input) is clean, accessible, and consistent across all field types.
- **Border radius and spacing** are applied consistently within the form. The form has good vertical rhythm.
- **Mobile responsive layout** at 375px works well — sidebar collapses to hamburger, form fills the width, no horizontal scroll, no clipped content beyond the small floating-arrow note from the QA report.
- **Color choice** — the dark teal primary reads as clinical / healthcare without being stereotypical. Not pharma-blue, not WHO-blue.
- **Inline loading state** ("Refreshing…" with disabled button) is the right pattern.
- **Empty state copy** on the Sync page ("No submissions yet. Nothing to sync") is friendly and helpful.

---

## Coverage and limits

**Tested:**
- Visual hierarchy and typography sizing (computed styles)
- Color tokens and contrast (computed values + manual luminance calc on disabled state)
- Touch target sizing (computed button height)
- Focus states (Tab navigation + computed `:focus` styles)
- Layout at 375px, 768px, 1280px, 1920px
- AI-slop pattern check (gradients, glassmorphism, generic iconography)
- Empty / loading / error / disabled states

**Not tested:**
- Animation / motion (no transitions of substance to evaluate)
- Print styles (probably not used in field, but worth a sanity check)
- High-contrast / forced-colors mode (Windows accessibility setting)
- Right-to-left layout (FIL doesn't need RTL; flagging only because future locales might)
- Color contrast in axe-core full audit (manual spot-check only)
- Real-device rendering (DPI, color profile differences on field tablets)

---

## Files

```
deliverables/F2/PWA/qa-reports/
├── design-review-2026-04-25.md      (this file)
└── screenshots/
    ├── initial.png                   (1280 desktop, enrollment)
    ├── desktop-wide.png              (1920 desktop, off-center bug)
    ├── focus-state.png               (4 tabs in, no visible focus ring)
    ├── section-a-loaded.png          (full Section A — typography hierarchy)
    ├── mobile-viewport.png           (375 mobile)
    ├── tablet-viewport.png           (768 tablet)
    └── (others — see qa-report-2026-04-25.md)
```

---

## Suggested triage order

The functional QA report has 1 high + 2 medium. This visual review adds 3 high + 3 medium + 3 low. Combined picture:

| Priority | Source | Issue |
|----------|--------|-------|
| 1 | QA-001 | Raw Zod errors leaking to UI (`Expected number, received nan`) |
| 2 | D-01 | H1 < H2 (inverted heading hierarchy) |
| 3 | D-03 | Disabled button contrast fails WCAG AA |
| 4 | D-05 | No visible focus indicator |
| 5 | D-02 | 1920px layout off-center |
| 6 | D-04 | Buttons below 44px touch-target minimum |
| 7 | QA-002 | Q6 / Q8 missing — verify against spec |
| 8 | QA-003 | FIL toggle has no user-facing effect |
| 9 | D-06 | No typographic identity |
| 10+ | various lows | … |

Items 1-4 are the cheapest big-impact wins — all can land before the next UAT round and noticeably lift the polish bar. Items 5-6 need design decisions (layout strategy, button sizing for tablet vs desktop) and are worth a dedicated session.
