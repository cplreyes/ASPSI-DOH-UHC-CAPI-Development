// Regression repro for Issue #33 — multi-select / matrix state pollution across
// questions in the same section. Surfaced during 2026-04-26 cutover smoke test.
//
// Hypothesis pool (none confirmed at write time):
//  H1: register(item.id) re-call on Question re-render resets multi-select array
//  H2: matrix grouping (Q75-Q81 in G) shares state via the radio-name mechanism
//  H3: nextMultiValue closure captures stale `selected` when Question re-renders
//  H4: visibleChoices recomputation orphans previously-selected values
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { z } from 'zod';
import type * as React from 'react';
import type { Section as SectionModel } from '@/types/survey';
import { LocaleProvider } from '@/i18n/locale-context';
import { Section } from './Section';

const dual = (en: string) => ({ en, fil: en });

function renderWithProviders(ui: React.ReactElement) {
  return render(<LocaleProvider>{ui}</LocaleProvider>);
}

// Note: MatrixQuestion renders BOTH desktop <table> and mobile <div> in jsdom
// (media queries are not applied), so radios with the same aria-label appear
// twice. Pick by index via getAllByLabelText to disambiguate.

describe('<Section> cross-question state isolation (Issue #33)', () => {
  // Section F-style fixture: multi-select with distinct choice labels per item
  // so getByLabelText is unambiguous.
  const sectionF: SectionModel = {
    id: 'F',
    title: dual('Referrals'),
    items: [
      {
        id: 'Q56',
        section: 'F',
        type: 'multi',
        required: true,
        label: dual('How do you SEND referrals?'),
        choices: [
          { label: dual('Send-Slip'), value: 'Send-Slip' },
          { label: dual('Send-EReferral'), value: 'Send-EReferral' },
          { label: dual('Send-Phone'), value: 'Send-Phone' },
        ],
      },
      {
        id: 'Q57',
        section: 'F',
        type: 'single',
        required: true,
        label: dual('Form type?'),
        choices: [
          { label: dual('DOH-standard'), value: 'DOH-standard' },
          { label: dual('No-standard'), value: 'No-standard' },
        ],
      },
      {
        id: 'Q60',
        section: 'F',
        type: 'multi',
        required: true,
        label: dual('How do you RECEIVE referrals?'),
        choices: [
          { label: dual('Recv-Slip'), value: 'Recv-Slip' },
          { label: dual('Recv-EReferral'), value: 'Recv-EReferral' },
          { label: dual('Recv-Phone'), value: 'Recv-Phone' },
        ],
      },
    ],
  };

  const fSchema = z.object({
    Q56: z.array(z.string()).min(1),
    Q57: z.string().min(1),
    Q60: z.array(z.string()).min(1),
  });

  it('Q56 multi-select retains selections after answering Q57 single', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Section section={sectionF} schema={fSchema} onSubmit={() => {}} />);

    const slip = screen.getByLabelText('Send-Slip') as HTMLInputElement;
    const eref = screen.getByLabelText('Send-EReferral') as HTMLInputElement;
    await user.click(slip);
    await user.click(eref);
    expect(slip.checked).toBe(true);
    expect(eref.checked).toBe(true);

    await user.click(screen.getByLabelText('DOH-standard'));

    expect(slip.checked).toBe(true);
    expect(eref.checked).toBe(true);
  });

  it('Q56 retains selections after toggling another multi-select Q60', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Section section={sectionF} schema={fSchema} onSubmit={() => {}} />);

    const q56Slip = screen.getByLabelText('Send-Slip') as HTMLInputElement;
    const q56Eref = screen.getByLabelText('Send-EReferral') as HTMLInputElement;
    await user.click(q56Slip);
    await user.click(q56Eref);
    expect(q56Slip.checked).toBe(true);
    expect(q56Eref.checked).toBe(true);

    const q60Phone = screen.getByLabelText('Recv-Phone') as HTMLInputElement;
    await user.click(q60Phone);
    expect(q60Phone.checked).toBe(true);

    expect(q56Slip.checked).toBe(true);
    expect(q56Eref.checked).toBe(true);
  });

  // Section G fixture: 4 single-type rating items with shared 1-5 choices.
  // groupVisibleItems will collapse them into a matrix because they're all
  // `single` with the same choice values.
  const sectionG: SectionModel = {
    id: 'G',
    title: dual('KAP'),
    items: ['Q75', 'Q76', 'Q77', 'Q78'].map((id) => ({
      id,
      section: 'G',
      type: 'single' as const,
      required: true,
      label: dual(`${id} rating?`),
      choices: ['1', '2', '3', '4', '5'].map((v) => ({ label: dual(v), value: v })),
    })),
  };

  const gSchema = z.object({
    Q75: z.string().min(1),
    Q76: z.string().min(1),
    Q77: z.string().min(1),
    Q78: z.string().min(1),
  });

  it('Q75 matrix radio retains selection after answering Q76 (matrix-grouped)', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Section section={sectionG} schema={gSchema} onSubmit={() => {}} />);

    // Desktop matrix is the first occurrence (rendered before mobile in MatrixQuestion).
    const q75Three = screen.getAllByLabelText(/Q75 3/)[0] as HTMLInputElement;
    const q76Five = screen.getAllByLabelText(/Q76 5/)[0] as HTMLInputElement;

    await user.click(q75Three);
    expect(q75Three.checked).toBe(true);

    await user.click(q76Five);
    expect(q76Five.checked).toBe(true);

    expect(q75Three.checked).toBe(true);
  });

  it('Q75 retains selection after answering Q77 then Q78 (longer matrix sequence)', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Section section={sectionG} schema={gSchema} onSubmit={() => {}} />);

    const q75Three = screen.getAllByLabelText(/Q75 3/)[0] as HTMLInputElement;
    await user.click(q75Three);
    expect(q75Three.checked).toBe(true);

    await user.click(screen.getAllByLabelText(/Q77 4/)[0]);
    await user.click(screen.getAllByLabelText(/Q78 2/)[0]);

    expect(q75Three.checked).toBe(true);
  });
});
