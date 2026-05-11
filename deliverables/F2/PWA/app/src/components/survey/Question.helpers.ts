// Pure helper functions extracted from Question.tsx so the component file
// only exports React components (Vite HMR / react-refresh requirement).

// Compute the next selected-values array for a multi-select after the user
// clicks a checkbox. Encodes the exclusivity rules from issues #16 and #17.
//
// - Clicking an `isExclusive` option (e.g. "I don't know") clears all others.
// - Clicking an `isSelectAll` option (e.g. "All of the above") auto-selects
//   every non-exclusive non-otherSpecify choice.
// - Clicking a regular option clears any currently-selected exclusive or
//   selectAll values (mixed selection isn't compatible).
// - Unchecking `isSelectAll` clears the auto-selected values.
// - Unchecking a regular option also clears `isSelectAll` (the "all" claim
//   is no longer accurate).
export function nextMultiValue(
  current: string[],
  clicked: {
    value: string;
    isExclusive?: boolean;
    isSelectAll?: boolean;
    isOtherSpecify?: boolean;
  },
  willBeChecked: boolean,
  allChoices: ReadonlyArray<{
    value: string;
    isExclusive?: boolean;
    isSelectAll?: boolean;
    isOtherSpecify?: boolean;
  }>,
): string[] {
  const findChoice = (v: string) => allChoices.find((c) => c.value === v);

  if (willBeChecked) {
    if (clicked.isExclusive) return [clicked.value];
    if (clicked.isSelectAll) {
      return allChoices.filter((c) => !c.isExclusive && !c.isOtherSpecify).map((c) => c.value);
    }
    const filtered = current.filter((v) => {
      const c = findChoice(v);
      return c ? !c.isExclusive && !c.isSelectAll : true;
    });
    return filtered.includes(clicked.value) ? filtered : [...filtered, clicked.value];
  }

  // Unchecking
  if (clicked.isSelectAll) {
    return current.filter((v) => {
      const c = findChoice(v);
      return c?.isOtherSpecify || c?.isExclusive;
    });
  }
  const next = current.filter((v) => v !== clicked.value);
  return next.filter((v) => {
    const c = findChoice(v);
    return c ? !c.isSelectAll : true;
  });
}
