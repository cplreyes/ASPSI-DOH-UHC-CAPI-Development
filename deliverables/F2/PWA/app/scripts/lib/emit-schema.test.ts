import { describe, expect, it } from 'vitest';
import { emitSchema } from './emit-schema';
import type { ParseResult } from './types';

describe('emitSchema', () => {
  it('emits a module that imports zod and exports a section schema', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'Profile',
          items: [
            {
              id: 'Q3',
              section: 'A',
              type: 'single',
              required: true,
              label: 'Sex?',
              choices: [
                { label: 'Male', value: 'Male' },
                { label: 'Female', value: 'Female' },
              ],
            },
            { id: 'Q4', section: 'A', type: 'number', required: true, label: 'Age?', min: 18 },
          ],
        },
      ],
      unsupported: [],
    };

    const code = emitSchema(result);

    expect(code).toContain("import { z } from 'zod';");
    expect(code).toContain('export const sectionASchema = z.object({');
    expect(code).toContain("Q3: z.enum(['Male', 'Female'])");
    expect(code).toContain('Q4: z.coerce.number().min(18)');
    expect(code).toContain('export type SectionAValues = z.infer<typeof sectionASchema>;');
  });

  it('emits optional() for required=false', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'A',
          items: [
            { id: 'Q1', section: 'A', type: 'short-text', required: false, label: 'Optional?' },
          ],
        },
      ],
      unsupported: [],
    };
    const code = emitSchema(result);
    expect(code).toContain('Q1: z.string().optional()');
  });

  it('emits .min(1) for required short-text', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'A',
          items: [{ id: 'Q1', section: 'A', type: 'short-text', required: true, label: 'L' }],
        },
      ],
      unsupported: [],
    };
    expect(emitSchema(result)).toContain('Q1: z.string().min(1)');
  });

  it('adds a companion _other field for single+specify items', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'A',
          items: [
            {
              id: 'Q2',
              section: 'A',
              type: 'single',
              required: true,
              hasOtherSpecify: true,
              label: 'Employment?',
              choices: [
                { label: 'Regular', value: 'Regular' },
                { label: 'Other, specify', value: 'Other, specify', isOtherSpecify: true },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const code = emitSchema(result);
    expect(code).toContain("Q2: z.enum(['Regular', 'Other, specify'])");
    expect(code).toContain('Q2_other: z.string().optional()');
  });

  it('emits number range when both min and max present', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'A',
          items: [
            {
              id: 'Q11',
              section: 'A',
              type: 'number',
              required: true,
              label: 'L',
              min: 1,
              max: 24,
            },
          ],
        },
      ],
      unsupported: [],
    };
    expect(emitSchema(result)).toContain('Q11: z.coerce.number().min(1).max(24)');
  });

  it('quotes keys that are not valid JS identifiers', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'F',
          title: 'F',
          items: [
            {
              id: 'Q62.1',
              section: 'F',
              type: 'single',
              required: true,
              label: 'L',
              choices: [
                { label: 'Yes', value: 'Yes' },
                { label: 'No', value: 'No' },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const code = emitSchema(result);
    expect(code).toContain("'Q62.1': z.enum(['Yes', 'No'])");
  });

  it('emits multi as z.array(z.enum([...])).min(1) when required', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'C',
          title: 'C',
          items: [
            {
              id: 'Q28',
              section: 'C',
              type: 'multi',
              required: true,
              label: 'Which?',
              choices: [
                { label: 'Pap smear', value: 'Pap smear' },
                { label: 'Mammogram', value: 'Mammogram' },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const code = emitSchema(result);
    expect(code).toContain("Q28: z.array(z.enum(['Pap smear', 'Mammogram'])).min(1)");
  });

  it('emits multi as optional z.array when required=false', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'C',
          title: 'C',
          items: [
            {
              id: 'Q29',
              section: 'C',
              type: 'multi',
              required: false,
              label: 'Which?',
              choices: [{ label: 'A', value: 'A' }],
            },
          ],
        },
      ],
      unsupported: [],
    };
    expect(emitSchema(result)).toContain("Q29: z.array(z.enum(['A'])).optional()");
  });

  it('adds companion _other field for multi+specify', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'B',
          title: 'B',
          items: [
            {
              id: 'Q21',
              section: 'B',
              type: 'multi',
              required: true,
              hasOtherSpecify: true,
              label: 'Which?',
              choices: [
                { label: 'Salary', value: 'Salary' },
                { label: 'Other (specify)', value: 'Other (specify)', isOtherSpecify: true },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const code = emitSchema(result);
    expect(code).toContain("Q21: z.array(z.enum(['Salary', 'Other (specify)'])).min(1)");
    expect(code).toContain('Q21_other: z.string().optional()');
  });

  it('emits an ISO-date string schema for date items', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'C',
          title: 'C',
          items: [{ id: 'Q31', section: 'C', type: 'date', required: false, label: 'When?' }],
        },
      ],
      unsupported: [],
    };
    const out = emitSchema(result);
    expect(out).toContain('Q31: z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/).optional()');
  });

  it('flattens multi-field items into per-subfield schema entries', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'A',
          items: [
            {
              id: 'Q1',
              section: 'A',
              type: 'multi-field',
              required: true,
              label: 'name',
              subFields: [
                { id: 'Q1_1', label: 'Last', kind: 'short-text' },
                { id: 'Q1_2', label: 'First', kind: 'short-text' },
              ],
            },
            {
              id: 'Q9',
              section: 'A',
              type: 'multi-field',
              required: false,
              label: 'how long',
              subFields: [
                { id: 'Q9_1', label: 'Y', kind: 'number' },
                { id: 'Q9_2', label: 'M', kind: 'number' },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const out = emitSchema(result);
    expect(out).toContain('Q1_1: z.string().min(1)');
    expect(out).toContain('Q1_2: z.string().min(1)');
    expect(out).toContain('Q9_1: z.coerce.number().optional()');
    expect(out).toContain('Q9_2: z.coerce.number().optional()');
  });

  it('emits long-text with .min(1) when required', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'C',
          title: 'C',
          items: [
            { id: 'Q36', section: 'C', type: 'long-text', required: true, label: 'What might?' },
          ],
        },
      ],
      unsupported: [],
    };
    expect(emitSchema(result)).toContain('Q36: z.string().min(1)');
  });

  it('emits a .superRefine that requires _other when parent single equals the other-specify value', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'A',
          title: 'A',
          items: [
            {
              id: 'Q2',
              section: 'A',
              type: 'single',
              required: true,
              hasOtherSpecify: true,
              label: 'Employment?',
              choices: [
                { label: 'Regular', value: 'Regular' },
                { label: 'Other, specify', value: 'Other, specify', isOtherSpecify: true },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const code = emitSchema(result);
    expect(code).toContain('.superRefine((data, ctx) => {');
    expect(code).toContain("if (data.Q2 === 'Other, specify'");
    expect(code).toContain("path: ['Q2_other']");
  });

  it('emits a .superRefine clause that uses .includes for multi+specify parents', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'B',
          title: 'B',
          items: [
            {
              id: 'Q21',
              section: 'B',
              type: 'multi',
              required: true,
              hasOtherSpecify: true,
              label: 'Which?',
              choices: [
                { label: 'Salary', value: 'Salary' },
                { label: 'Other (specify)', value: 'Other (specify)', isOtherSpecify: true },
              ],
            },
          ],
        },
      ],
      unsupported: [],
    };
    const code = emitSchema(result);
    expect(code).toContain("Array.isArray(data.Q21) && data.Q21.includes('Other (specify)')");
    expect(code).toContain("path: ['Q21_other']");
  });

  it('does not emit .superRefine when the section has no hasOtherSpecify items', () => {
    const result: ParseResult = {
      sections: [
        {
          id: 'H',
          title: 'H',
          items: [
            { id: 'Q88', section: 'H', type: 'single', required: true, label: 'L', choices: [{ label: 'A', value: 'A' }] },
          ],
        },
      ],
      unsupported: [],
    };
    expect(emitSchema(result)).not.toContain('.superRefine');
  });
});
