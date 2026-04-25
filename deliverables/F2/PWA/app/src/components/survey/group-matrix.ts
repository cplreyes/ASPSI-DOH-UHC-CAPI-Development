import type { Choice, Item } from '@/types/survey';

export interface MatrixGroup {
  kind: 'matrix';
  /** The shared choice set every row uses. */
  choices: Choice[];
  /** The rows. Always >= 2 items per group. */
  items: Item[];
}

function isMatrixCandidate(item: Item): boolean {
  return (
    item.type === 'single' &&
    item.hasOtherSpecify !== true &&
    Array.isArray(item.choices) &&
    item.choices.length > 0
  );
}

function sameChoiceValues(a: Choice[], b: Choice[]): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i].value !== b[i].value) return false;
  }
  return true;
}

/**
 * Walk an already-shouldShow-filtered list of items. Group consecutive
 * `single`-type items that share the same choice values into matrix groups
 * of size >= 2. Everything else flows through unchanged in original order.
 */
export function groupVisibleItems(items: Item[]): Array<MatrixGroup | Item> {
  const out: Array<MatrixGroup | Item> = [];
  let i = 0;

  while (i < items.length) {
    const start = items[i];

    if (!isMatrixCandidate(start)) {
      out.push(start);
      i++;
      continue;
    }

    const startChoices = start.choices!;
    let j = i + 1;
    while (
      j < items.length &&
      isMatrixCandidate(items[j]) &&
      sameChoiceValues(items[j].choices!, startChoices)
    ) {
      j++;
    }

    const runLength = j - i;
    if (runLength >= 2) {
      out.push({ kind: 'matrix', choices: startChoices, items: items.slice(i, j) });
    } else {
      out.push(start);
    }
    i = j;
  }

  return out;
}
