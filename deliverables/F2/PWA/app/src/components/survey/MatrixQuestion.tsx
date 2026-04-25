import type * as React from 'react';
import { useFormContext } from 'react-hook-form';
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
    setValue,
    formState: { errors },
  } = useFormContext();

  return (
    <div className="flex flex-col gap-2 py-3">
      {/* Desktop / tablet: a real <table>. Hidden on phones via md:table. */}
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
          {items.flatMap((item) => {
            const error = errors[item.id];
            const errorMessage = typeof error?.message === 'string' ? error.message : undefined;
            const out: React.ReactElement[] = [
              <tr key={item.id} className="border-b">
                <th scope="row" className="py-2 pr-2 text-left text-sm font-normal">
                  <span className="mr-1 text-muted-foreground">{item.id}.</span>
                  {localized(item.label, locale)}
                  {item.required ? <span className="ml-1 text-red-600">*</span> : null}
                </th>
                {choices.map((c) => (
                  <td key={c.value} className="py-2 px-1 text-center">
                    <input
                      type="radio"
                      name={item.id}
                      value={c.value}
                      aria-label={`${item.id} ${localized(c.label, locale)}`}
                      onChange={(e) => {
                        setValue(item.id, e.target.value, {
                          shouldValidate: true,
                          shouldDirty: true,
                        });
                      }}
                    />
                  </td>
                ))}
              </tr>,
            ];
            if (errorMessage || error) {
              out.push(
                <tr key={`${item.id}-err`}>
                  <td colSpan={choices.length + 1} className="py-1 text-xs text-red-600" role="alert">
                    {errorMessage ?? t('question.requiredFallback')}
                  </td>
                </tr>,
              );
            }
            return out;
          })}
        </tbody>
      </table>
    </div>
  );
}
