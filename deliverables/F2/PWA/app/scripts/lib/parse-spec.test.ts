import { describe, expect, it } from 'vitest';
import { splitSections, parseTableRows, normalizeRow, parseSpec } from './parse-spec';

describe('splitSections', () => {
  it('extracts section headers and bodies', () => {
    const md = [
      '# Top title',
      '',
      'Intro text',
      '',
      '## Section A — Healthcare Worker Profile',
      '',
      '> *Preamble:* "A preamble"',
      '',
      '| pdf_q | type |',
      '|---|---|',
      '| Q1 | single |',
      '',
      '---',
      '',
      '## Section B — UHC Awareness',
      '',
      '| pdf_q | type |',
      '|---|---|',
      '| Q12 | single |',
    ].join('\n');

    const sections = splitSections(md);

    expect(sections).toHaveLength(2);
    expect(sections[0]).toMatchObject({
      id: 'A',
      title: 'Healthcare Worker Profile',
    });
    expect(sections[0].body).toContain('Q1 | single');
    expect(sections[1]).toMatchObject({
      id: 'B',
      title: 'UHC Awareness',
    });
    expect(sections[1].body).toContain('Q12 | single');
  });

  it('returns empty array when no sections match', () => {
    expect(splitSections('# just a title\n\nno sections here')).toEqual([]);
  });

  it('handles a single section', () => {
    const md = ['## Section A — Only one', '', 'body content'].join('\n');
    const sections = splitSections(md);
    expect(sections).toHaveLength(1);
    expect(sections[0].id).toBe('A');
    expect(sections[0].title).toBe('Only one');
    expect(sections[0].body).toContain('body content');
  });
});

describe('parseTableRows', () => {
  it('extracts rows from a 9-column table (Section A shape)', () => {
    const body = [
      '> *Preamble:* "A preamble"',
      '',
      '| pdf_q | legacy_q | type | required | label (verbatim) | choices / notes | gate | skip | gf_risk |',
      '|---|---|---|---|---|---|---|---|---|',
      '| Q3 | Q3 | single | Y | What is your sex at birth? | Male · Female | — | — | OK |',
      '| Q4 | Q4 | number | Y | How old are you? | integer, min 18 | — | — | OK |',
    ].join('\n');

    const rows = parseTableRows(body);

    expect(rows).toHaveLength(2);
    expect(rows[0]).toMatchObject({
      pdf_q: 'Q3',
      legacy_q: 'Q3',
      type: 'single',
      required: 'Y',
      label: 'What is your sex at birth?',
      choices: 'Male · Female',
    });
    expect(rows[1]).toMatchObject({
      pdf_q: 'Q4',
      type: 'number',
      label: 'How old are you?',
      choices: 'integer, min 18',
    });
  });

  it('extracts rows from an 8-column table (Section C+ shape, no gate column)', () => {
    const body = [
      '| pdf_q | legacy_q | type | required | label (verbatim) | choices / notes | skip | gf_risk |',
      '|---|---|---|---|---|---|---|---|',
      '| Q27 | Q33 | single | Y | Have you heard of YAKAP? | Yes · No | No → Q37 | SECTION |',
    ].join('\n');

    const rows = parseTableRows(body);

    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      pdf_q: 'Q27',
      type: 'single',
      label: 'Have you heard of YAKAP?',
      choices: 'Yes · No',
    });
  });

  it('returns empty array when no table is present', () => {
    expect(parseTableRows('just some prose, no table')).toEqual([]);
  });

  it('ignores non-item rows (empty, alignment-only)', () => {
    const body = [
      '| pdf_q | type | label |',
      '|---|---|---|',
      '| Q1 | single | Name? |',
      '|  |  |  |',
    ].join('\n');

    const rows = parseTableRows(body);
    expect(rows).toHaveLength(1);
    expect(rows[0].pdf_q).toBe('Q1');
  });
});

describe('normalizeRow', () => {
  it('parses a single-choice row with 2 options', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q3',
        legacy_q: 'Q3',
        type: 'single',
        required: 'Y',
        label: 'What is your sex at birth?',
        choices: 'Male · Female',
      },
      'A',
    );
    expect(result.item).toMatchObject({
      id: 'Q3',
      legacyId: 'Q3',
      section: 'A',
      type: 'single',
      required: true,
      label: 'What is your sex at birth?',
      hasOtherSpecify: false,
    });
    expect(result.item?.choices).toEqual([
      { label: 'Male', value: 'Male' },
      { label: 'Female', value: 'Female' },
    ]);
    expect(result.unsupported).toBeUndefined();
  });

  it('parses a single+specify row and marks hasOtherSpecify', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q2',
        type: 'single + specify',
        required: 'Y',
        label: 'What type of employment?',
        choices: 'Regular · Casual · Other, specify',
      },
      'A',
    );
    expect(result.item?.type).toBe('single');
    expect(result.item?.hasOtherSpecify).toBe(true);
    expect(result.item?.choices?.map((c) => c.label)).toEqual([
      'Regular',
      'Casual',
      'Other, specify',
    ]);
    expect(result.item?.choices?.[2].isOtherSpecify).toBe(true);
  });

  it('parses a number row with integer min/max from choices hint', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q4',
        type: 'number',
        required: 'Y',
        label: 'How old are you?',
        choices: 'integer, min 18',
      },
      'A',
    );
    expect(result.item).toMatchObject({
      type: 'number',
      min: 18,
    });
    expect(result.item?.max).toBeUndefined();
  });

  it('parses number with range like "integer 1–24"', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q11',
        type: 'number',
        required: 'Y',
        label: 'Hours per day?',
        choices: 'integer 1–24',
      },
      'A',
    );
    expect(result.item?.min).toBe(1);
    expect(result.item?.max).toBe(24);
  });

  it('parses short-text', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q30',
        type: 'short-text',
        required: 'N',
        label: 'Specify:',
        choices: '',
      },
      'A',
    );
    expect(result.item?.type).toBe('short-text');
    expect(result.item?.required).toBe(false);
  });

  it('parses long-text', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q36',
        type: 'long-text',
        required: 'Y',
        label: 'What would convince you?',
        choices: '',
      },
      'C',
    );
    expect(result.item?.type).toBe('long-text');
  });

  it('treats "conditional" required as false (M3 handles conditional show/hide)', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q8',
        type: 'single + specify',
        required: 'conditional',
        label: 'How do you divide your time?',
        choices: 'All private · Equally · Other, specify',
      },
      'A',
    );
    expect(result.item?.required).toBe(false);
  });

  it('flags ×N multi-field items as unsupported', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q1',
        type: 'short-text ×3',
        required: 'Y',
        label: 'What is your name?',
        choices: 'Last Name / First Name / Middle Initial',
      },
      'A',
    );
    expect(result.item).toBeUndefined();
    expect(result.unsupported).toMatchObject({
      id: 'Q1',
      section: 'A',
      rawType: 'short-text ×3',
    });
  });

  it('flags multi-choice items as unsupported (M6)', () => {
    const result = normalizeRow(
      { pdf_q: 'Q21', type: 'multi + specify', required: 'Y', label: 'Which?', choices: 'A · B' },
      'B',
    );
    expect(result.item).toBeUndefined();
    expect(result.unsupported?.rawType).toBe('multi + specify');
  });

  it('flags date/grid items as unsupported (M6)', () => {
    expect(
      normalizeRow({ pdf_q: 'Q31', type: 'date', required: 'N', label: 'When?' }, 'C').unsupported,
    ).toBeDefined();
    expect(
      normalizeRow(
        { pdf_q: 'Q60', type: 'grid-single', required: 'N', label: 'Grid' },
        'G',
      ).unsupported,
    ).toBeDefined();
  });

  it('captures help text after semicolon in choices', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q11',
        type: 'number',
        required: 'Y',
        label: 'Hours per day?',
        choices: 'integer 1–24; help: "full-time is 8 hours per day"',
      },
      'A',
    );
    expect(result.item?.help).toContain('full-time is 8 hours per day');
  });
});

describe('parseSpec (integration)', () => {
  it('parses a minimal spec with one section and 2 items', () => {
    const md = [
      '# F2 Spec',
      '',
      '## Section A — Healthcare Worker Profile',
      '',
      '| pdf_q | legacy_q | type | required | label (verbatim) | choices / notes | gate | skip | gf_risk |',
      '|---|---|---|---|---|---|---|---|---|',
      '| Q3 | Q3 | single | Y | What is your sex at birth? | Male · Female | — | — | OK |',
      '| Q4 | Q4 | number | Y | How old are you? | integer, min 18 | — | — | OK |',
    ].join('\n');

    const result = parseSpec(md);

    expect(result.sections).toHaveLength(1);
    expect(result.sections[0].items).toHaveLength(2);
    expect(result.sections[0].items[0].id).toBe('Q3');
    expect(result.sections[0].items[1].min).toBe(18);
    expect(result.unsupported).toEqual([]);
  });
});
