import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Section as SectionModel } from '@/types/survey';
import { cn } from '@/lib/utils';

export interface SectionEntry {
  id: string;
  section: SectionModel;
}

interface SectionTreeProps {
  sections: SectionEntry[];
  currentIndex: number;
  onNavigate: (index: number) => void;
  onClose?: () => void;
}

export function SectionTree({ sections, currentIndex, onNavigate, onClose }: SectionTreeProps) {
  const { locale } = useLocale();

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <span className="text-sm font-semibold tracking-tight">Sections</span>
        {onClose ? (
          <button
            type="button"
            aria-label="Close menu"
            className="rounded p-1 hover:bg-muted"
            onClick={onClose}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        ) : null}
      </div>

      <nav aria-label="Survey sections" className="flex flex-col py-1">
        {sections.map((s, i) => {
          const isCompleted = i < currentIndex;
          const isCurrent = i === currentIndex;

          return (
            <button
              key={s.id}
              type="button"
              aria-current={isCurrent ? 'step' : undefined}
              onClick={() => onNavigate(i)}
              className={cn(
                'flex w-full items-start gap-3 px-4 py-2 text-left text-sm transition-colors hover:bg-muted',
                isCurrent && 'bg-primary/10 font-medium text-primary',
              )}
            >
              <span
                className={cn(
                  'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold',
                  isCurrent && 'bg-primary text-primary-foreground',
                  isCompleted && 'bg-green-100 text-green-700',
                  !isCurrent && !isCompleted && 'bg-muted text-muted-foreground',
                )}
              >
                {isCompleted ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  s.id
                )}
              </span>
              <span
                className={cn(
                  'leading-snug',
                  isCurrent ? 'text-primary' : isCompleted ? 'text-muted-foreground' : 'text-foreground',
                )}
              >
                {localized(s.section.title, locale)}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
