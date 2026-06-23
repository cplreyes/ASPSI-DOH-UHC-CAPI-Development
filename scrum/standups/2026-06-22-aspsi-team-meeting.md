June 22, 2026 Monday ASPSI Team Meeting

A. Team Meeting Concerns
    1. What did I do/accomplish last week?
        a. F3/F4 mid-interview stop/withdraw handling - working on device; finished vs. partial cases now clearly separated in the data. (Marriz's flag)
        b. Built a Supervisor workflow/review tool (v1) - coverage vs. plan, partials, and data-quality flags.
        c. CSWeb monitoring dashboard is live - cases by instrument, region, status, date. Improved maps and visualization.
        d. Round 5 testing OPENED (June 22-27) across all surfaces (F1, F3, F4, F2, Admin, CSWeb).
    2. What will I work on this week?
        a. Continued development together with the testers - run Round 5 and turn their feedback into fixes/improvements as it comes in.
            Issues tackled per instrument so far (resolved through UAT):
                F1 (Facility Head): 51
                F3 (Patient): 43
                F4 (Household): 124
                F2 (HCW survey + Admin Portal): 79
                CSWeb: 7   |   PLF: 5
            Round 5 (June 22-27) just opened - 6 logged, 0 closed yet (Day 1).
        b. Align with the Survey Manual, not just the instruments-only MVP - broaden from the forms to the full survey operation (monitoring, supervisor review, field-ops/training).
        c. Get the Supervisor review tool ready to go live.
        d. Plan the move of the F2 Survey and Admin Portal to our own server - we're hitting Cloudflare's free-tier limits, and that free setup won't handle the full intended user load once live (still in development now).
    3. Are there any blockers/constraints?
        a. No blockers yet.

Note: A few items need a separate discussion with the ASPSI RAs (after the team meeting):
    - PhilHealth option lists - the 3 images from Kidd's June 9 email (to build Q38.1/Q38.2 on F3 and Q45.1/Q45.2 on F4).
    - QA-supervisor names - to bring the Supervisor tool live.
    - Translations: Hiligaynon (F3 & F4), *Tagalog and Ilocano (F1-F4).
    - Checkbox style piloted on Q148 - roll out to the other ~60 select-all questions, or keep on Q148 only?
    - Supervisor app Phase 2 (Bluetooth sync hub) - build now or keep deferred?

Meeting with Team:

- Dashboard and Visualizations
- Show progress, which lagging
- Coverage per site
- Performance metrics of the enums
- What regions, lag, completion rates, coverage, see ahead of time
- Basis for request of extension
  - Aug, for Training
  - Sep, Rollout