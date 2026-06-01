import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { LocalizedString, ParseResult, Section } from './types';

// Dialect codes whose survey-content translations live in spec/translations/{loc}.json.
// English is the source (always present on every LocalizedString) and is not listed.
export const TRANSLATION_LOCALES = ['fil', 'ceb', 'bis', 'ilo', 'hil', 'war', 'bcl'] as const;
export type TranslationLocale = (typeof TRANSLATION_LOCALES)[number];

// Each file maps an EXACT English source string -> its translation in that language.
// Keying by English text means a label translates consistently everywhere it appears,
// and the spec stays a clean English-only extraction (no per-language columns).
export type TranslationMaps = Record<string, Record<string, string>>;

const DEFAULT_DIR = resolve(dirname(fileURLToPath(import.meta.url)), '../../spec/translations');

// Load all per-language translation maps from disk. Missing/empty/malformed files
// are tolerated (the locale just contributes nothing); a BOM-prefixed file is handled.
export function loadTranslationMaps(dir: string = DEFAULT_DIR): TranslationMaps {
  const maps: TranslationMaps = {};
  for (const loc of TRANSLATION_LOCALES) {
    maps[loc] = readMap(resolve(dir, `${loc}.json`));
  }
  return maps;
}

function readMap(path: string): Record<string, string> {
  try {
    const raw = readFileSync(path, 'utf-8').replace(/^\uFEFF/, '');
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {};
    // Keep only string->string entries; ignore anything else defensively.
    const out: Record<string, string> = {};
    for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
      if (typeof v === 'string' && v.length > 0) out[k] = v;
    }
    return out;
  } catch {
    return {};
  }
}

// Return a copy of `label` with each delivered dialect translation attached, looked
// up by the exact English text. English is preserved; a dialect key is added only
// when a non-empty translation exists, so untranslated strings stay lean and fall
// back to English at render time (see src/i18n/localized.ts).
export function localizeString(label: LocalizedString, maps: TranslationMaps): LocalizedString {
  const out: LocalizedString = { en: label.en };
  for (const loc of TRANSLATION_LOCALES) {
    const t = maps[loc]?.[label.en];
    if (typeof t === 'string' && t.length > 0) out[loc] = t;
  }
  return out;
}

// Apply the translation overlay across an entire ParseResult, returning a new
// ParseResult with every LocalizedString (section titles/preambles, item labels/help,
// choice labels, subfield labels) enriched with available dialect strings. Pure: it
// does not mutate the input and reads nothing from disk (callers pass the maps).
export function applyTranslations(result: ParseResult, maps: TranslationMaps): ParseResult {
  const L = (s: LocalizedString) => localizeString(s, maps);
  const sections: Section[] = result.sections.map((section) => ({
    ...section,
    title: L(section.title),
    ...(section.preamble ? { preamble: L(section.preamble) } : {}),
    items: section.items.map((item) => ({
      ...item,
      label: L(item.label),
      ...(item.help ? { help: L(item.help) } : {}),
      ...(item.choices
        ? { choices: item.choices.map((c) => ({ ...c, label: L(c.label) })) }
        : {}),
      ...(item.subFields
        ? { subFields: item.subFields.map((sf) => ({ ...sf, label: L(sf.label) })) }
        : {}),
    })),
  }));
  return { sections, unsupported: result.unsupported };
}
