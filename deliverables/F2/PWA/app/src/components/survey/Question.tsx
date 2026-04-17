import { useFormContext } from 'react-hook-form';
import type { Item } from '@/types/survey';

interface QuestionProps {
  item: Item;
}

export function Question({ item }: QuestionProps) {
  const { register, watch } = useFormContext();
  const currentValue = watch(item.id);
  const showSpecify =
    (item.hasOtherSpecify &&
      item.choices?.some((c) => c.isOtherSpecify && c.value === currentValue)) ??
    false;

  return (
    <div className="flex flex-col gap-2 py-3">
      <label htmlFor={item.id} className="text-sm font-medium">
        {item.label}
        {item.required ? <span className="ml-1 text-red-600">*</span> : null}
      </label>
      {item.help ? <p className="text-xs text-muted-foreground">{item.help}</p> : null}
      {renderControl(item, register, showSpecify)}
    </div>
  );
}

function renderControl(
  item: Item,
  register: ReturnType<typeof useFormContext>['register'],
  showSpecify: boolean,
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
                {choice.label}
              </label>
            ))}
          </fieldset>
          {showSpecify ? (
            <div className="mt-2 flex flex-col gap-1 pl-6">
              <label htmlFor={`${item.id}_other`} className="text-xs text-muted-foreground">
                Please specify
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
  }
}
