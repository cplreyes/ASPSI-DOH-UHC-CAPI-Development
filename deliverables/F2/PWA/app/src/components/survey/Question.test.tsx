import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useForm, FormProvider } from 'react-hook-form';
import type * as React from 'react';
import type { Item } from '@/types/survey';
import { Question } from './Question';
import { LocaleProvider } from '@/i18n/locale-context';

const dual = (en: string) => ({ en, fil: en });

function renderWithProviders(ui: React.ReactElement) {
  return render(<LocaleProvider>{ui}</LocaleProvider>);
}

function Harness({ item }: { item: Item }) {
  const methods = useForm();
  return (
    <FormProvider {...methods}>
      <form>
        <Question item={item} />
      </form>
    </FormProvider>
  );
}

describe('<Question>', () => {
  it('renders short-text as a text input with the label', () => {
    const item: Item = {
      id: 'Q1',
      section: 'A',
      type: 'short-text',
      required: true,
      label: dual('What is your name?'),
    };
    renderWithProviders(<Harness item={item} />);
    expect(screen.getByLabelText(/What is your name\?/)).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveAttribute('type', 'text');
  });

  it('renders long-text as a textarea', () => {
    const item: Item = {
      id: 'Q36',
      section: 'C',
      type: 'long-text',
      required: true,
      label: dual('What might convince you?'),
    };
    renderWithProviders(<Harness item={item} />);
    expect(screen.getByLabelText(/What might convince you/)).toBeInstanceOf(HTMLTextAreaElement);
  });

  it('renders number as a numeric input with min/max', () => {
    const item: Item = {
      id: 'Q11',
      section: 'A',
      type: 'number',
      required: true,
      label: dual('Hours per day?'),
      min: 1,
      max: 24,
    };
    renderWithProviders(<Harness item={item} />);
    const input = screen.getByLabelText(/Hours per day/) as HTMLInputElement;
    expect(input.type).toBe('number');
    expect(input.min).toBe('1');
    expect(input.max).toBe('24');
  });

  it('renders single as a radio group', () => {
    const item: Item = {
      id: 'Q3',
      section: 'A',
      type: 'single',
      required: true,
      label: dual('What is your sex at birth?'),
      choices: [
        { label: dual('Male'), value: 'Male' },
        { label: dual('Female'), value: 'Female' },
      ],
    };
    renderWithProviders(<Harness item={item} />);
    expect(screen.getAllByRole('radio')).toHaveLength(2);
    expect(screen.getByLabelText('Male')).toBeInTheDocument();
    expect(screen.getByLabelText('Female')).toBeInTheDocument();
  });

  it('shows a specify input when the "Other" choice is selected', async () => {
    const user = userEvent.setup();
    const item: Item = {
      id: 'Q2',
      section: 'A',
      type: 'single',
      required: true,
      label: dual('Employment?'),
      hasOtherSpecify: true,
      choices: [
        { label: dual('Regular'), value: 'Regular' },
        { label: dual('Other, specify'), value: 'Other, specify', isOtherSpecify: true },
      ],
    };
    renderWithProviders(<Harness item={item} />);

    expect(screen.queryByLabelText(/Please specify/)).toBeNull();

    await user.click(screen.getByLabelText('Other, specify'));
    expect(screen.getByLabelText(/Please specify/)).toBeInTheDocument();
  });

  it('renders multi as a checkbox group', () => {
    const item: Item = {
      id: 'Q28',
      section: 'C',
      type: 'multi',
      required: true,
      label: dual('Which are included?'),
      choices: [
        { label: dual('Pap smear'), value: 'Pap smear' },
        { label: dual('Mammogram'), value: 'Mammogram' },
        { label: dual('Lipid profile'), value: 'Lipid profile' },
      ],
    };
    renderWithProviders(<Harness item={item} />);
    const boxes = screen.getAllByRole('checkbox');
    expect(boxes).toHaveLength(3);
    expect(screen.getByLabelText('Pap smear')).toBeInTheDocument();
  });

  it('shows specify input when an "Other" checkbox is selected in multi', async () => {
    const user = userEvent.setup();
    const item: Item = {
      id: 'Q21',
      section: 'B',
      type: 'multi',
      required: true,
      label: dual('Which do you expect to change?'),
      hasOtherSpecify: true,
      choices: [
        { label: dual('Salary'), value: 'Salary' },
        { label: dual('Other (specify)'), value: 'Other (specify)', isOtherSpecify: true },
      ],
    };
    renderWithProviders(<Harness item={item} />);
    expect(screen.queryByLabelText(/Please specify/)).toBeNull();
    await user.click(screen.getByLabelText('Other (specify)'));
    expect(screen.getByLabelText(/Please specify/)).toBeInTheDocument();
  });

  it('renders date as an input type=date', () => {
    const item: Item = {
      id: 'Q31',
      section: 'C',
      type: 'date',
      required: false,
      label: dual('Since when?'),
    };
    renderWithProviders(<Harness item={item} />);
    const input = screen.getByLabelText(/since when/i);
    expect(input).toHaveAttribute('type', 'date');
  });

  it('renders multi-field as one input per subField, labelled', () => {
    const item: Item = {
      id: 'Q1',
      section: 'A',
      type: 'multi-field',
      required: true,
      label: dual('What is your name?'),
      subFields: [
        { id: 'Q1_1', label: dual('Last Name'), kind: 'short-text' },
        { id: 'Q1_2', label: dual('First Name'), kind: 'short-text' },
        { id: 'Q1_3', label: dual('Middle Initial'), kind: 'short-text' },
      ],
    };
    renderWithProviders(<Harness item={item} />);
    expect(screen.getByLabelText('Last Name')).toBeInTheDocument();
    expect(screen.getByLabelText('First Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Middle Initial')).toBeInTheDocument();
  });

  it('uses input type=number for number subFields', () => {
    const item: Item = {
      id: 'Q9',
      section: 'A',
      type: 'multi-field',
      required: true,
      label: dual('How many?'),
      subFields: [
        { id: 'Q9_1', label: dual('Years'), kind: 'number' },
        { id: 'Q9_2', label: dual('Months'), kind: 'number' },
      ],
    };
    renderWithProviders(<Harness item={item} />);
    expect(screen.getByLabelText('Years')).toHaveAttribute('type', 'number');
    expect(screen.getByLabelText('Months')).toHaveAttribute('type', 'number');
  });

  it('shows a required asterisk when required=true', () => {
    const item: Item = {
      id: 'Q1',
      section: 'A',
      type: 'short-text',
      required: true,
      label: dual('Req'),
    };
    renderWithProviders(<Harness item={item} />);
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('omits the asterisk when required=false', () => {
    const item: Item = {
      id: 'Q1',
      section: 'A',
      type: 'short-text',
      required: false,
      label: dual('Opt'),
    };
    renderWithProviders(<Harness item={item} />);
    expect(screen.queryByText('*')).toBeNull();
  });

  it('renders help text when present', () => {
    const item: Item = {
      id: 'Q11',
      section: 'A',
      type: 'number',
      required: true,
      label: dual('Hours?'),
      help: dual('full-time is 8 hours'),
    };
    renderWithProviders(<Harness item={item} />);
    expect(screen.getByText(/full-time is 8 hours/)).toBeInTheDocument();
  });
});
