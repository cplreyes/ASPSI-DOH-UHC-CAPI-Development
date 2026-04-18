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
