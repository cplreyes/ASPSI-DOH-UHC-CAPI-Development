import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';

interface ProgressBarProps {
  current: number;
  total: number;
  className?: string;
}

const TRACK_WIDTH = 18;

export function ProgressBar({ current, total, className }: ProgressBarProps) {
  const { t } = useTranslation();
  const ratio = Math.min(1, Math.max(0, current / total));
  const percent = Math.round(ratio * 100);
  const filled = Math.round(ratio * TRACK_WIDTH);
  const padded = (n: number) => String(n).padStart(String(total).length, '0');
  return (
    <div className={cn('flex flex-col gap-1 px-6 pt-3', className)}>
      <p className="font-mono text-xs uppercase tracking-wide text-muted-foreground">
        {t('progressBar.sectionLabel', { current, total })}
      </p>
      <div
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        className="font-mono text-sm leading-none"
      >
        <span className="text-foreground">{padded(current)}</span>
        <span aria-hidden="true">{'  '}</span>
        <span aria-hidden="true" className="text-primary">
          {'━'.repeat(filled)}
        </span>
        <span aria-hidden="true" className="text-muted-foreground opacity-45">
          {'━'.repeat(TRACK_WIDTH - filled)}
        </span>
        <span aria-hidden="true">{'  '}</span>
        <span className="text-muted-foreground">{padded(total)}</span>
      </div>
    </div>
  );
}
