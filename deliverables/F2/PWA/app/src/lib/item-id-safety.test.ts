import { describe, expect, it } from 'vitest';
import { sections } from '@/generated/items';

// #1291 (UAT R7, 2026-08-20) — REGRESSION GATE FOR A WHOLE BUG CLASS.
//
// react-hook-form does not treat a field name as an opaque string. `isKey()` is
// `/^\w*$/`; anything failing it goes through `stringToPath()`, which splits on
// `.` and `[`. So a field registered as `Q13.1` addresses `values.Q13['1']`, and
// RHF's `set()` will REPLACE whatever sits at `Q13` (the parent's answer string)
// with an array or object in order to store the child. That is silent and
// destructive: the Aug-17 attribution battery shipped with ids taken verbatim
// from the paper's printed sub-item numbers, and answering any probe wiped its
// parent stem — testers saw "you cannot select an answer, and the main answer is
// removed".
//
// Every id below is used directly as an RHF field name (Question.tsx registers
// `item.id`, `${item.id}_other`, and each sub-field id), so the safe set is
// exactly what `isKey` accepts: word characters only. The printed number is not
// lost — it lives on `displayNumber`, which the renderer prefers.
//
// Keep this test. The spec is the input to a generator, so the next time a paper
// question is numbered `Q31.1` the id would silently become path syntax again.
const RHF_PATH_SYNTAX = /[.[\]]/;
const RHF_SAFE_KEY = /^\w+$/;

const allItems = sections.flatMap((s) => s.items);

describe('#1291: generated item ids must be safe react-hook-form field names', () => {
  it('exposes items to check (guards against an empty-scan false pass)', () => {
    expect(allItems.length).toBeGreaterThan(100);
  });

  it('no item id contains react-hook-form path syntax', () => {
    const offenders = allItems.map((i) => i.id).filter((id) => RHF_PATH_SYNTAX.test(id));
    expect(offenders).toEqual([]);
  });

  it('every item id is a plain RHF key', () => {
    const offenders = allItems.map((i) => i.id).filter((id) => !RHF_SAFE_KEY.test(id));
    expect(offenders).toEqual([]);
  });

  it('every derived "_other" field name is a plain RHF key', () => {
    const offenders = allItems
      .filter((i) => i.hasOtherSpecify)
      .map((i) => `${i.id}_other`)
      .filter((name) => !RHF_SAFE_KEY.test(name));
    expect(offenders).toEqual([]);
  });

  it('every multi-field sub-field id is a plain RHF key', () => {
    const offenders = allItems
      .flatMap((i) => i.subFields ?? [])
      .map((sf) => sf.id)
      .filter((id) => !RHF_SAFE_KEY.test(id));
    expect(offenders).toEqual([]);
  });

  it('item ids are unique across the whole instrument', () => {
    const ids = allItems.map((i) => i.id);
    expect(ids.length).toBe(new Set(ids).size);
  });

  it('the Aug-17 attribution sub-items kept their printed numbers on displayNumber', () => {
    // The eleven items the ticket was filed against. Renaming the id must not
    // change what the enumerator reads on screen.
    const subItems = allItems.filter((i) => /^Q\d+_\d+$/.test(i.id) && i.section === 'B');
    expect(subItems.map((i) => i.id)).toEqual([
      'Q13_1',
      'Q15_1',
      'Q17_1',
      'Q18_1',
      'Q19_1',
      'Q20_1',
      'Q21_1',
      'Q22_1',
      'Q23_1',
      'Q24_1',
      'Q24_2',
    ]);
    for (const item of subItems) {
      expect(item.displayNumber).toBe(item.id.replace(/_/g, '.'));
    }
  });
});
