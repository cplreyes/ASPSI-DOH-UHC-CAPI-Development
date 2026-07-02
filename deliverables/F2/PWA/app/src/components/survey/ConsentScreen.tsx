import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';

/**
 * #808: per-case informed-consent gate, shown after enrollment (and after
 * every "Start new survey"), before Section A. Content is the SJREB-mandated
 * cover block from F2-Cover-Block-Rewrite-Draft.md (Blocks 2-5), adapted for
 * the PWA: the Google-Forms save/return sentence is replaced with the app's
 * autosave behavior and the unresolved "[X] minutes" duration sentence is
 * omitted pending ASPSI's estimate. Strings live in the i18n chrome bundles
 * (consent.*), not the spec translations overlay — this is app chrome, not a
 * generated survey item.
 *
 * The admin paper-encoder path (mode='encoded') never mounts this gate —
 * paper consent is already on file for encoded responses.
 */
interface ConsentScreenProps {
  onAgree: () => void;
  onDecline: () => void;
}

type Choice = 'agree' | 'decline';

export function ConsentScreen({ onAgree, onDecline }: ConsentScreenProps) {
  const { t } = useTranslation();
  const [choice, setChoice] = useState<Choice | null>(null);

  const handleContinue = () => {
    if (choice === 'agree') onAgree();
    else if (choice === 'decline') onDecline();
  };

  return (
    <section className="mx-auto flex max-w-xl flex-col gap-4 p-6">
      <h2 className="font-serif text-2xl font-medium tracking-tight">{t('consent.heading')}</h2>
      <p className="text-sm text-muted-foreground">{t('consent.intro')}</p>

      <div className="flex flex-col gap-3 border-t border-border pt-4">
        <h3 className="font-mono text-xs uppercase tracking-wide text-muted-foreground">
          {t('consent.infoHeading')}
        </h3>
        <p className="text-sm leading-relaxed">{t('consent.infoStudy')}</p>
        <p className="text-sm leading-relaxed">{t('consent.infoPrivacy')}</p>
        <p className="text-sm leading-relaxed">{t('consent.infoBenefits')}</p>
        <p className="text-sm leading-relaxed">{t('consent.infoRights')}</p>
      </div>

      <div className="flex flex-col gap-2 border-t border-border pt-4">
        <p className="text-sm text-muted-foreground">{t('consent.contactsHeading')}</p>
        <p className="whitespace-pre-line font-mono text-xs leading-relaxed text-muted-foreground">
          {t('consent.contactsBody')}
        </p>
      </div>

      <fieldset className="flex flex-col gap-3 border-t border-border pt-4">
        <legend className="sr-only">{t('consent.confirmHeading')}</legend>
        <h3 className="font-mono text-xs uppercase tracking-wide text-muted-foreground">
          {t('consent.confirmHeading')}
        </h3>
        <p className="text-sm text-muted-foreground">{t('consent.confirmPrompt')}</p>

        <label className="flex items-start gap-3 text-sm">
          <input
            type="radio"
            name="consent-choice"
            checked={choice === 'agree'}
            onChange={() => setChoice('agree')}
            className="mt-0.5"
            data-testid="consent-agree"
          />
          <span>{t('consent.agreeOption')}</span>
        </label>
        <label className="flex items-start gap-3 text-sm">
          <input
            type="radio"
            name="consent-choice"
            checked={choice === 'decline'}
            onChange={() => setChoice('decline')}
            className="mt-0.5"
            data-testid="consent-decline"
          />
          <span>{t('consent.declineOption')}</span>
        </label>

        <div className="pt-2">
          <Button onClick={handleContinue} disabled={choice === null} data-testid="consent-continue">
            {t('consent.continueButton')}
          </Button>
        </div>
      </fieldset>
    </section>
  );
}
