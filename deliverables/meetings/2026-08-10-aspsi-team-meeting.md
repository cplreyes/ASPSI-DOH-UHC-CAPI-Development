August 10, 2026 Monday — ASPSI Team Meeting

3 Stand-up Points/Items

    1. What did I do/accomplish last week?
        a. Cleared the whole Aug 6-7 review batch — 64 findings across F1/F3/F4, all fixed,
           deployed and closed. The big one: 43 questions where "I don't know" / "None of the
           above" could be ticked together with a real answer now BLOCK instead of just warning.
           Several had no check at all — their option was coded outside the usual convention so
           nothing ever matched it.
        b. Deployed again this morning with the rest: F1 v1.3.1, F3 v1.4.1, F4 v1.5.9.
           - Visit dates are now typed MMDDYYYY like the paper (F1 and F3), with the MM/DD/YYYY
             line underneath confirming it read the date right.
           - F1 Q57 — the capitation definition is back as a blue note. It had been taken off
             the question in an earlier round and never put back anywhere, so enumerators had
             no definition at all. That one was our miss.
           - F4 Q46 — each PhilHealth category now shows its definition beside its own option,
             and the duplicate "Dependent" option is removed per the list ops confirmed.
        c. Moved tablet syncing off csweb.asiansocial.org onto capi.asiansocial.org. Takes
           effect when they re-add the app, so the old address stays up until every tablet has.
        d. Found and fixed a bug nobody reported: on a single-visit case in F3, leaving the
           final-visit date blank could wrongly block the enumerator.

    2. What will I work on this week?
        a. Training prep — this is the priority now, it's August 10 na.
        b. Get the remaining decisions closed so the instruments stop moving before training
           (list in item 3).
        c. F2 HCW side: the Facilities management page is built but was never merged, so it's
           not on the live admin portal. Ready to go, just needs the merge.
        d. Whatever comes back from the testers on this morning's build.

    3. Are there any blockers/constraints preventing progress?
        - Yung roster po, kailangan ko na talaga. Nasa 7 accounts pa rin ako, kailangan natin
          ng mga 147 (22 FS + 125 SE). Day 2 starts with everyone signing in and installing at
          the same time — hindi po matutuloy yun sa 7 logins. Names in a list is enough, ako na
          bahala sa iba. Same request as last week po.
        - Wala pa rin pong training dates. "August, 2026" pa rin ang nakalagay sa dalawang
          programme. August 10 na po ngayon.
        - Apat na venue nang sabay, ako lang po ang nakapangalan — Pampanga, Los Baños, Cebu,
          CDO. Train-the-trainer na lang po kaya sa RAs?
        - TRANSLATIONS. This is the one I'd flag hardest. I measured the deployed builds:
            · The validation/error messages are 0% translated — English only, all three
              instruments. Every warning an enumerator hits is in English whatever language
              they're interviewing in.
            · The question text itself is 28-68% translated depending on language. Ilocano F1
              is the worst — roughly 7 of every 10 questions still read in English.
            · Hiligaynon and Ilocano are consistently the weakest.
          The system is ready to take them the moment they're supplied — it's not a build
          problem. But if enumerators are interviewing in Ilocano or Hiligaynon, a big part of
          the instrument is English on screen. Better to decide now than at training.
        - Six items are waiting on ASPSI/DOH before I touch them, kasi data ang kasama:
            · Payment-source option order (F3 Q92/Q96/Q107/Q109) — reordering renumbers the
              codes, which moves the codebook, the committed tabulations, and the pretest data
              already collected. Held to round close.
            · F4 Q18 income brackets, 7 → 13 — every boundary moves, so the income data can't
              be pooled across the change. Held to round close.
            · The -98/-99 "don't know / refused" gate — waiting on approval since before this
              batch.

    * Small ones, if there's time:
        - SE headcount says 125 but the cluster table adds up to 122. Still unreconciled.
        - Result of Visit — I declined removing "Completed" and "Replaced" from the list. The
          app writes those codes itself (every finished interview is assigned "Completed"), so
          taking them off the list would mis-record the round's completion counts. Reasons are
          on the tickets.
        - One display item left on F1 Q2: the "Other (specify)" box shows on screen even when
          it can't be typed into. Confirmed on a tablet. Harmless to the data, but I need a
          decision on whether to split it onto its own screen — it costs an extra screen for
          everyone.

Notes
    - CAPI SHOULD BE PREPARED BY FRIDAY Later in the afternoon
    - How do we do performance matrix almost realtime?
    - 

Carry-over from Aug 3
    - Roster and training dates were raised last week; both still open.
    - Revised Forms (Instruments) and the pretesting results presentation were due this week.
    - Directory of Mayors / Hospital Directors — with Ma'am Myra.

For decision today
    - Training dates and venue assignments.
    - Translations: who supplies the remaining ones, and by when.
    - Whether the six parked data items wait for round close (my recommendation) or move now.

Dates
    - End of Project in the Contract — tentative end of November.
