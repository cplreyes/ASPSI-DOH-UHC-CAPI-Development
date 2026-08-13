import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { z } from 'zod';
import { sections } from '@/generated/items';
import { LocaleProvider } from '@/i18n/locale-context';
import { Section } from './Section';

// #1179/#1180/#1181 + Aly's 2026-08-13 re-report ("hindi pa rin nalabas ang
// notes/instruction"). The component tests above prove the render path works
// against FIXTURES; this file proves it against the REAL generated spec, which
// is what respondents actually see. A preamble that exists in items.ts but
// never reaches the DOM is precisely the failure testers kept re-filing.
const permissive = z.object({}).passthrough();

function renderSection(id: string) {
  const section = sections.find((s) => s.id === id);
  if (!section) throw new Error(`section ${id} not in generated spec`);
  const { container } = render(
    <LocaleProvider>
      <Section section={section} schema={permissive} onSubmit={() => {}} />
    </LocaleProvider>,
  );
  return { section, container };
}

describe('real generated spec — mid-section notes reach the DOM', () => {
  it('Section G shows the doctor professional-fee definition as subtext (#1179)', () => {
    const { container } = renderSection('G');
    const text = container.textContent ?? '';
    expect(text).toContain('negotiable');
    expect(text).toContain('capacity to pay');
  });

  it('Section J shows the "past 6 months" battery instruction (#1180/#1181)', () => {
    const { container } = renderSection('J');
    const text = container.textContent ?? '';
    expect(text).toContain('past 6 months');
  });

  // MultiSectionForm renders the header as localized(section.title, locale), so
  // a corrupted dialect title becomes the on-screen heading in that locale.
  // The fil/bis/ceb/hil/war title slots had note text and preamble TAILS
  // misfiled into them by a row-misaligned translation import -- which is
  // exactly the "shown as the main text instead of subtext" half of #1179.
  // Asserting on the data covers all 7 locales at once.
  it('no section title in any locale contains note prose or a sentence fragment', () => {
    const locales = ['en', 'fil', 'ceb', 'bis', 'ilo', 'hil', 'war', 'bcl'] as const;
    const failures: string[] = [];

    for (const s of sections) {
      for (const loc of locales) {
        const raw = (s.title as unknown as Record<string, string | undefined>)[loc];
        if (!raw) continue; // absent -> falls back to English, which is fine
        if (/negotiable|capacity to pay/i.test(raw)) {
          failures.push(`${s.id}.${loc}: contains the professional-fee note`);
        }
        if (/to be answered by|proceed to Section/i.test(raw)) {
          failures.push(`${s.id}.${loc}: contains a routing instruction`);
        }
        if (/^(ng|sa|sang|han)\s/i.test(raw.trim())) {
          failures.push(`${s.id}.${loc}: starts mid-sentence (preamble tail)`);
        }
        if (/\s[A-Z]?\d{1,3}\s*$|\s[A-Z]\s*$/.test(raw)) {
          failures.push(`${s.id}.${loc}: trailing anchor -- "${raw.slice(-28)}"`);
        }
      }
    }

    expect(failures, `corrupted section titles:\n${failures.join('\n')}`).toEqual([]);
  });
});
