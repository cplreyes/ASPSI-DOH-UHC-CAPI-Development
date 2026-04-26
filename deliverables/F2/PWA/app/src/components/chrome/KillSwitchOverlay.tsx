import { useTranslation } from 'react-i18next';

interface Props {
  active: boolean;
}

export function KillSwitchOverlay({ active }: Props) {
  const { t } = useTranslation();
  if (!active) return null;
  return (
    <div
      role="alert"
      aria-labelledby="kill-switch-title"
      aria-describedby="kill-switch-body"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-6"
    >
      <div className="max-w-md rounded-md border border-border bg-background p-6">
        <h2 id="kill-switch-title" className="mb-2 font-serif text-lg font-medium tracking-tight">
          {t('chrome.killSwitchTitle')}
        </h2>
        <p id="kill-switch-body" className="text-sm text-muted-foreground">
          {t('chrome.killSwitchBody')}
        </p>
      </div>
    </div>
  );
}
