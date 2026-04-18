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
