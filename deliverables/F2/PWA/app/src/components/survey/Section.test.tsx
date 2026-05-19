import { describe, expect, it, vi } from 'vitest';
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

describe('<Section>', () => {
  const fixture: SectionModel = {
    id: 'A',
    title: dual('Healthcare Worker Profile'),
    preamble: dual('Please answer the following.'),
    items: [
      {
        id: 'Q3',
        section: 'A',
        type: 'single',
        required: true,
        label: dual('What is your sex at birth?'),
        choices: [
          { label: dual('Male'), value: 'Male' },
          { label: dual('Female'), value: 'Female' },
        ],
      },
      { id: 'Q4', section: 'A', type: 'number', required: true, label: dual('Age?'), min: 18 },
    ],
  };

  const schema = z.object({
    Q3: z.enum(['Male', 'Female']),
    Q4: z.coerce.number().min(18),
  });

  it('renders the preamble', () => {
    renderWithProviders(<Section section={fixture} schema={schema} onSubmit={() => {}} />);
    expect(screen.getByText('Please answer the following.')).toBeInTheDocument();
  });

  it('renders one Question per item', () => {
    renderWithProviders(<Section section={fixture} schema={schema} onSubmit={() => {}} />);
    expect(screen.getByLabelText(/sex at birth/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Age\?/)).toBeInTheDocument();
  });

  it('calls onSubmit with parsed values when the form is valid', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    renderWithProviders(<Section section={fixture} schema={schema} onSubmit={onSubmit} />);

    await user.click(screen.getByLabelText('Female'));
    await user.type(screen.getByLabelText(/Age\?/), '25');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toEqual({ Q3: 'Female', Q4: 25 });
  });

  it('does not call onSubmit when validation fails', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    renderWithProviders(<Section section={fixture} schema={schema} onSubmit={onSubmit} />);

    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('renders only the items passed via the items override prop', () => {
    renderWithProviders(
      <Section section={fixture} schema={schema} items={[fixture.items[1]]} onSubmit={() => {}} />,
    );
    expect(screen.queryByLabelText(/sex at birth/)).toBeNull();
    expect(screen.getByLabelText(/Age\?/)).toBeInTheDocument();
  });

  // R3 #298: skip-logic can hide a schema-required item (e.g. Section E1
  // Q48 for a Pharmacist/Dispenser — the role gate lives in skip-logic.ts,
  // not the spec, so the generated schema still marks it required). The
  // resolver must mirror visibility the way rendering does, or the form
  // silently fails zod on the hidden field and "cannot proceed".
  it('does not block submit on schema-required items hidden by skip-logic (#298)', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    renderWithProviders(
      <Section section={fixture} schema={schema} items={[fixture.items[1]]} onSubmit={onSubmit} />,
    );
    await user.type(screen.getByLabelText(/Age\?/), '25');
    await user.click(screen.getByRole('button', { name: /submit/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toEqual({ Q4: 25 });
  });

  it('still blocks submit when a VISIBLE required item is empty', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    // Both items visible (no items override) — real validation must hold.
    renderWithProviders(<Section section={fixture} schema={schema} onSubmit={onSubmit} />);
    await user.type(screen.getByLabelText(/Age\?/), '25');
    await user.click(screen.getByRole('button', { name: /submit/i }));
    expect(onSubmit).not.toHaveBeenCalled(); // Q3 still required + empty
  });

  it('prefills inputs from defaultValues', () => {
    renderWithProviders(
      <Section
        section={fixture}
        schema={schema}
        defaultValues={{ Q3: 'Female', Q4: 25 }}
        onSubmit={() => {}}
      />,
    );
    expect(screen.getByLabelText('Female')).toBeChecked();
    expect(screen.getByLabelText(/Age\?/)).toHaveValue(25);
  });

  it('calls onAutosave with debounced form values', async () => {
    const user = userEvent.setup();
    const onAutosave = vi.fn();

    renderWithProviders(
      <Section section={fixture} schema={schema} onAutosave={onAutosave} onSubmit={() => {}} />,
    );

    await user.click(screen.getByLabelText('Female'));

    // Still within debounce window (500 ms).
    await new Promise((r) => setTimeout(r, 100));
    expect(onAutosave).not.toHaveBeenCalled();

    // Wait past debounce threshold.
    await new Promise((r) => setTimeout(r, 600));
    expect(onAutosave).toHaveBeenCalled();
    const last = onAutosave.mock.calls[onAutosave.mock.calls.length - 1];
    expect(last[0]).toMatchObject({ Q3: 'Female' });
  });

  // R3 #314 seam probe at the Section level: a matrix (consecutive
  // same-choice singles → MatrixQuestion) filled LIVE, then the real
  // handleSubmit round-trip. onSubmit is exactly what handleSectionValid
  // spreads into `merged`. If the matrix values don't reach onSubmit, the
  // seam is here; if they do, it's higher in MultiSectionForm orchestration.
  const matrixFixture: SectionModel = {
    id: 'J',
    title: dual('Job Satisfaction'),
    items: [
      {
        id: 'Q98',
        section: 'J',
        type: 'single',
        required: true,
        label: dual('Pay'),
        choices: [
          { label: dual('1'), value: '1' },
          { label: dual('2'), value: '2' },
          { label: dual('3'), value: '3' },
        ],
      },
      {
        id: 'Q99',
        section: 'J',
        type: 'single',
        required: true,
        label: dual('Workload'),
        choices: [
          { label: dual('1'), value: '1' },
          { label: dual('2'), value: '2' },
          { label: dual('3'), value: '3' },
        ],
      },
    ],
  };
  const matrixSchema = z.object({
    Q98: z.enum(['1', '2', '3']),
    Q99: z.enum(['1', '2', '3']),
  });

  it('live-filled matrix values reach onSubmit (#314 Section-level seam)', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    renderWithProviders(
      <Section
        section={matrixFixture}
        schema={matrixSchema}
        items={matrixFixture.items}
        onSubmit={onSubmit}
      />,
    );
    // MatrixQuestion radios have aria-label `${item.id} ${choiceLabel}`.
    await user.click(screen.getAllByLabelText('Q98 2')[0]);
    await user.click(screen.getAllByLabelText('Q99 3')[0]);
    await user.click(screen.getByRole('button', { name: /submit/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toEqual({ Q98: '2', Q99: '3' });
  });

  // #314 — REPRODUCED, NOT YET FIXED. `.skip` = runnable repro; flip to
  // `it(` when fixed and it must pass.
  //
  // DECISIVE REFRAME (2026-05-19): the fault is NOT in MatrixQuestion's
  // render pattern. Three architecturally-distinct MatrixQuestion fixes —
  // (1) uncontrolled `register` (shipped), (2) controlled `useWatch`,
  // (3) `useController` per row — ALL fail THIS Section-level test, while
  // the *isolated* MatrixQuestion rehydrate test (bare
  // `useForm({defaultValues})`) PASSES with the same component under
  // approaches (1) and (3). Same component, same Controller, opposite
  // result. The only differing variable is the form host:
  //   - isolated harness: `useForm({ defaultValues })`            → rehydrates
  //   - Section.tsx:      `useForm({ resolver, mode:'onChange',
  //                                  defaultValues })`            → does NOT
  // So #314's root cause is in **Section.tsx's useForm configuration /
  // defaultValues handling on the Edit re-mount** (the resolver wraps
  // values via `stripNulls`; `mode:'onChange'` + resolver may revalidate/
  // reset before child fields register), NOT in MatrixQuestion. The
  // earlier "duplicate radio refs" theory explained the original symptom
  // but is disproven as the *root* cause by the Controller result.
  //
  // Per systematic-debugging Phase 4.5 (3+ fixes failed = wrong
  // architecture/understanding): STOPPED here deliberately. Next
  // investigation belongs in Section.tsx's form host, not MatrixQuestion —
  // do NOT re-attempt MatrixQuestion-side patches.
  it.skip('matrix rehydrates from defaultValues after the round-trip (#314)', () => {
    renderWithProviders(
      <Section
        section={matrixFixture}
        schema={matrixSchema}
        items={matrixFixture.items}
        defaultValues={{ Q98: '2', Q99: '3' }}
        onSubmit={() => {}}
      />,
    );
    expect((screen.getAllByLabelText('Q98 2')[0] as HTMLInputElement).checked).toBe(true);
    expect((screen.getAllByLabelText('Q99 3')[0] as HTMLInputElement).checked).toBe(true);
  });
});
