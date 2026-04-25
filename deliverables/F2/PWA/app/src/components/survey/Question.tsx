import { useFormContext, type FieldErrors } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Locale } from '@/i18n/index';
import { filterChoices } from '@/lib/skip-logic';
import type { Item } from '@/types/survey';

interface QuestionProps {
  item: Item;
}

export function Question({ item }: QuestionProps) {
  const { t } = useTranslation();
  const { locale } = useLocale();
  const {
    register,
    watch,
    formState: { errors },
  } = useFormContext();
  const currentValue = watch(item.id);
  const allValues = watch();
  const visibleChoices = item.choices
    ? filterChoices(item.section, item.id, allValues, item.choices)
    : undefined;
  const showSpecify =
    (item.hasOtherSpecify &&
      visibleChoices?.some((c) => {
        if (!c.isOtherSpecify) return false;
        if (Array.isArray(currentValue)) return currentValue.includes(c.value);
        return c.value === currentValue;
      })) ??
    false;
  const error = errors[item.id];
  const errorMessage = typeof error?.message === 'string' ? error.message : undefined;

  return (
    <div className="flex flex-col gap-2 py-3">
      <label htmlFor={item.id} className="text-sm font-medium">
        <span className="mr-1 text-muted-foreground">{item.id}.</span>
        {localized(item.label, locale)}
        {item.required ? <span className="ml-1 text-red-600">*</span> : null}
      </label>
      {item.help ? (
        <p className="text-xs text-muted-foreground">{localized(item.help, locale)}</p>
      ) : null}
      {renderControl(item, register, showSpecify, t, locale, errors, visibleChoices)}
      {errorMessage ? (
        <p role="alert" className="text-xs text-red-600">
          {errorMessage}
        </p>
      ) : error ? (
        <p role="alert" className="text-xs text-red-600">
          {t('question.requiredFallback')}
        </p>
      ) : null}
    </div>
  );
}

// Block characters HTML5 number inputs accept but we don't want for survey integers
// (e.g. age, months, days): scientific notation `e`/`E`, sign `+`/`-`, decimal `.`.
// Survey items expect non-negative integers; min/max are enforced separately by Zod.
function blockNonNumericKeys(event: React.KeyboardEvent<HTMLInputElement>) {
  if (['e', 'E', '+', '-', '.'].includes(event.key)) {
    event.preventDefault();
  }
}

function renderControl(
  item: Item,
  register: ReturnType<typeof useFormContext>['register'],
  showSpecify: boolean,
  t: ReturnType<typeof useTranslation>['t'],
  locale: Locale,
  errors: FieldErrors,
  visibleChoices?: Item['choices'],
) {
  // Use filtered choices if provided (e.g., A.Q6 specialty narrowed by Q5 role).
  const choices = visibleChoices ?? item.choices;
  switch (item.type) {
    case 'short-text':
      return (
        <input
          id={item.id}
          type="text"
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'long-text':
      return (
        <textarea
          id={item.id}
          rows={4}
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'number':
      return (
        <input
          id={item.id}
          type="number"
          min={item.min}
          max={item.max}
          inputMode="numeric"
          onKeyDown={blockNonNumericKeys}
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'single':
      return (
        <div className="flex flex-col gap-1">
          <fieldset className="flex flex-col gap-1">
            {choices?.map((choice, idx) => (
              <label key={choice.value} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  value={choice.value}
                  {...(idx === 0 ? { id: item.id } : {})}
                  {...register(item.id)}
                />
                {localized(choice.label, locale)}
              </label>
            ))}
          </fieldset>
          {showSpecify ? (
            <div className="mt-2 flex flex-col gap-1 pl-6">
              <label htmlFor={`${item.id}_other`} className="text-xs text-muted-foreground">
                {t('question.pleaseSpecifyLabel')}
              </label>
              <input
                id={`${item.id}_other`}
                type="text"
                className="rounded border border-input bg-background px-3 py-2"
                {...register(`${item.id}_other`)}
              />
            </div>
          ) : null}
        </div>
      );
    case 'multi':
      return (
        <div className="flex flex-col gap-1">
          <fieldset className="flex flex-col gap-1">
            {choices?.map((choice, idx) => (
              <label key={choice.value} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  value={choice.value}
                  {...(idx === 0 ? { id: item.id } : {})}
                  {...register(item.id)}
                />
                {localized(choice.label, locale)}
              </label>
            ))}
          </fieldset>
          {showSpecify ? (
            <div className="mt-2 flex flex-col gap-1 pl-6">
              <label htmlFor={`${item.id}_other`} className="text-xs text-muted-foreground">
                {t('question.pleaseSpecifyLabel')}
              </label>
              <input
                id={`${item.id}_other`}
                type="text"
                className="rounded border border-input bg-background px-3 py-2"
                {...register(`${item.id}_other`)}
              />
            </div>
          ) : null}
        </div>
      );
    case 'date':
      return (
        <input
          id={item.id}
          type="date"
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'multi-field':
      return (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {item.subFields?.map((sf) => {
            const sfError = errors[sf.id];
            const sfErrorMessage =
              typeof sfError?.message === 'string' ? sfError.message : undefined;
            return (
              <div key={sf.id} className="flex flex-col gap-1">
                <label htmlFor={sf.id} className="text-xs text-muted-foreground">
                  {localized(sf.label, locale)}
                </label>
                <input
                  id={sf.id}
                  type={sf.kind === 'number' ? 'number' : 'text'}
                  min={sf.min}
                  max={sf.max}
                  {...(sf.kind === 'number'
                    ? { inputMode: 'numeric', onKeyDown: blockNonNumericKeys }
                    : {})}
                  className="rounded border border-input bg-background px-3 py-2"
                  {...register(sf.id)}
                />
                {sfErrorMessage ? (
                  <p role="alert" className="text-xs text-red-600">
                    {sfErrorMessage}
                  </p>
                ) : sfError ? (
                  <p role="alert" className="text-xs text-red-600">
                    {t('question.requiredFallback')}
                  </p>
                ) : null}
              </div>
            );
          })}
        </div>
      );
  }
}
