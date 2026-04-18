import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MultiSectionForm } from './MultiSectionForm';

describe('<MultiSectionForm>', () => {
  it('starts on Section A and shows the correct progress', () => {
    render(
      <MultiSectionForm
        initialValues={{}}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Section 1 of 11/)).toBeInTheDocument();
  });

  it('blocks Next when Section A validation fails and advances when it passes', async () => {
    const user = userEvent.setup();
    render(
      <MultiSectionForm
        initialValues={{}}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
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
    expect(screen.getByText(/Section 2 of 11/)).toBeInTheDocument();
  });

  it('applies intra-section skip logic — Q8 appears when Q7 = Yes', async () => {
    const user = userEvent.setup();
    render(
      <MultiSectionForm
        initialValues={{}}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.queryByLabelText(/divide your time/)).toBeNull();
    await user.click(screen.getByLabelText('Yes'));
    await waitFor(() =>
      expect(screen.getByLabelText(/divide your time/)).toBeInTheDocument(),
    );
  });

  it('restores merged values when navigating back', async () => {
    const user = userEvent.setup();
    render(
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
});
