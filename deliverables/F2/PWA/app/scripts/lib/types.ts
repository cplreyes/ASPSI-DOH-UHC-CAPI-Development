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
}

export interface Item {
  id: string;
  legacyId?: string;
  section: string;
  type: ItemType;
  required: boolean;
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
