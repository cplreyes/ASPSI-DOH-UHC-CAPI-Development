// Fixture only -- invented content, never copy real survey wording here.
// Shaped like deliverables/F2/PWA/app/src/generated/items.ts (one item per line).
import type { Section } from '@/types/survey';

export const sectionA: Section = {
  id: 'A',
  title: { en: 'Mini Invented Section' },
  items: [
    { id: 'Q1', section: 'A', type: 'single', required: true, label: { en: 'Do you like invented tea? (fixture only)' }, choices: [{ label: { en: 'Yes' }, value: 'Yes' }, { label: { en: 'No' }, value: 'No' }] },
  ],
};
