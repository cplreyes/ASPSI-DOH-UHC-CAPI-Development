import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  sectionA, sectionB, sectionC, sectionD, sectionE1, sectionE2,
  sectionF, sectionG, sectionH, sectionI, sectionJ,
} from '@/generated/items';
import type { Section as SectionModel, Item } from '@/types/survey';
import { evaluateCrossField, type Warning } from '@/lib/cross-field';
import type { FormValues } from '@/lib/skip-logic';
import { Button } from '@/components/ui/button';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Locale } from '@/i18n/index';

const SECTIONS: SectionModel[] = [
  sectionA, sectionB, sectionC, sectionD, sectionE1, sectionE2,
  sectionF, sectionG, sectionH, sectionI, sectionJ,
];

interface ReviewSectionProps {
  values: FormValues;
  onEdit: (sectionId: string) => void;
  onSubmit: () => void;
}

function formatValue(v: unknown): string {
  if (v === undefined || v === null || v === '') return '';
  if (Array.isArray(v)) return v.join(', ');
  return String(v);
}

function rowsForItem(item: Item, values: FormValues, locale: Locale): Array<{ key: string; label: string; value: string }> {
  if (item.type === 'multi-field' && item.subFields) {
    return item.subFields
      .map((sf) => ({ key: sf.id, label: `${item.id} ${localized(sf.label, locale)}`, value: formatValue(values[sf.id]) }))
      .filter((r) => r.value !== '');
  }
  const primary = formatValue(values[item.id]);
  const rows: Array<{ key: string; label: string; value: string }> = [];
  if (primary !== '') rows.push({ key: item.id, label: `${item.id} ${localized(item.label, locale)}`, value: primary });
  const otherKey = `${item.id}_other`;
  const otherVal = formatValue(values[otherKey]);
  if (otherVal !== '') rows.push({ key: otherKey, label: `${item.id} (specify)`, value: otherVal });
  return rows;
}

const SEVERITY_STYLES: Record<Warning['severity'], string> = {
  error: 'border-red-300 bg-red-50 text-red-900',
  warn: 'border-amber-300 bg-amber-50 text-amber-900',
  clean: 'border-blue-300 bg-blue-50 text-blue-900',
  info: 'border-slate-200 bg-slate-50 text-slate-700',
};

export function ReviewSection({ values, onEdit, onSubmit }: ReviewSectionProps) {
  const { t } = useTranslation();
  const { locale } = useLocale();
  const warnings = useMemo(() => evaluateCrossField(values), [values]);

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-6 p-6">
      <h2 className="text-2xl font-semibold tracking-tight">{t('review.heading')}</h2>

      {warnings.length > 0 ? (
        <section aria-label={t('review.crossFieldRegion')} className="flex flex-col gap-2">
          {warnings.map((w) => (
            <div
              key={w.id}
              className={`rounded-md border px-3 py-2 text-sm ${SEVERITY_STYLES[w.severity]}`}
            >
              <strong className="mr-2">{w.id}</strong>
              {w.message}
            </div>
          ))}
        </section>
      ) : null}

      {SECTIONS.map((section) => {
        const rows = section.items.flatMap((item) => rowsForItem(item, values, locale));
        if (rows.length === 0) return null;
        return (
          <section key={section.id} className="flex flex-col gap-2">
            <header className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {t('review.sectionHeading', { id: section.id, title: localized(section.title, locale) })}
              </h3>
              <Button type="button" variant="outline" size="sm" onClick={() => onEdit(section.id)}>
                {t('review.edit')}
              </Button>
            </header>
            <dl className="divide-y divide-slate-200 rounded border border-slate-200">
              {rows.map((r) => (
                <div key={r.key} className="grid grid-cols-3 gap-3 px-3 py-2 text-sm">
                  <dt className="col-span-2 text-slate-700">{r.label}</dt>
                  <dd className="text-slate-900">{r.value}</dd>
                </div>
              ))}
            </dl>
          </section>
        );
      })}

      <div className="pt-2">
        <Button type="button" onClick={onSubmit}>
          {t('review.submit')}
        </Button>
      </div>
    </div>
  );
}
