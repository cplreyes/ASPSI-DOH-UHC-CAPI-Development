import { describe, expect, it } from 'vitest';
import { splitSections, parseTableRows } from './parse-spec';

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
