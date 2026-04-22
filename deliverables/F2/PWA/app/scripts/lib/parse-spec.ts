import type {
  Item,
  ParseResult,
  Section,
  UnsupportedItem,
  ItemType,
  Choice,
  SubField,
  LocalizedString,
} from './types';

function dual(en: string): LocalizedString {
  return { en, fil: en };
}

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
const GRID_HEADER = /^\*\*Grid #\d+[^(]*\(([^)]+)\)/;

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
  const rows: RowFields[] = [];
  let i = 0;
  let currentGridChoices: string | undefined;

  while (i < lines.length) {
    const line = lines[i];
    const gridMatch = line.match(GRID_HEADER);
    if (gridMatch) {
      currentGridChoices = gridMatch[1].trim();
      i++;
      continue;
    }

    const next = lines[i + 1];
    const isTableHeader =
      TABLE_HEADER.test(line) &&
      next &&
      ALIGNMENT_ROW.test(next) &&
      splitCells(line)[0] === 'pdf_q';

    if (!isTableHeader) {
      i++;
      continue;
    }

    const header = splitCells(line);
    i += 2;

    while (i < lines.length && TABLE_HEADER.test(lines[i])) {
      const cells = splitCells(lines[i]);
      if (cells[0] && /^Q\d+/.test(cells[0])) {
        const row: RowFields = {};
        header.forEach((col, idx) => {
          row[normalizeHeader(col)] = cells[idx] ?? '';
        });
        if (
          (!row.choices || row.choices === '') &&
          row.type === 'grid-single' &&
          currentGridChoices
        ) {
          row.choices = currentGridChoices;
        }
        rows.push(row);
      }
      i++;
    }
  }

  return rows;
}

const SUPPORTED_TYPES: Record<string, ItemType> = {
  single: 'single',
  'single + specify': 'single',
  'single (1–5)': 'single',
  'grid-single': 'single',
  multi: 'multi',
  'multi + specify': 'multi',
  date: 'date',
  'short-text': 'short-text',
  'long-text': 'long-text',
  number: 'number',
};

const CHOICE_SEP = /\s*·\s*/;

const MULTI_FIELD_RE = /^(short-text|number)\s*×\s*(\d+)$/;

export interface NormalizeRowResult {
  item?: Item;
  unsupported?: UnsupportedItem;
}

export function normalizeRow(row: RowFields, section: string): NormalizeRowResult {
  const rawType = (row.type ?? '').trim();

  const multiFieldMatch = rawType.match(MULTI_FIELD_RE);
  if (multiFieldMatch) {
    const kind = multiFieldMatch[1] as 'short-text' | 'number';
    const count = Number(multiFieldMatch[2]);
    const labels = (row.choices ?? '')
      .split('/')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    const subFields: SubField[] = [];
    for (let i = 0; i < count; i++) {
      subFields.push({
        id: `${row.pdf_q}_${i + 1}`,
        label: dual(labels[i] ?? `Field ${i + 1}`),
        kind,
      });
    }
    const required = (row.required ?? '').trim() === 'Y';
    const item: Item = {
      id: row.pdf_q,
      section,
      type: 'multi-field',
      required,
      label: dual(row.label ?? ''),
      subFields,
    };
    if (row.legacy_q && row.legacy_q !== '—' && row.legacy_q !== '') {
      item.legacyId = row.legacy_q;
    }
    return { item };
  }

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
    label: dual(row.label ?? ''),
  };

  if (row.legacy_q && row.legacy_q !== '—' && row.legacy_q !== '') {
    item.legacyId = row.legacy_q;
  }
  if (help) item.help = dual(help);
  if (min !== undefined) item.min = min;
  if (max !== undefined) item.max = max;

  if (type === 'single' || type === 'multi') {
    item.hasOtherSpecify = hasOtherSpecify;
    const choices = parseChoiceList(choicesText, hasOtherSpecify);
    if (choices) item.choices = choices;
  }

  return { item };
}

const SAME_CHOICE_SET_RE = /same choice set as (Q\d+(?:\.\d+)?)/i;
const NAMED_SET_RE = /\*\*([A-Za-z0-9-]+) set\*\*[^\n]*\n((?:-\s+[^\n]+\n?)+)/g;
const NAMED_SET_BULLET_RE = /^-\s+(.+?)\s*$/;
const SPECIFY_OTHER_RE = /other[s]?(?:,\s*specify|\s*\(specify\))|specify\s+other\s+reason/i;

export function parseSpec(markdown: string): ParseResult {
  const sections: Section[] = [];
  const unsupported: UnsupportedItem[] = [];
  const namedSets = extractNamedSets(markdown);

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
      title: dual(raw.title),
      ...(preamble ? { preamble: dual(preamble) } : {}),
      items,
    });
  }

  resolveSameChoiceSetReferences(sections);
  resolveNamedSetReferences(sections, namedSets);

  return { sections, unsupported };
}

function resolveSameChoiceSetReferences(sections: Section[]): void {
  const byId = new Map<string, Item>();
  for (const section of sections) {
    for (const item of section.items) byId.set(item.id, item);
  }

  for (const section of sections) {
    for (const item of section.items) {
      if (!item.choices || item.choices.length !== 1) continue;
      const match = item.choices[0].label.en.match(SAME_CHOICE_SET_RE);
      if (!match) continue;
      const referenced = byId.get(match[1]);
      if (referenced?.choices) {
        item.choices = referenced.choices.map((c) => ({ ...c }));
      }
    }
  }
}

export function extractNamedSets(markdown: string): Map<string, string[]> {
  const sets = new Map<string, string[]>();
  for (const match of markdown.matchAll(NAMED_SET_RE)) {
    const name = match[1];
    const bullets = match[2]
      .split('\n')
      .map((line) => line.match(NAMED_SET_BULLET_RE)?.[1])
      .filter((v): v is string => Boolean(v));
    if (bullets.length > 0) sets.set(name, bullets);
  }
  return sets;
}

function resolveNamedSetReferences(sections: Section[], sets: Map<string, string[]>): void {
  if (sets.size === 0) return;
  for (const section of sections) {
    for (const item of section.items) {
      if (!item.choices || item.choices.length !== 1) continue;
      const label = item.choices[0].label.en;
      for (const [name, options] of sets) {
        const re = new RegExp(`${escapeRegex(name)}\\s+set`, 'i');
        if (!re.test(label)) continue;
        item.choices = options.map((raw) => {
          const trimmed = raw.trim();
          const choice: Choice = { label: dual(trimmed), value: trimmed };
          if (SPECIFY_OTHER_RE.test(trimmed)) choice.isOtherSpecify = true;
          return choice;
        });
        break;
      }
    }
  }
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
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
  if (tail) {
    const wrapped = tail.match(/^help:\s*"([\s\S]+)"\s*$/);
    result.help = wrapped ? wrapped[1] : tail;
  }

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
    const choice: Choice = { label: dual(trimmed), value: trimmed };
    if (isOther) choice.isOtherSpecify = true;
    return choice;
  });
}

function extractPreamble(body: string): string | undefined {
  const match = body.match(/^> \*Preamble.*?:\*\s*"(.+?)"/ms);
  return match ? match[1].trim() : undefined;
}

function unsupportedReason(rawType: string): string {
  if (rawType.startsWith('grid') && rawType !== 'grid-single') {
    return 'grid item — handled in a later milestone';
  }
  if (rawType === 'section-break') return 'section break — not a renderable item';
  return `unsupported type "${rawType}" — handled in a later milestone`;
}
