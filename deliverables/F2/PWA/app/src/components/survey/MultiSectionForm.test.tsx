import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type * as React from 'react';
import { LocaleProvider } from '@/i18n/locale-context';
import { MultiSectionForm } from './MultiSectionForm';

function renderWithProviders(ui: React.ReactElement) {
  return render(<LocaleProvider>{ui}</LocaleProvider>);
}

describe('<MultiSectionForm>', () => {
  it('starts on Section A and shows the correct progress', () => {
    renderWithProviders(
      <MultiSectionForm initialValues={{}} onAutosave={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).toBeInTheDocument();
    // With Q5 unset on initial render: Sections C/D/E (R2-#114 patient-care
    // gating) + G (prescribing-role gating) are all hidden. Visible: A, B, F,
    // H, I, J = 6.
    expect(screen.getByText(/Section 1 of 6/)).toBeInTheDocument();
  });

  it('blocks Next when Section A validation fails and advances when it passes', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm initialValues={{}} onAutosave={vi.fn()} onSubmit={vi.fn()} />,
    );

    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument();

    await user.type(screen.getByLabelText('Last Name'), 'Reyes');
    await user.type(screen.getByLabelText('First Name'), 'Carl');
    await user.type(screen.getByLabelText('Middle Initial'), 'P');
    await user.click(screen.getByLabelText('Regular'));
    await user.click(screen.getByLabelText('Female'));
    await user.type(screen.getByLabelText(/How old are you/), '30');
    await user.click(screen.getByLabelText('Nurse'));
    await user.click(screen.getByLabelText('No'));
    await user.type(screen.getByLabelText('Year(s)'), '3');
    await user.type(screen.getByLabelText('Month(s)'), '6');
    await user.type(screen.getByLabelText(/days in a week/), '5');
    await user.type(screen.getByLabelText(/hours do you work/), '8');

    await user.click(screen.getByRole('button', { name: /next/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /Section B/ })).toBeInTheDocument(),
    );
    // Q5='Nurse' is not a prescribing role → Section G hidden → 9 visible sections total
    expect(screen.getByText(/Section 2 of 9/)).toBeInTheDocument();
  });

  it('applies intra-section skip logic — Q8 appears when Q7 = Yes', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm initialValues={{}} onAutosave={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.queryByLabelText(/divide your time/)).toBeNull();
    await user.click(screen.getByLabelText('Yes'));
    await waitFor(() => expect(screen.getByLabelText(/divide your time/)).toBeInTheDocument());
  });

  it('restores merged values when navigating back', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q5: 'Nurse',
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    await user.click(screen.getByRole('button', { name: /next/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /Section B/ })).toBeInTheDocument(),
    );
    await user.click(screen.getByRole('button', { name: /previous/i }));
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument(),
    );
    expect(screen.getByLabelText('Female')).toBeChecked();
  });

  it('blocks Next when Q5 is "Other (specify)" but Q5_other is empty', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    // Q2 and Q5 both have an "Other (specify)" choice; Q5's is the second instance
    // in document order and the one this test is actually exercising.
    const otherChoices = screen.getAllByLabelText('Other (specify)');
    await user.click(otherChoices[otherChoices.length - 1]!);
    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument();
  });

  it('renders the review screen when initialIndex points past the last section', () => {
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q5: 'Nurse',
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        initialIndex={10}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole('heading', { name: /Review your answers/i })).toBeInTheDocument();
  });

  it('calls onSubmit with merged values when Submit is clicked on the review screen', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const values = {
      Q1_1: 'Reyes',
      Q1_2: 'Carl',
      Q1_3: 'P',
      Q2: 'Regular',
      Q3: 'Female',
      Q4: 30,
      Q5: 'Nurse',
      Q7: 'No',
      Q9_1: 3,
      Q9_2: 6,
      Q10: 5,
      Q11: 8,
    };
    renderWithProviders(
      <MultiSectionForm
        initialValues={values}
        initialIndex={10}
        onAutosave={vi.fn()}
        onSubmit={onSubmit}
      />,
    );
    await user.click(screen.getByRole('button', { name: /^submit$/i }));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining(values));
  });

  it('returns to the chosen section when Edit is clicked on the review screen', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q5: 'Nurse',
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        initialIndex={10}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    const editButtons = screen.getAllByRole('button', { name: /^edit$/i });
    await user.click(editButtons[0]);
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/i }),
    ).toBeInTheDocument();
  });

  // R3 #314: edit a matrix section from Review → the matrix must show the
  // prior answers. Tester saw a blank Job-Satisfaction matrix on edit/back.
  it('rehydrates a matrix section when edited from the review screen (#314)', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q5: 'Physician/Doctor', // makes Section G (matrix) visible
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
          Q75: '3', // Section G matrix (1–5 scale) prior answer
        }}
        initialIndex={10} // REVIEW_INDEX (SECTIONS A–J = 10)
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    // Target Section G's Edit button via its review header (ReviewSection
    // only renders sections that have answered blocks, so a fixed index is
    // unreliable).
    const gHeading = screen.getByText(/^Section G —/);
    const gSection = gHeading.closest('section') as HTMLElement;
    await user.click(within(gSection).getByRole('button', { name: /edit/i }));
    const q75at3 = screen.getAllByLabelText('Q75 3') as HTMLInputElement[];
    expect(q75at3.length).toBeGreaterThan(0);
    expect(q75at3.some((r) => r.checked)).toBe(true);
  });

  it('R2-#118+#119: blocks advance when Section B Q25 (multi, conditional, required) is an empty array', async () => {
    // Pre-fix: hasValue([]) returned true (since [] !== '') so a multi-type
    // required field initialized to [] in sectionDefaults appeared filled.
    // getSectionStatus returned 'complete', auto-advance fired, and the
    // form sailed past Section B with Q25 unanswered. Same shape on
    // J.Q124/J.Q125 — tester reported submission proceeded with Q124/Q125
    // empty.
    //
    // After the fix: hasValue handles Array.isArray + length, so Q25 = []
    // is detected as not-filled. Section B status = 'incomplete'.
    // handleSectionValid's runtime gate refuses to advance.
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          // Section A — fill everything required so we can land on B
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q5: 'Nurse',
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
          // Section B — Q12=Yes opens Q13–Q30. Fill all visible required
          // (Q13/Q15='No' hides Q14/Q16). Leave Q25 as [] — the bug surface.
          Q12: 'Yes',
          Q13: 'No',
          Q15: 'No',
          Q17: 'something',
          Q18: 'something',
          Q19: 'something',
          Q20: 'something',
          Q21: 'something',
          Q22: 'something',
          Q23: 'something',
          Q24: 'something',
          Q25: [],
        }}
        initialIndex={1}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(
      screen.getByRole('heading', { name: /Section B/ }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /next/i }));

    // After fix: form stays on B because Q25=[] is correctly detected as
    // unfilled. Pre-fix this would have advanced to Section C.
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /Section B/ })).toBeInTheDocument(),
    );
  });

  // #524: "answering a question automatically skips to the next section even
  // though there are remaining questions to be answered" — reported on gate
  // questions whose Yes-answer reveals required follow-ups (Q44→Q45-47,
  // Q54→Q55, Q123→Q124/Q125), "more common toward the end of a section."
  //
  // This is the AUTO-ADVANCE path (the entryStatus useEffect), not the manual
  // Next path the R2-#118 test covers. Mechanism check: answering the gate
  // makes the section briefly *look* finished only if the revealed follow-ups
  // aren't counted. They ARE counted — getSectionStatus filters by shouldShow
  // (the gate reveals them) AND require:true, so the section stays 'incomplete'
  // and auto-advance's `currentStatus !== 'complete'` guard returns. These two
  // cases pin that: a Yes gate must NOT auto-skip; a No gate (no follow-ups)
  // legitimately may. Section J / Q123 is the named gate and the last section.
  const J_REQUIRED_MINUS_GATE = {
    // Section A — landing-state requirements (so merged is well-formed)
    Q1_1: 'Reyes',
    Q1_2: 'Carl',
    Q1_3: 'P',
    Q2: 'Regular',
    Q3: 'Female',
    Q4: 30,
    Q5: 'Nurse',
    Q7: 'No',
    Q9_1: 3,
    Q9_2: 6,
    Q10: 5,
    Q11: 8,
    // Section J — every visible required item answered EXCEPT the Q123 gate.
    // Q114='Never' hides Q122 (predicate: Q114 !== 'Never'); Q124/Q125 stay
    // hidden until Q123 is a "Yes,…".
    Q98: 'Agree',
    Q99: 'Agree',
    Q100: 'Agree',
    Q101: 'Agree',
    Q102: 'Agree',
    Q103: 'Agree',
    Q104: 'Agree',
    Q105: 'Agree',
    Q106: 'Agree',
    Q107: 'Agree',
    Q109: 'None',
    Q110: ['None'],
    Q111: ['Supervisory trainings'],
    Q112: ['Clinical audits'],
    Q113: ['Clinical audits'],
    Q114: 'Never',
    Q115: 'Sometimes',
    Q116: 'Sometimes',
    Q117: 'Sometimes',
    Q118: 'Sometimes',
    Q119: 'Sometimes',
    Q120: 'Sometimes',
    Q121: 'Sometimes',
  };

  it('#524: answering a gate Yes (Q123) reveals required follow-ups and does NOT auto-skip', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={J_REQUIRED_MINUS_GATE}
        initialIndex={9} // Section J
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole('heading', { name: /Section J/ })).toBeInTheDocument();
    // Q124/Q125 are hidden until the gate is a "Yes,…"
    expect(screen.queryByText(/Why are you planning on leaving/)).toBeNull();

    // Answer the gate "Yes" — reveals Q124 (required, multi, empty)
    await user.click(screen.getByLabelText(/definite plans to leave/));

    // The follow-up must appear (the gate's reveal works)…
    await waitFor(() =>
      expect(screen.getByText(/Why are you planning on leaving/)).toBeInTheDocument(),
    );
    // …and crucially the form must STILL be on Section J — no auto-skip past
    // the freshly-revealed Q124/Q125. Settle the autosave (500ms) + any
    // auto-advance timer (400ms) window, then re-assert.
    await new Promise((r) => setTimeout(r, 1000));
    expect(screen.getByRole('heading', { name: /Section J/ })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /Review your answers/i })).toBeNull();
  });

  it('#524 control: answering the same gate No (no follow-ups) DOES auto-advance', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MultiSectionForm
        initialValues={J_REQUIRED_MINUS_GATE}
        initialIndex={9} // Section J (last section → advances to Review)
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole('heading', { name: /Section J/ })).toBeInTheDocument();

    // "No, I haven't thought about it" — reveals nothing, so the section is now
    // complete and the entryStatus useEffect auto-advances to the review screen.
    await user.click(screen.getByLabelText(/^No, I haven.*thought about it/));

    await waitFor(
      () => expect(screen.getByRole('heading', { name: /Review your answers/i })).toBeInTheDocument(),
      { timeout: 3000 },
    );
  });

  it('renders Section G Q75-Q81 as a single matrix table on tablet+', async () => {
    // Q5='Physician/Doctor' triggers Section G visibility (per shouldShowSection)
    // and reaches Section G with Q75-Q81 visible.
    renderWithProviders(
      <MultiSectionForm
        initialValues={{
          Q1_1: 'Reyes',
          Q1_2: 'Carl',
          Q1_3: 'P',
          Q2: 'Regular',
          Q3: 'Female',
          Q4: 30,
          Q5: 'Physician/Doctor',
          Q7: 'No',
          Q9_1: 3,
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        initialIndex={6} // Section G is index 6 (0-based: A B C D E F G)
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    // Section G (with all gating answers unset) renders 3 matrix tables:
    //   - Q63/Q66/Q69/Q72 (Yes/No) — gating questions Q64/Q65/Q67/Q68/Q70/Q71 are hidden,
    //     so all four Yes/No items are consecutive and collapse into one matrix.
    //   - Q75-Q81 (1-5 scale)
    //   - Q83-Q85 (frequency Never–Always)
    const tables = screen.getAllByRole('table');
    // At least 2 distinct matrix clusters proves the dispatch works across multiple
    // groupings. The exact count depends on Section G's gating predicates and
    // would be brittle as the spec evolves; the q75Q81Matrix probe below is the
    // structural assertion that actually proves Q75-Q81 forms a matrix.
    expect(tables.length).toBeGreaterThanOrEqual(2);
    // Specifically confirm the Q75-Q81 cluster: find a table that contains both
    // Q75's and Q81's question prefixes (the matrix renders "Q75. <label>" in
    // the row header for each row).
    const q75Q81Matrix = tables.find(
      (t) => t.textContent?.includes('Q75.') && t.textContent?.includes('Q81.'),
    );
    expect(q75Q81Matrix).toBeDefined();
  });
});
