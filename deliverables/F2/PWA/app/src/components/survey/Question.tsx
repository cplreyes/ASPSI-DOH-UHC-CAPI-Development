import { useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Locale } from '@/i18n/index';
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
  const showSpecify =
    (item.hasOtherSpecify &&
      item.choices?.some((c) => {
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
        {localized(item.label, locale)}
        {item.required ? <span className="ml-1 text-red-600">*</span> : null}
      </label>
      {item.help ? (
        <p className="text-xs text-muted-foreground">{localized(item.help, locale)}</p>
      ) : null}
      {renderControl(item, register, showSpecify, t, locale)}
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

function renderControl(
  item: Item,
  register: ReturnType<typeof useFormContext>['register'],
  showSpecify: boolean,
  t: ReturnType<typeof useTranslation>['t'],
  locale: Locale,
) {
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
          className="rounded border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'single':
      return (
        <div className="flex flex-col gap-1">
          <fieldset className="flex flex-col gap-1">
            {item.choices?.map((choice, idx) => (
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
            {item.choices?.map((choice, idx) => (
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
          {item.subFields?.map((sf) => (
            <div key={sf.id} className="flex flex-col gap-1">
              <label htmlFor={sf.id} className="text-xs text-muted-foreground">
                {localized(sf.label, locale)}
              </label>
              <input
                id={sf.id}
                type={sf.kind === 'number' ? 'number' : 'text'}
                className="rounded border border-input bg-background px-3 py-2"
                {...register(sf.id)}
              />
            </div>
          ))}
        </div>
      );
  }
}
