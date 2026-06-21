import { useEffect, useMemo, type MutableRefObject } from 'react';
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
import { evaluateCrossField } from '@/lib/cross-field';

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

  // R3 #298: the generated zod schema marks an item required whenever the
  // *spec* says so. Skip-logic (skip-logic.ts) hides items the spec can't
  // express as conditional — e.g. the Section E1 role gate hides Q48 for a
  // Pharmacist while schema.ts still has `Q48: z.enum([...])` (required).
  // Rendering and the status gate already key off the shouldShow-filtered
  // `items`; validation must too, or handleSubmit silently fails zod on a
  // field the respondent was never shown. Only suppress errors for items
  // NOT in the visible set — visible required items still validate.
  const visibleKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const it of items ?? section.items) {
      keys.add(it.id);
      keys.add(`${it.id}_other`);
      for (const sf of it.subFields ?? []) keys.add(sf.id);
    }
    return keys;
  }, [items, section.items]);

  const visibleItemList = items ?? section.items;

  const baseResolver = zodResolver(schema) as Resolver<T>;
  const resolver: Resolver<T> = async (values, context, options) => {
    const result = await baseResolver(stripNulls(values) as T, context, options);
    const errs = (result.errors ?? {}) as Record<string, unknown>;
    const hadErrors = Object.keys(errs).length > 0;

    // #587: error-severity cross-field findings (e.g. PROF-01 tenure ≥ age−20) are
    // in-survey hard blocks (Myra 2026-05-21), not just review-time warnings. When
    // THIS section owns every field a finding references, surface it as a form error
    // so advance is blocked here and the message renders inline — not only at review.
    const crossFieldErrors = (vals: unknown): Record<string, { type: string; message: string }> => {
      const out: Record<string, { type: string; message: string }> = {};
      for (const w of evaluateCrossField(vals as Parameters<typeof evaluateCrossField>[0])) {
        if (w.severity !== 'error') continue;
        if (!w.fields.every((f) => visibleKeys.has(f))) continue;
        const message = t(w.message.key, w.message.values as Record<string, unknown>);
        for (const f of w.fields) if (!out[f]) out[f] = { type: w.id, message };
      }
      return out;
    };

    if (!hadErrors) {
      const cf = crossFieldErrors(result.values);
      return (Object.keys(cf).length > 0 ? { values: {} as T, errors: cf } : result) as typeof result;
    }

    for (const key of Object.keys(errs)) {
      if (!visibleKeys.has(key)) delete errs[key];
    }
    if (Object.keys(errs).length > 0) return result;

    // Every remaining failure was a hidden field — zod zeroed `result.values`
    // because the whole-object parse failed. Rebuild the visible subset so
    // the form can advance with real data. zod's only coercion in the
    // generated schema is `z.coerce.number()`, so mirror just that; enums
    // (string), multi (array) and text already hold the correct runtime type.
    const stripped = stripNulls(values) as Record<string, unknown>;
    const out: Record<string, unknown> = {};
    for (const it of visibleItemList) {
      if (it.id in stripped) {
        out[it.id] = it.type === 'number' ? Number(stripped[it.id]) : stripped[it.id];
      }
      const other = `${it.id}_other`;
      if (other in stripped) out[other] = stripped[other];
      for (const sf of it.subFields ?? []) {
        if (sf.id in stripped) out[sf.id] = stripped[sf.id];
      }
    }
    const cf = crossFieldErrors(out);
    return (Object.keys(cf).length > 0
      ? { values: {} as T, errors: cf }
      : { values: out as T, errors: {} }) as typeof result;
  };

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
