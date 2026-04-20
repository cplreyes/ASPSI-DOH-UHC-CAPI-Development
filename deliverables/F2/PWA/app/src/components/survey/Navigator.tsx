import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';

interface NavigatorProps {
  isFirst: boolean;
  isLast: boolean;
  onPrev: () => void;
  onNext: () => void;
  onSubmit: () => void;
}

export function Navigator({ isFirst, isLast, onPrev, onNext, onSubmit }: NavigatorProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-between gap-3 pt-4">
      <Button type="button" variant="outline" onClick={onPrev} disabled={isFirst}>
        {t('navigator.previous')}
      </Button>
      {isLast ? (
        <Button type="button" onClick={onSubmit}>
          {t('navigator.submit')}
        </Button>
      ) : (
        <Button type="button" onClick={onNext}>
          {t('navigator.next')}
        </Button>
      )}
    </div>
  );
}
