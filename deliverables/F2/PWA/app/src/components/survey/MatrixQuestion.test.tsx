import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useForm, FormProvider } from 'react-hook-form';
import { useEffect } from 'react';
import type * as React from 'react';
import { LocaleProvider } from '@/i18n/locale-context';
import type { Choice, Item } from '@/types/survey';
import { MatrixQuestion } from './MatrixQuestion';

const dual = (en: string) => ({ en, fil: en });

function row(id: string, label: string, choices: Choice[]): Item {
  return {
    id,
    section: 'G',
    type: 'single',
    required: true,
    label: dual(label),
    choices,
  };
}

function Harness({ items, choices }: { items: Item[]; choices: Choice[] }) {
  const methods = useForm({ defaultValues: {} });
  return (
    <LocaleProvider>
      <FormProvider {...methods}>
        <form>
          <MatrixQuestion items={items} choices={choices} />
        </form>
      </FormProvider>
    </LocaleProvider>
  );
}

const scale15: Choice[] = [
  { label: dual('1'), value: '1' },
  { label: dual('2'), value: '2' },
  { label: dual('3'), value: '3' },
  { label: dual('4'), value: '4' },
  { label: dual('5'), value: '5' },
];

describe('<MatrixQuestion>', () => {
  it('renders one column header per choice plus a Statement header', () => {
    render(<Harness items={[row('Q75', 'fairness ZBB', scale15), row('Q76', 'fairness NBB', scale15)]} choices={scale15} />);
    // Column headers
    expect(screen.getByText(/Statement/i)).toBeInTheDocument();
    for (const c of scale15) {
      expect(screen.getAllByText(c.value).length).toBeGreaterThan(0);
    }
  });

  it('renders one row per item with the localised statement text', () => {
    render(<Harness items={[row('Q75', 'fairness ZBB', scale15), row('Q76', 'fairness NBB', scale15)]} choices={scale15} />);
    expect(screen.getByText(/fairness ZBB/)).toBeInTheDocument();
    expect(screen.getByText(/fairness NBB/)).toBeInTheDocument();
  });

  it('clicking a radio in row Q75 sets only that row\'s value', async () => {
    const user = userEvent.setup();
    let captured: Record<string, unknown> = {};
    function CaptureHarness({ items, choices }: { items: Item[]; choices: Choice[] }) {
      const methods = useForm({ defaultValues: {} });
      captured = methods.getValues();
      // Re-read inside the render so test can inspect after each act
      return (
        <LocaleProvider>
          <FormProvider {...methods}>
            <form>
              <MatrixQuestion items={items} choices={choices} />
              <button type="button" onClick={() => (captured = methods.getValues())}>snapshot</button>
            </form>
          </FormProvider>
        </LocaleProvider>
      );
    }
    render(<CaptureHarness items={[row('Q75', 'fairness ZBB', scale15), row('Q76', 'fairness NBB', scale15)]} choices={scale15} />);
    // Each row's radios share name = item.id; click the "5" radio in row Q75
    const q75Radios = screen.getAllByRole('radio').filter((el) => (el as HTMLInputElement).name === 'Q75');
    expect(q75Radios).toHaveLength(5);
    await user.click(q75Radios[4]);
    await user.click(screen.getByText('snapshot'));
    expect(captured).toMatchObject({ Q75: '5' });
    // Q76 is registered but untouched — RHF may represent it as null or undefined
    const q76 = (captured as Record<string, unknown>).Q76;
    expect(q76 == null).toBe(true);
  });

  it('renders a row\'s required error inline when triggered', async () => {
    function ErrHarness({ items, choices }: { items: Item[]; choices: Choice[] }) {
      const methods = useForm({
        defaultValues: {},
      });
      // Force an error on Q76 to test display — use effect so it runs after
      // mount and doesn't trigger an infinite re-render loop.
      useEffect(() => {
        methods.setError('Q76', { type: 'required', message: 'This field is required.' });
      // eslint-disable-next-line react-hooks/exhaustive-deps
      }, []);
      return (
        <LocaleProvider>
          <FormProvider {...methods}>
            <form>
              <MatrixQuestion items={items} choices={choices} />
            </form>
          </FormProvider>
        </LocaleProvider>
      );
    }
    render(<ErrHarness items={[row('Q75', 'A', scale15), row('Q76', 'B', scale15)]} choices={scale15} />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/required/i);
  });
});
