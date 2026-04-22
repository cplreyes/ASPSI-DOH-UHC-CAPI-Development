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
    expect(screen.getByText(/Section 1 of 10/)).toBeInTheDocument();
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
    expect(screen.getByText(/Section 2 of 10/)).toBeInTheDocument();
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
    await user.click(screen.getByLabelText('Other (specify)'));
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
});
