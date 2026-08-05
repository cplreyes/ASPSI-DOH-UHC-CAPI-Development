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
  /**
   * #1002: rafflePhone is the optional contact number for raffle winners
   * (null when the respondent proceeds without one). Only ever non-null on
   * the agree path — decliners are never asked for a number.
   */
  onAgree: (rafflePhone: string | null) => void;
  onDecline: () => void;
}

type Choice = 'agree' | 'decline';

export function ConsentScreen({ onAgree, onDecline }: ConsentScreenProps) {
  const { t } = useTranslation();
  const [choice, setChoice] = useState<Choice | null>(null);
  // #1002: optional raffle contact number, shown only after "agree" is picked.
  const [rafflePhone, setRafflePhone] = useState('');
  // Inline confirmation (not window.confirm) when agreeing with a blank
  // number — the respondent must acknowledge they forfeit the prize contact.
  const [confirmBlankPhone, setConfirmBlankPhone] = useState(false);

  const pickChoice = (next: Choice) => {
    setChoice(next);
    setConfirmBlankPhone(false);
  };

  const handleContinue = () => {
    if (choice === 'agree') {
      const trimmed = rafflePhone.trim();
      if (!trimmed) {
        // Blank number → the confirm panel below takes over; its "proceed"
        // button is the only path forward without a number.
        setConfirmBlankPhone(true);
        return;
      }
      onAgree(trimmed);
    } else if (choice === 'decline') {
      onDecline();
    }
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
            onChange={() => pickChoice('agree')}
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
            onChange={() => pickChoice('decline')}
            className="mt-0.5"
            data-testid="consent-decline"
          />
          <span>{t('consent.declineOption')}</span>
        </label>

        {choice === 'agree' ? (
          <div className="flex flex-col gap-2 border-t border-border pt-4">
            <h3 className="font-mono text-xs uppercase tracking-wide text-muted-foreground">
              {t('consent.rafflePhoneHeading')}
            </h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {t('consent.rafflePhoneNote')}
            </p>
            <label className="flex flex-col gap-1 text-sm">
              <span className="sr-only">{t('consent.rafflePhoneLabel')}</span>
              <input
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                value={rafflePhone}
                onChange={(e) => {
                  setRafflePhone(e.target.value);
                  setConfirmBlankPhone(false);
                }}
                placeholder={t('consent.rafflePhonePlaceholder')}
                className="border-0 border-b border-border bg-transparent py-2 text-base outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal focus:ring-0"
                data-testid="consent-raffle-phone"
              />
            </label>
          </div>
        ) : null}

        {confirmBlankPhone && choice === 'agree' ? (
          <div
            role="alertdialog"
            aria-label={t('consent.rafflePhoneConfirmHeading')}
            className="flex flex-col gap-3 border-l-2 border-signal pl-3 py-2"
            data-testid="consent-blank-phone-confirm"
          >
            <p className="text-sm leading-relaxed">{t('consent.rafflePhoneConfirmBody')}</p>
            <div className="flex flex-wrap items-center gap-3">
              <Button
                variant="outline"
                onClick={() => setConfirmBlankPhone(false)}
                data-testid="consent-blank-phone-back"
              >
                {t('consent.rafflePhoneConfirmBack')}
              </Button>
              <Button onClick={() => onAgree(null)} data-testid="consent-blank-phone-proceed">
                {t('consent.rafflePhoneConfirmProceed')}
              </Button>
            </div>
          </div>
        ) : (
          <div className="pt-2">
            <Button
              onClick={handleContinue}
              disabled={choice === null}
              data-testid="consent-continue"
            >
              {t('consent.continueButton')}
            </Button>
          </div>
        )}
      </fieldset>
    </section>
  );
}
