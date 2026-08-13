import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { READY_LOCALES, LOCALE_META, isLocale } from '@/i18n';

// Language selector — a single native <select> listing every READY locale, i.e.
// those with delivered + wired translations (see LOCALE_META in src/i18n/index.ts).
// A dropdown rather than a button row, to match how the CSPro/CSEntry instruments
// (F1/F3/F4) present language choice and to keep the chrome bar compact now that
// the list spans 8 languages (English + the 7 PSA-target PH languages). Each
// option is labelled by its native name; the current locale is the selected
// option. A native <select> is fully keyboard-accessible and self-announces the
// chosen option to screen readers, so no separate aria-live mirror is needed.
// Hidden entirely when English is the only ready locale (VITE_ENGLISH_ONLY) — a
// one-option dropdown would be a dead control.
export function LanguageSwitcher() {
  const { t } = useTranslation();
  const { locale, setLocale } = useLocale();

  if (READY_LOCALES.length <= 1) {
    return null;
  }

  return (
    <select
      value={locale}
      onChange={(e) => {
        const next = e.target.value;
        if (isLocale(next)) setLocale(next);
      }}
      aria-label={t('language.label')}
      data-testid="language-switcher"
      className="h-8 cursor-pointer rounded-md border border-input bg-background px-3 text-xs font-medium hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      {READY_LOCALES.map((loc) => (
        <option key={loc} value={loc}>
          {LOCALE_META[loc].native}
        </option>
      ))}
    </select>
  );
}
