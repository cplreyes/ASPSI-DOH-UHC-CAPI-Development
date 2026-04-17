export type ItemType = 'short-text' | 'long-text' | 'number' | 'single';

export interface Choice {
  label: string;
  value: string;
  isOtherSpecify?: boolean;
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
}

export interface Section {
  id: string;
  title: string;
  preamble?: string;
  items: Item[];
}
