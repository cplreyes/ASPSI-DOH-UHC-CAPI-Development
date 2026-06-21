// #587 — error-severity cross-field findings (PROF-01: tenure ≥ age − 20) are
// IN-SURVEY hard blocks, not just review-time warnings. When a section owns every
// field a finding references (Q4 + Q9_1 both in Section A), submitting must NOT
// advance, and the inline error must show — before the review screen.
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { z } from 'zod';
import { createRef } from 'react';
import type * as React from 'react';
import type { Section as SectionModel } from '@/types/survey';
import { LocaleProvider } from '@/i18n/locale-context';
import { Section } from './Section';

const dual = (en: string) => ({ en, fil: en });

function renderWithProviders(ui: React.ReactElement) {
  return render(<LocaleProvider>{ui}</LocaleProvider>);
}

const sectionA: SectionModel = {
  id: 'A',
  title: dual('HCW Profile'),
  items: [
    { id: 'Q4', section: 'A', type: 'number', required: true, label: dual('Age') },
    { id: 'Q9_1', section: 'A', type: 'number', required: true, label: dual('Tenure years') },
  ],
};
const schema = z.object({ Q4: z.coerce.number(), Q9_1: z.coerce.number() });

describe('<Section> cross-field in-survey block (#587 / PROF-01)', () => {
  it('blocks advance when tenure ≥ age − 20 (Q4=40, Q9_1=25)', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const submitRef = createRef<(() => void) | null>();
    renderWithProviders(
      <Section section={sectionA} schema={schema} submitRef={submitRef} onSubmit={onSubmit} />,
    );
    await user.type(screen.getByLabelText(/Age/), '40');
    await user.type(screen.getByLabelText(/Tenure years/), '25');
    submitRef.current?.();
    await waitFor(() =>
      expect(screen.getByText(/must be less than your age/i)).toBeInTheDocument(),
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('allows advance with a plausible tenure (Q4=40, Q9_1=10)', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const submitRef = createRef<(() => void) | null>();
    renderWithProviders(
      <Section section={sectionA} schema={schema} submitRef={submitRef} onSubmit={onSubmit} />,
    );
    await user.type(screen.getByLabelText(/Age/), '40');
    await user.type(screen.getByLabelText(/Tenure years/), '10');
    submitRef.current?.();
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
  });
});
