export interface LocalizedString {
  en: string;
  fil: string;
}

export type ItemType =
  | 'short-text'
  | 'long-text'
  | 'number'
  | 'single'
  | 'multi'
  | 'date'
  | 'multi-field';

export interface Choice {
  label: LocalizedString;
  value: string;
  isOtherSpecify?: boolean;
}

export interface SubField {
  id: string;
  label: LocalizedString;
  kind: 'short-text' | 'number';
  min?: number;
  max?: number;
  // Per-subfield override of the parent multi-field's required flag. Defaults to
  // true (inherit). Set false via `[optional]` in the spec's choices column when
  // a multi-field has one always-required subfield and one optional one (e.g.
  // Q9: years required, months optional).
  required?: boolean;
}

export interface Item {
  id: string;
  legacyId?: string;
  section: string;
  type: ItemType;
  required: boolean;
  // True when the spec marks the item as `conditional` — required when shown via skip-logic
  // but absent (undefined) when hidden. Schema emits `.optional()` for these so submission
  // isn't blocked when the item is filtered out by shouldShow.
  conditional?: boolean;
  label: LocalizedString;
  help?: LocalizedString;
  choices?: Choice[];
  hasOtherSpecify?: boolean;
  min?: number;
  max?: number;
  subFields?: SubField[];
}

export interface Section {
  id: string;
  title: LocalizedString;
  preamble?: LocalizedString;
  items: Item[];
}

export interface UnsupportedItem {
  id: string;
  section: string;
  rawType: string;
  reason: string;
}

export interface ParseResult {
  sections: Section[];
  unsupported: UnsupportedItem[];
}
