import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';

interface ProgressBarProps {
  current: number;
  total: number;
  className?: string;
}

export function ProgressBar({ current, total, className }: ProgressBarProps) {
  const { t } = useTranslation();
  const percent = Math.min(100, Math.round((current / total) * 100));
  return (
    <div className={cn('flex flex-col gap-1 px-6 pt-3', className)}>
      <p className="text-xs text-muted-foreground">
        {t('progressBar.sectionLabel', { current, total })}
      </p>
      <div
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2 w-full overflow-hidden rounded bg-muted"
      >
        <div className="h-full bg-primary transition-all" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
