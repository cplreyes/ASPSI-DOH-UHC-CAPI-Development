import { useMemo, useRef, useState } from 'react';
import type { ZodTypeAny } from 'zod';
import type { Item, Section as SectionModel } from '@/types/survey';
import { sectionA, sectionB, sectionC } from '@/generated/items';
import {
  sectionASchema,
  sectionBSchema,
  sectionCSchema,
} from '@/generated/schema';
import { shouldShow, type FormValues } from '@/lib/skip-logic';
import { Section } from './Section';
import { ProgressBar } from './ProgressBar';
import { Navigator } from './Navigator';

interface SectionConfig {
  id: string;
  section: SectionModel;
  schema: ZodTypeAny;
}

const SECTIONS: SectionConfig[] = [
  { id: 'A', section: sectionA, schema: sectionASchema },
  { id: 'B', section: sectionB, schema: sectionBSchema },
  { id: 'C', section: sectionC, schema: sectionCSchema },
];

interface MultiSectionFormProps {
  initialValues: FormValues;
  onAutosave: (values: FormValues) => void;
  onSubmit: (values: FormValues) => void;
}

export function MultiSectionForm({
  initialValues,
  onAutosave,
  onSubmit,
}: MultiSectionFormProps) {
  const [merged, setMerged] = useState<FormValues>(initialValues);
  const [index, setIndex] = useState(0);
  const submitRef = useRef<(() => void) | null>(null);

  const current = SECTIONS[index]!;
  const isFirst = index === 0;
  const isLast = index === SECTIONS.length - 1;

  const visibleItems: Item[] = useMemo(
    () =>
      current.section.items.filter((it) =>
        shouldShow(current.id, it.id, merged),
      ),
    [current, merged],
  );

  const sectionDefaults = useMemo(() => {
    const out: FormValues = {};
    for (const it of current.section.items) {
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
    if (isLast) {
      onSubmit(next);
    } else {
      setIndex(index + 1);
    }
  };

  const handlePrev = () => {
    if (isFirst) return;
    setIndex(index - 1);
  };

  const handleNext = () => {
    submitRef.current?.();
  };

  const handleSubmitClick = () => {
    submitRef.current?.();
  };

  return (
    <div className="flex flex-col">
      <ProgressBar current={index + 1} total={SECTIONS.length} />
      <Section<FormValues>
        key={current.id}
        section={current.section}
        schema={current.schema}
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
          isLast={isLast}
          onPrev={handlePrev}
          onNext={handleNext}
          onSubmit={handleSubmitClick}
        />
      </div>
    </div>
  );
}
