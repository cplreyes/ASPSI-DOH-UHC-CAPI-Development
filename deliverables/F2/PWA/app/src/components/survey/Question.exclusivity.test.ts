import { describe, expect, it } from 'vitest';
import { nextMultiValue } from './Question';

const choices = [
  { value: 'Salary' },
  { value: 'Number of patients' },
  { value: 'Working hours' },
  { value: "I don't know", isExclusive: true },
  { value: 'Other (specify)', isOtherSpecify: true },
] as const;

const choicesWithSelectAll = [
  { value: 'Pap smear' },
  { value: 'Mammogram' },
  { value: 'Lipid profile' },
  { value: 'All of the above', isSelectAll: true },
  { value: "I don't know", isExclusive: true },
] as const;

describe('nextMultiValue — exclusivity ("I don\'t know") rules', () => {
  it('checking the exclusive option clears all other selections', () => {
    const next = nextMultiValue(
      ['Salary', 'Working hours'],
      choices.find((c) => c.value === "I don't know")!,
      true,
      choices,
    );
    expect(next).toEqual(["I don't know"]);
  });

  it('checking a regular option while exclusive is selected clears the exclusive', () => {
    const next = nextMultiValue(
      ["I don't know"],
      choices.find((c) => c.value === 'Salary')!,
      true,
      choices,
    );
    expect(next).toEqual(['Salary']);
  });

  it('unchecking the exclusive option leaves the array empty (or at least without it)', () => {
    const next = nextMultiValue(
      ["I don't know"],
      choices.find((c) => c.value === "I don't know")!,
      false,
      choices,
    );
    expect(next).not.toContain("I don't know");
  });

  it('checking exclusive does not clear an already-typed Other-specify value', () => {
    // The Other (specify) option's value gets added to the array when checked;
    // after exclusive is clicked, only the exclusive value remains.
    const next = nextMultiValue(
      ['Salary', 'Other (specify)'],
      choices.find((c) => c.value === "I don't know")!,
      true,
      choices,
    );
    // Per spec: exclusive overrides everything in the multi-select array.
    // The companion text field `_other` lives outside this array and stays.
    expect(next).toEqual(["I don't know"]);
  });
});

describe('nextMultiValue — select-all ("All of the above") rules', () => {
  it('checking the select-all option auto-selects every non-exclusive non-otherSpecify choice', () => {
    const next = nextMultiValue(
      [],
      choicesWithSelectAll.find((c) => c.value === 'All of the above')!,
      true,
      choicesWithSelectAll,
    );
    expect(next).toEqual(['Pap smear', 'Mammogram', 'Lipid profile', 'All of the above']);
    expect(next).not.toContain("I don't know");
  });

  it('unchecking the select-all option clears the auto-selected values', () => {
    const next = nextMultiValue(
      ['Pap smear', 'Mammogram', 'Lipid profile', 'All of the above'],
      choicesWithSelectAll.find((c) => c.value === 'All of the above')!,
      false,
      choicesWithSelectAll,
    );
    expect(next).toEqual([]);
  });

  it('unchecking a regular option while select-all is selected clears the select-all', () => {
    const next = nextMultiValue(
      ['Pap smear', 'Mammogram', 'Lipid profile', 'All of the above'],
      choicesWithSelectAll.find((c) => c.value === 'Mammogram')!,
      false,
      choicesWithSelectAll,
    );
    expect(next).toEqual(['Pap smear', 'Lipid profile']);
    expect(next).not.toContain('All of the above');
  });

  it('checking the exclusive option overrides select-all', () => {
    const next = nextMultiValue(
      ['Pap smear', 'Mammogram', 'Lipid profile', 'All of the above'],
      choicesWithSelectAll.find((c) => c.value === "I don't know")!,
      true,
      choicesWithSelectAll,
    );
    expect(next).toEqual(["I don't know"]);
  });

  it('checking select-all overrides a previously-checked exclusive', () => {
    const next = nextMultiValue(
      ["I don't know"],
      choicesWithSelectAll.find((c) => c.value === 'All of the above')!,
      true,
      choicesWithSelectAll,
    );
    expect(next).toEqual(['Pap smear', 'Mammogram', 'Lipid profile', 'All of the above']);
  });
});

describe('nextMultiValue — regular options', () => {
  it('checking a regular option appends to the array', () => {
    const next = nextMultiValue(
      ['Salary'],
      choices.find((c) => c.value === 'Working hours')!,
      true,
      choices,
    );
    expect(next).toEqual(['Salary', 'Working hours']);
  });

  it('unchecking a regular option removes it from the array', () => {
    const next = nextMultiValue(
      ['Salary', 'Working hours'],
      choices.find((c) => c.value === 'Salary')!,
      false,
      choices,
    );
    expect(next).toEqual(['Working hours']);
  });

  it('checking the same regular option twice keeps it once (idempotent)', () => {
    const next = nextMultiValue(
      ['Salary'],
      choices.find((c) => c.value === 'Salary')!,
      true,
      choices,
    );
    expect(next).toEqual(['Salary']);
  });
});
