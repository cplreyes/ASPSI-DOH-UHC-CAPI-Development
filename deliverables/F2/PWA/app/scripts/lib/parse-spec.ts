import type { Item, ParseResult, Section, UnsupportedItem, ItemType, Choice } from './types';

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

const SUPPORTED_TYPES: Record<string, ItemType> = {
  single: 'single',
  'single + specify': 'single',
  'short-text': 'short-text',
  'long-text': 'long-text',
  number: 'number',
};

const CHOICE_SEP = /\s*·\s*/;

export interface NormalizeRowResult {
  item?: Item;
  unsupported?: UnsupportedItem;
}

export function normalizeRow(row: RowFields, section: string): NormalizeRowResult {
  const rawType = (row.type ?? '').trim();

  if (!(rawType in SUPPORTED_TYPES)) {
    return {
      unsupported: {
        id: row.pdf_q,
        section,
        rawType,
        reason: unsupportedReason(rawType),
      },
    };
  }

  const type = SUPPORTED_TYPES[rawType];
  const hasOtherSpecify = rawType.includes('+ specify');
  const required = (row.required ?? '').trim() === 'Y';

  const { help, choicesText, min, max } = parseChoicesColumn(row.choices ?? '', type);

  const item: Item = {
    id: row.pdf_q,
    section,
    type,
    required,
    label: row.label ?? '',
  };

  if (row.legacy_q && row.legacy_q !== '—' && row.legacy_q !== '') {
    item.legacyId = row.legacy_q;
  }
  if (help) item.help = help;
  if (min !== undefined) item.min = min;
  if (max !== undefined) item.max = max;

  if (type === 'single') {
    item.hasOtherSpecify = hasOtherSpecify;
    const choices = parseChoiceList(choicesText, hasOtherSpecify);
    if (choices) item.choices = choices;
  }

  return { item };
}

export function parseSpec(markdown: string): ParseResult {
  const sections: Section[] = [];
  const unsupported: UnsupportedItem[] = [];

  for (const raw of splitSections(markdown)) {
    const preamble = extractPreamble(raw.body);
    const rows = parseTableRows(raw.body);
    const items: Item[] = [];

    for (const row of rows) {
      const normalized = normalizeRow(row, raw.id);
      if (normalized.item) items.push(normalized.item);
      if (normalized.unsupported) unsupported.push(normalized.unsupported);
    }

    sections.push({
      id: raw.id,
      title: raw.title,
      ...(preamble ? { preamble } : {}),
      items,
    });
  }

  return { sections, unsupported };
}

function parseChoicesColumn(
  raw: string,
  type: ItemType,
): { help?: string; choicesText: string; min?: number; max?: number } {
  const trimmed = raw.trim();
  if (!trimmed || trimmed === '—') return { choicesText: '' };

  const semiIdx = trimmed.indexOf(';');
  const head = semiIdx >= 0 ? trimmed.slice(0, semiIdx).trim() : trimmed;
  const tail = semiIdx >= 0 ? trimmed.slice(semiIdx + 1).trim() : '';

  const result: { help?: string; choicesText: string; min?: number; max?: number } = {
    choicesText: head,
  };
  if (tail) result.help = tail;

  if (type === 'number') {
    const rangeMatch = head.match(/(\d+)\s*[–-]\s*(\d+)/);
    if (rangeMatch) {
      result.min = Number(rangeMatch[1]);
      result.max = Number(rangeMatch[2]);
    } else {
      const minMatch = head.match(/min\s+(\d+)/i);
      if (minMatch) result.min = Number(minMatch[1]);
      const maxMatch = head.match(/max\s+(\d+)/i);
      if (maxMatch) result.max = Number(maxMatch[1]);
    }
  }

  return result;
}

function parseChoiceList(text: string, hasOtherSpecify: boolean): Choice[] | undefined {
  if (!text) return undefined;
  return text.split(CHOICE_SEP).map((label) => {
    const trimmed = label.trim();
    const isOther = hasOtherSpecify && /other[s]?(?:,\s*specify|\s*\(specify\))/i.test(trimmed);
    const choice: Choice = { label: trimmed, value: trimmed };
    if (isOther) choice.isOtherSpecify = true;
    return choice;
  });
}

function extractPreamble(body: string): string | undefined {
  const match = body.match(/^> \*Preamble.*?:\*\s*"(.+?)"/ms);
  return match ? match[1].trim() : undefined;
}

function unsupportedReason(rawType: string): string {
  if (/×\d+/.test(rawType)) return 'multi-field (×N) — handled in M6';
  if (rawType.startsWith('multi')) return 'multi-choice — handled in M6';
  if (rawType === 'date') return 'date picker — handled in M6';
  if (rawType.startsWith('grid')) return 'grid item — handled in M6';
  if (rawType === 'section-break') return 'section break — rendered in M3';
  return `unsupported type "${rawType}" — handled in a later milestone`;
}
