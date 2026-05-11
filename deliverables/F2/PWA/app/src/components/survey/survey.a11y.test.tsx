import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { useForm, FormProvider } from 'react-hook-form';
import type * as React from 'react';
import { axe, AXE_COMPONENT_CONFIG } from '@/test/axe-helpers';
import { LocaleProvider } from '@/i18n/locale-context';
import type { Choice, Item } from '@/types/survey';
import { Question } from './Question';
import { MatrixQuestion } from './MatrixQuestion';

const dual = (en: string) => ({ en, fil: en });

function Wrap({ children }: { children: React.ReactNode }) {
  const methods = useForm();
  return (
    <LocaleProvider>
      <FormProvider {...methods}>
        <form>{children}</form>
      </FormProvider>
    </LocaleProvider>
  );
}

const scale5: Choice[] = [
  { label: dual('Strongly disagree'), value: '1' },
  { label: dual('Disagree'), value: '2' },
  { label: dual('Neutral'), value: '3' },
  { label: dual('Agree'), value: '4' },
  { label: dual('Strongly agree'), value: '5' },
];

describe('a11y — <Question> variants', () => {
  it('short-text has no violations', async () => {
    const item: Item = {
      id: 'Q1',
      section: 'A',
      type: 'short-text',
      required: true,
      label: dual('What is your name?'),
    };
    const { container } = render(
      <Wrap>
        <Question item={item} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('long-text has no violations', async () => {
    const item: Item = {
      id: 'Q40',
      section: 'C',
      type: 'long-text',
      required: true,
      label: dual('What might convince you?'),
    };
    const { container } = render(
      <Wrap>
        <Question item={item} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('number has no violations', async () => {
    const item: Item = {
      id: 'Q4',
      section: 'A',
      type: 'number',
      required: true,
      min: 18,
      max: 99,
      label: dual('How old are you as of your last birthday (in years)?'),
    };
    const { container } = render(
      <Wrap>
        <Question item={item} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('single radio group has no violations', async () => {
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
    const { container } = render(
      <Wrap>
        <Question item={item} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('multi checkbox group with isExclusive has no violations', async () => {
    // Mirrors Q25 (Section B) — multi with "I don't know" exclusive option
    const item: Item = {
      id: 'Q25',
      section: 'B',
      type: 'multi',
      required: true,
      label: dual('Which of the following do you expect to change in your personal work?'),
      hasOtherSpecify: true,
      choices: [
        { label: dual('Salary'), value: 'Salary' },
        { label: dual('Working hours'), value: 'Working hours' },
        { label: dual('I don\'t know'), value: 'I don\'t know', isExclusive: true },
        { label: dual('Other (specify)'), value: 'Other (specify)', isOtherSpecify: true },
      ],
    };
    const { container } = render(
      <Wrap>
        <Question item={item} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('multi checkbox group with isSelectAll + isExclusive has no violations', async () => {
    // Mirrors Q32 (Section C) — both flags
    const item: Item = {
      id: 'Q32',
      section: 'C',
      type: 'multi',
      required: true,
      label: dual('Which of the following are included in the YAKAP/Konsulta package?'),
      choices: [
        { label: dual('Pap smear'), value: 'Pap smear' },
        { label: dual('Mammogram'), value: 'Mammogram' },
        { label: dual('All of the above'), value: 'All of the above', isSelectAll: true },
        { label: dual('I don\'t know'), value: 'I don\'t know', isExclusive: true },
      ],
    };
    const { container } = render(
      <Wrap>
        <Question item={item} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('date picker has no violations', async () => {
    const item: Item = {
      id: 'QDate',
      section: 'A',
      type: 'date',
      required: true,
      label: dual('Date of interview'),
    };
    const { container } = render(
      <Wrap>
        <Question item={item} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('multi-field (Q9 year+month) has no violations', async () => {
    const item: Item = {
      id: 'Q9',
      section: 'A',
      type: 'multi-field',
      required: true,
      label: dual('How many months/years have you worked at this health facility?'),
      subFields: [
        { id: 'Q9_1', label: dual('Year(s)'), kind: 'number', min: 0, max: 60, required: true },
        { id: 'Q9_2', label: dual('Month(s)'), kind: 'number', min: 0, max: 11, required: false },
      ],
    };
    const { container } = render(
      <Wrap>
        <Question item={item} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });
});

describe('a11y — <MatrixQuestion>', () => {
  function matrixRow(id: string, label: string): Item {
    return {
      id,
      section: 'J',
      type: 'single',
      required: true,
      label: dual(label),
      choices: scale5,
    };
  }

  it('matrix grid (3 rows × 5 columns) has no violations', async () => {
    const items = [
      matrixRow('Q98', 'I am satisfied with my salary'),
      matrixRow('Q99', 'I am satisfied with my working hours'),
      matrixRow('Q100', 'I am satisfied with my workload'),
    ];
    const { container } = render(
      <Wrap>
        <MatrixQuestion items={items} choices={scale5} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('matrix grid (2 rows minimum) has no violations', async () => {
    const items = [
      matrixRow('Q120', 'fairness statement A'),
      matrixRow('Q121', 'fairness statement B'),
    ];
    const { container } = render(
      <Wrap>
        <MatrixQuestion items={items} choices={scale5} />
      </Wrap>,
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });
});
