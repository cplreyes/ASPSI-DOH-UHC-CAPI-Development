import type { LocalizedString } from '@/i18n/localized';

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
  // True for "I don't know" / "None of the above" — checking it clears other
  // selections in a multi-select; checking another option clears it.
  isExclusive?: boolean;
  // True for "All of the above" — checking it auto-selects every non-exclusive
  // non-otherSpecify option; unchecking it clears them all.
  isSelectAll?: boolean;
}

export interface SubField {
  id: string;
  label: LocalizedString;
  kind: 'short-text' | 'number';
  min?: number;
  max?: number;
  required?: boolean;
}

export interface Item {
  id: string;
  legacyId?: string;
  // Contiguous on-screen number. `id` stays 1:1 with the source PDF (data keys,
  // cross-field rules, the Apps Script column map all depend on it), but the
  // official questionnaire skips Q108 (Q107→Q109), which reads as a missing item
  // to respondents. displayNumber removes that gap for DISPLAY ONLY — any id
  // numbered above the gap shows one less (Q109→Q108 … Q125→Q124). Absent for
  // items at/below the gap (there the displayed number already equals `id`).
  // (#519.) Always render the number as `item.displayNumber ?? item.id`.
  displayNumber?: string;
  section: string;
  type: ItemType;
  required: boolean;
  // Required when shown via skip-logic but absent when hidden — runtime blocks completion
  // while visible; schema treats as optional so submission survives hidden state.
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
