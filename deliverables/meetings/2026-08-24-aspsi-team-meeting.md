August 24, 2026 Monday — ASPSI Team Meeting

3 Stand-up Points/Items

    1. What did I do/accomplish last week?
        a. Rebuilt all four instruments against the Aug-17 questionnaire set — this was the
           bulk of the two weeks. F1 and F2 were renumbered, so it wasn't just new wording,
           the question IDs moved underneath.
        b. Translation cleanup, around 30 tickets. Two were systemic, not one-off typos:
           - The enumerator directive was printing twice in 6 locales — 365 stored values.
           - 257 stored translations still had instructions, answer codes or routing notes
             sitting inside the translated text, so enumerators would have read them out.
        c. Opened UAT Round 7 on Aug 19 against the Aug-17 PAPI, and cleared 23 findings on
           Aug 20 in one pass across all four instruments.
        d. F3 section order is back to the printed sequence (#1305). That was a real
           divergence from the paper, not cosmetic.
        e. FROZE THE PSA SUBMISSION SET on Aug 20 — F1 v3.1.5, F2 v3.0.0, F3 v6.0.2,
           F4 v3.1.3. Saved two ways: the source code is tagged, and the actual installable
           packages are archived. So we can put the exact submitted version back on a tablet
           any time, even months from now. This is what ASPSI sends to PSA.
        f. Everything I build from now on shows "DEV BUILD — NOT THE VERSION SUBMITTED TO PSA"
           on the opening screen. Nobody can confuse a work-in-progress build with the
           submitted one, on a tablet or in a screenshot.

    2. What will I work on this week?
        a. Two new findings came in this morning — #1311 (F1 Q35.2) and #1312 (F2 Q24.2).
           Same class as each other: adopt DOH's final option list. Straightforward, but
           they change stored options, so they go in as a versioned build, not a quiet edit.
        b. Fleet propagation. The tablets are still on older builds — they need REMOVE and
           RE-ADD, not the Update menu, which doesn't reliably see our redeploys. Four
           tickets in Round 7 turned out to be stale apps, not real bugs, so this is worth
           doing properly once.
        c. Training prep — same priority as two weeks ago, and now it's August 24.
        d. Whatever else comes back from the testers on the Aug-20 builds.

    3. Are there any blockers/constraints preventing progress?
        - Yung roster po, pangatlong beses ko na pong hinihingi. Nasa 7 accounts pa rin ako,
          kailangan natin ng mga 147 (22 FS + 125 SE). Day 2 starts with everyone signing in
          and installing at the same time — hindi po talaga matutuloy yun sa 7 logins. Names
          in a list is enough po, ako na bahala sa iba.
        - Wala pa rin pong training dates. "August, 2026" pa rin ang nakalagay. August 24 na po.
          Kung may training pa this month, dalawang linggo na lang po ang natitira.
        - Apat na venue nang sabay, ako lang po ang nakapangalan — Pampanga, Los Baños, Cebu,
          CDO. Train-the-trainer na po kaya sa RAs?
        - TRANSLATIONS — and this one changed shape since I last reported it. The Aug-17 set
          rewrote the English, so the percentages I gave on Aug 10 no longer describe what's
          on screen. The old translations were re-keyed to the new English where they still
          matched, but anything DOH reworded on Aug 17 is now untranslated again. I need to
          re-measure before I can give a number I'd stand behind. What has NOT changed:
          validation and error messages are still 0% translated in all three instruments —
          every warning an enumerator hits is in English, whatever language the interview is in.
          The system takes translations the moment they're supplied. It is not a build problem.
        - Still waiting on ASPSI/DOH before I touch these, kasi data ang kasama:
            · Payment-source option order (F3 Q92/Q96/Q107/Q109) — reordering renumbers the
              codes, which moves the codebook and the committed tabulations.
            · F4 Q18 income brackets, 7 to 13 — every boundary moves, so income data can't be
              pooled across the change.
            · The -98/-99 "don't know / refused" gate.
            · F2 Q120 scale, and the "None" option on Q47/Q109.

    * Small ones, if there's time:
        - SE headcount says 125 but the cluster table adds up to 122. Still unreconciled,
          third meeting running.
        - F1 Q2 — the "Other (specify)" box still shows on screen even when it can't be typed
          into. Harmless to the data. Needs a decision whether to split it onto its own
          screen, which costs an extra screen for everyone.

Notes
    - The submitted set is frozen and recoverable. Any change from here is a new version —
      that's the point of the freeze, so please treat "can we just tweak this" as a version
      decision, not a small edit.

Carry-over from Aug 10
    - Roster and training dates — raised Aug 3 and Aug 10, both still open.
    - Translations — who supplies the remaining ones, and by when. Still unanswered.
    - The parked data items were held to round close. Round 7 is now open, so this is the
      moment to decide them.

For decision today
    - Training dates and venue assignments. This is the one blocking real preparation.
    - Translations: who supplies them, by when — especially the error messages.
    - The parked data items: decide now, or hold to the end of Round 7.
    - Roster: can I get the 147 names this week?

Dates
    - End of Project in the Contract — tentative end of November.
