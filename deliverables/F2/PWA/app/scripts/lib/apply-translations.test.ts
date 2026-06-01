import { describe, expect, it } from 'vitest';
import { applyTranslations, localizeString, type TranslationMaps } from './apply-translations';
import type { ParseResult } from './types';

const MAPS: TranslationMaps = {
  fil: { Yes: 'Oo', 'What is your name?': 'Ano ang pangalan mo?' },
  ceb: { Yes: 'Oo' },
  ilo: { Yes: 'Wen' },
  bis: {},
  hil: {},
  war: {},
  bcl: {},
};

describe('localizeString', () => {
  it('attaches only the dialects that have a non-empty translation', () => {
    expect(localizeString({ en: 'Yes' }, MAPS)).toEqual({ en: 'Yes', fil: 'Oo', ceb: 'Oo', ilo: 'Wen' });
  });

  it('leaves a string English-only when no dialect has it', () => {
    expect(localizeString({ en: 'Untranslated' }, MAPS)).toEqual({ en: 'Untranslated' });
  });

  it('preserves the English source even when dialects are present', () => {
    expect(localizeString({ en: 'What is your name?' }, MAPS)).toEqual({
      en: 'What is your name?',
      fil: 'Ano ang pangalan mo?',
    });
  });
});

describe('applyTranslations', () => {
  const base: ParseResult = {
    sections: [
      {
        id: 'A',
        title: { en: 'Profile' },
        preamble: { en: 'Intro' },
        items: [
          {
            id: 'Q1',
            section: 'A',
            type: 'single',
            required: true,
            label: { en: 'What is your name?' },
            help: { en: 'Untranslated' },
            choices: [{ label: { en: 'Yes' }, value: 'Yes' }],
            subFields: [{ id: 'Q1_1', label: { en: 'Yes' }, kind: 'short-text' }],
          },
        ],
      },
    ],
    unsupported: [],
  };

  it('enriches labels, choices, and subfields without mutating the input', () => {
    const out = applyTranslations(base, MAPS);
    const item = out.sections[0].items[0];
    expect(item.label).toEqual({ en: 'What is your name?', fil: 'Ano ang pangalan mo?' });
    expect(item.help).toEqual({ en: 'Untranslated' }); // not in any map → English-only
    expect(item.choices?.[0].label).toEqual({ en: 'Yes', fil: 'Oo', ceb: 'Oo', ilo: 'Wen' });
    expect(item.subFields?.[0].label).toEqual({ en: 'Yes', fil: 'Oo', ceb: 'Oo', ilo: 'Wen' });
    // input untouched
    expect(base.sections[0].items[0].label).toEqual({ en: 'What is your name?' });
  });

  it('preserves choice value codes (never localized)', () => {
    const out = applyTranslations(base, MAPS);
    expect(out.sections[0].items[0].choices?.[0].value).toBe('Yes');
  });
});
