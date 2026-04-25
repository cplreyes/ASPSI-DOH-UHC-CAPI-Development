import type { LocalizedString } from '@/i18n/localized';

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
