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
    setValue,
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
    <div className="grid grid-cols-1 gap-y-2 py-3 sm:grid-cols-[80px_1fr]">
      <span
        aria-hidden="true"
        className="font-mono text-sm text-muted-foreground sm:pt-1 sm:pr-4 sm:text-right sm:text-base sm:leading-snug"
      >
        {item.id}
      </span>
      <div className="flex min-w-0 flex-col gap-2">
        <label htmlFor={item.id} className="text-base font-medium leading-snug">
          <span className="sr-only">
            {item.id}
            {'. '}
          </span>
          {localized(item.label, locale)}
          {item.required ? <span className="ml-1 text-destructive">*</span> : null}
        </label>
        {item.help ? (
          <p className="text-xs text-muted-foreground">{localized(item.help, locale)}</p>
        ) : null}
        {renderControl(
          item,
          register,
          showSpecify,
          t,
          locale,
          errors,
          visibleChoices,
          currentValue,
          (next) => setValue(item.id, next, { shouldValidate: true, shouldDirty: true }),
        )}
        {errorMessage ? (
          <p role="alert" className="text-xs text-destructive">
            {errorMessage}
          </p>
        ) : error ? (
          <p role="alert" className="text-xs text-destructive">
            {t('question.requiredFallback')}
          </p>
        ) : null}
      </div>
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

// Compute the next selected-values array for a multi-select after the user
// clicks a checkbox. Encodes the exclusivity rules from issues #16 and #17.
//
// - Clicking an `isExclusive` option (e.g. "I don't know") clears all others.
// - Clicking an `isSelectAll` option (e.g. "All of the above") auto-selects
//   every non-exclusive non-otherSpecify choice.
// - Clicking a regular option clears any currently-selected exclusive or
//   selectAll values (mixed selection isn't compatible).
// - Unchecking `isSelectAll` clears the auto-selected values.
// - Unchecking a regular option also clears `isSelectAll` (the "all" claim
//   is no longer accurate).
export function nextMultiValue(
  current: string[],
  clicked: {
    value: string;
    isExclusive?: boolean;
    isSelectAll?: boolean;
    isOtherSpecify?: boolean;
  },
  willBeChecked: boolean,
  allChoices: ReadonlyArray<{
    value: string;
    isExclusive?: boolean;
    isSelectAll?: boolean;
    isOtherSpecify?: boolean;
  }>,
): string[] {
  const findChoice = (v: string) => allChoices.find((c) => c.value === v);

  if (willBeChecked) {
    if (clicked.isExclusive) return [clicked.value];
    if (clicked.isSelectAll) {
      return allChoices.filter((c) => !c.isExclusive && !c.isOtherSpecify).map((c) => c.value);
    }
    const filtered = current.filter((v) => {
      const c = findChoice(v);
      return c ? !c.isExclusive && !c.isSelectAll : true;
    });
    return filtered.includes(clicked.value) ? filtered : [...filtered, clicked.value];
  }

  // Unchecking
  if (clicked.isSelectAll) {
    return current.filter((v) => {
      const c = findChoice(v);
      return c?.isOtherSpecify || c?.isExclusive;
    });
  }
  const next = current.filter((v) => v !== clicked.value);
  return next.filter((v) => {
    const c = findChoice(v);
    return c ? !c.isSelectAll : true;
  });
}

function renderControl(
  item: Item,
  register: ReturnType<typeof useFormContext>['register'],
  showSpecify: boolean,
  t: ReturnType<typeof useTranslation>['t'],
  locale: Locale,
  errors: FieldErrors,
  visibleChoices?: Item['choices'],
  currentValue?: unknown,
  onChange?: (next: string[]) => void,
) {
  // Use filtered choices if provided (e.g., A.Q6 specialty narrowed by Q5 role).
  const choices = visibleChoices ?? item.choices;
  switch (item.type) {
    case 'short-text':
      return (
        <input
          id={item.id}
          type="text"
          className="rounded-md border border-input bg-background px-3 py-2"
          {...register(item.id)}
        />
      );
    case 'long-text':
      return (
        <textarea
          id={item.id}
          rows={4}
          className="rounded-md border border-input bg-background px-3 py-2"
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
          className="rounded-md border border-input bg-background px-3 py-2"
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
                className="rounded-md border border-input bg-background px-3 py-2"
                {...register(`${item.id}_other`)}
              />
            </div>
          ) : null}
        </div>
      );
    case 'multi': {
      // Fully controlled checkboxes. Exclusivity ("I don't know") and
      // select-all ("All of the above") rules are computed in nextMultiValue().
      //
      // Issue #33: do NOT attach RHF's `name`/`ref` (from register()) to
      // these checkbox inputs. When several inputs share a single `name`,
      // RHF treats them as a checkbox group and re-derives the field value
      // from the DOM during its internal updateValid pass — which fires on
      // *any* other field's change. That re-derivation clobbers the array
      // we set via setValue() back to `false`/`[]`, wiping previous
      // selections when the user answers a different question in the same
      // section. We register the field (so dirty/validation state is
      // tracked) but bind the ref to a focus-only sentinel (the first
      // checkbox carries `id={item.id}` so the question's <label> still
      // focuses it on click).
      const selected: string[] = Array.isArray(currentValue) ? (currentValue as string[]) : [];
      const allChoices = choices ?? [];
      const reg = register(item.id);
      return (
        <div className="flex flex-col gap-1">
          <fieldset className="flex flex-col gap-1">
            {allChoices.map((choice, idx) => {
              const isChecked = selected.includes(choice.value);
              return (
                <label key={choice.value} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    value={choice.value}
                    checked={isChecked}
                    onChange={(e) => {
                      if (!onChange) return;
                      const next = nextMultiValue(selected, choice, e.target.checked, allChoices);
                      onChange(next);
                    }}
                    onBlur={idx === 0 ? reg.onBlur : undefined}
                    {...(idx === 0 ? { id: item.id, ref: reg.ref } : {})}
                  />
                  {localized(choice.label, locale)}
                </label>
              );
            })}
          </fieldset>
          {showSpecify ? (
            <div className="mt-2 flex flex-col gap-1 pl-6">
              <label htmlFor={`${item.id}_other`} className="text-xs text-muted-foreground">
                {t('question.pleaseSpecifyLabel')}
              </label>
              <input
                id={`${item.id}_other`}
                type="text"
                className="rounded-md border border-input bg-background px-3 py-2"
                {...register(`${item.id}_other`)}
              />
            </div>
          ) : null}
        </div>
      );
    }
    case 'date':
      return (
        <input
          id={item.id}
          type="date"
          className="rounded-md border border-input bg-background px-3 py-2"
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
                  className="rounded-md border border-input bg-background px-3 py-2"
                  {...register(sf.id)}
                />
                {sfErrorMessage ? (
                  <p role="alert" className="text-xs text-destructive">
                    {sfErrorMessage}
                  </p>
                ) : sfError ? (
                  <p role="alert" className="text-xs text-destructive">
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
