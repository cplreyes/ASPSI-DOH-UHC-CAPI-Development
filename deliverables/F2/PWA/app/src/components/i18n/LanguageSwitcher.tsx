import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useLocale } from '@/i18n/locale-context';
import { READY_LOCALES, LOCALE_META } from '@/i18n';

// Renders one button per READY locale — those with delivered + wired translations
// (see LOCALE_META in src/i18n/index.ts). A locale's button appears only once its
// spec/translations/{locale}.json and chrome bundle are populated and its `ready`
// flag is flipped, so the control never shows a language that would render as
// English. Hidden entirely when English is the only ready locale.
export function LanguageSwitcher() {
  const { t } = useTranslation();
  const { locale, setLocale } = useLocale();

  if (READY_LOCALES.length <= 1) {
    return null;
  }

  const activeNative = LOCALE_META[locale]?.native ?? LOCALE_META.en.native;

  return (
    <div
      className="flex items-center gap-1"
      role="group"
      aria-label={t('language.label')}
      data-testid="language-switcher"
    >
      {READY_LOCALES.map((loc) => {
        const active = locale === loc;
        return (
          <Button
            key={loc}
            size="sm"
            variant={active ? 'default' : 'outline'}
            aria-pressed={active}
            aria-label={LOCALE_META[loc].native}
            onClick={() => setLocale(loc)}
            className={active ? 'font-bold ring-2 ring-primary/40' : ''}
          >
            {loc === 'fil' ? 'FIL' : loc.toUpperCase()}
          </Button>
        );
      })}
      <span role="status" aria-live="polite" className="sr-only" data-testid="active-locale">
        {activeNative}
      </span>
    </div>
  );
}
