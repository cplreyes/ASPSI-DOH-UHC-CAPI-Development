import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { ZodTypeAny } from 'zod';
import type { Item, Section as SectionModel } from '@/types/survey';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import { cn } from '@/lib/utils';
import {
  sectionA,
  sectionB,
  sectionC,
  sectionD,
  sectionE,
  sectionF,
  sectionG,
  sectionH,
  sectionI,
  sectionJ,
} from '@/generated/items';
import {
  sectionASchema,
  sectionBSchema,
  sectionCSchema,
  sectionDSchema,
  sectionESchema,
  sectionFSchema,
  sectionGSchema,
  sectionHSchema,
  sectionISchema,
  sectionJSchema,
} from '@/generated/schema';
import { shouldShow, shouldShowSection, type FormValues } from '@/lib/skip-logic';
import { Section } from './Section';
import { ProgressBar } from './ProgressBar';
import { ReviewSection } from './ReviewSection';
import { SectionTree, type SectionStatus } from './SectionTree';

interface SectionConfig {
  id: string;
  section: SectionModel;
  schema: ZodTypeAny;
}

const SECTIONS: SectionConfig[] = [
  { id: 'A', section: sectionA, schema: sectionASchema },
  { id: 'B', section: sectionB, schema: sectionBSchema },
  { id: 'C', section: sectionC, schema: sectionCSchema },
  { id: 'D', section: sectionD, schema: sectionDSchema },
  { id: 'E', section: sectionE, schema: sectionESchema },
  { id: 'F', section: sectionF, schema: sectionFSchema },
  { id: 'G', section: sectionG, schema: sectionGSchema },
  { id: 'H', section: sectionH, schema: sectionHSchema },
  { id: 'I', section: sectionI, schema: sectionISchema },
  { id: 'J', section: sectionJ, schema: sectionJSchema },
];

const REVIEW_INDEX = SECTIONS.length;

function hasValue(v: unknown): boolean {
  return v !== undefined && v !== null && v !== '';
}

function getSectionStatus(section: SectionConfig, values: FormValues): SectionStatus {
  const items = section.section.items;

  const hasAnyData = items.some((it) => {
    if (it.type === 'multi-field' && it.subFields) {
      return it.subFields.some((sf) => hasValue(values[sf.id]));
    }
    return hasValue(values[it.id]);
  });

  if (!hasAnyData) return 'empty';

  const visibleItems = items.filter((it) => shouldShow(section.id, it.id, values));
  const allRequiredFilled = visibleItems.every((it) => {
    if (!it.required) return true;
    if (it.type === 'multi-field' && it.subFields) {
      // A subfield is required only if the parent is required AND its own required
      // flag isn't explicitly false. Optional subfields don't block completion.
      return it.subFields.every(
        (sf) => sf.required === false || hasValue(values[sf.id]),
      );
    }
    return hasValue(values[it.id]);
  });

  return allRequiredFilled ? 'complete' : 'incomplete';
}

interface MultiSectionFormProps {
  initialValues: FormValues;
  initialIndex?: number;
  onAutosave: (values: FormValues) => void;
  onSubmit: (values: FormValues) => void;
  onSaveDraft?: () => void;
}

export function MultiSectionForm({
  initialValues,
  initialIndex = 0,
  onAutosave,
  onSubmit,
  onSaveDraft,
}: MultiSectionFormProps) {
  const { t } = useTranslation();
  const { locale } = useLocale();
  const [merged, setMerged] = useState<FormValues>(initialValues);
  const [index, setIndex] = useState(initialIndex);
  const [maxVisitedIndex, setMaxVisitedIndex] = useState(initialIndex);
  const [showSaved, setShowSaved] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [animKey, setAnimKey] = useState(0);
  const [lockMsg, setLockMsg] = useState('');
  const submitRef = useRef<(() => void) | null>(null);
  const savedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lockTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const directionRef = useRef<'forward' | 'back'>('forward');
  const touchStartXRef = useRef(0);
  const touchStartYRef = useRef(0);
  // Tracks the section status when we arrived at the current section,
  // so auto-advance only fires on a non-complete → complete transition.
  const entryStatusRef = useRef<SectionStatus>(
    getSectionStatus(SECTIONS[initialIndex] ?? SECTIONS[0]!, initialValues),
  );

  const isReview = index === REVIEW_INDEX;
  const current = isReview ? null : SECTIONS[index]!;
  const isFirst = index === 0;
  const isLastSection = index === SECTIONS.length - 1;

  const sectionStatuses = useMemo<SectionStatus[]>(
    () => SECTIONS.map((s) => getSectionStatus(s, merged)),
    [merged],
  );

  const visibleSectionEntries = useMemo(
    () => SECTIONS.reduce<Array<{ config: SectionConfig; originalIndex: number }>>(
      (acc, s, i) => {
        if (shouldShowSection(s.id, merged)) acc.push({ config: s, originalIndex: i });
        return acc;
      },
      [],
    ),
    [merged],
  );

  const visibleIndex = visibleSectionEntries.findIndex((e) => e.originalIndex === index);

  const visibleItems: Item[] = useMemo(() => {
    if (!current) return [];
    return current.section.items.filter((it) => shouldShow(current.id, it.id, merged));
  }, [current, merged]);

  const sectionDefaults = useMemo(() => {
    if (!current) return {};
    const out: FormValues = {};
    for (const it of current.section.items) {
      if (it.type === 'multi-field' && it.subFields) {
        for (const sf of it.subFields) {
          if (sf.id in merged) out[sf.id] = merged[sf.id];
        }
        continue;
      }
      if (it.id in merged) {
        out[it.id] = merged[it.id];
      } else if (it.type === 'multi') {
        out[it.id] = [];
      }
      const otherKey = `${it.id}_other`;
      if (otherKey in merged) out[otherKey] = merged[otherKey];
    }
    return out;
  }, [current, merged]);

  // Reset entry status when navigating to a new section (must be before the auto-advance effect)
  useEffect(() => {
    entryStatusRef.current = sectionStatuses[index] ?? 'empty';
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  // Auto-advance when current section transitions from non-complete to complete
  useEffect(() => {
    if (isReview) return;
    const currentStatus = sectionStatuses[index];
    if (currentStatus !== 'complete') return;
    if (entryStatusRef.current === 'complete') return; // was already complete on arrival

    const timer = setTimeout(() => {
      handleNext();
    }, 400);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sectionStatuses]);

  const showLockMsg = () => {
    setLockMsg(t('navigator.sectionLocked'));
    if (lockTimerRef.current) clearTimeout(lockTimerRef.current);
    lockTimerRef.current = setTimeout(() => setLockMsg(''), 3000);
  };

  const handleSectionAutosave = (values: FormValues) => {
    setMerged((prev) => {
      const next = { ...prev, ...values };
      onAutosave(next);
      return next;
    });
  };

  const handleSectionValid = (values: FormValues) => {
    const next = { ...merged, ...values };
    setMerged(next);
    let nextIndex = index + 1;
    while (nextIndex < SECTIONS.length && !shouldShowSection(SECTIONS[nextIndex]!.id, next)) {
      nextIndex++;
    }
    setMaxVisitedIndex((prev) => Math.max(prev, nextIndex));
    directionRef.current = 'forward';
    setAnimKey((k) => k + 1);
    setIndex(nextIndex);
    window.scrollTo(0, 0);
  };

  const handlePrev = () => {
    if (isFirst) return;
    let prevIndex = index - 1;
    while (prevIndex > 0 && !shouldShowSection(SECTIONS[prevIndex]!.id, merged)) {
      prevIndex--;
    }
    directionRef.current = 'back';
    setAnimKey((k) => k + 1);
    setIndex(prevIndex);
    window.scrollTo(0, 0);
  };

  const handleNavigate = (targetIndex: number) => {
    if (targetIndex > maxVisitedIndex) {
      showLockMsg();
      return;
    }
    directionRef.current = targetIndex > index ? 'forward' : 'back';
    setAnimKey((k) => k + 1);
    setIndex(targetIndex);
    window.scrollTo(0, 0);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartXRef.current = e.touches[0].clientX;
    touchStartYRef.current = e.touches[0].clientY;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const dx = e.changedTouches[0].clientX - touchStartXRef.current;
    const dy = e.changedTouches[0].clientY - touchStartYRef.current;
    if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy)) return;
    if (dx < 0) handleNext();
    else handlePrev();
  };

  const handleSaveDraftClick = () => {
    onAutosave(merged);
    onSaveDraft?.();
    setShowSaved(true);
    if (savedTimerRef.current) clearTimeout(savedTimerRef.current);
    savedTimerRef.current = setTimeout(() => setShowSaved(false), 2000);
  };

  const handleNext = () => {
    submitRef.current?.();
  };

  const handleEdit = (sectionId: string) => {
    const target = SECTIONS.findIndex((s) => s.id === sectionId);
    if (target >= 0) setIndex(target);
  };

  const handleFinalSubmit = () => {
    onSubmit(merged);
  };

  if (isReview) {
    return <ReviewSection values={merged} onEdit={handleEdit} onSubmit={handleFinalSubmit} />;
  }

  return (
    <div className="flex flex-col lg:flex-row lg:items-start">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:w-56 lg:shrink-0 lg:border-r lg:sticky lg:top-0 lg:self-start lg:h-screen lg:overflow-y-auto">
        <SectionTree
          sections={visibleSectionEntries.map((e) => e.config)}
          currentIndex={visibleIndex}
          statuses={visibleSectionEntries.map((e) => sectionStatuses[e.originalIndex]!)}
          maxVisitedIndex={visibleSectionEntries.filter((e) => e.originalIndex <= maxVisitedIndex).length - 1}
          onNavigate={(i) => handleNavigate(visibleSectionEntries[i]!.originalIndex)}
        />
      </aside>

      {/* Mobile drawer */}
      {drawerOpen ? (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Section menu"
          onClick={() => setDrawerOpen(false)}
        >
          <div className="absolute inset-0 bg-black/50" />
          <aside
            className="absolute left-0 top-0 h-full w-64 overflow-y-auto border-r bg-background"
            onClick={(e) => e.stopPropagation()}
          >
            <SectionTree
              sections={visibleSectionEntries.map((e) => e.config)}
              currentIndex={visibleIndex}
              statuses={visibleSectionEntries.map((e) => sectionStatuses[e.originalIndex]!)}
              maxVisitedIndex={visibleSectionEntries.filter((e) => e.originalIndex <= maxVisitedIndex).length - 1}
              onNavigate={(i) => { handleNavigate(visibleSectionEntries[i]!.originalIndex); setDrawerOpen(false); }}
              onClose={() => setDrawerOpen(false)}
            />
          </aside>
        </div>
      ) : null}

      {/* Fixed side arrow — Previous */}
      <button
        type="button"
        aria-label="Previous section"
        onClick={handlePrev}
        className={cn(
          'fixed top-1/2 left-1 z-30 -translate-y-1/2 rounded-full border bg-background/90 p-2 shadow-md transition-colors hover:bg-muted lg:left-[232px]',
          isFirst && 'invisible',
        )}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      {/* Fixed side arrow — Next / Submit */}
      <button
        type="button"
        aria-label="Next section"
        onClick={handleNext}
        className={cn(
          'fixed top-1/2 right-1 z-30 -translate-y-1/2 rounded-full border p-2 shadow-md transition-colors',
          isLastSection
            ? 'bg-primary text-primary-foreground hover:bg-primary/90'
            : 'bg-background/90 hover:bg-muted',
        )}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Main content */}
      <div
        className="flex min-w-0 flex-1 flex-col"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {/* Sticky header */}
        <div className="sticky top-0 z-10 border-b bg-background">
          <div className="flex items-center gap-2 px-4 pt-3 pb-1">
            <button
              type="button"
              aria-label="Open section menu"
              className="shrink-0 rounded p-1 hover:bg-muted lg:hidden"
              onClick={() => setDrawerOpen(true)}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <ProgressBar current={visibleIndex + 1} total={visibleSectionEntries.length} className="flex-1 px-0 pt-0" />
            {/* Save Draft — upper right */}
            <button
              type="button"
              onClick={handleSaveDraftClick}
              className="shrink-0 rounded border px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted"
            >
              {showSaved ? (
                <span className="text-green-600">{t('navigator.draftSaved')}</span>
              ) : (
                t('navigator.saveDraft')
              )}
            </button>
          </div>

          {/* Lock notification strip */}
          {lockMsg ? (
            <div className="border-t border-amber-200 bg-amber-50 px-4 py-1.5 text-xs text-amber-700">
              {lockMsg}
            </div>
          ) : null}

          <div className="mx-auto max-w-xl px-6 pb-2">
            <h2 className="text-xl font-semibold tracking-tight">
              {t('review.sectionHeading', {
                id: current!.id,
                title: localized(current!.section.title, locale),
              })}
            </h2>
          </div>
        </div>

        <div
          key={animKey}
          className={cn(
            'animate-in duration-200',
            directionRef.current === 'forward' ? 'slide-in-from-right-4' : 'slide-in-from-left-4',
          )}
        >
          <Section<FormValues>
            key={current!.id}
            section={current!.section}
            schema={current!.schema}
            items={visibleItems}
            defaultValues={sectionDefaults}
            hideSubmit
            submitRef={submitRef}
            onAutosave={handleSectionAutosave}
            onSubmit={handleSectionValid}
          />
        </div>
      </div>
    </div>
  );
}
