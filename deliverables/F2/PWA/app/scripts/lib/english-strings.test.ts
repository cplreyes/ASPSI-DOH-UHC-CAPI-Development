import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { collectEnglishStrings } from './english-strings';
import { parseSpec } from './parse-spec';
import type { ParseResult } from './types';

const base: ParseResult = {
  sections: [
    {
      id: 'A',
      title: { en: 'Profile' },
      preamble: { en: 'Intro' },
      items: [
        {
          id: 'Q1', section: 'A', type: 'single', required: true,
          label: { en: 'Yes or no?' },
          help: { en: 'Tick one' },
          preamble: { en: 'NOT LOCALIZED' },
          inputLabel: { en: 'ALSO NOT LOCALIZED' },
          choices: [
            { label: { en: 'Yes' }, value: 'Yes' },
            { label: { en: 'No' }, value: 'No' },
          ],
        },
        {
          id: 'Q2', section: 'A', type: 'multi-field', required: true,
          label: { en: 'Yes or no?' },
          subFields: [{ id: 'Q2_1', label: { en: 'Yes' }, kind: 'short-text' }],
        },
      ],
    },
  ],
  unsupported: [],
};

describe('collectEnglishStrings', () => {
  it('collects exactly the six fields applyTranslations localizes, unique, in first-appearance order', () => {
    const out = collectEnglishStrings(base);
    expect(out.map((e) => e.text)).toEqual(['Profile', 'Intro', 'Yes or no?', 'Tick one', 'Yes', 'No']);
    expect(out.map((e) => e.text)).not.toContain('NOT LOCALIZED');
    expect(out.map((e) => e.text)).not.toContain('ALSO NOT LOCALIZED');
  });

  it('merges kinds and ids when the same English recurs', () => {
    const yes = collectEnglishStrings(base).find((e) => e.text === 'Yes')!;
    expect(yes.kinds).toEqual(['choice.label', 'subField.label']);
    expect(yes.ids).toEqual(['Q1', 'Q2_1']);
    const stem = collectEnglishStrings(base).find((e) => e.text === 'Yes or no?')!;
    expect(stem.ids).toEqual(['Q1', 'Q2']);
  });

  it('real spec: unique English string count is stable (snapshot = the Aug-21 anchor universe)', () => {
    const md = readFileSync(resolve(__dirname, '../../spec/F2-Spec.md'), 'utf-8');
    const out = collectEnglishStrings(parseSpec(md));
    expect(out.length).toMatchSnapshot();
    expect(out.length).toBeGreaterThan(100);
  });
});
