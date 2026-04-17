export interface RawSection {
  id: string;
  title: string;
  body: string;
}

const SECTION_HEADER = /^## Section ([A-Z0-9]+(?:[0-9])?) — (.+?)\s*$/gm;

export function splitSections(markdown: string): RawSection[] {
  const sections: RawSection[] = [];
  const matches = [...markdown.matchAll(SECTION_HEADER)];

  for (let i = 0; i < matches.length; i++) {
    const current = matches[i];
    const next = matches[i + 1];
    const startIdx = (current.index ?? 0) + current[0].length;
    const endIdx = next ? (next.index ?? markdown.length) : markdown.length;
    const body = markdown.slice(startIdx, endIdx).trim();

    sections.push({
      id: current[1],
      title: current[2].trim(),
      body,
    });
  }

  return sections;
}

export type RowFields = Record<string, string>;

const TABLE_HEADER = /^\|(.+)\|\s*$/;
const ALIGNMENT_ROW = /^\|[\s\-|:]+\|\s*$/;

function splitCells(line: string): string[] {
  return line
    .replace(/^\||\|$/g, '')
    .split('|')
    .map((c) => c.trim());
}

function normalizeHeader(header: string): string {
  if (header.startsWith('label')) return 'label';
  if (header.startsWith('choices')) return 'choices';
  return header;
}

export function parseTableRows(body: string): RowFields[] {
  const lines = body.split('\n');
  let headerIdx = -1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const next = lines[i + 1];
    if (TABLE_HEADER.test(line) && next && ALIGNMENT_ROW.test(next)) {
      const firstCell = splitCells(line)[0];
      if (firstCell === 'pdf_q') {
        headerIdx = i;
        break;
      }
    }
  }

  if (headerIdx === -1) return [];

  const header = splitCells(lines[headerIdx]);
  const rows: RowFields[] = [];

  for (let i = headerIdx + 2; i < lines.length; i++) {
    const line = lines[i];
    if (!TABLE_HEADER.test(line)) break;
    const cells = splitCells(line);
    if (!cells[0] || !/^Q\d+/.test(cells[0])) continue;

    const row: RowFields = {};
    header.forEach((col, idx) => {
      row[normalizeHeader(col)] = cells[idx] ?? '';
    });
    rows.push(row);
  }

  return rows;
}
