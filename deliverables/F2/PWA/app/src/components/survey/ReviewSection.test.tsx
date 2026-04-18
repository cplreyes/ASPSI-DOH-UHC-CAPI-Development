import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type * as React from 'react';
import { LocaleProvider } from '@/i18n/locale-context';
import { ReviewSection } from './ReviewSection';

function renderWithProviders(ui: React.ReactElement) {
  return render(<LocaleProvider>{ui}</LocaleProvider>);
}

describe('<ReviewSection>', () => {
  const baseValues = {
    Q1_1: 'Reyes',
    Q1_2: 'Carl',
    Q1_3: 'P',
    Q2: 'Regular',
    Q3: 'Female',
    Q4: 30,
    Q5: 'Nurse',
    Q7: 'No',
    Q9_1: 3,
    Q9_2: 6,
    Q10: 5,
    Q11: 8,
  };

  it('renders a summary heading and section labels', () => {
    renderWithProviders(
      <ReviewSection values={baseValues} onEdit={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(
      screen.getByRole('heading', { name: /Review your answers/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/i }),
    ).toBeInTheDocument();
  });

  it('lists answered fields and omits empty ones', () => {
    renderWithProviders(
      <ReviewSection values={baseValues} onEdit={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByText('Reyes')).toBeInTheDocument();
    expect(screen.getByText('Nurse')).toBeInTheDocument();
    expect(screen.queryByText(/^Q6\b/)).toBeNull();
  });

  it('surfaces a warning when GATE-05 fires (pharmacist + Section C answers)', () => {
    renderWithProviders(
      <ReviewSection
        values={{ ...baseValues, Q5: 'Pharmacist/Dispenser', Q27: 'Yes' }}
        onEdit={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByText(/GATE-05/)).toBeInTheDocument();
    expect(
      screen.getByText(/Sections C and D are for clinical-care roles/i),
    ).toBeInTheDocument();
  });

  it('renders an info-level PROF-03 derivation alongside warnings', () => {
    renderWithProviders(
      <ReviewSection values={baseValues} onEdit={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByText(/PROF-03/)).toBeInTheDocument();
    expect(screen.getByText(/full-time/i)).toBeInTheDocument();
  });

  it('calls onSubmit when the Submit button is clicked', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <ReviewSection values={baseValues} onEdit={vi.fn()} onSubmit={onSubmit} />,
    );
    await user.click(screen.getByRole('button', { name: /^submit$/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('calls onEdit with the section id when an Edit button is clicked', async () => {
    const onEdit = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <ReviewSection values={baseValues} onEdit={onEdit} onSubmit={vi.fn()} />,
    );
    const editButtons = screen.getAllByRole('button', { name: /^edit$/i });
    await user.click(editButtons[0]);
    expect(onEdit).toHaveBeenCalledWith('A');
  });
});
