import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';

interface Props {
  drift: boolean;
  localVersion: string;
  serverMin: string;
}

export function SpecDriftOverlay({ drift, localVersion, serverMin }: Props) {
  const { t } = useTranslation();
  const reloadRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (drift) reloadRef.current?.focus();
  }, [drift]);

  if (!drift) return null;
  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="spec-drift-title"
      aria-describedby="spec-drift-body"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-6"
    >
      <div className="max-w-md rounded-md border border-border bg-background p-6">
        <h2 id="spec-drift-title" className="mb-2 font-serif text-lg font-medium tracking-tight">
          {t('chrome.specDriftTitle')}
        </h2>
        <p id="spec-drift-body" className="mb-4 text-sm text-muted-foreground">
          {t('chrome.specDriftBody', { localVersion, serverMin })}
        </p>
        <Button ref={reloadRef} onClick={() => window.location.reload()}>
          {t('chrome.reload')}
        </Button>
      </div>
    </div>
  );
}
