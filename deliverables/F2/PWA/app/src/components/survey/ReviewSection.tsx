import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  sectionA,
  sectionB,
  sectionC,
  sectionD,
  sectionE,
  sectionF,
  sectionG,
  sectionH,
  sectionI,
  sectionJ,
} from '@/generated/items';
import type { Section as SectionModel, Item } from '@/types/survey';
import { evaluateCrossField, type Warning } from '@/lib/cross-field';
import type { FormValues } from '@/lib/skip-logic';
import { Button } from '@/components/ui/button';
import { useLocale } from '@/i18n/locale-context';
import { localized } from '@/i18n/localized';
import type { Locale } from '@/i18n/index';
import { groupVisibleItems, isMatrixGroup, type MatrixGroup } from './group-matrix';

const SECTIONS: SectionModel[] = [
  sectionA,
  sectionB,
  sectionC,
  sectionD,
  sectionE,
  sectionF,
  sectionG,
  sectionH,
  sectionI,
  sectionJ,
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

function rowsForItem(
  item: Item,
  values: FormValues,
  locale: Locale,
): Array<{ key: string; label: string; value: string }> {
  if (item.type === 'multi-field' && item.subFields) {
    return item.subFields
      .map((sf) => ({
        key: sf.id,
        label: `${item.id} ${localized(sf.label, locale)}`,
        value: formatValue(values[sf.id]),
      }))
      .filter((r) => r.value !== '');
  }
  const primary = formatValue(values[item.id]);
  const rows: Array<{ key: string; label: string; value: string }> = [];
  if (primary !== '')
    rows.push({
      key: item.id,
      label: `${item.id} ${localized(item.label, locale)}`,
      value: primary,
    });
  const otherKey = `${item.id}_other`;
  const otherVal = formatValue(values[otherKey]);
  if (otherVal !== '') rows.push({ key: otherKey, label: `${item.id} (specify)`, value: otherVal });
  return rows;
}

// Hairline-bordered alerts with a colored left border (no full background fill).
const SEVERITY_STYLES: Record<Warning['severity'], string> = {
  error: 'border-border border-l-4 border-l-destructive text-foreground',
  warn: 'border-border border-l-4 border-l-warning text-foreground',
  clean: 'border-border border-l-4 border-l-primary text-foreground',
  info: 'border-border border-l-4 border-l-muted-foreground text-foreground',
};

export function ReviewSection({ values, onEdit, onSubmit }: ReviewSectionProps) {
  const { t } = useTranslation();
  const { locale } = useLocale();
  const warnings = useMemo(() => evaluateCrossField(values), [values]);

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-6 p-6">
      <h2 className="font-serif text-2xl font-medium tracking-tight">{t('review.heading')}</h2>

      {warnings.length > 0 ? (
        <section aria-label={t('review.crossFieldRegion')} className="flex flex-col gap-2">
          {warnings.map((w) => (
            <div key={w.id} className={`border px-3 py-2 text-sm ${SEVERITY_STYLES[w.severity]}`}>
              <strong className="mr-2 font-mono text-xs uppercase tracking-wide">{w.id}</strong>
              {t(w.message.key, w.message.values ?? {})}
            </div>
          ))}
        </section>
      ) : null}

      {SECTIONS.map((section) => {
        const grouped = groupVisibleItems(section.items);
        type Block =
          | { kind: 'rows'; rows: ReturnType<typeof rowsForItem> }
          | { kind: 'matrix'; group: MatrixGroup };
        const blocks: Block[] = [];
        for (const entry of grouped) {
          if (isMatrixGroup(entry)) {
            // Only include the matrix if at least one row has a value
            const hasAny = entry.items.some((it) => formatValue(values[it.id]) !== '');
            if (hasAny) blocks.push({ kind: 'matrix', group: entry });
          } else {
            const rows = rowsForItem(entry, values, locale);
            if (rows.length > 0) blocks.push({ kind: 'rows', rows });
          }
        }
        if (blocks.length === 0) return null;
        return (
          <section key={section.id} className="flex flex-col gap-2">
            <header className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {t('review.sectionHeading', {
                  id: section.id,
                  title: localized(section.title, locale),
                })}
              </h3>
              <Button type="button" variant="outline" size="sm" onClick={() => onEdit(section.id)}>
                {t('review.edit')}
              </Button>
            </header>
            <div className="divide-y divide-border border border-border">
              {blocks.map((block, blockIdx) =>
                block.kind === 'matrix' ? (
                  <div key={`matrix-${block.group.items[0].id}`} className="px-3 py-2">
                    <table className="w-full text-sm">
                      <tbody>
                        {block.group.items.map((it) => (
                          <tr key={it.id}>
                            <td className="py-1 pr-2 text-muted-foreground">
                              {it.id} {localized(it.label, locale)}
                            </td>
                            <td className="py-1 text-foreground">{formatValue(values[it.id])}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <dl key={`rows-${blockIdx}`} className="divide-y divide-border">
                    {block.rows.map((r) => (
                      <div key={r.key} className="grid grid-cols-3 gap-3 px-3 py-2 text-sm">
                        <dt className="col-span-2 text-muted-foreground">{r.label}</dt>
                        <dd className="text-foreground">{r.value}</dd>
                      </div>
                    ))}
                  </dl>
                ),
              )}
            </div>
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
