import { describe, expect, it } from 'vitest';
import type { Item, Choice } from '@/types/survey';
import { groupVisibleItems, type MatrixGroup } from './group-matrix';

const dual = (en: string) => ({ en, fil: en });
const ch = (vals: string[]): Choice[] => vals.map((v) => ({ label: dual(v), value: v }));

const single = (id: string, choices: Choice[], extra: Partial<Item> = {}): Item => ({
  id,
  section: 'G',
  type: 'single',
  required: true,
  label: dual(`Statement ${id}`),
  choices,
  ...extra,
});

const isMatrix = (e: Item | MatrixGroup): e is MatrixGroup =>
  (e as MatrixGroup).kind === 'matrix';

describe('groupVisibleItems', () => {
  it('returns an empty array for empty input', () => {
    expect(groupVisibleItems([])).toEqual([]);
  });

  it('returns a single non-grouping item unchanged', () => {
    const items = [single('Q75', ch(['1', '2', '3', '4', '5']))];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('groups two consecutive same-choice single items into a matrix', () => {
    const choices = ch(['1', '2', '3', '4', '5']);
    const items = [single('Q75', choices), single('Q76', choices)];
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(1);
    expect(isMatrix(out[0])).toBe(true);
    if (isMatrix(out[0])) {
      expect(out[0].items).toHaveLength(2);
      expect(out[0].choices).toEqual(choices);
    }
  });

  it('keeps two single items with different choice sets separate', () => {
    const items = [
      single('Q75', ch(['1', '2', '3', '4', '5'])),
      single('Q83', ch(['Never', 'Rarely', 'Sometimes', 'Often', 'Always'])),
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('mixed sequence groups only consecutive runs >= 2', () => {
    const ch15 = ch(['1', '2', '3', '4', '5']);
    const items: Item[] = [
      single('Q75', ch15),
      single('Q76', ch15),
      { ...single('Qmulti', ch15), type: 'multi' as const },
      single('Q80', ch15),
    ];
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(3);
    expect(isMatrix(out[0])).toBe(true);
    expect(isMatrix(out[1])).toBe(false);
    expect(isMatrix(out[2])).toBe(false);
  });

  it('does not group items with hasOtherSpecify = true', () => {
    const choices = ch(['1', '2', '3', '4', '5']);
    const items = [
      single('Q75', choices, { hasOtherSpecify: true }),
      single('Q76', choices, { hasOtherSpecify: true }),
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('does not group items if choices differ in order', () => {
    const items = [
      single('Q1', ch(['Yes', 'No'])),
      single('Q2', ch(['No', 'Yes'])),
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('does not group items if choices differ in length', () => {
    const items = [
      single('Q1', ch(['1', '2', '3', '4', '5'])),
      single('Q2', ch(['1', '2', '3'])),
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });

  it('groups by value only (label translations may differ)', () => {
    const a: Choice[] = [
      { label: { en: 'Yes', fil: 'Oo' }, value: 'Yes' },
      { label: { en: 'No', fil: 'Hindi' }, value: 'No' },
    ];
    const b: Choice[] = [
      { label: { en: 'Yes', fil: 'Oo' }, value: 'Yes' },
      { label: { en: 'No', fil: 'Hindi' }, value: 'No' },
    ];
    const items = [single('Q1', a), single('Q2', b)];
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(1);
    expect(isMatrix(out[0])).toBe(true);
  });

  it('groups a long realistic Likert cluster (Q75-Q81)', () => {
    const ch15 = ch(['1', '2', '3', '4', '5']);
    const items = ['Q75', 'Q76', 'Q77', 'Q78', 'Q79', 'Q80', 'Q81'].map((id) =>
      single(id, ch15),
    );
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(1);
    if (isMatrix(out[0])) {
      expect(out[0].items.map((i) => i.id)).toEqual([
        'Q75',
        'Q76',
        'Q77',
        'Q78',
        'Q79',
        'Q80',
        'Q81',
      ]);
    }
  });

  it('groups Section J Agreement battery (5 statements, same scale)', () => {
    const agreement = ch([
      'Strongly Agree',
      'Agree',
      'Neither Agree nor Disagree',
      'Disagree',
      'Strongly Disagree',
    ]);
    const items = ['Q108', 'Q109', 'Q110', 'Q111', 'Q112'].map((id) =>
      single(id, agreement),
    );
    const out = groupVisibleItems(items);
    expect(out).toHaveLength(1);
  });

  it('does not group multi-field items', () => {
    const items: Item[] = [
      {
        id: 'Q9',
        section: 'A',
        type: 'multi-field',
        required: true,
        label: dual('How long?'),
        subFields: [
          { id: 'Q9_1', label: dual('Years'), kind: 'number' },
          { id: 'Q9_2', label: dual('Months'), kind: 'number' },
        ],
      },
      {
        id: 'Q10',
        section: 'A',
        type: 'multi-field',
        required: true,
        label: dual('How long?'),
        subFields: [
          { id: 'Q10_1', label: dual('Years'), kind: 'number' },
          { id: 'Q10_2', label: dual('Months'), kind: 'number' },
        ],
      },
    ];
    expect(groupVisibleItems(items)).toEqual(items);
  });
});
