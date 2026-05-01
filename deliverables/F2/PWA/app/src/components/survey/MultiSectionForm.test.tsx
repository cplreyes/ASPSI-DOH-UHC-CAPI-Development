import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type * as React from 'react';
import { LocaleProvider } from '@/i18n/locale-context';
import { MultiSectionForm } from './MultiSectionForm';

function renderWithProviders(ui: React.ReactElement) {
  return render(<LocaleProvider>{ui}</LocaleProvider>);
}

describe('<MultiSectionForm>', () => {
  it('starts on Section A and shows the correct progress', () => {
    renderWithProviders(
      <MultiSectionForm initialValues={{}} onAutosave={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).toBeInTheDocument();
    // Section G is hidden when Q5 is not a prescribing role (or unset), so total visible = 9
    expect(screen.getByText(/Section 1 of 9/)).toBeInTheDocument();
  });

  it('blocks Next when Section A validation fails and advances when it passes', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm initialValues={{}} onAutosave={vi.fn()} onSubmit={vi.fn()} />,
    );

    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument();

    await user.type(screen.getByLabelText('Last Name'), 'Reyes');
    await user.type(screen.getByLabelText('First Name'), 'Carl');
    await user.type(screen.getByLabelText('Middle Initial'), 'P');
    await user.click(screen.getByLabelText('Regular'));
    await user.click(screen.getByLabelText('Female'));
    await user.type(screen.getByLabelText(/How old are you/), '30');
    await user.click(screen.getByLabelText('Nurse'));
    await user.click(screen.getByLabelText('No'));
    await user.type(screen.getByLabelText('Year(s)'), '3');
    await user.type(screen.getByLabelText('Month(s)'), '6');
    await user.type(screen.getByLabelText(/days in a week/), '5');
    await user.type(screen.getByLabelText(/hours do you work/), '8');

    await user.click(screen.getByRole('button', { name: /next/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /Section B/ })).toBeInTheDocument(),
    );
    // Q5='Nurse' is not a prescribing role → Section G hidden → 9 visible sections total
    expect(screen.getByText(/Section 2 of 9/)).toBeInTheDocument();
  });

  it('applies intra-section skip logic — Q8 appears when Q7 = Yes', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm initialValues={{}} onAutosave={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.queryByLabelText(/divide your time/)).toBeNull();
    await user.click(screen.getByLabelText('Yes'));
    await waitFor(() => expect(screen.getByLabelText(/divide your time/)).toBeInTheDocument());
  });

  it('restores merged values when navigating back', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
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
        }}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    await user.click(screen.getByRole('button', { name: /next/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /Section B/ })).toBeInTheDocument(),
    );
    await user.click(screen.getByRole('button', { name: /previous/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument(),
    );
    expect(screen.getByLabelText('Female')).toBeChecked();
  });

  it('blocks Next when Q5 is "Other (specify)" but Q5_other is empty', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    // Q2 and Q5 both have an "Other (specify)" choice; Q5's is the second instance
    // in document order and the one this test is actually exercising.
    const otherChoices = screen.getAllByLabelText('Other (specify)');
    await user.click(otherChoices[otherChoices.length - 1]!);
    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument();
  });

  it('renders the review screen when initialIndex points past the last section', () => {
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
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
        }}
        initialIndex={10}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole('heading', { name: /Review your answers/i })).toBeInTheDocument();
  });

  it('calls onSubmit with merged values when Submit is clicked on the review screen', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const values = {
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
    renderWithProviders(
      <MultiSectionForm
        initialValues={values}
        initialIndex={10}
        onAutosave={vi.fn()}
        onSubmit={onSubmit}
      />,
    );
    await user.click(screen.getByRole('button', { name: /^submit$/i }));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining(values));
  });

  it('returns to the chosen section when Edit is clicked on the review screen', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
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
        }}
        initialIndex={10}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    const editButtons = screen.getAllByRole('button', { name: /^edit$/i });
    await user.click(editButtons[0]);
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/i }),
    ).toBeInTheDocument();
  });

  it('renders Section G Q75-Q81 as a single matrix table on tablet+', async () => {
    // Q5='Physician/Doctor' triggers Section G visibility (per shouldShowSection)
    // and reaches Section G with Q75-Q81 visible.
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q5: 'Physician/Doctor',
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        initialIndex={6} // Section G is index 6 (0-based: A B C D E F G)
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    // Section G (with all gating answers unset) renders 3 matrix tables:
    //   - Q63/Q66/Q69/Q72 (Yes/No) — gating questions Q64/Q65/Q67/Q68/Q70/Q71 are hidden,
    //     so all four Yes/No items are consecutive and collapse into one matrix.
    //   - Q75-Q81 (1-5 scale)
    //   - Q83-Q85 (frequency Never–Always)
    const tables = screen.getAllByRole('table');
    // At least 2 distinct matrix clusters proves the dispatch works across multiple
    // groupings. The exact count depends on Section G's gating predicates and
    // would be brittle as the spec evolves; the q75Q81Matrix probe below is the
    // structural assertion that actually proves Q75-Q81 forms a matrix.
    expect(tables.length).toBeGreaterThanOrEqual(2);
    // Specifically confirm the Q75-Q81 cluster: find a table that contains both
    // Q75's and Q81's question prefixes (the matrix renders "Q75. <label>" in
    // the row header for each row).
    const q75Q81Matrix = tables.find(
      (t) => t.textContent?.includes('Q75.') && t.textContent?.includes('Q81.'),
    );
    expect(q75Q81Matrix).toBeDefined();
  });
});
