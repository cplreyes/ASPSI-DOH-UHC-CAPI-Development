export type ItemType =
  | 'short-text'
  | 'long-text'
  | 'number'
  | 'single'
  | 'multi'
  | 'date'
  | 'multi-field';

export interface Choice {
  label: string;
  value: string;
  isOtherSpecify?: boolean;
}

export interface SubField {
  id: string;
  label: string;
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
  label: string;
  help?: string;
  choices?: Choice[];
  hasOtherSpecify?: boolean;
  min?: number;
  max?: number;
  subFields?: SubField[];
}

export interface Section {
  id: string;
  title: string;
  preamble?: string;
  items: Item[];
}
