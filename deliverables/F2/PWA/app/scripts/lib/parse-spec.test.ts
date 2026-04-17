import { describe, expect, it } from 'vitest';
import { splitSections } from './parse-spec';

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
