import { useFormContext, type FieldErrors } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Locale } from '@/i18n/index';
import { filterChoices } from '@/lib/skip-logic';
import type { Item } from '@/types/survey';
import { nextMultiValue } from './Question.helpers';

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

  // Compound questions (multi-field — Q1 name, Q9 tenure, etc.) need a
  // <fieldset>/<legend> wrapper instead of <div>/<label htmlFor>: a single
  // <label> can't legally point to multiple sub-inputs, and pre-fix it
  // pointed at item.id which had no matching element — broke screen-reader
  // announcement of the question text on each sub-input + tripped axe's
  // label-no-for + form-field-no-id rules. Closes #277.
  const isCompound = item.type === 'multi-field' || item.type === 'partial-date';
  const Outer = isCompound ? 'fieldset' : 'div';
  const Heading = isCompound ? 'legend' : 'label';
  const headingProps = isCompound ? {} : { htmlFor: item.id };

  return (
    <Outer className="m-0 grid min-w-0 grid-cols-1 gap-y-2 border-0 p-0 py-3 sm:grid-cols-[80px_1fr]">
      <span
        aria-hidden="true"
        className="font-mono text-sm text-muted-foreground sm:pt-1 sm:pr-4 sm:text-right sm:text-base sm:leading-snug"
      >
        {item.id}
      </span>
      <div className="flex min-w-0 flex-col gap-2">
        <Heading {...headingProps} className="text-base font-medium leading-snug">
          <span className="sr-only">
            {item.id}
            {'. '}
          </span>
          {localized(item.label, locale)}
          {item.required ? <span className="ml-1 text-destructive">*</span> : null}
        </Heading>
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
    </Outer>
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
  currentValue?: unknown,
  onChange?: (next: string | string[]) => void,
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
          {/* R3 #313: every multi-select shows this affordance so respondents
              know more than one answer is allowed (raised for Q25/Q32/.../Q124). */}
          <p className="text-xs text-muted-foreground">{t('question.selectAllThatApply')}</p>
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
    case 'partial-date': {
      // One field, ISO-8601 variable precision: '' | 'YYYY' | 'YYYY-MM' |
      // 'YYYY-MM-DD'. Year required; month + day each optional (blank = "Don't
      // know"). Day enables only when month is set — ISO 8601 has no
      // day-without-month, and it matches the approved year→month→day shape.
      //
      // Fully controlled (like `multi`): the field value is the composite
      // string, driven via setValue (onChange). We bind only register()'s ref +
      // onBlur to the year input (focus + touched tracking) and DON'T spread the
      // full register() onto any sub-input, so RHF never re-derives the value
      // from a single sub-input's DOM `.value`. R3 #306.
      const raw = typeof currentValue === 'string' ? currentValue : '';
      const [yPart = '', mPart = '', dPart = ''] = raw.split('-');
      const reg = register(item.id);
      const compose = (y: string, m: string, d: string): string => {
        const yy = y.trim();
        if (!yy) return '';
        let out = yy;
        const mm = m.trim();
        if (mm) {
          out += `-${mm.padStart(2, '0')}`;
          const dd = d.trim();
          if (dd) out += `-${dd.padStart(2, '0')}`;
        }
        return out;
      };
      const emit = (y: string, m: string, d: string) => onChange?.(compose(y, m, d));
      const inputClass = 'rounded-md border border-input bg-background px-3 py-2';
      // Display month/day without the storage zero-pad ('06' -> '6').
      const show = (p: string) => (p ? String(Number(p)) : '');
      return (
        <div className="flex flex-col gap-1">
          <div className="grid grid-cols-3 gap-2">
            <div className="flex flex-col gap-1">
              <label htmlFor={item.id} className="text-xs text-muted-foreground">
                {t('question.partialDate.year')}
                <span className="ml-1 text-destructive">*</span>
              </label>
              <input
                id={item.id}
                type="number"
                inputMode="numeric"
                onKeyDown={blockNonNumericKeys}
                placeholder="YYYY"
                value={yPart}
                ref={reg.ref}
                onBlur={reg.onBlur}
                onChange={(e) => emit(e.target.value, mPart, dPart)}
                className={inputClass}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor={`${item.id}_month`} className="text-xs text-muted-foreground">
                {t('question.partialDate.month')}
              </label>
              <input
                id={`${item.id}_month`}
                type="number"
                inputMode="numeric"
                min={1}
                max={12}
                onKeyDown={blockNonNumericKeys}
                placeholder={t('question.partialDate.optional')}
                value={show(mPart)}
                onChange={(e) => emit(yPart, e.target.value, dPart)}
                className={inputClass}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor={`${item.id}_day`} className="text-xs text-muted-foreground">
                {t('question.partialDate.day')}
              </label>
              <input
                id={`${item.id}_day`}
                type="number"
                inputMode="numeric"
                min={1}
                max={31}
                onKeyDown={blockNonNumericKeys}
                placeholder={t('question.partialDate.optional')}
                value={show(dPart)}
                disabled={!mPart}
                onChange={(e) => emit(yPart, mPart, e.target.value)}
                className={inputClass}
              />
            </div>
          </div>
        </div>
      );
    }
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
