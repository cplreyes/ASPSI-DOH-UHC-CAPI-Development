import { useMemo, useRef, useState } from 'react';
import type { ZodTypeAny } from 'zod';
import type { Item, Section as SectionModel } from '@/types/survey';
import {
  sectionA,
  sectionB,
  sectionC,
  sectionD,
  sectionE1,
  sectionE2,
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
  sectionE1Schema,
  sectionE2Schema,
  sectionFSchema,
  sectionGSchema,
  sectionHSchema,
  sectionISchema,
  sectionJSchema,
} from '@/generated/schema';
import { shouldShow, type FormValues } from '@/lib/skip-logic';
import { Section } from './Section';
import { ProgressBar } from './ProgressBar';
import { Navigator } from './Navigator';
import { ReviewSection } from './ReviewSection';

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
  { id: 'E1', section: sectionE1, schema: sectionE1Schema },
  { id: 'E2', section: sectionE2, schema: sectionE2Schema },
  { id: 'F', section: sectionF, schema: sectionFSchema },
  { id: 'G', section: sectionG, schema: sectionGSchema },
  { id: 'H', section: sectionH, schema: sectionHSchema },
  { id: 'I', section: sectionI, schema: sectionISchema },
  { id: 'J', section: sectionJ, schema: sectionJSchema },
];

const REVIEW_INDEX = SECTIONS.length;

interface MultiSectionFormProps {
  initialValues: FormValues;
  initialIndex?: number;
  onAutosave: (values: FormValues) => void;
  onSubmit: (values: FormValues) => void;
}

export function MultiSectionForm({
  initialValues,
  initialIndex = 0,
  onAutosave,
  onSubmit,
}: MultiSectionFormProps) {
  const [merged, setMerged] = useState<FormValues>(initialValues);
  const [index, setIndex] = useState(initialIndex);
  const submitRef = useRef<(() => void) | null>(null);

  const isReview = index === REVIEW_INDEX;
  const current = isReview ? null : SECTIONS[index]!;
  const isFirst = index === 0;
  const isLastSection = index === SECTIONS.length - 1;

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
      if (it.id in merged) out[it.id] = merged[it.id];
      const otherKey = `${it.id}_other`;
      if (otherKey in merged) out[otherKey] = merged[otherKey];
    }
    return out;
  }, [current, merged]);

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
    setIndex(index + 1);
  };

  const handlePrev = () => {
    if (isFirst) return;
    setIndex(index - 1);
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
    <div className="flex flex-col">
      <ProgressBar current={index + 1} total={SECTIONS.length} />
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
      <div className="mx-auto w-full max-w-xl px-6 pb-6">
        <Navigator
          isFirst={isFirst}
          isLast={isLastSection}
          onPrev={handlePrev}
          onNext={handleNext}
          onSubmit={handleNext}
        />
      </div>
    </div>
  );
}
