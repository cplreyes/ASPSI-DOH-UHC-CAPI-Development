import type * as React from 'react';
import { useFormContext, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Choice, Item } from '@/types/survey';

interface MatrixQuestionProps {
  items: Item[];
  choices: Choice[];
}

export function MatrixQuestion({ items, choices }: MatrixQuestionProps) {
  const { t } = useTranslation();
  const { locale } = useLocale();
  const {
    register,
    setValue,
    formState: { errors },
  } = useFormContext();
  // R3 #314: controlled radios via setValue + useWatch, with a single
  // register call per item issued through a hidden input below. The dual-DOM
  // responsive layout (desktop <table> + mobile <div> cards) previously
  // called register(item.id) on EVERY visible radio in both copies — RHF
  // kept only the last ref, so defaultValues prefill applied only to the
  // mobile copy, leaving the desktop view blank on Edit-from-Review. Now
  // each item registers exactly once (on the hidden input), and both visible
  // copies render as controlled inputs that read form state via useWatch.
  const watchedValues = useWatch({ name: items.map((i) => i.id) }) as
    | (string | undefined)[]
    | undefined;

  return (
    <div className="flex flex-col gap-2 py-3">
      {/* Hidden registrations — exactly one ref per item.id, so RHF picks up
          defaultValues for matrix fields. Visible radios below are controlled. */}
      {items.map((item) => (
        <input key={`reg-${item.id}`} type="hidden" {...register(item.id)} />
      ))}

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
          {items.flatMap((item, itemIdx) => {
            const error = errors[item.id];
            const errorMessage = typeof error?.message === 'string' ? error.message : undefined;
            const currentValue = (watchedValues ?? [])[itemIdx];
            const out: React.ReactElement[] = [
              <tr key={item.id} className="border-b">
                <th scope="row" className="py-2 pr-2 text-left text-sm font-normal">
                  <span className="mr-1 text-muted-foreground">{item.displayNumber ?? item.id}.</span>
                  {localized(item.label, locale)}
                  {item.required ? <span className="ml-1 text-destructive">*</span> : null}
                </th>
                {choices.map((c) => (
                  <td key={c.value} className="py-2 px-1 text-center">
                    <input
                      type="radio"
                      value={c.value}
                      aria-label={`${item.displayNumber ?? item.id} ${localized(c.label, locale)}`}
                      checked={currentValue === c.value}
                      onChange={() =>
                        setValue(item.id, c.value, {
                          shouldValidate: true,
                          shouldDirty: true,
                        })
                      }
                    />
                  </td>
                ))}
              </tr>,
            ];
            if (errorMessage || error) {
              out.push(
                <tr key={`${item.id}-err`}>
                  <td
                    colSpan={choices.length + 1}
                    className="py-1 text-xs text-destructive"
                    role="alert"
                  >
                    {errorMessage ?? t('question.requiredFallback')}
                  </td>
                </tr>,
              );
            }
            return out;
          })}
        </tbody>
      </table>

      {/* Mobile (below md): stacked card per row */}
      <div className="flex flex-col gap-3 md:hidden">
        {items.map((item, itemIdx) => {
          const error = errors[item.id];
          const errorMessage = typeof error?.message === 'string' ? error.message : undefined;
          const groupId = `${item.id}-statement`;
          const currentValue = (watchedValues ?? [])[itemIdx];
          return (
            <div key={item.id} className="flex flex-col gap-2 border-t pt-3">
              <p id={groupId} className="text-sm font-medium">
                <span className="mr-1 text-muted-foreground">{item.displayNumber ?? item.id}.</span>
                {localized(item.label, locale)}
                {item.required ? <span className="ml-1 text-destructive">*</span> : null}
              </p>
              <div role="radiogroup" aria-labelledby={groupId} className="flex flex-wrap gap-3">
                {choices.map((c) => (
                  <label key={c.value} className="flex items-center gap-1 text-sm">
                    <input
                      type="radio"
                      value={c.value}
                      aria-label={`${item.displayNumber ?? item.id} ${localized(c.label, locale)}`}
                      checked={currentValue === c.value}
                      onChange={() =>
                        setValue(item.id, c.value, {
                          shouldValidate: true,
                          shouldDirty: true,
                        })
                      }
                    />
                    {localized(c.label, locale)}
                  </label>
                ))}
              </div>
              {errorMessage || error ? (
                <p role="alert" className="text-xs text-destructive">
                  {errorMessage ?? t('question.requiredFallback')}
                </p>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
