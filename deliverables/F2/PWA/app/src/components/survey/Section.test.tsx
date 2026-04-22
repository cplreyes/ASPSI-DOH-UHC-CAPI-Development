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
});
