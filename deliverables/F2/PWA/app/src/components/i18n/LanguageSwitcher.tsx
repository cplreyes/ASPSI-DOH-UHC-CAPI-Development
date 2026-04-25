import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useLocale } from '@/i18n/locale-context';

export function LanguageSwitcher() {
  const { t } = useTranslation();
  const { locale, setLocale } = useLocale();

  return (
    <div
      className="flex items-center gap-1"
      role="group"
      aria-label={t('language.label')}
      data-testid="language-switcher"
    >
      <Button
        size="sm"
        variant={locale === 'en' ? 'default' : 'outline'}
        aria-pressed={locale === 'en'}
        aria-label={t('language.en')}
        onClick={() => setLocale('en')}
        className={locale === 'en' ? 'font-bold ring-2 ring-primary/40' : ''}
      >
        EN
      </Button>
      <Button
        size="sm"
        variant={locale === 'fil' ? 'default' : 'outline'}
        aria-pressed={locale === 'fil'}
        aria-label={t('language.fil')}
        onClick={() => setLocale('fil')}
        className={locale === 'fil' ? 'font-bold ring-2 ring-primary/40' : ''}
      >
        FIL
      </Button>
      <span
        role="status"
        aria-live="polite"
        className="sr-only"
        data-testid="active-locale"
      >
        {locale === 'en' ? t('language.en') : t('language.fil')}
      </span>
    </div>
  );
}
