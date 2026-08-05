// English is the source and is always present. Each dialect is optional —
// missing keys fall back to `en` at render time (see src/i18n/localized.ts).
// Dialect strings are populated by the generator from spec/translations/{locale}.json.
export interface LocalizedString {
  en: string;
  fil?: string; // Tagalog
  ceb?: string; // Cebuano
  bis?: string; // Bisaya
  ilo?: string; // Ilocano
  hil?: string; // Hiligaynon (pending ASPSI)
  war?: string; // Waray (pending ASPSI)
  bcl?: string; // Bikol/Bicolano (pending ASPSI)
}

export type ItemType =
  | 'short-text'
  | 'long-text'
  | 'number'
  | 'single'
  | 'multi'
  | 'date'
  // One field, ISO-8601 variable precision ('YYYY' | 'YYYY-MM' | 'YYYY-MM-DD').
  // Year required; month + day each optional ("Don't know" = blank). R3 #306.
  | 'partial-date'
  | 'multi-field';

export interface Choice {
  label: LocalizedString;
  value: string;
  isOtherSpecify?: boolean;
  // True for options like "I don't know" / "None of the above" — checking it
  // clears all other selections in a multi-select; checking another option
  // clears the exclusive one.
  isExclusive?: boolean;
  // True for options like "All of the above" — checking it auto-selects every
  // non-exclusive non-otherSpecify option; unchecking it clears them all.
  isSelectAll?: boolean;
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
  // #1042/#1043/#1040/#1041 (pretest 2026-08-04): mid-section instructions,
  // sub-headers (E1/E2) and notes from the paper attach to the item they
  // precede and render above the question.
  preamble?: LocalizedString;
  // #1046/#1047: unit label shown directly above a number/short-text input
  // ("Number of days") — separate from `help`, which stays below the label.
  inputLabel?: LocalizedString;
  // #1045: paper bolds the component being asked about; renderer wraps the
  // first occurrence of this EN phrase (per-locale when present) in <strong>.
  emphasis?: string;
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
