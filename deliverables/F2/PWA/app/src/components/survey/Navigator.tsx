import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';

interface NavigatorProps {
  onSaveDraft?: () => void;
  showSaved?: boolean;
}

export function Navigator({ onSaveDraft, showSaved }: NavigatorProps) {
  const { t } = useTranslation();
  if (!onSaveDraft) return null;
  return (
    <div className="flex items-center gap-3 pt-4">
      <Button type="button" variant="outline" className="w-full" onClick={onSaveDraft}>
        {t('navigator.saveDraft')}
      </Button>
      {showSaved ? (
        <span className="whitespace-nowrap text-sm text-primary">{t('navigator.draftSaved')}</span>
      ) : null}
    </div>
  );
}
