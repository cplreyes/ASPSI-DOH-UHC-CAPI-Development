import type { Locale } from './index';

// English is the source and always present. Each dialect is optional; a missing
// or empty dialect string falls back to English so a partially-translated locale
// degrades gracefully instead of showing blanks. Survey-content dialect strings
// are populated by the generator from spec/translations/{locale}.json.
export interface LocalizedString {
  en: string;
  fil?: string; // Tagalog
  ceb?: string; // Cebuano
  bis?: string; // Bisaya
  ilo?: string; // Ilocano
  hil?: string; // Hiligaynon (pending ASPSI)
  war?: string; // Waray (pending ASPSI)
  bcl?: string; // Bikol/Bicolano (pending ASPSI)
}

export function localized(label: LocalizedString, locale: Locale): string {
  const v = label[locale];
  return typeof v === 'string' && v.length > 0 ? v : label.en;
}
