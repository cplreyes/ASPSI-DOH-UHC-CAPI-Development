interface ProgressBarProps {
  current: number;
  total: number;
}

export function ProgressBar({ current, total }: ProgressBarProps) {
  const percent = Math.min(100, Math.round((current / total) * 100));
  return (
    <div className="flex flex-col gap-1 px-6 pt-3">
      <p className="text-xs text-muted-foreground">
        Section {current} of {total}
      </p>
      <div
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2 w-full overflow-hidden rounded bg-muted"
      >
        <div
          className="h-full bg-primary transition-all"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
