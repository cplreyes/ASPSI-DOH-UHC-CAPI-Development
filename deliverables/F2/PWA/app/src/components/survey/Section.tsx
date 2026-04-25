import { useEffect, type MutableRefObject } from 'react';
import { FormProvider, useForm, type DefaultValues, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslation } from 'react-i18next';
import type { ZodTypeAny } from 'zod';
import type { Item, Section as SectionModel } from '@/types/survey';
import { Button } from '@/components/ui/button';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import { Question } from './Question';
import { MatrixQuestion } from './MatrixQuestion';
import { groupVisibleItems, isMatrixGroup } from './group-matrix';

function stripNulls(values: unknown): unknown {
  if (values === null || values === '') return undefined;
  if (Array.isArray(values)) return values.map(stripNulls);
  if (values && typeof values === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(values as Record<string, unknown>)) {
      if (v === null) continue;
      out[k] = stripNulls(v);
    }
    return out;
  }
  return values;
}

interface SectionProps<T extends Record<string, unknown>> {
  section: SectionModel;
  schema: ZodTypeAny;
  items?: Item[];
  defaultValues?: DefaultValues<T>;
  hideSubmit?: boolean;
  submitRef?: MutableRefObject<(() => void) | null>;
  onAutosave?: (values: Partial<T>) => void;
  onSubmit: (values: T) => void;
}

export function Section<T extends Record<string, unknown>>({
  section,
  schema,
  items,
  defaultValues,
  hideSubmit,
  submitRef,
  onAutosave,
  onSubmit,
}: SectionProps<T>) {
  const { t } = useTranslation();
  const { locale } = useLocale();

  const baseResolver = zodResolver(schema) as Resolver<T>;
  const resolver: Resolver<T> = async (values, context, options) =>
    baseResolver(stripNulls(values) as T, context, options);

  const methods = useForm<T>({
    resolver,
    mode: 'onChange',
    ...(defaultValues ? { defaultValues } : {}),
  });

  useEffect(() => {
    if (!onAutosave) return;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const sub = methods.watch((values) => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => onAutosave(values as Partial<T>), 500);
    });
    return () => {
      sub.unsubscribe();
      if (timer) clearTimeout(timer);
    };
  }, [methods, onAutosave]);

  const submit = methods.handleSubmit((values) => onSubmit(values as unknown as T));

  useEffect(() => {
    if (!submitRef) return;
    submitRef.current = () => {
      void submit();
    };
    return () => {
      submitRef.current = null;
    };
  }, [submitRef, submit]);

  return (
    <FormProvider {...methods}>
      <form onSubmit={submit} className="mx-auto flex max-w-xl flex-col gap-4 p-6" noValidate>
        {section.preamble ? (
          <p className="text-sm text-muted-foreground">{localized(section.preamble, locale)}</p>
        ) : null}

        {groupVisibleItems(items ?? section.items).map((entry) =>
          isMatrixGroup(entry) ? (
            <MatrixQuestion
              key={`matrix-${entry.items[0].id}`}
              items={entry.items}
              choices={entry.choices}
            />
          ) : (
            <Question key={entry.id} item={entry} />
          ),
        )}

        {!hideSubmit ? (
          <div className="pt-4">
            <Button type="submit">{t('navigator.submit')}</Button>
          </div>
        ) : null}
      </form>
    </FormProvider>
  );
}
