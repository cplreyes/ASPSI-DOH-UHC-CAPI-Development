import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Section as SectionModel } from '@/types/survey';
import { cn } from '@/lib/utils';

export interface SectionEntry {
  id: string;
  section: SectionModel;
}

export type SectionStatus = 'complete' | 'incomplete' | 'empty';

interface SectionTreeProps {
  sections: SectionEntry[];
  currentIndex: number;
  statuses: SectionStatus[];
  maxVisitedIndex: number;
  onNavigate: (index: number) => void;
  onClose?: () => void;
}

export function SectionTree({
  sections,
  currentIndex,
  statuses,
  maxVisitedIndex,
  onNavigate,
  onClose,
}: SectionTreeProps) {
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
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        ) : null}
      </div>

      <nav aria-label="Survey sections" className="flex flex-col py-1">
        {sections.map((s, i) => {
          const isCurrent = i === currentIndex;
          const isLocked = i > maxVisitedIndex;
          const status = statuses[i] ?? 'empty';

          return (
            <button
              key={s.id}
              type="button"
              aria-current={isCurrent ? 'step' : undefined}
              aria-disabled={isLocked || undefined}
              aria-describedby={isLocked ? `${s.id}-locked-reason` : undefined}
              onClick={() => onNavigate(i)}
              className={cn(
                'flex w-full items-start gap-3 px-4 py-2 text-left text-sm transition-colors hover:bg-muted',
                isCurrent && 'bg-primary/10 font-medium text-primary',
                isLocked && 'opacity-50 cursor-not-allowed hover:bg-transparent',
              )}
            >
              {isLocked ? (
                <span id={`${s.id}-locked-reason`} className="sr-only">
                  Section locked. Complete earlier sections to unlock.
                </span>
              ) : null}
              {/* Status / lock badge */}
              <span
                className={cn(
                  'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold',
                  isCurrent && 'bg-primary text-primary-foreground',
                  !isCurrent && isLocked && 'bg-muted text-muted-foreground',
                  !isCurrent && !isLocked && status === 'complete' && 'bg-primary/10 text-primary',
                  !isCurrent &&
                    !isLocked &&
                    status === 'incomplete' &&
                    'bg-destructive/10 text-destructive',
                  !isCurrent && !isLocked && status === 'empty' && 'bg-muted text-muted-foreground',
                )}
              >
                {isCurrent ? (
                  s.id
                ) : isLocked ? (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="9"
                    height="9"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
                    />
                  </svg>
                ) : status === 'complete' ? (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="10"
                    height="10"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={3}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : status === 'incomplete' ? (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="10"
                    height="10"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={3}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  s.id
                )}
              </span>

              {/* Section title */}
              <span
                className={cn(
                  'leading-snug',
                  isCurrent
                    ? 'text-primary'
                    : isLocked
                      ? 'text-muted-foreground'
                      : 'text-foreground',
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
