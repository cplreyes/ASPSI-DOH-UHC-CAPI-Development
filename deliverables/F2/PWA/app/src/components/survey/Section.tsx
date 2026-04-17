import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { ZodTypeAny } from 'zod';
import type { Section as SectionModel } from '@/types/survey';
import { Button } from '@/components/ui/button';
import { Question } from './Question';

interface SectionProps<T extends Record<string, unknown>> {
  section: SectionModel;
  schema: ZodTypeAny;
  onSubmit: (values: T) => void;
}

export function Section<T extends Record<string, unknown>>({
  section,
  schema,
  onSubmit,
}: SectionProps<T>) {
  const methods = useForm<T>({
    resolver: zodResolver(schema),
    mode: 'onSubmit',
  });

  return (
    <FormProvider {...methods}>
      <form
        onSubmit={methods.handleSubmit((values) => onSubmit(values as T))}
        className="mx-auto flex max-w-xl flex-col gap-4 p-6"
        noValidate
      >
        <header className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold tracking-tight">
            Section {section.id} — {section.title}
          </h2>
          {section.preamble ? (
            <p className="text-sm text-muted-foreground">{section.preamble}</p>
          ) : null}
        </header>

        {section.items.map((item) => (
          <Question key={item.id} item={item} />
        ))}

        <div className="pt-4">
          <Button type="submit">Submit</Button>
        </div>
      </form>
    </FormProvider>
  );
}
