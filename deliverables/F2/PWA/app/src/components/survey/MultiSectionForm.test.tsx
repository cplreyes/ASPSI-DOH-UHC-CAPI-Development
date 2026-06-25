import { describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
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

  it('#587: blocks advance out of Section A on an implausible tenure (PROF-01) with an inline error', async () => {
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
          Q9_1: 15, // age 30 → threshold age − 20 = 10; tenure 15 ≥ 10 → PROF-01 hard block
          Q9_2: 6,
          Q10: 5,
          Q11: 8,
        }}
        onAutosave={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    // The cross-field error fires inline at section exit — not only at review.
    await waitFor(() =>
      expect(screen.getByText(/must be less than your age/i)).toBeInTheDocument(),
    );
    expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument();
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

  it('#524: continued interaction cancels a pending auto-advance (no mid-answer bounce)', async () => {
    // Bug: once the visible-required set is filled the section reads "complete"
    // and a 400ms auto-advance fires — but that 400ms is shorter than the 500ms
    // autosave debounce, so a user still answering (adding multi-select options,
    // or about to reveal a conditional required question) gets bounced to the
    // next section. Fix: Section.onInteract fires synchronously on every field
    // change and cancels the pending advance; it only re-schedules once input
    // settles. Without the fix this test lands on Section B; with it, stays on A.
    vi.useFakeTimers();
    try {
      renderWithProviders(
        <MultiSectionForm
          initialValues={{
            // Section A — everything required except Q11 (last field) → A starts incomplete.
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
          }}
          onAutosave={vi.fn()}
          onSubmit={vi.fn()}
        />,
      );
      expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument();

      // Fill the last required field → after the 500ms autosave, A is complete
      // and a 400ms auto-advance is scheduled. (fireEvent, not userEvent, to
      // avoid the userEvent+fake-timers deadlock.)
      await act(async () => {
        fireEvent.change(screen.getByLabelText(/hours do you work/), { target: { value: '8' } });
      });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(500);
      });

      // The user keeps editing the section BEFORE the 400ms advance elapses.
      await act(async () => {
        await vi.advanceTimersByTimeAsync(150);
      });
      await act(async () => {
        fireEvent.change(screen.getByLabelText(/days in a week/), { target: { value: '6' } });
      }); // onInteract → cancels the pending advance

      // Let the original 400ms advance window fully elapse (150 + 300 > 400).
      await act(async () => {
        await vi.advanceTimersByTimeAsync(300);
      });

      // Still on Section A — the interaction canceled the pending auto-advance.
      expect(screen.getByRole('heading', { name: /Section A/ })).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
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
