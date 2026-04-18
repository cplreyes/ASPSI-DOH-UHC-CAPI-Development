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

  it('collects rows from multiple pdf_q tables in the same section body (Section J shape)', () => {
    const body = [
      '**Grid #1:**',
      '',
      '| pdf_q | type | required | label (verbatim) | gf_risk |',
      '|---|---|---|---|---|',
      '| Q88 | grid-single | Y | I am compensated fairly. | OK |',
      '',
      '**Open/closed items between grids:**',
      '',
      '| pdf_q | legacy_q | type | required | label (verbatim) | choices / notes | skip | gf_risk |',
      '|---|---|---|---|---|---|---|---|',
      '| Q98 | Q62 | long-text | Y | In addition to your salary, what other benefits? | — | — | OK |',
      '',
      '**Closing items:**',
      '',
      '| pdf_q | legacy_q | type | required | label (verbatim) | choices / notes | skip | gf_risk |',
      '|---|---|---|---|---|---|---|---|',
      '| Q112 | Q70 | single | Y | Have you considered leaving? | Yes · No | No → end | SECTION |',
    ].join('\n');

    const rows = parseTableRows(body);
    expect(rows.map((r) => r.pdf_q)).toEqual(['Q88', 'Q98', 'Q112']);
    expect(rows[1].type).toBe('long-text');
    expect(rows[2].choices).toBe('Yes · No');
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

  it('parses "short-text ×3" as multi-field with three short-text subfields', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q1',
        legacy_q: 'Q1',
        type: 'short-text ×3',
        required: 'Y',
        label: 'What is your name?',
        choices: 'Last Name / First Name / Middle Initial',
      },
      'A',
    );
    expect(result.unsupported).toBeUndefined();
    expect(result.item).toMatchObject({
      id: 'Q1',
      type: 'multi-field',
      subFields: [
        { id: 'Q1_1', label: 'Last Name', kind: 'short-text' },
        { id: 'Q1_2', label: 'First Name', kind: 'short-text' },
        { id: 'Q1_3', label: 'Middle Initial', kind: 'short-text' },
      ],
    });
  });

  it('parses "number ×2" as multi-field with two number subfields', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q9',
        legacy_q: 'Q13',
        type: 'number ×2',
        required: 'Y',
        label: 'How many?',
        choices: 'Year(s) / Month(s)',
      },
      'A',
    );
    expect(result.item).toMatchObject({
      id: 'Q9',
      type: 'multi-field',
      subFields: [
        { id: 'Q9_1', label: 'Year(s)', kind: 'number' },
        { id: 'Q9_2', label: 'Month(s)', kind: 'number' },
      ],
    });
  });

  it('treats "single (1–5)" as a single with auto-generated 1..5 numeric choices', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q68',
        legacy_q: '—',
        type: 'single (1–5)',
        required: 'Y',
        label: 'How adequate is your fee?',
        choices: '1 · 2 · 3 · 4 · 5',
      },
      'G',
    );
    expect(result.unsupported).toBeUndefined();
    expect(result.item).toMatchObject({
      id: 'Q68',
      type: 'single',
      choices: [
        { label: '1', value: '1' },
        { label: '2', value: '2' },
        { label: '3', value: '3' },
        { label: '4', value: '4' },
        { label: '5', value: '5' },
      ],
    });
  });

  it('parses "multi" as multi-select with choices', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q28',
        legacy_q: 'Q34',
        type: 'multi',
        required: 'Y',
        label: 'Which are included in the package?',
        choices: 'Pap smear · Mammogram · Lipid profile',
      },
      'C',
    );
    expect(result.unsupported).toBeUndefined();
    expect(result.item).toMatchObject({
      id: 'Q28',
      type: 'multi',
      hasOtherSpecify: false,
      choices: [
        { label: 'Pap smear', value: 'Pap smear' },
        { label: 'Mammogram', value: 'Mammogram' },
        { label: 'Lipid profile', value: 'Lipid profile' },
      ],
    });
  });

  it('parses "multi + specify" with the Other choice flagged', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q21',
        legacy_q: 'Q28',
        type: 'multi + specify',
        required: 'Y',
        label: 'Which do you expect to change?',
        choices: 'Salary · Working hours · Other (specify)',
      },
      'B',
    );
    expect(result.item).toMatchObject({
      id: 'Q21',
      type: 'multi',
      hasOtherSpecify: true,
    });
    expect(result.item?.choices?.find((c) => c.isOtherSpecify)).toMatchObject({
      label: 'Other (specify)',
    });
  });

  it('parses "date" as a date item', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q31',
        legacy_q: '—',
        type: 'date',
        required: 'conditional',
        label: 'Since when?',
        choices: 'Month / Day / Year',
      },
      'C',
    );
    expect(result.unsupported).toBeUndefined();
    expect(result.item).toMatchObject({ id: 'Q31', type: 'date', required: false });
  });

  it('treats "grid-single" as a single with the inline choice set', () => {
    const result = normalizeRow(
      {
        pdf_q: 'Q74',
        legacy_q: '—',
        type: 'grid-single',
        required: 'Y',
        label: 'How often do you charge?',
        choices: 'Never · Rarely · Sometimes · Often · Always',
      },
      'G',
    );
    expect(result.unsupported).toBeUndefined();
    expect(result.item).toMatchObject({
      id: 'Q74',
      type: 'single',
      choices: [
        { label: 'Never', value: 'Never' },
        { label: 'Rarely', value: 'Rarely' },
        { label: 'Sometimes', value: 'Sometimes' },
        { label: 'Often', value: 'Often' },
        { label: 'Always', value: 'Always' },
      ],
    });
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

  it('strips the `help: "..."` wrapper from help text', () => {
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
    expect(result.item?.help).toBe('full-time is 8 hours per day');
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

  it('resolves "same choice set as QN" references to the referenced item\'s choices', () => {
    const md = [
      '# F2 Spec',
      '',
      '## Section B — UHC Awareness',
      '',
      '| pdf_q | legacy_q | type | required | label (verbatim) | choices / notes | gate | skip | gf_risk |',
      '|---|---|---|---|---|---|---|---|---|',
      '| Q13 | Q22 | single + specify | Y | Equipment implemented? | Yes, direct · Yes, pre-existing · No · I don\'t know | — | — | OK |',
      '| Q15 | — | single + specify | Y | Supplies implemented? | *(same choice set as Q13)* | — | — | OK |',
      '| Q17 | Q23 | single + specify | Y | EMR implemented? | _(same choice set as Q13)_ | — | — | OK |',
    ].join('\n');

    const result = parseSpec(md);
    const items = result.sections[0].items;
    const q13 = items.find((i) => i.id === 'Q13');
    const q15 = items.find((i) => i.id === 'Q15');
    const q17 = items.find((i) => i.id === 'Q17');

    expect(q13?.choices?.map((c) => c.label)).toEqual([
      'Yes, direct',
      'Yes, pre-existing',
      'No',
      "I don't know",
    ]);
    expect(q15?.choices?.map((c) => c.label)).toEqual(q13?.choices?.map((c) => c.label));
    expect(q17?.choices?.map((c) => c.label)).toEqual(q13?.choices?.map((c) => c.label));
  });
});
