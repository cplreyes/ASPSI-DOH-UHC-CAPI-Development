import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { en } from './locales/en';
import { fil } from './locales/fil';
// Chrome bundles for ceb/bis/ilo are added here once their translations land and
// LOCALE_META flips them to ready. Until then only en + fil chrome are registered;
// the Locale type below still spans all 8 so survey content stays well-typed.

// Full locale universe: English (source) + the 7 PSA-target Philippine languages.
// The Locale TYPE spans all 8 so survey content — which may carry any of them in
// its LocalizedString labels — stays well-typed. Only locales whose translations
// are delivered + wired are REGISTERED for chrome and shown in the switcher
// (LOCALE_META.ready / READY_LOCALES). Bisaya is tracked DISTINCT from Cebuano
// per project convention (the build is 7 layers, not 6).
export const SUPPORTED_LOCALES = ['en', 'fil', 'ceb', 'bis', 'ilo', 'hil', 'war', 'bcl'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

// Display name (native) + readiness per locale. `ready` gates switcher visibility:
// flip a dialect to true once its spec/translations/{locale}.json is populated and
// its chrome bundle is wired. hil/war/bcl await ASPSI delivery (no Drive folders yet).
export const LOCALE_META: Record<Locale, { native: string; ready: boolean }> = {
  en: { native: 'English', ready: true },
  fil: { native: 'Filipino', ready: true }, // Tagalog — ASPSI doc extracted + wired
  // ceb/bis/ilo: ASPSI translations exist on Drive but the per-instrument F2 docs
  // are not file-accessible via the API yet (folders enumerate empty). Flip to true
  // once spec/translations/{ceb,bis,ilo}.json + their chrome bundles are populated.
  ceb: { native: 'Cebuano', ready: false },
  bis: { native: 'Bisaya', ready: false },
  ilo: { native: 'Ilocano', ready: false },
  hil: { native: 'Hiligaynon', ready: false }, // not yet delivered by ASPSI
  war: { native: 'Waray', ready: false }, // not yet delivered by ASPSI
  bcl: { native: 'Bikol', ready: false }, // not yet delivered by ASPSI
};

// Locales offered in the language switcher (those with delivered translations).
export const READY_LOCALES: readonly Locale[] = (SUPPORTED_LOCALES as readonly Locale[]).filter(
  (l) => LOCALE_META[l].ready,
);

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
