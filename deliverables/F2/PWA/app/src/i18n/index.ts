import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { en } from './locales/en';
import { fil } from './locales/fil';
import { ceb } from './locales/ceb';
import { bis } from './locales/bis';
import { ilo } from './locales/ilo';
import { hil } from './locales/hil';
import { war } from './locales/war';
import { bcl } from './locales/bcl';

// Full locale universe: English (source) + the 7 PSA-target Philippine languages.
// The Locale TYPE spans all 8 so survey content — which may carry any of them in
// its LocalizedString labels — stays well-typed. Only locales whose translations
// are delivered + wired are REGISTERED for chrome and shown in the switcher
// (LOCALE_META.ready / READY_LOCALES). Bisaya is tracked DISTINCT from Cebuano
// per project convention (the build is 7 layers, not 6).
export const SUPPORTED_LOCALES = ['en', 'fil', 'ceb', 'bis', 'ilo', 'hil', 'war', 'bcl'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

// Display name (native) + readiness per locale. All 7 PSA-target languages are wired
// from ASPSI's v2.1/v2.1.1 questionnaire docs (spec/translations/{locale}.json + chrome
// bundles). Survey-content coverage varies 74–95%; untranslated strings fall back to
// English at render time. `ready` gates switcher visibility.
export const LOCALE_META: Record<Locale, { native: string; ready: boolean }> = {
  en: { native: 'English', ready: true },
  fil: { native: 'Filipino', ready: true }, // Tagalog
  ceb: { native: 'Cebuano', ready: true },
  bis: { native: 'Bisaya', ready: true },
  ilo: { native: 'Ilocano', ready: true },
  hil: { native: 'Hiligaynon', ready: true },
  war: { native: 'Waray', ready: true },
  bcl: { native: 'Bikol', ready: true },
};

// TEMPORARY English-only mode — Shan request 2026-06-16: ship the survey English-only
// so the team can capture clean English screenshots. When the production build sets
// VITE_ENGLISH_ONLY=true (.env.production), READY_LOCALES collapses to just English,
// which (a) hides the language switcher — LanguageSwitcher returns null at <=1 ready
// locale — and (b) makes any persisted dialect fall back to English (see locale-context).
// vitest runs in test mode WITHOUT the flag, so all 7 PSA languages stay wired + fully
// tested and CI stays green. REVERT: delete .env.production (or its VITE_ENGLISH_ONLY
// line) and let CI redeploy, or `git revert` the commit.
export const ENGLISH_ONLY = import.meta.env.VITE_ENGLISH_ONLY === 'true';

// Locales offered in the language switcher (those with delivered translations).
export const READY_LOCALES: readonly Locale[] = ENGLISH_ONLY
  ? (['en'] as const)
  : (SUPPORTED_LOCALES as readonly Locale[]).filter((l) => LOCALE_META[l].ready);

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (SUPPORTED_LOCALES as readonly string[]).includes(value);
}

if (!i18n.isInitialized) {
  void i18n.use(initReactI18next).init({
    resources: {
      en: { translation: en },
      fil: { translation: fil },
      ceb: { translation: ceb },
      bis: { translation: bis },
      ilo: { translation: ilo },
      hil: { translation: hil },
      war: { translation: war },
      bcl: { translation: bcl },
    },
    lng: 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
    returnNull: false,
  });
}

export { i18n };
