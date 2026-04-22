# F2 PWA — M9 i18n (Filipino) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add bilingual (English / Filipino) UI to the F2 PWA — externalize every user-visible string into `react-i18next` resource bundles, route generated instrument labels through a `{ en, fil }` data structure, ship a header language switcher whose choice persists in `localStorage` and survives reload.

**Architecture:** A new `src/i18n/` module wraps `i18next` + `react-i18next`. UI chrome (header, EnrollmentScreen, Navigator, ReviewSection, SyncPage, error toasts) calls `t('key')`. The generator's `Item.label` / `Choice.label` / `SubField.label` / `Section.title` change from `string` to `LocalizedString = { en: string; fil: string }`; a `localized(label, locale)` helper resolves it at render time with English as the safe fallback. The `fil` half of every generated label initially mirrors `en` (placeholder pending ASPSI translator delivery — see "Open question resolution" below); when ASPSI delivers a `spec/F2-Spec.fil.md` overlay, a follow-up patch wires it into the generator. Cross-field warning messages move to interpolated i18n keys. Locale state lives in React Context backed by `localStorage` key `f2_locale`.

**Tech Stack:** `react-i18next` ^14 · `i18next` ^23 · `i18next-browser-languagedetector` ^7 (for first-load best-effort browser-language match) · React 18 Context · Vitest 4 + @testing-library/react.

**Spec section reference:**
- `2026-04-17-design-spec.md` §5.5 ("UI language → React Context + `localStorage`. Survives reload.")
- §6.2 (generated `items.ts` row: "id, type, label keys (**en + fil**), options, required, group" — already prescribed bilingual)
- §11.1 row M9 ("i18n — Filipino translations", **10–15h** core, **+20–30h if Carl translates**, "react-i18next, label bundles", ships "Bilingual instrument")
- §13 open question #1 ("ASPSI-provided Filipino translations, or Carl translates?")

**Open question resolution (per memory `feedback_align_dont_flag.md`):** Build the bilingual plumbing now and assume ASPSI delivers the Filipino translation bundle later. The `fil` half of every label/string initially shadows the English text so the app *runs* under `locale='fil'` (it just shows English) — when ASPSI's translator returns a Filipino spec overlay, a small follow-up commit (NOT in this plan) drops it into the generator and the app becomes truly bilingual without any structural change. Estimated incremental effort to wire that overlay: ~3-5h. This keeps M9's core scope inside the spec's 10–15h band.

**Out of scope (deferred):**
- **Actual Filipino translations of generated labels.** Placeholder = English copy. Real strings land via a follow-up "M9-translations" content patch when ASPSI delivers.
- **Bilingual server-side validation messages.** Apps Script error messages remain English; the M11 hardening pass owns the call on whether to localize backend errors.
- **Right-to-left support, locale-aware date formatting.** Filipino is LTR and uses the same Gregorian calendar; not needed.
- **Per-respondent language preference.** Locale is device-wide (`localStorage`), not part of `EnrollmentRow`.
- **Translation of installed-PWA name / app manifest.** Manifest edits ship in M11.

---

## File Structure (decomposition)

| File | Responsibility | Status |
|---|---|---|
| `app/package.json` | add `i18next`, `react-i18next`, `i18next-browser-languagedetector` deps | modify |
| `app/src/i18n/index.ts` | initialize i18next with the en/fil resource bundles, expose `i18n` instance | create |
| `app/src/i18n/locales/en.ts` | English resource bundle (chrome strings, cross-field message templates, validation messages) | create |
| `app/src/i18n/locales/fil.ts` | Filipino resource bundle — same key set; values placeholder-equal-to-English for now | create |
| `app/src/i18n/locale-context.tsx` | `LocaleProvider` + `useLocale()` — React Context that mirrors i18next's `language`, persists to `localStorage` key `f2_locale` | create |
| `app/src/i18n/locale-context.test.tsx` | provider boot, switch, persist, hydrate-from-localStorage tests | create |
| `app/src/i18n/localized.ts` | `LocalizedString` type + `localized(label, locale)` helper for generator output | create |
| `app/src/i18n/localized.test.ts` | helper resolution + fallback tests | create |
| `app/src/components/i18n/LanguageSwitcher.tsx` | EN / FIL toggle button; reads/writes through `useLocale()` | create |
| `app/src/components/i18n/LanguageSwitcher.test.tsx` | render + click + persistence tests | create |
| `app/scripts/lib/types.ts` | change `Item.label`, `Item.help`, `Choice.label`, `SubField.label`, `Section.title`, `Section.preamble` from `string` to `LocalizedString` | modify |
| `app/scripts/lib/parse-spec.ts` | wrap parsed strings in `{ en, fil }` (fil = en placeholder) | modify |
| `app/scripts/lib/parse-spec.test.ts` | update assertions to expect `{en, fil}` shape | modify |
| `app/scripts/lib/emit-items.ts` | emit `LocalizedString` literals for label/help/choices/subFields/title/preamble; add the import for the type alias | modify |
| `app/scripts/lib/emit-items.test.ts` | update snapshot/string assertions to expect `{ en: '…', fil: '…' }` syntax | modify |
| `app/src/types/survey.ts` | mirror the type changes on the runtime side (`Item.label: LocalizedString`, etc.) + import alias | modify |
| `app/src/generated/items.ts` | regenerated by `npm run generate` | regenerated |
| `app/src/components/survey/Question.tsx` | resolve `item.label`, `item.help`, `choice.label`, `subField.label` via `localized(...)`; route required-field error message + "Please specify" through `t()` | modify |
| `app/src/components/survey/Question.test.tsx` | update assertions for the new English label resolution | modify |
| `app/src/components/survey/Section.tsx` | resolve `section.title` and `section.preamble` via `localized(...)`; "Submit" button label via `t()` | modify |
| `app/src/components/survey/Section.test.tsx` | update title-rendering assertions | modify |
| `app/src/components/survey/Navigator.tsx` | route Previous / Next / Submit labels through `t()` | modify |
| `app/src/components/survey/Navigator.test.tsx` | update label assertions to use the resolved English value | modify |
| `app/src/components/survey/ReviewSection.tsx` | route heading, "Edit", "Submit", per-section label, severity rendering through `t()`; resolve generated labels | modify |
| `app/src/components/survey/ReviewSection.test.tsx` | update label assertions | modify |
| `app/src/components/survey/ProgressBar.tsx` | route any visible string (e.g. "Step X of Y") through `t()` (read file first to see what needs touching) | modify |
| `app/src/components/sync/SyncPage.tsx` | "Sync", "No submissions yet.", status labels, "submitted", "retry at" via `t()` | modify |
| `app/src/components/sync/SyncPage.test.tsx` | update visible-text assertions | modify |
| `app/src/components/sync/SyncButton.tsx` | "Sync now", "Syncing…", "Synced N", "Nothing to sync", error fallback via `t()` (with interpolation for counts) | modify |
| `app/src/components/sync/SyncButton.test.tsx` | update visible-text assertions | modify |
| `app/src/components/sync/PendingCount.tsx` | "{count} pending" via `t()` interpolation | modify |
| `app/src/components/sync/PendingCount.test.tsx` | update visible-text assertions | modify |
| `app/src/components/enrollment/EnrollmentScreen.tsx` | every visible string through `t()` ("Enroll", helper paragraph, "HCW ID", "Facility", "No facilities cached…", select placeholder, "Refresh facility list", "Refreshing…") | modify |
| `app/src/components/enrollment/EnrollmentScreen.test.tsx` | update visible-text assertions | modify |
| `app/src/lib/cross-field.ts` | replace inline message strings with `(t, values) => string` factories so messages can be re-rendered when locale flips; keep severity/id columns as-is | modify |
| `app/src/lib/cross-field.test.ts` | update message assertions to call the factory with a stub `t` | modify |
| `app/src/App.tsx` | wrap `<AuthProvider>` in `<LocaleProvider>`; mount `<LanguageSwitcher>` in the header next to PendingCount; route header title, "Loading…", "Form" / "Sync" toggle, "Install", "Thank you", "Your response is saved…" through `t()` | modify |
| `app/src/App.test.tsx` | update visible-text assertions | modify |
| `app/src/test-setup.ts` | initialize i18next once before tests (so `t()` works in any rendered component without each test installing the provider) | modify |
| `app/NEXT.md` | rewrite to point at M10 (Admin dashboard) | modify |

---

## Task 1: Install i18next + react-i18next dependencies

**Files:**
- Modify: `app/package.json`
- Modify: `app/package-lock.json` (auto)

- [ ] **Step 1: Add the packages**

Run from `app/`:

```bash
npm install i18next@^23 react-i18next@^14 i18next-browser-languagedetector@^7
```

Expected: three packages added to `dependencies`, `package-lock.json` updated.

- [ ] **Step 2: Verify the install**

Run from `app/`:

```bash
npm ls i18next react-i18next i18next-browser-languagedetector
```

Expected output contains `i18next@23.x.x`, `react-i18next@14.x.x`, `i18next-browser-languagedetector@7.x.x` — no UNMET PEER DEPENDENCY warnings.

- [ ] **Step 3: Confirm the existing test suite still passes (no behavioral change yet)**

Run from `app/`:

```bash
npm test
```

Expected: 230 tests pass, no failures.

- [ ] **Step 4: Commit**

```bash
git add app/package.json app/package-lock.json
git commit -m "chore(f2-pwa): add i18next + react-i18next deps for M9"
```

---

## Task 2: Create the English resource bundle

**Files:**
- Create: `app/src/i18n/locales/en.ts`

Single file. We co-locate every chrome string here in one nested object so adding `fil.ts` later is a copy-paste-translate exercise. No tests on this file directly — its correctness is exercised by every component test that resolves strings through it.

- [ ] **Step 1: Create the bundle**

Write `app/src/i18n/locales/en.ts`:

```ts
// English resource bundle for the F2 PWA.
// Mirror every key in fil.ts. New keys MUST be added to both files.
export const en = {
  chrome: {
    appTitle: 'F2 Survey',
    install: 'Install',
    loading: 'Loading…',
    formView: 'Form',
    syncView: 'Sync',
    thankYouHeading: 'Thank you',
    thankYouBody: 'Your response is saved on this device and will sync when the app is online.',
  },
  language: {
    label: 'Language',
    en: 'English',
    fil: 'Filipino',
  },
  enrollment: {
    heading: 'Enroll',
    helper: 'Enter your HCW ID and select your facility. You can change these later from the Sync page.',
    hcwIdLabel: 'HCW ID',
    facilityLabel: 'Facility',
    facilityPlaceholder: 'Select a facility…',
    noFacilitiesCached: 'No facilities cached. Tap Refresh to download the master list.',
    enrollButton: 'Enroll',
    refreshButton: 'Refresh facility list',
    refreshingButton: 'Refreshing…',
  },
  navigator: {
    previous: 'Previous',
    next: 'Next',
    submit: 'Submit',
  },
  question: {
    requiredFallback: 'This field is required.',
    pleaseSpecifyLabel: 'Please specify',
    pleaseSpecifyError: 'Please specify',
  },
  review: {
    heading: 'Review your answers',
    crossFieldRegion: 'Cross-field warnings',
    sectionHeading: 'Section {{id}} — {{title}}',
    edit: 'Edit',
    submit: 'Submit',
  },
  sync: {
    heading: 'Sync',
    none: 'No submissions yet.',
    runButton: 'Sync now',
    runningButton: 'Syncing…',
    syncedSummary: 'Synced {{count}}',
    retryingSummary: 'Retrying {{count}}',
    rejectedSummary: '{{count}} rejected',
    nothingToSync: 'Nothing to sync',
    submittedAt: 'submitted {{at}}',
    retryAt: 'retry at {{at}}',
    pendingBadge: '{{count}} pending',
    statusPending: 'Pending',
    statusSyncing: 'Syncing',
    statusRetryScheduled: 'Retry scheduled',
    statusRejected: 'Rejected',
    statusSynced: 'Synced',
    syncFailedFallback: 'Sync failed',
  },
  crossField: {
    tenureImplausible:
      'Reported tenure ({{years}} years) is implausible for age {{age}}.',
    specialtyMismatch:
      'Role "{{role}}" does not normally carry a medical specialty ({{specialty}}).',
    employmentClassDerived:
      'Derived employment class: {{employmentClass}}.',
    workloadExceeds80:
      'Reported workload ({{days}} days × {{hours}} hrs = {{total}} hrs/week) exceeds 80.',
    sectionGRoleMismatch:
      'Section G is for physicians and dentists only; answers from "{{role}}" will be dropped server-side.',
    sectionsCDRoleMismatch:
      'Sections C and D are for clinical-care roles only; answers from "{{role}}" will be dropped server-side.',
  },
} as const;

export type EnBundle = typeof en;
```

- [ ] **Step 2: Typecheck**

Run from `app/`:

```bash
npm run typecheck
```

Expected: clean (no diagnostics).

- [ ] **Step 3: Commit**

```bash
git add app/src/i18n/locales/en.ts
git commit -m "feat(f2-pwa): add English i18n resource bundle"
```

---

## Task 3: Create the Filipino resource bundle (placeholder = English)

**Files:**
- Create: `app/src/i18n/locales/fil.ts`

The Filipino bundle MUST have exactly the same key shape as `en.ts`. We seed it with English values as placeholders — when ASPSI's translator delivers, this file is the single point of edit.

- [ ] **Step 1: Create the bundle**

Write `app/src/i18n/locales/fil.ts`:

```ts
// Filipino resource bundle for the F2 PWA.
// Values are placeholder-equal-to-English until ASPSI delivers translations.
// Key shape MUST match en.ts exactly — i18next will fall back to en for any
// missing key, but a TypeScript constraint below makes drift a compile error.
import type { EnBundle } from './en';

export const fil: EnBundle = {
  chrome: {
    appTitle: 'F2 Survey',
    install: 'Install',
    loading: 'Loading…',
    formView: 'Form',
    syncView: 'Sync',
    thankYouHeading: 'Thank you',
    thankYouBody: 'Your response is saved on this device and will sync when the app is online.',
  },
  language: {
    label: 'Language',
    en: 'English',
    fil: 'Filipino',
  },
  enrollment: {
    heading: 'Enroll',
    helper: 'Enter your HCW ID and select your facility. You can change these later from the Sync page.',
    hcwIdLabel: 'HCW ID',
    facilityLabel: 'Facility',
    facilityPlaceholder: 'Select a facility…',
    noFacilitiesCached: 'No facilities cached. Tap Refresh to download the master list.',
    enrollButton: 'Enroll',
    refreshButton: 'Refresh facility list',
    refreshingButton: 'Refreshing…',
  },
  navigator: {
    previous: 'Previous',
    next: 'Next',
    submit: 'Submit',
  },
  question: {
    requiredFallback: 'This field is required.',
    pleaseSpecifyLabel: 'Please specify',
    pleaseSpecifyError: 'Please specify',
  },
  review: {
    heading: 'Review your answers',
    crossFieldRegion: 'Cross-field warnings',
    sectionHeading: 'Section {{id}} — {{title}}',
    edit: 'Edit',
    submit: 'Submit',
  },
  sync: {
    heading: 'Sync',
    none: 'No submissions yet.',
    runButton: 'Sync now',
    runningButton: 'Syncing…',
    syncedSummary: 'Synced {{count}}',
    retryingSummary: 'Retrying {{count}}',
    rejectedSummary: '{{count}} rejected',
    nothingToSync: 'Nothing to sync',
    submittedAt: 'submitted {{at}}',
    retryAt: 'retry at {{at}}',
    pendingBadge: '{{count}} pending',
    statusPending: 'Pending',
    statusSyncing: 'Syncing',
    statusRetryScheduled: 'Retry scheduled',
    statusRejected: 'Rejected',
    statusSynced: 'Synced',
    syncFailedFallback: 'Sync failed',
  },
  crossField: {
    tenureImplausible:
      'Reported tenure ({{years}} years) is implausible for age {{age}}.',
    specialtyMismatch:
      'Role "{{role}}" does not normally carry a medical specialty ({{specialty}}).',
    employmentClassDerived:
      'Derived employment class: {{employmentClass}}.',
    workloadExceeds80:
      'Reported workload ({{days}} days × {{hours}} hrs = {{total}} hrs/week) exceeds 80.',
    sectionGRoleMismatch:
      'Section G is for physicians and dentists only; answers from "{{role}}" will be dropped server-side.',
    sectionsCDRoleMismatch:
      'Sections C and D are for clinical-care roles only; answers from "{{role}}" will be dropped server-side.',
  },
};
```

- [ ] **Step 2: Typecheck**

Run from `app/`:

```bash
npm run typecheck
```

Expected: clean. The `fil: EnBundle` annotation forces shape parity — if `en.ts` adds a key and `fil.ts` doesn't, this fails to compile.

- [ ] **Step 3: Commit**

```bash
git add app/src/i18n/locales/fil.ts
git commit -m "feat(f2-pwa): add Filipino i18n bundle (English placeholder)"
```

---

## Task 4: Initialize i18next + write the locale-context provider (TDD)

**Files:**
- Create: `app/src/i18n/index.ts`
- Create: `app/src/i18n/locale-context.tsx`
- Create: `app/src/i18n/locale-context.test.tsx`

The `index.ts` boots i18next with both bundles. The `LocaleProvider` mirrors i18next's current language into React state and persists to `localStorage`.

- [ ] **Step 1: Write the failing test**

Write `app/src/i18n/locale-context.test.tsx`:

```tsx
import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocaleProvider, useLocale } from './locale-context';

function Probe() {
  const { locale, setLocale } = useLocale();
  return (
    <div>
      <span data-testid="locale">{locale}</span>
      <button onClick={() => setLocale('fil')}>fil</button>
      <button onClick={() => setLocale('en')}>en</button>
    </div>
  );
}

describe('<LocaleProvider>', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('defaults to en when nothing is persisted', async () => {
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('en'));
  });

  it('hydrates from localStorage', async () => {
    localStorage.setItem('f2_locale', 'fil');
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('fil'));
  });

  it('setLocale persists to localStorage and updates state', async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('en'));
    await user.click(screen.getByRole('button', { name: 'fil' }));
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('fil'));
    expect(localStorage.getItem('f2_locale')).toBe('fil');
  });

  it('ignores garbage in localStorage and falls back to en', async () => {
    localStorage.setItem('f2_locale', 'klingon');
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('en'));
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `app/`:

```bash
npx vitest run src/i18n/locale-context.test.tsx
```

Expected: FAIL — module `./locale-context` does not exist.

- [ ] **Step 3: Write the i18next bootstrap**

Write `app/src/i18n/index.ts`:

```ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { en } from './locales/en';
import { fil } from './locales/fil';

export const SUPPORTED_LOCALES = ['en', 'fil'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (SUPPORTED_LOCALES as readonly string[]).includes(value);
}

if (!i18n.isInitialized) {
  void i18n.use(initReactI18next).init({
    resources: {
      en: { translation: en },
      fil: { translation: fil },
    },
    lng: 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
    returnNull: false,
  });
}

export { i18n };
```

- [ ] **Step 4: Write the locale-context provider**

Write `app/src/i18n/locale-context.tsx`:

```tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { i18n, isLocale, type Locale } from './index';

const STORAGE_KEY = 'f2_locale';

interface LocaleContextValue {
  locale: Locale;
  setLocale: (next: Locale) => void;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

function readPersisted(): Locale {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return isLocale(raw) ? raw : 'en';
  } catch {
    return 'en';
  }
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => readPersisted());

  useEffect(() => {
    if (i18n.language !== locale) {
      void i18n.changeLanguage(locale);
    }
  }, [locale]);

  const setLocale = (next: Locale) => {
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // best-effort; still update in-memory state
    }
    setLocaleState(next);
  };

  return (
    <LocaleContext.Provider value={{ locale, setLocale }}>{children}</LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) {
    throw new Error('useLocale must be used within a <LocaleProvider>');
  }
  return ctx;
}
```

- [ ] **Step 5: Run the test to verify it passes**

Run from `app/`:

```bash
npx vitest run src/i18n/locale-context.test.tsx
```

Expected: PASS — all 4 tests green.

- [ ] **Step 6: Commit**

```bash
git add app/src/i18n/index.ts app/src/i18n/locale-context.tsx app/src/i18n/locale-context.test.tsx
git commit -m "feat(f2-pwa): bootstrap i18next + LocaleProvider with localStorage persistence"
```

---

## Task 5: Create the LocalizedString helper (TDD)

**Files:**
- Create: `app/src/i18n/localized.ts`
- Create: `app/src/i18n/localized.test.ts`

This is the bridge between the generator's output and i18next. The generator emits `{ en, fil }` per label; runtime calls `localized(label, locale)`.

- [ ] **Step 1: Write the failing test**

Write `app/src/i18n/localized.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { localized, type LocalizedString } from './localized';

describe('localized()', () => {
  const greeting: LocalizedString = { en: 'Hello', fil: 'Kumusta' };

  it('returns the en value for locale=en', () => {
    expect(localized(greeting, 'en')).toBe('Hello');
  });

  it('returns the fil value for locale=fil', () => {
    expect(localized(greeting, 'fil')).toBe('Kumusta');
  });

  it('falls back to en when fil is the empty string', () => {
    const partial: LocalizedString = { en: 'Hello', fil: '' };
    expect(localized(partial, 'fil')).toBe('Hello');
  });

  it('falls back to en when fil is missing entirely', () => {
    const partial = { en: 'Hello' } as unknown as LocalizedString;
    expect(localized(partial, 'fil')).toBe('Hello');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `app/`:

```bash
npx vitest run src/i18n/localized.test.ts
```

Expected: FAIL — module `./localized` does not exist.

- [ ] **Step 3: Implement the helper**

Write `app/src/i18n/localized.ts`:

```ts
import type { Locale } from './index';

export interface LocalizedString {
  en: string;
  fil: string;
}

export function localized(label: LocalizedString, locale: Locale): string {
  if (locale === 'fil') {
    const v = label.fil;
    return v && v.length > 0 ? v : label.en;
  }
  return label.en;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run from `app/`:

```bash
npx vitest run src/i18n/localized.test.ts
```

Expected: PASS — 4/4.

- [ ] **Step 5: Commit**

```bash
git add app/src/i18n/localized.ts app/src/i18n/localized.test.ts
git commit -m "feat(f2-pwa): add LocalizedString + localized() resolver"
```

---

## Task 6: Initialize i18next once in test-setup

**Files:**
- Modify: `app/src/test-setup.ts`

Component tests that call `t()` need i18next initialized; importing `@/i18n` once in test-setup means individual tests don't have to wrap every `render` in a provider for the chrome-string lookups.

- [ ] **Step 1: Read the existing test-setup**

Run from `app/`:

```bash
cat src/test-setup.ts
```

Expected: a small file that imports `@testing-library/jest-dom` and `fake-indexeddb/auto`.

- [ ] **Step 2: Append the i18n import**

Open `app/src/test-setup.ts` and append at the bottom (DO NOT remove existing lines):

```ts
import '@/i18n';
```

(Side-effect import — `@/i18n/index.ts` runs `i18n.init` on first import, idempotent thanks to the `isInitialized` guard.)

- [ ] **Step 3: Run the full test suite**

Run from `app/`:

```bash
npm test
```

Expected: 230 + 8 (Tasks 4–5 added 4 + 4 = 8) = 238 tests, all green. No regressions.

- [ ] **Step 4: Commit**

```bash
git add app/src/test-setup.ts
git commit -m "test(f2-pwa): preload i18next bundles in test-setup"
```

---

## Task 7: Build the LanguageSwitcher component (TDD)

**Files:**
- Create: `app/src/components/i18n/LanguageSwitcher.tsx`
- Create: `app/src/components/i18n/LanguageSwitcher.test.tsx`

Two-button toggle. Reads/writes through `useLocale()`. The button for the *current* locale gets `variant='default'`; the other gets `variant='outline'`.

- [ ] **Step 1: Write the failing test**

Write `app/src/components/i18n/LanguageSwitcher.test.tsx`:

```tsx
import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocaleProvider } from '@/i18n/locale-context';
import { LanguageSwitcher } from './LanguageSwitcher';

describe('<LanguageSwitcher>', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders both EN and FIL buttons', () => {
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    expect(screen.getByRole('button', { name: /english/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /filipino/i })).toBeInTheDocument();
  });

  it('clicking FIL persists fil to localStorage', async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    await user.click(screen.getByRole('button', { name: /filipino/i }));
    expect(localStorage.getItem('f2_locale')).toBe('fil');
  });

  it('marks the current locale button as pressed', async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    expect(screen.getByRole('button', { name: /english/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /filipino/i })).toHaveAttribute('aria-pressed', 'false');
    await user.click(screen.getByRole('button', { name: /filipino/i }));
    expect(screen.getByRole('button', { name: /filipino/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /english/i })).toHaveAttribute('aria-pressed', 'false');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `app/`:

```bash
npx vitest run src/components/i18n/LanguageSwitcher.test.tsx
```

Expected: FAIL — module `./LanguageSwitcher` does not exist.

- [ ] **Step 3: Implement the component**

Write `app/src/components/i18n/LanguageSwitcher.tsx`:

```tsx
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useLocale } from '@/i18n/locale-context';

export function LanguageSwitcher() {
  const { t } = useTranslation();
  const { locale, setLocale } = useLocale();

  return (
    <div className="flex items-center gap-1" role="group" aria-label={t('language.label')}>
      <Button
        size="sm"
        variant={locale === 'en' ? 'default' : 'outline'}
        aria-pressed={locale === 'en'}
        onClick={() => setLocale('en')}
      >
        {t('language.en')}
      </Button>
      <Button
        size="sm"
        variant={locale === 'fil' ? 'default' : 'outline'}
        aria-pressed={locale === 'fil'}
        onClick={() => setLocale('fil')}
      >
        {t('language.fil')}
      </Button>
    </div>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run from `app/`:

```bash
npx vitest run src/components/i18n/LanguageSwitcher.test.tsx
```

Expected: PASS — 3/3.

- [ ] **Step 5: Commit**

```bash
git add app/src/components/i18n/LanguageSwitcher.tsx app/src/components/i18n/LanguageSwitcher.test.tsx
git commit -m "feat(f2-pwa): add LanguageSwitcher component"
```

---

## Task 8: Change generator types to LocalizedString

**Files:**
- Modify: `app/scripts/lib/types.ts`
- Modify: `app/scripts/lib/parse-spec.ts`
- Modify: `app/scripts/lib/parse-spec.test.ts`

Mirror the runtime `LocalizedString` shape inside the generator (the generator can't import from `src/` because it runs under `tsx` against `scripts/`, so we duplicate the trivial 4-line type — and that duplication is the *point*: the two artifacts evolve together).

- [ ] **Step 1: Update the generator types**

Replace `app/scripts/lib/types.ts` entirely:

```ts
export interface LocalizedString {
  en: string;
  fil: string;
}

export type ItemType =
  | 'short-text'
  | 'long-text'
  | 'number'
  | 'single'
  | 'multi'
  | 'date'
  | 'multi-field';

export interface Choice {
  label: LocalizedString;
  value: string;
  isOtherSpecify?: boolean;
}

export interface SubField {
  id: string;
  label: LocalizedString;
  kind: 'short-text' | 'number';
  min?: number;
  max?: number;
}

export interface Item {
  id: string;
  legacyId?: string;
  section: string;
  type: ItemType;
  required: boolean;
  label: LocalizedString;
  help?: LocalizedString;
  choices?: Choice[];
  hasOtherSpecify?: boolean;
  min?: number;
  max?: number;
  subFields?: SubField[];
}

export interface Section {
  id: string;
  title: LocalizedString;
  preamble?: LocalizedString;
  items: Item[];
}

export interface UnsupportedItem {
  id: string;
  section: string;
  rawType: string;
  reason: string;
}

export interface ParseResult {
  sections: Section[];
  unsupported: UnsupportedItem[];
}
```

- [ ] **Step 2: Run parse-spec tests — they should fail**

Run from `app/`:

```bash
npx vitest run scripts/lib/parse-spec.test.ts
```

Expected: FAIL — many type-mismatch errors because `parse-spec.ts` still produces `string` labels but the type now demands `LocalizedString`.

- [ ] **Step 3: Update parse-spec.ts to wrap strings in `{ en, fil }`**

Open `app/scripts/lib/parse-spec.ts`. Find every place a string is assigned to `label`, `title`, `preamble`, `help`, or a `Choice.label` / `SubField.label` and wrap it. Pattern:

```ts
// before:
const item = { id, label: rawLabel, ... };
// after:
const item = { id, label: dual(rawLabel), ... };
```

Add at the top of the file (after existing imports):

```ts
import type { LocalizedString } from './types';

function dual(en: string): LocalizedString {
  return { en, fil: en };
}
```

Then replace every occurrence of a raw string assignment to one of the localized-typed fields with `dual(...)`.

(The list of replacement sites is mechanical and will surface as TypeScript errors — fix each one until `npm run typecheck` is clean. Run `npx tsc --noEmit -p app/tsconfig.json` after edits to enumerate the remaining sites if any are missed.)

- [ ] **Step 4: Update parse-spec.test.ts assertions**

Open `app/scripts/lib/parse-spec.test.ts`. For every assertion that checks a `label`, `title`, `preamble`, `help`, choice `label`, or subField `label` against a string literal, change the expected value to the `{ en: '…', fil: '…' }` shape (with `fil` equal to `en`). Use a small helper to keep the test file readable:

Add at the top of the test file (after imports):

```ts
const dual = (en: string) => ({ en, fil: en });
```

Then in each assertion replace e.g. `expect(item.label).toBe('What is your name?')` with `expect(item.label).toEqual(dual('What is your name?'))`.

- [ ] **Step 5: Run parse-spec tests — should pass**

Run from `app/`:

```bash
npx vitest run scripts/lib/parse-spec.test.ts
```

Expected: PASS — every test green.

- [ ] **Step 6: Commit**

```bash
git add app/scripts/lib/types.ts app/scripts/lib/parse-spec.ts app/scripts/lib/parse-spec.test.ts
git commit -m "feat(f2-pwa): generator parses labels as LocalizedString {en, fil}"
```

---

## Task 9: Update emit-items to serialize LocalizedString literals

**Files:**
- Modify: `app/scripts/lib/emit-items.ts`
- Modify: `app/scripts/lib/emit-items.test.ts`

The emitter currently calls `quote(label)` to produce `'string'` literals. Now it must produce `{ en: '...', fil: '...' }` literals.

- [ ] **Step 1: Update the failing test first**

Open `app/scripts/lib/emit-items.test.ts`. For every assertion that checks emitted output contains a quoted string from a label/title/help/choice, update it to expect the new `{ en: '...', fil: '...' }` form. (Run the existing tests first — `npx vitest run scripts/lib/emit-items.test.ts` — to see which assertions need updating; the failures point at the exact lines.)

Pattern in the test file:

```ts
// before:
expect(out).toContain("label: 'What is your name?'");
// after:
expect(out).toContain("label: { en: 'What is your name?', fil: 'What is your name?' }");
```

Apply the same swap for `title:`, `preamble:`, `help:`, choice `label:`, subField `label:`.

- [ ] **Step 2: Run the tests — they should fail**

Run from `app/`:

```bash
npx vitest run scripts/lib/emit-items.test.ts
```

Expected: FAIL — emitter still produces bare strings.

- [ ] **Step 3: Update emit-items.ts**

Open `app/scripts/lib/emit-items.ts`. Add a helper just below `quote(...)`:

```ts
function quoteLocalized(s: { en: string; fil: string }): string {
  return `{ en: ${quote(s.en)}, fil: ${quote(s.fil)} }`;
}
```

Then change the import line at the top so the file declares the localized type for downstream consumers:

```ts
const header = [
  '// AUTOGENERATED — do not edit by hand.',
  '// Regenerate via `npm run generate`.',
  "import type { Section } from '@/types/survey';",
  '',
].join('\n');
```

(no change to the import itself — `Section` already pulls in `LocalizedString` once `types/survey.ts` is updated in Task 11.)

Now find every `quote(...)` call inside `emitSectionConst`, `emitItem`, choice mapping, and sub-field mapping that wraps a `label`, `title`, `preamble`, or `help` value, and swap to `quoteLocalized(...)`. Specific lines:

- In `emitSectionConst`:
  - `\`  title: ${quote(section.title)}\`` → `\`  title: ${quoteLocalized(section.title)}\``
  - `\`  preamble: ${quote(section.preamble)}\`` → `\`  preamble: ${quoteLocalized(section.preamble)}\``
- In `emitItem`:
  - `\`label: ${quote(item.label)}\`` → `\`label: ${quoteLocalized(item.label)}\``
  - `\`help: ${quote(item.help)}\`` → `\`help: ${quoteLocalized(item.help)}\``
- In the choice mapping:
  - `\`{ label: ${quote(c.label)}, value: ${quote(c.value)}${c.isOtherSpecify ? ', isOtherSpecify: true' : ''} }\`` → `\`{ label: ${quoteLocalized(c.label)}, value: ${quote(c.value)}${c.isOtherSpecify ? ', isOtherSpecify: true' : ''} }\``
- In the sub-field mapping:
  - `\`label: ${quote(sf.label)}\`` → `\`label: ${quoteLocalized(sf.label)}\``

`item.value` (the answer code) and `sf.id` stay as plain `quote(...)` — those are not user-facing labels.

- [ ] **Step 4: Run the tests — should pass**

Run from `app/`:

```bash
npx vitest run scripts/lib/emit-items.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/scripts/lib/emit-items.ts app/scripts/lib/emit-items.test.ts
git commit -m "feat(f2-pwa): emit LocalizedString literals from generator"
```

---

## Task 10: Regenerate items.ts

**Files:**
- Regenerate: `app/src/generated/items.ts`

- [ ] **Step 1: Run the generator**

Run from `app/`:

```bash
npm run generate
```

Expected: console reports `35+ section(s)` and `124 supported item(s)` (Apr 20 rev; or whatever the current counts are — same as before this milestone). `app/src/generated/items.ts` is rewritten in place.

- [ ] **Step 2: Spot-check the output**

Run from `app/`:

```bash
head -20 src/generated/items.ts
```

Expected: every `label:`, `title:`, choice `label:`, etc. now appears as `{ en: '...', fil: '...' }`. The `id`, `value`, `kind`, `min`, `max`, `required`, `type`, `section` fields are unchanged.

- [ ] **Step 3: Don't run the suite yet — many runtime tests will break**

Move on to Task 11 to fix the runtime types. (We bundle the generated-file commit with the type-update commit to keep the tree compilable across commits.)

- [ ] **Step 4: Stage but do not commit yet**

```bash
git add app/src/generated/items.ts
```

(Commit happens at the end of Task 11.)

---

## Task 11: Mirror LocalizedString in the runtime survey types

**Files:**
- Modify: `app/src/types/survey.ts`

This is the type that `Question`, `Section`, `ReviewSection`, etc. consume from `@/types/survey`. After this change those components stop compiling — Tasks 12–15 fix them one by one.

- [ ] **Step 1: Replace the file**

Replace `app/src/types/survey.ts` entirely:

```ts
import type { LocalizedString } from '@/i18n/localized';

export type ItemType =
  | 'short-text'
  | 'long-text'
  | 'number'
  | 'single'
  | 'multi'
  | 'date'
  | 'multi-field';

export interface Choice {
  label: LocalizedString;
  value: string;
  isOtherSpecify?: boolean;
}

export interface SubField {
  id: string;
  label: LocalizedString;
  kind: 'short-text' | 'number';
  min?: number;
  max?: number;
}

export interface Item {
  id: string;
  legacyId?: string;
  section: string;
  type: ItemType;
  required: boolean;
  label: LocalizedString;
  help?: LocalizedString;
  choices?: Choice[];
  hasOtherSpecify?: boolean;
  min?: number;
  max?: number;
  subFields?: SubField[];
}

export interface Section {
  id: string;
  title: LocalizedString;
  preamble?: LocalizedString;
  items: Item[];
}
```

- [ ] **Step 2: Stage with the regenerated items**

```bash
git add app/src/types/survey.ts
git commit -m "feat(f2-pwa): runtime survey types use LocalizedString + regenerate items.ts"
```

(`app/src/generated/items.ts` was staged at the end of Task 10 — both files commit together so the tree compiles after this commit even though the components don't yet.)

- [ ] **Step 3: Sanity check**

Run from `app/`:

```bash
npm run typecheck 2>&1 | head -40
```

Expected: errors in `Question.tsx`, `Section.tsx`, `ReviewSection.tsx` complaining that `LocalizedString` cannot be assigned to a `ReactNode` (or similar). This is expected — we fix them next.

---

## Task 12: Localize Question.tsx + tests

**Files:**
- Modify: `app/src/components/survey/Question.tsx`
- Modify: `app/src/components/survey/Question.test.tsx`

- [ ] **Step 1: Update Question.tsx**

Open `app/src/components/survey/Question.tsx` and apply these changes:

Add imports at the top:

```tsx
import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
```

Inside `Question`, add hooks at the top of the function body:

```tsx
const { t } = useTranslation();
const { locale } = useLocale();
```

Replace the label render:

```tsx
// before:
{item.label}
// after:
{localized(item.label, locale)}
```

Replace the help render:

```tsx
// before:
{item.help ? <p ...>{item.help}</p> : null}
// after:
{item.help ? <p className="text-xs text-muted-foreground">{localized(item.help, locale)}</p> : null}
```

Replace the required-fallback message:

```tsx
// before:
This field is required.
// after:
{t('question.requiredFallback')}
```

Replace the "Please specify" label and inline error in `renderControl` — but `renderControl` is a free function with no access to `t`/`locale`. Refactor: change `renderControl` to accept `t` and `locale` parameters.

Update the call site:

```tsx
// before:
{renderControl(item, register, showSpecify)}
// after:
{renderControl(item, register, showSpecify, t, locale)}
```

Update the function signature:

```tsx
function renderControl(
  item: Item,
  register: ReturnType<typeof useFormContext>['register'],
  showSpecify: boolean,
  t: ReturnType<typeof useTranslation>['t'],
  locale: import('@/i18n/index').Locale,
) {
```

Inside `renderControl`, every `choice.label` render becomes `{localized(choice.label, locale)}`, every `sf.label` render becomes `{localized(sf.label, locale)}`, and the two "Please specify" hard-coded strings become `{t('question.pleaseSpecifyLabel')}`.

The full revised file should look like this (use this as the canonical version):

```tsx
import { useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Locale } from '@/i18n/index';
import type { Item } from '@/types/survey';

interface QuestionProps {
  item: Item;
}

export function Question({ item }: QuestionProps) {
  const { t } = useTranslation();
  const { locale } = useLocale();
  const {
    register,
    watch,
    formState: { errors },
  } = useFormContext();
  const currentValue = watch(item.id);
  const showSpecify =
    (item.hasOtherSpecify &&
      item.choices?.some((c) => {
        if (!c.isOtherSpecify) return false;
        if (Array.isArray(currentValue)) return currentValue.includes(c.value);
        return c.value === currentValue;
      })) ??
    false;
  const error = errors[item.id];
  const errorMessage = typeof error?.message === 'string' ? error.message : undefined;

  return (
    <div className="flex flex-col gap-2 py-3">
      <label htmlFor={item.id} className="text-sm font-medium">
        {localized(item.label, locale)}
        {item.required ? <span className="ml-1 text-red-600">*</span> : null}
      </label>
      {item.help ? (
        <p className="text-xs text-muted-foreground">{localized(item.help, locale)}</p>
      ) : null}
      {renderControl(item, register, showSpecify, t, locale)}
      {errorMessage ? (
        <p role="alert" className="text-xs text-red-600">
          {errorMessage}
        </p>
      ) : error ? (
        <p role="alert" className="text-xs text-red-600">
          {t('question.requiredFallback')}
        </p>
      ) : null}
    </div>
  );
}

function renderControl(
  item: Item,
  register: ReturnType<typeof useFormContext>['register'],
  showSpecify: boolean,
  t: ReturnType<typeof useTranslation>['t'],
  locale: Locale,
) {
  switch (item.type) {
    case 'short-text':
      return (
        <input
          id={item.id}
          type="text"
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'long-text':
      return (
        <textarea
          id={item.id}
          rows={4}
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'number':
      return (
        <input
          id={item.id}
          type="number"
          min={item.min}
          max={item.max}
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'single':
      return (
        <div className="flex flex-col gap-1">
          <fieldset className="flex flex-col gap-1">
            {item.choices?.map((choice, idx) => (
              <label key={choice.value} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  value={choice.value}
                  {...(idx === 0 ? { id: item.id } : {})}
                  {...register(item.id)}
                />
                {localized(choice.label, locale)}
              </label>
            ))}
          </fieldset>
          {showSpecify ? (
            <div className="mt-2 flex flex-col gap-1 pl-6">
              <label htmlFor={`${item.id}_other`} className="text-xs text-muted-foreground">
                {t('question.pleaseSpecifyLabel')}
              </label>
              <input
                id={`${item.id}_other`}
                type="text"
                className="rounded border border-input bg-background px-3 py-2"
                {...register(`${item.id}_other`)}
              />
            </div>
          ) : null}
        </div>
      );
    case 'multi':
      return (
        <div className="flex flex-col gap-1">
          <fieldset className="flex flex-col gap-1">
            {item.choices?.map((choice, idx) => (
              <label key={choice.value} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  value={choice.value}
                  {...(idx === 0 ? { id: item.id } : {})}
                  {...register(item.id)}
                />
                {localized(choice.label, locale)}
              </label>
            ))}
          </fieldset>
          {showSpecify ? (
            <div className="mt-2 flex flex-col gap-1 pl-6">
              <label htmlFor={`${item.id}_other`} className="text-xs text-muted-foreground">
                {t('question.pleaseSpecifyLabel')}
              </label>
              <input
                id={`${item.id}_other`}
                type="text"
                className="rounded border border-input bg-background px-3 py-2"
                {...register(`${item.id}_other`)}
              />
            </div>
          ) : null}
        </div>
      );
    case 'date':
      return (
        <input
          id={item.id}
          type="date"
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'multi-field':
      return (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {item.subFields?.map((sf) => (
            <div key={sf.id} className="flex flex-col gap-1">
              <label htmlFor={sf.id} className="text-xs text-muted-foreground">
                {localized(sf.label, locale)}
              </label>
              <input
                id={sf.id}
                type={sf.kind === 'number' ? 'number' : 'text'}
                className="rounded border border-input bg-background px-3 py-2"
                {...register(sf.id)}
              />
            </div>
          ))}
        </div>
      );
  }
}
```

- [ ] **Step 2: Update Question.test.tsx fixtures**

Open `app/src/components/survey/Question.test.tsx`. Every test fixture that builds a fake `Item` with `label: '...'` etc. needs the localized shape. Use this top-of-file helper:

```ts
const dual = (en: string) => ({ en, fil: en });
```

And in every fixture, replace:
- `label: 'X'` → `label: dual('X')` for `Item`, `Choice`, `SubField`
- `title: 'Y'` → `title: dual('Y')` for `Section`
- `help: 'Z'` → `help: dual('Z')`
- `preamble: 'P'` → `preamble: dual('P')`

The visible-text assertions (`expect(screen.getByText('X')).toBeInTheDocument()`) DO NOT change — they check the rendered text, which is still 'X' in English locale.

Tests that need to render `<Question>` must be wrapped in `<LocaleProvider>`. Add a small helper at the top of the test file:

```tsx
import { LocaleProvider } from '@/i18n/locale-context';

function renderWithProviders(ui: React.ReactElement) {
  return render(<LocaleProvider>{ui}</LocaleProvider>);
}
```

Replace every `render(...)` call in this file with `renderWithProviders(...)` (the form-context wrapping that the test already does should remain inside the `renderWithProviders` argument).

- [ ] **Step 3: Run Question tests**

Run from `app/`:

```bash
npx vitest run src/components/survey/Question.test.tsx
```

Expected: PASS — every test green.

- [ ] **Step 4: Commit**

```bash
git add app/src/components/survey/Question.tsx app/src/components/survey/Question.test.tsx
git commit -m "feat(f2-pwa): localize Question + tests"
```

---

## Task 13: Localize Section.tsx + tests

**Files:**
- Modify: `app/src/components/survey/Section.tsx`
- Modify: `app/src/components/survey/Section.test.tsx`

- [ ] **Step 1: Update Section.tsx**

Open `app/src/components/survey/Section.tsx`. Add imports:

```tsx
import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
```

Add hooks at the top of `Section`:

```tsx
const { t } = useTranslation();
const { locale } = useLocale();
```

Replace the heading and preamble:

```tsx
// before:
<h2 className="text-2xl font-semibold tracking-tight">
  Section {section.id} — {section.title}
</h2>
{section.preamble ? (
  <p className="text-sm text-muted-foreground">{section.preamble}</p>
) : null}

// after:
<h2 className="text-2xl font-semibold tracking-tight">
  {t('review.sectionHeading', { id: section.id, title: localized(section.title, locale) })}
</h2>
{section.preamble ? (
  <p className="text-sm text-muted-foreground">{localized(section.preamble, locale)}</p>
) : null}
```

Replace the Submit button label:

```tsx
// before:
<Button type="submit">Submit</Button>
// after:
<Button type="submit">{t('navigator.submit')}</Button>
```

- [ ] **Step 2: Update Section.test.tsx**

Open `app/src/components/survey/Section.test.tsx`. Apply the same fixture updates as Task 12 (`dual()` helper, wrap renders in `<LocaleProvider>`). The visible-text expectation for the heading stays the same — `'Section A — Healthcare Worker Profile'` — because i18next's `sectionHeading` template `Section {{id}} — {{title}}` produces identical output in English.

- [ ] **Step 3: Run Section tests**

Run from `app/`:

```bash
npx vitest run src/components/survey/Section.test.tsx
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/src/components/survey/Section.tsx app/src/components/survey/Section.test.tsx
git commit -m "feat(f2-pwa): localize Section heading + Submit"
```

---

## Task 14: Localize Navigator + ProgressBar

**Files:**
- Modify: `app/src/components/survey/Navigator.tsx`
- Modify: `app/src/components/survey/Navigator.test.tsx`
- Modify: `app/src/components/survey/ProgressBar.tsx`
- Modify: `app/src/components/survey/ProgressBar.test.tsx` (only if it has visible strings)

- [ ] **Step 1: Read ProgressBar to learn what strings (if any) it shows**

Run from `app/`:

```bash
cat src/components/survey/ProgressBar.tsx
```

Expected: small file. Note any visible-to-user strings (e.g. "Step X of Y", "Progress"). If there are none, the only change needed is none — skip the ProgressBar substeps below.

- [ ] **Step 2: Update Navigator.tsx**

Replace `app/src/components/survey/Navigator.tsx`:

```tsx
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';

interface NavigatorProps {
  isFirst: boolean;
  isLast: boolean;
  onPrev: () => void;
  onNext: () => void;
  onSubmit: () => void;
}

export function Navigator({
  isFirst,
  isLast,
  onPrev,
  onNext,
  onSubmit,
}: NavigatorProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-between gap-3 pt-4">
      <Button type="button" variant="outline" onClick={onPrev} disabled={isFirst}>
        {t('navigator.previous')}
      </Button>
      {isLast ? (
        <Button type="button" onClick={onSubmit}>
          {t('navigator.submit')}
        </Button>
      ) : (
        <Button type="button" onClick={onNext}>
          {t('navigator.next')}
        </Button>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Update Navigator.test.tsx**

Open `app/src/components/survey/Navigator.test.tsx`. The visible-text expectations (`'Previous'`, `'Next'`, `'Submit'`) DO NOT change. Confirm tests still pass:

```bash
npx vitest run src/components/survey/Navigator.test.tsx
```

Expected: PASS.

- [ ] **Step 4: Update ProgressBar if it has visible strings**

If Step 1 surfaced any user-visible string in `ProgressBar.tsx`, externalize it the same way (add `useTranslation`, replace literal with `t(...)`, add the i18n key to both `en.ts` and `fil.ts`). If not, skip.

- [ ] **Step 5: Commit**

```bash
git add app/src/components/survey/Navigator.tsx app/src/components/survey/Navigator.test.tsx app/src/components/survey/ProgressBar.tsx app/src/components/survey/ProgressBar.test.tsx 2>/dev/null
git commit -m "feat(f2-pwa): localize Navigator (+ ProgressBar if applicable)"
```

---

## Task 15: Localize ReviewSection

**Files:**
- Modify: `app/src/components/survey/ReviewSection.tsx`
- Modify: `app/src/components/survey/ReviewSection.test.tsx`

`ReviewSection` shows `Section {id} — {title}` headings, "Edit" buttons, "Submit" button, "Review your answers" heading, and per-row `${item.id} ${item.label}` rows. The label must resolve via `localized(...)`; the row prefix can stay raw because it's the question id.

- [ ] **Step 1: Update ReviewSection.tsx**

Open `app/src/components/survey/ReviewSection.tsx`. Add imports:

```tsx
import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Locale } from '@/i18n/index';
```

Change the `rowsForItem` signature so it can resolve labels:

```tsx
function rowsForItem(item: Item, values: FormValues, locale: Locale): Array<{ key: string; label: string; value: string }> {
  if (item.type === 'multi-field' && item.subFields) {
    return item.subFields
      .map((sf) => ({ key: sf.id, label: `${item.id} ${localized(sf.label, locale)}`, value: formatValue(values[sf.id]) }))
      .filter((r) => r.value !== '');
  }
  const primary = formatValue(values[item.id]);
  const rows: Array<{ key: string; label: string; value: string }> = [];
  if (primary !== '') rows.push({ key: item.id, label: `${item.id} ${localized(item.label, locale)}`, value: primary });
  const otherKey = `${item.id}_other`;
  const otherVal = formatValue(values[otherKey]);
  if (otherVal !== '') rows.push({ key: otherKey, label: `${item.id} (specify)`, value: otherVal });
  return rows;
}
```

Inside `ReviewSection`, add hooks:

```tsx
const { t } = useTranslation();
const { locale } = useLocale();
```

Replace literal strings:

- `<h2 ...>Review your answers</h2>` → `<h2 ...>{t('review.heading')}</h2>`
- `aria-label="Cross-field warnings"` → `aria-label={t('review.crossFieldRegion')}`
- `<h3 ...>Section {section.id} — {section.title}</h3>` → `<h3 ...>{t('review.sectionHeading', { id: section.id, title: localized(section.title, locale) })}</h3>`
- `<Button ...>Edit</Button>` → `<Button ...>{t('review.edit')}</Button>`
- `<Button type="button" onClick={onSubmit}>Submit</Button>` → `<Button type="button" onClick={onSubmit}>{t('review.submit')}</Button>`

Update the `rowsForItem` call inside the SECTIONS map:

```tsx
const rows = section.items.flatMap((item) => rowsForItem(item, values, locale));
```

The cross-field warning rendering also needs localization — but that's owned by Task 18. For now, keep the existing `{w.message}` render; Task 18 changes the warning shape so this will be revisited then. Add a TODO-equivalent: leave the line as-is but DO NOT add a placeholder comment (per CLAUDE.md "no // TODO comments" rule — the unlocalized warning render is fixed in Task 18).

- [ ] **Step 2: Update ReviewSection.test.tsx**

Apply same fixture updates as Task 12. Wrap renders in `<LocaleProvider>`. Visible-text assertions stay the same.

- [ ] **Step 3: Run ReviewSection tests**

Run from `app/`:

```bash
npx vitest run src/components/survey/ReviewSection.test.tsx
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/src/components/survey/ReviewSection.tsx app/src/components/survey/ReviewSection.test.tsx
git commit -m "feat(f2-pwa): localize ReviewSection chrome + generated labels"
```

---

## Task 16: Localize EnrollmentScreen

**Files:**
- Modify: `app/src/components/enrollment/EnrollmentScreen.tsx`
- Modify: `app/src/components/enrollment/EnrollmentScreen.test.tsx`

- [ ] **Step 1: Update EnrollmentScreen.tsx**

Open `app/src/components/enrollment/EnrollmentScreen.tsx`. Add the import:

```tsx
import { useTranslation } from 'react-i18next';
```

Add hook at the top of the component:

```tsx
const { t } = useTranslation();
```

Replace each literal:

- `<h2 ...>Enroll</h2>` → `<h2 ...>{t('enrollment.heading')}</h2>`
- `Enter your HCW ID...` paragraph → `<p ...>{t('enrollment.helper')}</p>`
- `HCW ID` label text → `{t('enrollment.hcwIdLabel')}`
- `Facility` label text → `{t('enrollment.facilityLabel')}`
- `No facilities cached. Tap Refresh...` → `{t('enrollment.noFacilitiesCached')}`
- `<option value="">Select a facility…</option>` → `<option value="">{t('enrollment.facilityPlaceholder')}</option>`
- `<Button type="submit" disabled={!canSubmit}>Enroll</Button>` → `<Button type="submit" disabled={!canSubmit}>{t('enrollment.enrollButton')}</Button>`
- `{refreshing ? 'Refreshing…' : 'Refresh facility list'}` → `{refreshing ? t('enrollment.refreshingButton') : t('enrollment.refreshButton')}`

- [ ] **Step 2: Update EnrollmentScreen.test.tsx**

Open `app/src/components/enrollment/EnrollmentScreen.test.tsx`. Wrap renders in `<LocaleProvider>` (add the helper). Visible-text assertions ('Enroll', 'HCW ID', 'Facility', 'Refresh facility list', etc.) DO NOT change because EN bundle values match.

- [ ] **Step 3: Run EnrollmentScreen tests**

Run from `app/`:

```bash
npx vitest run src/components/enrollment/EnrollmentScreen.test.tsx
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/src/components/enrollment/EnrollmentScreen.tsx app/src/components/enrollment/EnrollmentScreen.test.tsx
git commit -m "feat(f2-pwa): localize EnrollmentScreen"
```

---

## Task 17: Localize SyncPage + SyncButton + PendingCount

**Files:**
- Modify: `app/src/components/sync/SyncPage.tsx`
- Modify: `app/src/components/sync/SyncPage.test.tsx`
- Modify: `app/src/components/sync/SyncButton.tsx`
- Modify: `app/src/components/sync/SyncButton.test.tsx`
- Modify: `app/src/components/sync/PendingCount.tsx`
- Modify: `app/src/components/sync/PendingCount.test.tsx`

- [ ] **Step 1: Update PendingCount.tsx**

Open `app/src/components/sync/PendingCount.tsx`. Add import + hook:

```tsx
import { useTranslation } from 'react-i18next';
// inside the component:
const { t } = useTranslation();
```

Replace the rendered string:

```tsx
// before:
{count} pending
// after:
{t('sync.pendingBadge', { count })}
```

- [ ] **Step 2: Update SyncButton.tsx**

Open `app/src/components/sync/SyncButton.tsx`. Add `useTranslation`. Replace the literals inside the JSX:

```tsx
// running button:
{state.kind === 'running' ? t('sync.runningButton') : t('sync.runButton')}
```

The summary panel needs interpolation. Replace the existing `state.kind === 'done'` block:

```tsx
{state.kind === 'done' ? (
  <span className="text-xs text-muted-foreground">
    {state.summary.synced > 0 ? t('sync.syncedSummary', { count: state.summary.synced }) : ''}
    {state.summary.retryScheduled > 0 ? ' · ' + t('sync.retryingSummary', { count: state.summary.retryScheduled }) : ''}
    {state.summary.failed > 0 ? ' · ' + t('sync.rejectedSummary', { count: state.summary.failed }) : ''}
    {state.summary.attempted === 0 ? t('sync.nothingToSync') : ''}
  </span>
) : null}
```

Replace the error fallback:

```tsx
// before:
setState({ kind: 'error', message: (err as Error).message || 'Sync failed' });
// after — the fallback string moves to the render-time, not the state. State holds the raw error message; render falls back when empty.
setState({ kind: 'error', message: (err as Error).message });

// and where state.kind === 'error' renders:
<span className="text-xs text-destructive">{state.message || t('sync.syncFailedFallback')}</span>
```

- [ ] **Step 3: Update SyncPage.tsx**

Open `app/src/components/sync/SyncPage.tsx`. Add `useTranslation`. Replace the `STATUS_LABEL` map: change it from a static `Record` to a function that takes `t` and returns the localized labels:

```tsx
function statusLabel(t: ReturnType<typeof useTranslation>['t'], status: SubmissionRow['status']): string {
  switch (status) {
    case 'pending_sync': return t('sync.statusPending');
    case 'syncing': return t('sync.statusSyncing');
    case 'retry_scheduled': return t('sync.statusRetryScheduled');
    case 'rejected': return t('sync.statusRejected');
    case 'synced': return t('sync.statusSynced');
  }
}
```

Delete the existing `const STATUS_LABEL: Record<...>` constant entirely.

Inside `SyncPage`, add `const { t } = useTranslation();` near the top. Replace:

- `<h2 ...>Sync</h2>` (both occurrences) → `<h2 ...>{t('sync.heading')}</h2>`
- `<p ...>No submissions yet.</p>` → `<p ...>{t('sync.none')}</p>`
- `STATUS_LABEL[s]` → `statusLabel(t, s)`
- `submitted {new Date(row.submitted_at).toLocaleString()}` → `{t('sync.submittedAt', { at: new Date(row.submitted_at).toLocaleString() })}`
- `retry at {new Date(row.next_retry_at).toLocaleString()}` → `{t('sync.retryAt', { at: new Date(row.next_retry_at).toLocaleString() })}`

- [ ] **Step 4: Update sync tests**

For each of `PendingCount.test.tsx`, `SyncButton.test.tsx`, `SyncPage.test.tsx`: visible-text assertions stay the same in English (because the bundle values match). Wrap renders in `<LocaleProvider>` if any test renders a component without already providing it.

- [ ] **Step 5: Run sync tests**

Run from `app/`:

```bash
npx vitest run src/components/sync/
```

Expected: PASS — all suites green.

- [ ] **Step 6: Commit**

```bash
git add app/src/components/sync/
git commit -m "feat(f2-pwa): localize SyncPage, SyncButton, PendingCount"
```

---

## Task 18: Localize cross-field warning messages

**Files:**
- Modify: `app/src/lib/cross-field.ts`
- Modify: `app/src/lib/cross-field.test.ts`
- Modify: `app/src/components/survey/ReviewSection.tsx` (use the new factory)
- Modify: `app/src/components/survey/ReviewSection.test.tsx` (update visible-text assertions if needed)

The challenge: `evaluateCrossField(values)` currently returns warnings with pre-built `message` strings. We want the message to localize when the user toggles language. Solution: change `Warning.message` from `string` to `{ key: string; values: Record<string, unknown> }` — render-time calls `t(key, values)`.

- [ ] **Step 1: Update cross-field.ts**

Open `app/src/lib/cross-field.ts`. Find the `Warning` interface (the file's first interface) and change:

```ts
// before:
export interface Warning {
  id: string;
  severity: 'error' | 'warn' | 'clean' | 'info';
  message: string;
}

// after:
export interface Warning {
  id: string;
  severity: 'error' | 'warn' | 'clean' | 'info';
  message: { key: string; values?: Record<string, unknown> };
}
```

Then for each existing rule, change the `message: \`...\``  literal to `{ key: 'crossField.<x>', values: { ... } }`. Mapping (use the lines reported by the earlier grep — line numbers may differ slightly, search for the literal text):

| Current literal | Replacement `key` | `values` |
|---|---|---|
| `Reported tenure (${tenureYears} years) is implausible for age ${age}.` | `crossField.tenureImplausible` | `{ years: tenureYears, age }` |
| `Role "${role}" does not normally carry a medical specialty (${specialty}).` | `crossField.specialtyMismatch` | `{ role, specialty }` |
| `` `Derived employment class: ${hours >= 8 ? 'full-time' : 'part-time'}.` `` | `crossField.employmentClassDerived` | `{ employmentClass: hours >= 8 ? 'full-time' : 'part-time' }` |
| `Reported workload (${days} days × ${hours} hrs = ${days * hours} hrs/week) exceeds 80.` | `crossField.workloadExceeds80` | `{ days, hours, total: days * hours }` |
| `Section G is for physicians and dentists only; answers from "${role}" will be dropped server-side.` | `crossField.sectionGRoleMismatch` | `{ role }` |
| `Sections C and D are for clinical-care roles only; answers from "${role}" will be dropped server-side.` | `crossField.sectionsCDRoleMismatch` | `{ role }` |

(If the file has more rules than the 6 above, follow the same pattern: add a key in `en.ts` + `fil.ts` under `crossField.`, update the rule.)

- [ ] **Step 2: Update cross-field.test.ts**

Open `app/src/lib/cross-field.test.ts`. Every assertion that checks `warning.message` against a string now needs to check the `key` and `values` shape. Pattern:

```ts
// before:
expect(warnings[0].message).toBe('Reported tenure (50 years) is implausible for age 25.');
// after:
expect(warnings[0].message).toEqual({
  key: 'crossField.tenureImplausible',
  values: { years: 50, age: 25 },
});
```

Apply the swap for every rule the suite covers.

- [ ] **Step 3: Update ReviewSection.tsx to render the new shape**

Open `app/src/components/survey/ReviewSection.tsx`. Change the warning render from `{w.message}` to:

```tsx
{t(w.message.key, w.message.values)}
```

(`useTranslation` is already imported from Task 15.)

- [ ] **Step 4: Update ReviewSection.test.tsx if any test asserts on warning text**

Visible warning text is the resolved EN string (e.g. `'Reported tenure (50 years) is implausible for age 25.'`). Existing assertions on that text continue to pass — confirm by running the suite. If a test also constructs a fake warning fixture, update its `message` to the new `{ key, values }` shape.

- [ ] **Step 5: Run cross-field + ReviewSection tests**

Run from `app/`:

```bash
npx vitest run src/lib/cross-field.test.ts src/components/survey/ReviewSection.test.tsx
```

Expected: PASS — all green.

- [ ] **Step 6: Commit**

```bash
git add app/src/lib/cross-field.ts app/src/lib/cross-field.test.ts app/src/components/survey/ReviewSection.tsx app/src/components/survey/ReviewSection.test.tsx
git commit -m "feat(f2-pwa): localize cross-field warning messages via i18n keys"
```

---

## Task 19: Mount LocaleProvider + LanguageSwitcher in App.tsx

**Files:**
- Modify: `app/src/App.tsx`
- Modify: `app/src/App.test.tsx`

- [ ] **Step 1: Update App.tsx**

Open `app/src/App.tsx`. Add imports:

```tsx
import { useTranslation } from 'react-i18next';
import { LocaleProvider } from '@/i18n/locale-context';
import { LanguageSwitcher } from '@/components/i18n/LanguageSwitcher';
```

Inside `AppShell`, add `const { t } = useTranslation();` near the other top-of-component hooks.

Replace literal strings inside the JSX:

- `<h1 ...>F2 Survey</h1>` → `<h1 ...>{t('chrome.appTitle')}</h1>`
- The `Form`/`Sync` toggle button text:
  ```tsx
  // before:
  {view === 'sync' ? 'Form' : 'Sync'}
  // after:
  {view === 'sync' ? t('chrome.formView') : t('chrome.syncView')}
  ```
- `Install` button → `{t('chrome.install')}`
- The two `Loading…` paragraphs → `{t('chrome.loading')}`
- The thank-you screen:
  ```tsx
  <h2 ...>Thank you</h2>
  <p ...>Your response is saved on this device and will sync when the app is online.</p>
  ```
  →
  ```tsx
  <h2 ...>{t('chrome.thankYouHeading')}</h2>
  <p ...>{t('chrome.thankYouBody')}</p>
  ```

Mount `<LanguageSwitcher />` inside the header `<div className="flex items-center gap-3">`, BEFORE `<PendingCount />`:

```tsx
<div className="flex items-center gap-3">
  <LanguageSwitcher />
  <PendingCount />
  ...rest unchanged...
</div>
```

Replace the `App` default export to wrap in `<LocaleProvider>`:

```tsx
export default function App() {
  return (
    <LocaleProvider>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </LocaleProvider>
  );
}
```

- [ ] **Step 2: Update App.test.tsx**

Open `app/src/App.test.tsx`. Existing tests already render `<App />` which now includes the providers — no wrapper update needed at the top-level. Visible-text assertions stay the same in English. If any test renders `<AppShell />` directly (bypassing `App`), wrap it in `<LocaleProvider><AuthProvider>...</AuthProvider></LocaleProvider>`.

- [ ] **Step 3: Run App tests**

Run from `app/`:

```bash
npx vitest run src/App.test.tsx
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/src/App.tsx app/src/App.test.tsx
git commit -m "feat(f2-pwa): wire LocaleProvider + LanguageSwitcher into App shell"
```

---

## Task 20: Full suite + typecheck + build green

**Files:** none modified — verification only.

- [ ] **Step 1: Run the full test suite**

Run from `app/`:

```bash
npm test
```

Expected: every test green. The new tests are:
- 4 in `locale-context.test.tsx`
- 4 in `localized.test.ts`
- 3 in `LanguageSwitcher.test.tsx`

Plus the old 230 minus any tests that have legitimately changed (none should be removed). Total ≈ 241+.

If any test fails, fix it before continuing. Do NOT proceed to typecheck/build with red tests.

- [ ] **Step 2: Run typecheck**

Run from `app/`:

```bash
npm run typecheck
```

Expected: clean (no diagnostics).

- [ ] **Step 3: Run the production build**

Run from `app/`:

```bash
npm run build
```

Expected: build succeeds. The bundle picks up i18next + the resource bundles; size should grow by ~50-80 KB minified (acceptable for the PWA budget).

- [ ] **Step 4: Smoke test in dev (optional, only if a UI sanity check is needed)**

Run from `app/`:

```bash
npm run dev
```

Visit http://localhost:5173. Verify:
- Header shows the EN/FIL toggle buttons next to the pending badge
- Clicking FIL leaves all visible text unchanged (because fil.ts mirrors en.ts) — this is correct
- Reloading the page after clicking FIL keeps the FIL button selected (`localStorage` persistence)
- Clicking EN reverts

If smoke test is skipped, mark this step as done explicitly in the checkbox — do not silently skip.

- [ ] **Step 5: Commit (if any test/build adjustments were needed in earlier steps)**

If steps 1-3 surfaced fixes, commit them now:

```bash
git add -A
git commit -m "fix(f2-pwa): resolve M9 i18n test/typecheck/build follow-ups"
```

If no fixes needed, skip the commit.

---

## Task 21: Update NEXT.md

**Files:**
- Modify: `app/NEXT.md`

- [ ] **Step 1: Rewrite NEXT.md**

Replace the entire contents of `app/NEXT.md` with the version below. (Don't preserve the old M8 content — its narrative is now history.)

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M9 — i18n / Filipino. react-i18next wired in, LocaleProvider persists locale to `localStorage` key `f2_locale`, header LanguageSwitcher toggles EN/FIL. Generator now emits `LocalizedString = { en, fil }` for every label/title/help/preamble/choice/subField; `localized(label, locale)` resolves at render time with English fallback. All chrome strings (header, EnrollmentScreen, Navigator, ReviewSection, Section, SyncPage, SyncButton, PendingCount) routed through `t()`. Cross-field warning messages converted to interpolated i18n keys (`{ key, values }`). **Filipino strings are placeholder-equal-to-English — drop in real translations by editing `app/src/i18n/locales/fil.ts` (chrome) and adding a `--with-translations spec/F2-Spec.fil.md` overlay to the generator (instrument labels) when ASPSI delivers.** Tests + typecheck + build clean.

**Next milestone:** M10 — Admin dashboard (Apps-Script-served HTML). 10–15h per spec §11.1.

**Before starting M10:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §4.7 (Admin dashboard) and §11.1 row M10.
2. Confirm the existing `backend/src/Handlers.js` exposes the data the dashboard needs (status counts, recent submissions, kill-switch toggle, broadcast_message editor). If not, the plan also needs backend additions.
3. Target: HtmlService template served from a new `?action=admin` route, basic-auth gated by a separate ADMIN_SECRET env var. CSV export. Status counters live-queried via the existing endpoints.
4. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M10-admin-dashboard.md`.

**M9 follow-ups (slot in when ASPSI delivers):**

- **Filipino instrument translations.** Add `spec/F2-Spec.fil.md` (parallel structure to `spec/F2-Spec.md`). Extend `app/scripts/lib/parse-spec.ts` to read it as an overlay (when present, populate `fil` from the overlay instead of mirroring `en`). Regenerate `items.ts`. Estimated 3-5h.
- **Filipino chrome translations.** Replace placeholder values in `app/src/i18n/locales/fil.ts` with the real translations. Estimated 1-2h.
- **Browser language auto-detection on first load.** Currently defaults to `'en'` if nothing is in `localStorage`. Optional: use `i18next-browser-languagedetector` to auto-pick `fil` for users whose browser locale is `fil-PH`. Estimated 30 minutes.

**M8 technical debt still outstanding:**

- **`facility_has_bucas` / `facility_has_gamot` flags** — backend schema additions still pending; needed before FAC-01..07 cross-field rules can wire up.
- **`response_source` per-respondent capture** — currently hardcoded `source: 'pwa'`. SRC-01..03 cross-field rules want this.
- **Sync-page "change enrollment" affordance** — `unenroll()` exists but no UI calls it.
- **Auto-refresh facilities on app open** — currently only the explicit Refresh button on EnrollmentScreen calls it.
- **`/config` endpoint** — backend has it; PWA never calls it. M11 hardening should poll on app open.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M9 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Copy `.env.example` → `.env.local` and fill both vars from the live Apps Script deployment.
- `npm run dev`, walk through: enrollment screen → fill form (toggle EN/FIL in header) → review → submit → sync.
- Open `../2026-04-17-design-spec.md` §4.7 + §11.1 row M10 to re-orient for the admin dashboard.
```

- [ ] **Step 2: Commit**

```bash
git add app/NEXT.md
git commit -m "docs(f2-pwa): update NEXT.md to point at M10 (admin dashboard)"
```

---

## Self-review (run before declaring done)

**Spec coverage check:**

| Spec section | Covered by task |
|---|---|
| §5.5 "UI language → React Context + localStorage. Survives reload." | Task 4 (LocaleProvider + persistence) + Task 7 (LanguageSwitcher) + Task 19 (mounted in App) |
| §6.2 "label keys (en + fil)" in generated items | Task 5 (LocalizedString type) + Task 8 (generator types) + Task 9 (emit) + Task 10 (regenerate) + Task 11 (runtime types) |
| §11.1 row M9 "react-i18next, label bundles, Bilingual instrument" | Tasks 1, 2, 3, 4, 5, 6, 7, 12-19 |
| §11.1 effort 10-15h | Plan fits: 21 tasks × ~30-45 min each = ~12-15h |
| §13 open question #1 "ASPSI translates or Carl translates?" | Resolved at top of plan: build infrastructure with placeholder fil = en; ASPSI's deliverable is a content-only patch deferred to a follow-up |

**Placeholder scan:** None. Every code step has a complete code block. The only "TBD-ish" line is "(if Step 1 surfaced any visible string in ProgressBar.tsx, externalize it the same way)" in Task 14 — that's conditional-on-discovery, not a placeholder; the engineer reads the file in Step 1 and decides in Step 4.

**Type consistency check:**

- `LocalizedString` defined identically in `app/scripts/lib/types.ts` (Task 8) and `app/src/i18n/localized.ts` (Task 5) — both have `{ en: string; fil: string }`. Runtime `app/src/types/survey.ts` (Task 11) imports from `@/i18n/localized` — single source of truth on the runtime side.
- `Locale` defined once in `app/src/i18n/index.ts` (Task 4), imported by `localized.ts` (Task 5), `locale-context.tsx` (Task 4), `Question.tsx` (Task 12), `ReviewSection.tsx` (Task 15) — consistent.
- `localized(label, locale)` signature stable across all call sites — `(label: LocalizedString, locale: Locale) => string`.
- `Warning.message` shape changes from `string` (Tasks 1-17) to `{ key, values? }` (Task 18). `ReviewSection.tsx` updated in Task 18 to match.
- i18n key paths consistent: `chrome.*`, `enrollment.*`, `navigator.*`, `question.*`, `review.*`, `sync.*`, `crossField.*`, `language.*` — all referenced from the bundles.

Plan is ready for execution.
