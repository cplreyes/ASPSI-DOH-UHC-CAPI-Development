# Design System — F2 PWA

> **This file is the visual source of truth for the F2 PWA.**
> Read it before making any UI, color, type, spacing, or motion decision.
> Do not deviate without explicit approval. In QA, flag any code that doesn't match.

---

## Memorable Thing

> **"This is real software, not a government form."**

Every type, color, spacing, and motion decision in this system serves that anchor.
Restraint compounds. Hairlines, pale verde paper, and one DOH emerald signal carry
the trust HCWs need to install government software on their personal phones.

---

## Product Context

- **What this is:** Offline-capable Progressive Web App for the F2 (Healthcare Worker Survey) instrument under the ASPSI → DOH UHC Act monitoring contract. Self-administered. 124 items, 35+ sections, 30 minutes to several hours to fill.
- **Who it's for:** Filipino healthcare workers (HCWs) using their own phones, tablets, or laptops. Bilingual: English + Filipino (Tagalog).
- **Space/industry:** Government health monitoring. Plan B to CSPro/CSEntry (Plan A) within the F2 track; PWA is the long-term F2 capture target per the 2026-04-21 track positioning.
- **Project type:** Single-purpose web app (form-heavy). Not a dashboard, not a marketing site, not a general survey platform.

---

## Aesthetic Direction

- **Direction:** **Verde Manual** — clinical stationery and utility, anchored on the Philippine DOH "Verde Vision / Berde para sa bayan" institutional palette.
- **Decoration level:** Minimal. Typography does the work. No drop shadows. No decorative SVGs. No glassmorphism.
- **Mood:** Quiet confidence. Print-influenced composition (hairlines, baseline grid, marginal numbering) translated to PWA. Tactile but not twee. Field manual, not SaaS dashboard.
- **Reference sites:** [gov.uk](https://www.gov.uk) (single-blue institutional restraint), [Linear](https://linear.app) (modern indie polish via restraint), DOH Philippines visual identity (Verde Vision palette).

---

## Color — Verde Manual

**Approach:** Restrained. One signal color. Warm-cool neutrals (verde-tinted) that read distinct from generic gov-tech white.

> **Caveat:** Hex values below are best-fit approximations of the visible DOH seal +
> the documented Verde Vision background tint `#e7efe7`. Refine when the official
> DOH brand-book PDF is available (Department Order 2020-0011, Verde Vision 2023+).

### Light mode (default)

| Token | Hex | Role |
|---|---|---|
| `--paper` | `#F2F5EE` | Background. Pale verde-tinted off-white. References DOH `#e7efe7`, slightly warmer for screen comfort. |
| `--ink` | `#1A1F1A` | Primary text. Warm near-black with subtle green undertone. ~14:1 contrast on paper, exceeds WCAG AAA. |
| `--hairline` | `#B5C0A9` | Rule color. Section dividers, input borders. Verde-tinted to harmonize. |
| `--muted` | `#5A655A` | Secondary text, helpers, eyebrows. Warm gray-green. |
| `--signal` | `#006B3F` | DOH emerald. Primary CTAs, current-question marker, active progress, selected radio rings. The recognizable institutional handshake. |
| `--signal-bg` | `#006B3F1A` | 10% alpha tint. Used only as the current-question background fade. |
| `--highlight` | `#E5B23B` | DOH yellow inner-rim color. Used **very sparingly** — only for "saved" toasts and similar punctuation moments. Never as fill or surface. |
| `--success` | `#006B3F` | Same as signal — green is intrinsically "OK" in DOH context, no separate success color. |
| `--warning` | `#C68A2E` | Ochre. Storage-quota warnings, near-stale draft notices. |
| `--error` | `#B72020` | Cherry red. References the cross at the center of the DOH seal. Used only on validation errors and submission rejections. |

### Dark mode

| Token | Hex | Role |
|---|---|---|
| `--paper` | `#0F1410` | Background. Warm graphite, never pure black. |
| `--ink` | `#DCE3D5` | Primary text. Warm off-white with subtle green undertone. |
| `--hairline` | `#2A3328` | Rule color. |
| `--muted` | `#828C82` | Secondary text. |
| `--signal` | `#2A9166` | Emerald shifted brighter for retina balance on dark ground. |
| `--signal-bg` | `#2A91661F` | 12% alpha tint. |
| `--highlight` | `#F1C95C` | DOH yellow shifted brighter. |
| `--error` | `#D6504C` | Cherry shifted brighter. |

### Color usage rules

1. The signal color (`--signal`) is the only place emerald appears. Never as background fill, never as text in body copy, only as: CTA buttons, current-question marker (gutter number + 10%-alpha row tint), active progress fill, selected radio/checkbox dot ring, focus ring on inputs.
2. The highlight color (`--highlight`) is reserved for save-confirmation toasts and the section-saved badge. Never use it for CTAs, links, or primary text.
3. Error color (`--error`) is reserved for validation errors and submission rejections. Never for warnings, never for emphasis.
4. No raw Tailwind color classes in app code (`text-red-500`, `bg-blue-100`, etc.). Always go through the CSS variable tokens.

---

## Typography

**All three fonts are free + open source. Loaded via local `/public/fonts/*.woff2` and precached by the service worker.** First-install bundle adds ~120 kB; zero runtime cost after install.

### Faces

| Role | Font | License | Why |
|---|---|---|---|
| **Display** | **Newsreader** by Production Type | OFL | Contemporary serif with clean terminals. Reads as edited document, not browser default. Carries Filipino diacritics (`ñ`, `ng`) cleanly. Variable axes for fine weight control. |
| **Body** | **Public Sans Variable** by US Web Design System | OFL | Designed specifically for government-form accessibility. Excellent x-height. Full Latin Extended for Filipino. Tabular-nums built in. Variable. |
| **Mono / Data** | **JetBrains Mono** | Apache 2.0 | Question numbers in margin, IDs, timestamps, sync counters, version tags. Genuine monospaced figures. |
| **Fallback (system)** | `Georgia, "Times New Roman", serif` for display; `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` for body; `"SF Mono", Menlo, Consolas, monospace` for mono | — | Only seen during initial load before woff2 hydrates. |

### Type scale (modular 1.250 ratio, 16px base)

| Token | Size / Line | Use |
|---|---|---|
| `text-xs` | 12 / 18 | Helper text, mono labels, badges |
| `text-sm` | 14 / 21 | Form labels, secondary copy |
| `text-base` | 16 / 25 | Body, question prompts (default) |
| `text-lg` | 18 / 27 | Question prompts at desktop, emphasized body |
| `text-xl` | 20 / 28 | Subsection headers |
| `text-2xl` | 24 / 32 | h2, dialog titles |
| `text-3xl` | 28 / 36 | Mobile section titles |
| `text-4xl` | 36 / 42 | Desktop section titles (Newsreader 500) |
| `text-5xl` | 48 / 54 | Splash / first-launch hero (Newsreader 500) |

### Type rules

1. Display sizes (`text-3xl` and above) always use Newsreader, weight 500 (medium) by default, 600 only for splash heroes.
2. Body sizes use Public Sans, weight 400 default, 500 for question prompts, 600 for active section indicators.
3. Mono is used in: (a) the marginal question number gutter at `text-2xl`, (b) all timestamps and IDs at `text-xs`, (c) the typographic ledger progress at `text-sm`. Never for body copy, never for prompts.
4. Letter-spacing: `tracking-tight` (-0.015em) on display sizes, default on body, `tracking-wide` (0.04em) on uppercase mono labels.
5. Line height: 1.55 for body, 1.45 for question prompts, 1.15 for display.
6. **Verbatim labels.** Per project convention (`feedback_verbatim_questionnaire_labels`): never paraphrase question text. Use the exact wording from the spec, including original question numbers — even when the rendered design diverges (e.g., the marginal `047` is rendered, but the prompt text is verbatim from `F2-Spec.md`).

---

## Spacing

- **Base unit:** 4px
- **Density:** Comfortable. Form-heavy app means HCWs read for hours; compact density causes fatigue.
- **Scale:** `2 / 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96`

### Spacing rules

| Where | Value |
|---|---|
| Form field vertical rhythm | 12px between label and input, 8px between input and helper, 24px between fields |
| Question vertical breathing | 32px between questions |
| Section breaks | 48px above section opener, 24px between section title and first question |
| Header padding | 16px vertical, 32px horizontal (desktop) / 12px vertical, 20px horizontal (mobile) |
| Section opener top margin | 56px (desktop) / 32px (mobile) |
| Margin gutter for question numbers | 88px (desktop/tablet, holds the JetBrains Mono `047` left of question text), 0 mobile (number stacks above) |
| Page max content width | 720px (the question column) |
| Frame max width | 1280px (centered with hairline borders left/right) |

---

## Layout

- **Approach:** Grid-disciplined, hairline-divided, asymmetric.
- **First viewport:** Reads as a poster (oversized Newsreader headline, signal-color question-count badge, single CTA, ample paper). Not a document.
- **Inside survey:** Strict 4pt baseline grid. Question text left-weighted in a 720px column. Question number hangs in an 88px left gutter on tablet/desktop, stacks above on phone.
- **Grid columns:** 1 column on mobile (≤640px), 2 columns on tablet (gutter + content), 3 columns on desktop (gutter + content + free space).
- **Max content width:** 720px (question column). 1280px (frame).
- **Border radius scale:** `0` (cards — but we don't use cards), `2px` (default — buttons, inputs, pills), `4px` (max — used only for the Likert outer container and yes/no toggles). No `rounded-lg`, no `rounded-2xl`, no `rounded-full` except for radio dots.

### Layout rules

1. **No cards.** Sections separated by 1px `--hairline` rules and whitespace only. No `bg-white rounded-lg shadow` patterns anywhere in the app. This is the single biggest move that drops the gov-SaaS smell.
2. **Hairlines are 1px solid `--hairline`.** Never thicker. Never dashed except in preview meta-bars.
3. **Question numbers** in JetBrains Mono live in the left margin gutter (`text-2xl` weight 500, color `--muted` for non-current questions, `--signal` for current). On mobile they stack above the prompt at `text-base`.
4. **Progress** is rendered as a typographic ledger (`047 ━━━━━━━━━━━━━╴╴╴╴╴ 124`) in JetBrains Mono, not a graphical progress bar. The filled portion uses `--signal`, the unfilled portion uses 45% opacity `--muted`.
5. Asymmetric: question text left-aligned, response affordances inline-block right-flowing on tablet/desktop, stacked on phone.

---

## Motion

- **Approach:** Minimal-functional. No entrance animations on form fields — distracting during 3-hour fills. Motion only at state transitions.
- **Easing:**
  - `enter`: `cubic-bezier(0.16, 1, 0.3, 1)` (gentle ease-out)
  - `exit`: `cubic-bezier(0.4, 0, 1, 1)` (ease-in)
  - `move`: `ease-in-out`
- **Duration:**
  - `micro` 80ms — save-confirm pulse on the question-number gutter (single flash, then back to neutral)
  - `short` 150ms — input focus rings, button press, hover transitions
  - `medium` 250ms — view transitions (form ↔ review ↔ sync), palette/theme switches
  - `long` — not used

### Motion rules

1. Form fields never animate on entrance. Once they're rendered, they're rendered.
2. The save-confirmation pulse is the only place `--signal` animates. 80ms flash on the question-number text, no other surface lights up.
3. View transitions use `opacity` + 8px `translateY`, never scale or rotate.
4. Respect `prefers-reduced-motion: reduce` — disable all transitions when the user has it set. Auto-fade still allowed but no `translate`.

---

## Components

This section grows as components are built. For every domain component:
- Document the component's role
- Specify the spacing rhythm in/around it
- List the color tokens used
- Note any deviation from the rules above (and why)

### `<Question>` (current)
- Role: renders one F2 item, dispatches by type (text, number, radio, multi-select, matrix, date)
- Layout: 88px gutter (desktop) holds the JetBrains Mono `047` number; 720px max-width content column with prompt + helper + response affordance
- Vertical breathing: 32px before, 32px after, hairline between
- Current-question style: background `--signal-bg` (10% alpha emerald), gutter number switches to `--signal`
- Required indicator: `*` in `--signal`, immediately after the prompt text

### `<Likert>`
- 5 options in a horizontal `border` `rounded-2px` `divide-x` row (desktop), stacks vertical on mobile
- Each option: 1.5px ring radio dot in `--muted`, switching to filled `--signal` (with paper-color inner ring) when selected
- Selected option's row gets `--signal-bg` background tint
- Hover: same `--signal-bg` tint, dot color stays muted

### `<YesNo>`
- 2 options, inline-flex, hairline border, `rounded-2px`
- Selected: `--signal` solid background, `--paper` text
- Unselected: transparent, `--ink` text, hairline-bordered

### `<Navigator>`
- Bottom-fixed bar at the survey level; hairline border-top
- Left: ghost `← Previous` button
- Center: typographic ledger progress in JetBrains Mono
- Right: solid `--signal` `Next →` button (default state) or ghost `Submit responses` (last question)

### `<SyncBadge>` / `<PendingCount>`
- Header pill, JetBrains Mono `text-xs`
- Format: `{count} pending` where `{count}` is `--signal` and "pending" is `--muted`

### `<LanguageSwitcher>`
- Inline-flex pill, hairline-bordered, `rounded-2px`
- Active language: `--ink` background, `--paper` text
- Inactive language: transparent, `--muted` text

---

## Accessibility

1. **Contrast:** All text-on-paper combos exceed WCAG AAA (`--ink` on `--paper` ≈ 14:1; `--muted` on `--paper` ≈ 4.6:1, AA at minimum).
2. **Focus:** Every interactive element gets a 2px `--signal` outline at 2px offset on `:focus-visible`. Never remove focus rings.
3. **Touch targets:** Minimum 44×44px hit area on all interactive elements. The Likert dots are 16px visually but the click target spans the full option cell (typically 80×60px at desktop).
4. **`prefers-reduced-motion`:** Disable all transitions and animations.
5. **`prefers-color-scheme`:** Respected on first paint. User can override via the in-app dark-mode toggle (M11 hardening).
6. **Screen readers:** All form fields have associated `<label>`. Required fields announce "required" via `aria-required`. The marginal `047` number is `aria-hidden="true"` so screen readers don't read "Question zero four seven" twice — use a `<span class="sr-only">Question 47</span>` inline with the prompt.
7. **Filipino + English diacritics:** Public Sans Variable carries full Latin Extended. Test on real devices for `ñ`, `ng`, and the stylized `ng̃` combining-tilde before each release.

---

## Implementation Notes

These are forward-looking notes for the PRs that will land this design system in code. Currently the app uses shadcn defaults + a teal primary; the migration to Verde Manual will land in 2-3 PRs.

### PR plan (suggested)

1. **PR 1 — Tokens.** Replace `:root` HSL variables in `src/index.css` with the Verde Manual hex tokens. Update `tailwind.config.ts` if needed (current config maps Tailwind classes to CSS vars, so most changes ride through automatically). Update `public/manifest.webmanifest` `theme_color` from `#0f766e` (teal) to `#006B3F` (DOH emerald).
2. **PR 2 — Typography.** Add `public/fonts/{newsreader, public-sans, jetbrains-mono}.woff2` (subset to Latin Extended). Reference in `index.css` `@font-face` rules. Precache via vite-plugin-pwa workbox config. Add `font-family` declarations to body + Tailwind theme extend.
3. **PR 3 — Layout & components.** Refactor `<Question>` to add the 88px gutter + marginal mono number. Replace any `border rounded-lg shadow` patterns with hairline rules. Update `<MultiSectionForm>` section dividers to hairlines + whitespace. Update `<Navigator>` to typographic-ledger progress.

Each PR is small enough to review in 10 minutes and ship under `/ship` (which does NOT bump version per `project_gstack_adoption`).

### Don't deviate without

1. Updating this file with the new decision and adding a row to the Decisions Log below.
2. Confirming the change doesn't break the Memorable Thing anchor: "real software, not a government form."
3. Running through the Anti-Slop checklist (next section).

---

## Anti-Slop Checklist

If you're about to commit a UI change, verify:

- [ ] No purple, violet, or generic SaaS-blue gradients
- [ ] No 3-column SaaS feature grid with circle-bg icons
- [ ] No centered-everything layout (use the asymmetric grid)
- [ ] No `rounded-2xl` or `rounded-full` (except radio dots)
- [ ] No `bg-white shadow-md rounded-lg` "card" patterns
- [ ] No gradient buttons (signal is flat, full stop)
- [ ] No emoji in UI chrome (emoji is fine in user-generated content)
- [ ] No system-ui or `-apple-system` as the *primary* display or body font (only as fallback while woff2 loads)
- [ ] No "Get Started" / "Built for X" / "Designed for Y" copy patterns
- [ ] No Lottie or decorative SVG blobs
- [ ] No glassmorphism, no backdrop-blur on chrome surfaces
- [ ] CTA reads "Begin Section 1" / "Next →" / "Submit responses" — concrete, not generic

---

## Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-04-26 | Initial design system created | Created by `/gstack-design-consultation`. Memorable thing: "real software, not a government form." Verde Manual chosen over Field Manual to ladder up to DOH institutional brand without losing craft. Hex values approximated from visible DOH seal + Verde Vision documented background; refine when official brand-book PDF is available. |

---

## References

- `../2026-04-17-design-spec.md` — F2 PWA architecture (this file is the visual layer)
- `../2026-04-21-implementation-plan.md` — milestone roadmap M0–M11
- DOH Philippines visual identity: Department Order 2020-0011, Verde Vision 2023+ (PDFs paywalled on Scribd; refine when available)
- gov.uk design system — institutional restraint reference: <https://design-system.service.gov.uk/>
- US Web Design System (Public Sans origin): <https://designsystem.digital.gov/>
- Bunny Fonts (CDN for development): <https://fonts.bunny.net/>
