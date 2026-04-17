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
});
