import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useForm, FormProvider } from 'react-hook-form';
import type { Item } from '@/types/survey';
import { Question } from './Question';

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
      label: 'What is your name?',
    };
    render(<Harness item={item} />);
    expect(screen.getByLabelText(/What is your name\?/)).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveAttribute('type', 'text');
  });

  it('renders long-text as a textarea', () => {
    const item: Item = {
      id: 'Q36',
      section: 'C',
      type: 'long-text',
      required: true,
      label: 'What might convince you?',
    };
    render(<Harness item={item} />);
    expect(screen.getByLabelText(/What might convince you/)).toBeInstanceOf(HTMLTextAreaElement);
  });

  it('renders number as a numeric input with min/max', () => {
    const item: Item = {
      id: 'Q11',
      section: 'A',
      type: 'number',
      required: true,
      label: 'Hours per day?',
      min: 1,
      max: 24,
    };
    render(<Harness item={item} />);
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
      label: 'What is your sex at birth?',
      choices: [
        { label: 'Male', value: 'Male' },
        { label: 'Female', value: 'Female' },
      ],
    };
    render(<Harness item={item} />);
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
      label: 'Employment?',
      hasOtherSpecify: true,
      choices: [
        { label: 'Regular', value: 'Regular' },
        { label: 'Other, specify', value: 'Other, specify', isOtherSpecify: true },
      ],
    };
    render(<Harness item={item} />);

    expect(screen.queryByLabelText(/Please specify/)).toBeNull();

    await user.click(screen.getByLabelText('Other, specify'));
    expect(screen.getByLabelText(/Please specify/)).toBeInTheDocument();
  });

  it('shows a required asterisk when required=true', () => {
    const item: Item = {
      id: 'Q1',
      section: 'A',
      type: 'short-text',
      required: true,
      label: 'Req',
    };
    render(<Harness item={item} />);
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('omits the asterisk when required=false', () => {
    const item: Item = {
      id: 'Q1',
      section: 'A',
      type: 'short-text',
      required: false,
      label: 'Opt',
    };
    render(<Harness item={item} />);
    expect(screen.queryByText('*')).toBeNull();
  });

  it('renders help text when present', () => {
    const item: Item = {
      id: 'Q11',
      section: 'A',
      type: 'number',
      required: true,
      label: 'Hours?',
      help: 'full-time is 8 hours',
    };
    render(<Harness item={item} />);
    expect(screen.getByText(/full-time is 8 hours/)).toBeInTheDocument();
  });
});
