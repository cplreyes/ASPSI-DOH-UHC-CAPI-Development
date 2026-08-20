// Regression repro for #1291 (UAT R7) — the Section-B two-step attribution
// battery. Tester report: "When you select YES in Q12-Q24 a follow up question
// will show but you cannot select an answer in the follow up question, and the
// answer in the main question will be removed."
//
// Root cause: the eleven Aug-17 sub-items were given ids taken verbatim from the
// paper's printed number ('Q13.1'). react-hook-form parses '.' as a nested-path
// separator, so register('Q13.1') addressed values.Q13['1'] and RHF's set()
// REPLACED the parent's answer string with an array to make room for the child.
// The parent's own gate then read false and the probe unmounted.
//
// WHY THIS FILE EXISTS RATHER THAN MORE skip-logic unit tests: the battery was
// already covered there, and those tests passed throughout — they call the pure
// predicate on plain objects and never mount a form, so react-hook-form's path
// handling was never exercised. This test drives the REAL generated items through
// a real <Section>, which is the only place the bug was observable.
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type * as React from 'react';
import type { Section as SectionModel } from '@/types/survey';
import { LocaleProvider } from '@/i18n/locale-context';
import { sections } from '@/generated/items';
import { sectionBSchema } from '@/generated/schema';
import { shouldShow } from '@/lib/skip-logic';
import { Section } from './Section';

function renderWithProviders(ui: React.ReactElement) {
  return render(<LocaleProvider>{ui}</LocaleProvider>);
}

const sectionB = sections.find((s) => s.id === 'B')!;

// Render only the stem + its probe, mirroring how MultiSectionForm filters the
// section down to the currently-visible items.
function batteryPair(stemId: string, probeId: string): SectionModel {
  const items = sectionB.items.filter((i) => i.id === stemId || i.id === probeId);
  expect(items).toHaveLength(2);
  return { ...sectionB, items };
}

describe('#1291: Section-B attribution battery (stem + probe)', () => {
  it('the probe id is a flat key, not a react-hook-form path', () => {
    const probe = sectionB.items.find((i) => i.id === 'Q13_1');
    expect(probe).toBeDefined();
    expect(probe!.id).not.toContain('.');
    // The enumerator still reads the paper's number.
    expect(probe!.displayNumber).toBe('Q13.1');
  });

  it('answering the probe does NOT erase the parent stem (the reported defect)', async () => {
    const user = userEvent.setup();
    const onAutosave = vi.fn();

    renderWithProviders(
      <Section
        section={batteryPair('Q13', 'Q13_1')}
        schema={sectionBSchema}
        defaultValues={{ Q12: 'Yes', Q13: 'Yes' }}
        onAutosave={onAutosave}
        onSubmit={() => {}}
        hideSubmit
      />,
    );

    // The probe is visible because the stem is Yes.
    const probeChoice = await screen.findByLabelText(
      'Implemented as a direct result of the UHC Act',
    );
    await user.click(probeChoice);

    // onAutosave is debounced (500ms) — wait for the settled values.
    await waitFor(
      () => {
        expect(onAutosave).toHaveBeenCalled();
        const latest = onAutosave.mock.calls[onAutosave.mock.calls.length - 1]![0] as Record<string, unknown>;
        // The probe holds its own answer as a flat string...
        expect(latest.Q13_1).toBe('Implemented as a direct result of the UHC Act');
        // ...and — the actual regression — the parent still holds 'Yes'.
        // Pre-fix this was ['', 'Implemented as a direct result of the UHC Act'].
        expect(latest.Q13).toBe('Yes');
      },
      { timeout: 3000 },
    );
  });

  it('the parent stays a string, so its own skip-logic gate still holds', async () => {
    const user = userEvent.setup();
    const onAutosave = vi.fn();

    renderWithProviders(
      <Section
        section={batteryPair('Q13', 'Q13_1')}
        schema={sectionBSchema}
        defaultValues={{ Q12: 'Yes', Q13: 'Yes' }}
        onAutosave={onAutosave}
        onSubmit={() => {}}
        hideSubmit
      />,
    );

    await user.click(
      await screen.findByLabelText('Implemented as a direct result of the UHC Act'),
    );

    await waitFor(
      () => {
        expect(onAutosave).toHaveBeenCalled();
        const latest = onAutosave.mock.calls[onAutosave.mock.calls.length - 1]![0] as Record<string, unknown>;
        // This is what made the probe vanish a moment after being clicked:
        // MultiSectionForm recomputes visibility from the autosaved values, and
        // the predicate requires `typeof v.Q13 === 'string'`.
        expect(typeof latest.Q13).toBe('string');
        expect(shouldShow('B', 'Q13_1', latest)).toBe(true);
      },
      { timeout: 3000 },
    );
  });

  it('every stem/probe pair in the battery is wired and mutually consistent', () => {
    const pairs: Array<[string, string]> = [
      ['Q13', 'Q13_1'],
      ['Q15', 'Q15_1'],
      ['Q17', 'Q17_1'],
      ['Q18', 'Q18_1'],
      ['Q19', 'Q19_1'],
      ['Q20', 'Q20_1'],
      ['Q21', 'Q21_1'],
      ['Q22', 'Q22_1'],
      ['Q23', 'Q23_1'],
      ['Q24', 'Q24_1'],
      ['Q24', 'Q24_2'],
    ];
    for (const [stem, probe] of pairs) {
      expect(sectionB.items.find((i) => i.id === stem), `${stem} missing`).toBeDefined();
      expect(sectionB.items.find((i) => i.id === probe), `${probe} missing`).toBeDefined();
      // Probe hidden when the stem is No, shown when Yes — with the outer Q12 gate met.
      expect(shouldShow('B', probe, { Q12: 'Yes', [stem]: 'No' })).toBe(false);
      expect(shouldShow('B', probe, { Q12: 'Yes', [stem]: 'Yes' })).toBe(true);
    }
  });
});
