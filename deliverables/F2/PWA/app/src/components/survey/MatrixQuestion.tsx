import type * as React from 'react';
import { useController, useFormContext, type Control, type FieldValues } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import type { TFunction } from 'i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Choice, Item } from '@/types/survey';
import type { Locale } from '@/i18n/locale-context';

interface MatrixQuestionProps {
  items: Item[];
  choices: Choice[];
}

// #314: MatrixQuestion renders every radio TWICE (desktop <table> + mobile
// cards). When both copies used uncontrolled `{...register(item.id)}`, RHF
// got duplicate refs for one radio-group name and applied `defaultValues`
// to only ONE copy — the desktop table (what tablet/desktop users see)
// rendered blank on the Edit-from-review remount.
//
// Fix: bind each row through `useController`. Controller is RHF's official
// controlled binding — `field.value` deterministically reflects
// `defaultValues` (no uncontrolled-ref ambiguity, none of the
// `useWatch`-pre-registration timing issues under Section's
// resolver+onChange useForm config). Two controllers for the same name
// (one per layout) is supported by RHF and is the idiomatic way to render
// one field in two places; both read the same field state, so both layout
// copies — and the rehydrated state — are deterministic.

function useRowField(name: string, control: Control<FieldValues>) {
  const { field, fieldState } = useController({ name, control });
  return {
    value: field.value as string | undefined,
    onChange: (v: string) => field.onChange(v),
    error: fieldState.error?.message,
    hasError: fieldState.error != null,
  };
}

function DesktopRow({
  item,
  choices,
  control,
  locale,
  t,
}: {
  item: Item;
  choices: Choice[];
  control: Control<FieldValues>;
  locale: Locale;
  t: TFunction;
}): React.ReactElement {
  const { value, onChange, error, hasError } = useRowField(item.id, control);
  return (
    <>
      <tr className="border-b">
        <th scope="row" className="py-2 pr-2 text-left text-sm font-normal">
          <span className="mr-1 text-muted-foreground">{item.id}.</span>
          {localized(item.label, locale)}
          {item.required ? <span className="ml-1 text-destructive">*</span> : null}
        </th>
        {choices.map((c) => (
          <td key={c.value} className="py-2 px-1 text-center">
            <input
              type="radio"
              name={item.id}
              value={c.value}
              aria-label={`${item.id} ${localized(c.label, locale)}`}
              checked={value === c.value}
              onChange={() => onChange(c.value)}
            />
          </td>
        ))}
      </tr>
      {hasError ? (
        <tr>
          <td colSpan={choices.length + 1} className="py-1 text-xs text-destructive" role="alert">
            {error ?? t('question.requiredFallback')}
          </td>
        </tr>
      ) : null}
    </>
  );
}

function MobileRow({
  item,
  choices,
  control,
  locale,
  t,
}: {
  item: Item;
  choices: Choice[];
  control: Control<FieldValues>;
  locale: Locale;
  t: TFunction;
}): React.ReactElement {
  const { value, onChange, error, hasError } = useRowField(item.id, control);
  const groupId = `${item.id}-statement`;
  return (
    <div className="flex flex-col gap-2 border-t pt-3">
      <p id={groupId} className="text-sm font-medium">
        <span className="mr-1 text-muted-foreground">{item.id}.</span>
        {localized(item.label, locale)}
        {item.required ? <span className="ml-1 text-destructive">*</span> : null}
      </p>
      <div role="radiogroup" aria-labelledby={groupId} className="flex flex-wrap gap-3">
        {choices.map((c) => (
          <label key={c.value} className="flex items-center gap-1 text-sm">
            <input
              type="radio"
              name={item.id}
              value={c.value}
              aria-label={`${item.id} ${localized(c.label, locale)}`}
              checked={value === c.value}
              onChange={() => onChange(c.value)}
            />
            {localized(c.label, locale)}
          </label>
        ))}
      </div>
      {hasError ? (
        <p role="alert" className="text-xs text-destructive">
          {error ?? t('question.requiredFallback')}
        </p>
      ) : null}
    </div>
  );
}

export function MatrixQuestion({ items, choices }: MatrixQuestionProps) {
  const { t } = useTranslation();
  const { locale } = useLocale();
  const { control } = useFormContext();

  return (
    <div className="flex flex-col gap-2 py-3">
      {/* Desktop / tablet (md and up): real <table> */}
      <table className="hidden w-full border-collapse text-sm md:table">
        <thead>
          <tr className="border-b">
            <th scope="col" className="py-2 pr-2 text-left font-medium">
              {t('matrix.statementHeader')}
            </th>
            {choices.map((c) => (
              <th key={c.value} scope="col" className="py-2 px-1 text-center font-medium">
                {localized(c.label, locale)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <DesktopRow
              key={item.id}
              item={item}
              choices={choices}
              control={control}
              locale={locale}
              t={t}
            />
          ))}
        </tbody>
      </table>

      {/* Mobile (below md): stacked card per row */}
      <div className="flex flex-col gap-3 md:hidden">
        {items.map((item) => (
          <MobileRow
            key={item.id}
            item={item}
            choices={choices}
            control={control}
            locale={locale}
            t={t}
          />
        ))}
      </div>
    </div>
  );
}
