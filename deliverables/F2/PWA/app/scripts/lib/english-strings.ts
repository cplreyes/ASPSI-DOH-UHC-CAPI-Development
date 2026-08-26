// The exact set of English source strings that scripts/lib/apply-translations.ts
// localizes (section.title, section.preamble, item.label, item.help, choice.label,
// subField.label). item.preamble / item.inputLabel are deliberately NOT included:
// applyTranslations() never passes them through localizeString(), so a map key for
// them would be dead. This list is the anchor universe for the F2 paper extractor.
//
// For a choice.label entry, `ids` carries the parent ITEM id (choices have no id of
// their own). For a subField.label entry, `ids` carries the SUBFIELD's own id.
import type { ParseResult } from './types';

export type EnglishKind =
  | 'section.title'
  | 'section.preamble'
  | 'item.label'
  | 'item.help'
  | 'choice.label'
  | 'subField.label';

export interface EnglishStringEntry {
  text: string;
  kinds: EnglishKind[];
  ids: string[];
}

export function collectEnglishStrings(result: ParseResult): EnglishStringEntry[] {
  const order: string[] = [];
  const byText = new Map<string, EnglishStringEntry>();
  const add = (text: string, kind: EnglishKind, id: string): void => {
    if (!text) return;
    let e = byText.get(text);
    if (!e) {
      e = { text, kinds: [], ids: [] };
      byText.set(text, e);
      order.push(text);
    }
    if (!e.kinds.includes(kind)) e.kinds.push(kind);
    if (!e.ids.includes(id)) e.ids.push(id);
  };
  for (const s of result.sections) {
    add(s.title.en, 'section.title', s.id);
    if (s.preamble) add(s.preamble.en, 'section.preamble', s.id);
    for (const it of s.items) {
      add(it.label.en, 'item.label', it.id);
      if (it.help) add(it.help.en, 'item.help', it.id);
      for (const c of it.choices ?? []) add(c.label.en, 'choice.label', it.id);
      for (const sf of it.subFields ?? []) add(sf.label.en, 'subField.label', sf.id);
    }
  }
  return order.map((t) => byText.get(t)!);
}
