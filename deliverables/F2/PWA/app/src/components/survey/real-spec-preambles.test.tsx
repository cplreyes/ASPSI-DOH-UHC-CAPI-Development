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

  // The same misaligned import also paired ANSWER OPTIONS with the wrong
  // dialect strings -- "Probationary" showed as "Project", "Nursing assistant"
  // as two other roles concatenated, "Administrator" (war) as "doctor, nurse".
  // Q5 is the role question that gates Sections C/D/E/G, so a mislabeled option
  // routes a respondent through the wrong sections. This is the severe class:
  // a wrong heading is cosmetic, a wrong option changes the recorded answer.
  it('no answer option in any locale carries a foreign or stray value', () => {
    const locales = ['fil', 'ceb', 'bis', 'ilo', 'hil', 'war', 'bcl'] as const;
    const failures: string[] = [];

    for (const s of sections) {
      for (const item of s.items) {
        const english = new Set((item.choices ?? []).map((c) => c.label.en.trim().toLowerCase()));
        for (const choice of item.choices ?? []) {
          const label = choice.label as unknown as Record<string, string | undefined>;
          for (const loc of locales) {
            const v = label[loc]?.trim();
            if (!v) continue;
            const self = choice.label.en.trim().toLowerCase();
            // the dialect value is verbatim a DIFFERENT option of the same question
            if (v.toLowerCase() !== self && english.has(v.toLowerCase())) {
              failures.push(`${item.id}.${loc}: "${self}" shows another option's text ("${v}")`);
            }
            // import debris that leaked in from adjacent spreadsheet cells
            if (/\bNote:\s*\d|\bNone\b\s*\w*\s*\d|[<>]|\s\d{1,3}$/.test(v)) {
              failures.push(`${item.id}.${loc}: "${self}" -> stray import debris ("${v}")`);
            }
          }
        }
      }
    }

    expect(failures, `corrupted answer options:\n${failures.join('\n')}`).toEqual([]);
  });

  // The structural rules above cannot catch every case: "Probationary" showed
  // as "Project", and "Project" is not a label anywhere in the spec, so no
  // rule derived from the spec can flag it. This blocklist pins the exact
  // debris strings this import produced, so re-importing the same bad source
  // fails loudly instead of silently shipping wrong options again.
  const IMPORT_DEBRIS = [
    'Project',
    'Project Project',
    'grants',
    'grant None Wala 112',
    'grants None Wala 112',
    'grants None Wara 112',
    'Note: 1',
    'doctor, nurse',
    'Nutrition action officer/ coordinator Pharmacist/Dispenser',
    'including compensation, work environment, and',
  ].map((s) => s.toLowerCase());

  it('no known import-debris string reappears anywhere in the spec', () => {
    const locales = ['fil', 'ceb', 'bis', 'ilo', 'hil', 'war', 'bcl'] as const;
    const failures: string[] = [];

    const scan = (where: string, ls: object | undefined) => {
      if (!ls) return;
      const rec = ls as unknown as Record<string, string | undefined>;
      for (const loc of locales) {
        const v = rec[loc]?.trim().toLowerCase();
        if (v && IMPORT_DEBRIS.includes(v)) failures.push(`${where}.${loc}: "${rec[loc]}"`);
      }
    };

    for (const s of sections) {
      scan(`section ${s.id} title`, s.title);
      scan(`section ${s.id} preamble`, s.preamble);
      for (const item of s.items) {
        scan(item.id, item.label);
        scan(`${item.id} preamble`, item.preamble);
        for (const c of item.choices ?? []) scan(`${item.id} choice`, c.label);
      }
    }

    expect(failures, `import debris resurfaced:\n${failures.join('\n')}`).toEqual([]);
  });
});
