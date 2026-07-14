"""Build pretest-guide.html by reusing hub-guide.html's exact shell (head + topbar + footer),
so the page is native to the docs site and cannot drift from the template."""
import pathlib, re

HERE = pathlib.Path(__file__).parent
# The shell lives with the published site, not here; resolve it so this builds
# from any working directory (it used to only work if run beside hub-guide.html).
SHELL = HERE / ".." / "landing" / "docs" / "hub-guide.html"
OUT = HERE / "pretest-guide.html"

src = SHELL.resolve().read_text(encoding="utf-8")

head = src[: src.index('<main id="main">')]
foot = src[src.index("    </main>") :]

# retitle the shell for this page
head = head.replace(
    "<title>Supervisor &amp; Enumerator Hub — Training Guide · UHC Survey Year 2</title>",
    "<title>CAPI Pretest — Field Guide (15 July 2026) · UHC Survey Year 2</title>",
)
head = re.sub(
    r'content="Training guide for the role-based hub[^"]*"',
    'content="Field guide for the UHC Survey Year 2 CAPI pretest (15 July 2026): what to do before you '
    'start, the new Interview status / replacement codes, and what each role — Enumerator, Supervisor, '
    'Data Manager and F2 Admin — needs to do and report."',
    head,
    flags=re.S,
)
head = head.replace(
    "<div class=\"topbar-sub\">Supervisor &amp; Enumerator Hub</div>",
    "<div class=\"topbar-sub\">CAPI Pretest — 15 July 2026</div>",
)

BODY = """
      <div class="container">
        <p class="page-eyebrow">Field guide · pretest · 15 July 2026 · Brgy. Mayondon, Los Ba&ntilde;os</p>
        <h1>The CAPI pretest &mdash; what to do, and what to tell us</h1>
        <p class="lede">
          This is a <strong>pretest</strong>, not another round of app testing. We are no longer asking
          &ldquo;does the app work?&rdquo; &mdash; we are asking <strong>&ldquo;does the questionnaire work on a real
          respondent?&rdquo;</strong> So the most valuable thing you can bring back is not a bug. It is the
          moment a respondent looked confused, the question you had to explain twice, the skip that felt
          wrong, or the household that simply was not there. Write those down. That is what a pretest is for.
        </p>

        <p class="banner">
          <strong>Everyone, before 08:00:</strong> remove the survey app from the tablet and add it again from
          CSWeb. Tapping <em>&ldquo;Update Installed Applications&rdquo;</em> is <strong>not</strong> enough &mdash; the tablet
          can silently keep yesterday&rsquo;s build, everything will look completely normal, and none of
          today&rsquo;s changes will be there. Details in step&nbsp;1.
        </p>

        <article>

          <section>
            <h2 class="sec">1. Before you start &mdash; remove and re-add the app <em>(everyone)</em></h2>
            <p>New builds went to CSWeb on <strong>14 July</strong>. CSEntry&rsquo;s
              <strong>&ldquo;Update Installed Applications&rdquo;</strong> does <strong>not</strong> reliably pick up a
              redeploy.</p>
            <ol>
              <li>In <strong>CSEntry</strong>, <strong>remove</strong> the survey application.</li>
              <li><strong>&#8942; &rarr; Add Application &rarr; CSWeb server</strong> &mdash;
                <code>https://csweb.asiansocial.org/csweb/api</code> &rarr; <strong>Connect</strong>.</li>
              <li>Download it again, then <strong>check the version in the app list</strong>:</li>
            </ol>
            <table>
              <thead><tr><th>Instrument</th><th>Must show</th></tr></thead>
              <tbody>
                <tr><td>Facility Head Survey (F1)</td><td><strong>v1.1.0</strong></td></tr>
                <tr><td>Patient Survey (F3)</td><td><strong>v1.1.0</strong></td></tr>
                <tr><td>Household Survey (F4)</td><td><strong>v1.4.0</strong></td></tr>
                <tr><td>Supervisor &amp; Enumerator Hub (LoginApp)</td><td>v1.0.2</td></tr>
              </tbody>
            </table>
            <div class="callout">
              <strong>If the version does not match, stop.</strong> Do not start interviewing on an old build &mdash;
              the data will be missing today&rsquo;s fields and we will not be able to tell it apart from a real
              result. Tell your STL, and report it on the pretest tracker.
            </div>
          </section>

          <section>
            <h2 class="sec">2. NEW &mdash; &ldquo;Interview status&rdquo;: what to do when there is no interview <em>(enumerators)</em></h2>
            <p>
              Every case now opens on an <strong>Interview status</strong> screen, right after you enter the
              Questionnaire Number. It has <strong>seven</strong> options &mdash; it used to have four.
            </p>
            <ul>
              <li><strong>Interview is going ahead</strong> &rarr; leave it on <strong>Continue interview</strong>.
                That is the default. Do nothing.</li>
              <li><strong>The interview cannot happen at all</strong> &rarr; you must <strong>still open the case</strong>,
                and choose the reason:</li>
            </ul>
            <table>
              <thead><tr><th>Choose</th><th>When</th></tr></thead>
              <tbody>
                <tr><td><strong>Not interviewed &mdash; refused</strong></td><td>They declined at the door, or declined consent.</td></tr>
                <tr><td><strong>Not interviewed &mdash; not found</strong></td><td>Nobody there, vacant, or you could not locate them after your call-backs.</td></tr>
                <tr><td><strong>Not interviewed &mdash; ineligible</strong></td><td>They do not qualify for this survey.</td></tr>
              </tbody>
            </table>
            <p>
              The app then jumps <strong>straight to the closing screen</strong>, records the visit as
              <strong>Replaced</strong>, and ends the case. You do <strong>not</strong> walk through the questionnaire.
            </p>
            <div class="callout">
              <strong>&#9940; Do not just skip the unit and move on.</strong>
              If you never open a case, that unit is <strong>invisible</strong> to the office &mdash; we cannot see that
              you went, we cannot see why it failed, and we cannot account for the replacement.
              <strong>A unit you could not interview is still work you did.</strong> Open the case, mark the reason,
              then move on to the substitute.
            </div>
            <p>
              <strong>&ldquo;Postponed / reschedule&rdquo; is different.</strong> Use it when you <em>are</em> coming back later.
              The three <em>Not interviewed</em> options mean this unit is being <strong>replaced by a substitute</strong>.
            </p>
            <div class="callout">
              This is <strong>brand new</strong> and today is its first real use. If anything about it felt unclear,
              slow, or wrong in the field, that is exactly the kind of finding we want &mdash; please report it.
            </div>
          </section>

          <section>
            <h2 class="sec">3. Questionnaire Numbers <em>(enumerators)</em></h2>
            <p>
              Enter the <strong>full 12 digits</strong>. The app checks the number against the PSGC, so a made-up or
              placeholder number is <strong>rejected at the very first field</strong> &mdash; use only the range assigned
              to you.
            </p>
            <p>
              <strong>Your assigned numbers are on your assignment sheet</strong> &mdash; your STL hands these out.
              They are deliberately <strong>not</strong> listed on this page: it is a public URL, and we do not publish
              who holds which login or which households.
            </p>
            <p>
              What the app actually checks is the <strong>first 7 digits</strong>, which are the
              city/municipality &mdash; <code>0403411</code> is Los Ba&ntilde;os, <code>0403402</code> is Bay. The rest
              of the number identifies the facility or household. Each enumerator gets a
              <strong>contiguous block</strong>; use only your own, so that two people can never open the same case.
            </p>
            <div class="callout callout-warn">
              <strong>Household survey (F4): the number does not set the barangay.</strong> It only carries the
              municipality. After the case opens you must still <strong>pick the barangay yourself</strong> from the
              dropdown &mdash; for Day 1 that is <strong>Mayondon</strong>. The case key will look perfectly valid if you
              pick the wrong one, so check it.
            </div>
            <div class="callout">
              If a Questionnaire Number is rejected at the first field, do <strong>not</strong> improvise another one.
              Check it against your sheet, and if it still fails, tell your STL &mdash; a rejected number usually means
              the sheet and the app disagree, which is itself a finding worth reporting.
            </div>
          </section>

          <section>
            <h2 class="sec">4. Where and when &mdash; and which app <em>(everyone)</em></h2>
            <p>
              Four different instruments are in the field this round. <strong>Which app you open depends on who you are
              interviewing</strong>, not on where you are:
            </p>
            <table>
              <thead>
                <tr><th>Respondent</th><th>App to open</th></tr>
              </thead>
              <tbody>
                <tr><td>Facility Head</td><td><strong>F1</strong> &mdash; Facility Head Survey (CSEntry)</td></tr>
                <tr><td>Healthcare Worker (HCW)</td><td><strong>F2</strong> &mdash; the <em>web app</em>, not CSEntry. No Questionnaire Number.</td></tr>
                <tr><td>Inpatient / Outpatient</td><td><strong>F3</strong> &mdash; Patient Survey (CSEntry)</td></tr>
                <tr><td>Household</td><td><strong>F4</strong> &mdash; Household Survey (CSEntry)</td></tr>
              </tbody>
            </table>
            <table>
              <thead>
                <tr><th>Day</th><th>Site</th><th>Instruments</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Wed 15 Jul</strong></td>
                  <td>Brgy. Mayondon, Los Ba&ntilde;os</td>
                  <td>F4 &mdash; 20 households <em>(continues 17 Jul if the quota is not met)</em></td>
                </tr>
                <tr>
                  <td><strong>Thu 16&ndash;17 Jul</strong></td>
                  <td>Laguna Provincial Hospital &ndash; Bay <em>(Bay, Laguna)</em></td>
                  <td>F1 facility head · F2 HCW · F3 &mdash; 3 inpatient, 2 outpatient</td>
                </tr>
                <tr>
                  <td><strong>Fri 17 Jul</strong></td>
                  <td>Los Ba&ntilde;os Rural Health Unit</td>
                  <td>F1 facility head · F2 HCW · F3 &mdash; 5 outpatient</td>
                </tr>
                <tr>
                  <td><strong>Mon 20 Jul</strong></td>
                  <td>Brgy. Mayondon, Los Ba&ntilde;os</td>
                  <td>F4 &mdash; target set on the day</td>
                </tr>
                <tr>
                  <td><em>TBD</em></td>
                  <td>Los Ba&ntilde;os Doctors Hospital · St. Jude Hospital</td>
                  <td>F1 facility head · F2 HCW · F3 patients</td>
                </tr>
              </tbody>
            </table>
            <div class="callout">
              <strong>Bay is a different municipality from Los Ba&ntilde;os.</strong> Its Questionnaire Numbers start
              <code>0403402</code>, not <code>0403411</code>. If you are at Laguna Provincial Hospital and your number
              starts <code>0403411</code>, it is the wrong number &mdash; stop and tell your STL before you enter it.
            </div>
          </section>

          <section>
            <h2 class="sec">5. Consent <em>(enumerators)</em></h2>
            <p>
              Consent is <strong>read aloud from the printed SJREB sheet</strong> (Annex&nbsp;H), in the language the
              respondent understands. <strong>There is no consent screen in the app</strong> &mdash; do not go looking for
              one. What you record in the app is the <em>outcome</em>, on the Interview status screen: a refusal at
              the door is <strong>Not interviewed &mdash; refused</strong>.
            </p>
          </section>

          <section>
            <h2 class="sec">6. Supervisors / STLs</h2>
            <ul>
              <li><strong>Before 08:00:</strong> confirm <em>every</em> tablet in your team has removed and re-added the
                app, and that the version matches step&nbsp;1. This is the single most likely thing to go wrong today.</li>
              <li><strong>Hub:</strong> sign in to <strong>LoginApp</strong>, hand out enumeration areas, and collect
                finished interviews over Bluetooth &mdash; see the
                <a href="/docs/hub-guide.html">Supervisor &amp; Enumerator Hub guide</a>.
                If Bluetooth misbehaves, enumerators type their 12-digit keys from paper and the pretest continues.
                <strong>The hub failing degrades convenience, not data collection.</strong></li>
              <li><strong>End of day:</strong> make sure every tablet has <strong>synced</strong>. A synced case is safe on
                the server; an un-synced case dies with the tablet.</li>
              <li><strong>Reconcile:</strong> cases synced vs cases assigned &mdash; including the <strong>replacements</strong>.
                A unit marked <em>Not interviewed</em> is still a case and still syncs. If an enumerator reports
                &ldquo;nobody was home&rdquo; but no case exists, that is a finding: they skipped the unit instead of
                recording it.</li>
            </ul>
          </section>

          <section>
            <h2 class="sec">7. Data Manager &mdash; CSWeb</h2>
            <ul>
              <li><strong>Sync Dashboard:</strong>
                <a href="https://csweb.asiansocial.org/docs/dashboard.html">csweb.asiansocial.org/docs/dashboard.html</a>
                &mdash; refreshes about every 2 minutes. Watch cases arrive live.</li>
              <li><strong>New today:</strong> a <strong>Replacements</strong> tile, and a per-enumerator
                <strong>Replaced</strong> column in the productivity panel. Rows are keyed on the
                <strong>CSWeb login</strong> that uploaded the case, not the typed name.</li>
              <li><strong>Expect zeros at first.</strong> The databases were cleaned for a fresh start, so the dashboard
                reads 0 until the first sync lands. A zero on the Replacements tile early in the day means
                &ldquo;no data yet&rdquo;, <em>not</em> &ldquo;no replacements&rdquo;.</li>
              <li><strong>Map report:</strong>
                <a href="https://csweb.asiansocial.org/docs/map.html">csweb.asiansocial.org/docs/map.html</a>.</li>
              <li>If cases do not appear, check the <strong>Data</strong> tab in CSWeb first &mdash; the dashboard is
                regenerated on a timer, so a short lag is normal and is <strong>not</strong> data loss.</li>
            </ul>
          </section>

          <section>
            <h2 class="sec">8. F2 Admin &mdash; Healthcare-Worker PWA</h2>
            <ul>
              <li>Portal: <a href="https://uhc-hcw.asiansocial.org/admin">uhc-hcw.asiansocial.org/admin</a></li>
              <li>The F2 database was <strong>reset to a clean state</strong> on 14 July: one bootstrap administrator, no
                responses, no HCWs. Re-create the ASPSI users and HCWs, then re-issue enrolment links.</li>
              <li>F2 is <strong>self-administered</strong> &mdash; it has no enumerator and no replacement concept. A
                non-response there is an <strong>unredeemed enrolment link</strong>, not a replaced case, and it will not
                appear in the pretest replacement counts.</li>
            </ul>
          </section>

          <section>
            <h2 class="sec">9. How to report a finding <em>(everyone)</em></h2>
            <p>
              Everything goes on the pretest tracker:
              <a href="https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/839"><strong>issue #839</strong></a>.
            </p>
            <ol>
              <li><strong>New issue &rarr; &ldquo;CAPI UAT feedback&rdquo;</strong>.</li>
              <li>Apply the label <code>from-pretest-2026-07</code> &mdash; <strong>required</strong>. This is what keeps pretest
                findings separate from the old UAT bug list.</li>
              <li>Add a severity (<code>severity:critical</code> &hellip; <code>severity:low</code>).</li>
            </ol>
            <p>Include the <strong>instrument</strong>, the <strong>Questionnaire Number</strong>, and the <strong>exact
              question or screen</strong>; what you expected; what actually happened. A photo or a screen recording is
              worth a paragraph.</p>
            <div class="callout">
              <strong>If the finding is a respondent&rsquo;s confusion, quote them.</strong> &ldquo;Q47 &mdash; the respondent
              asked me what &lsquo;out-of-pocket&rsquo; meant, I had to explain it twice&rdquo; is a <em>better</em> pretest
              finding than a cosmetic UI bug. That is the sort of thing that only a pretest can catch, and it is
              the reason we are in the field today.
            </div>
          </section>

          <section>
            <h2 class="sec">Credentials</h2>
            <p>
              Your usernames and passwords are sent to you <strong>privately</strong> &mdash; they are never posted in this
              guide, on the tracker, or in Slack. If you do not have yours by <strong>07:30</strong>, message Carl
              directly. Do not share or re-use another person&rsquo;s login: the dashboard now attributes every case to
              the account that uploaded it.
            </p>
          </section>

          <section>
            <h2 class="sec">Support</h2>
            <p>
              Problem during the pretest? Tell your STL first. Anything that <strong>blocks data collection</strong> &mdash;
              a tablet on the wrong build, a rejected Questionnaire Number, a case that will not sync &mdash; escalate
              to Carl immediately; do not work around it silently.
            </p>
          </section>

        </article>
      </div>
"""

pathlib.Path("pretest-guide.html").write_text(head + '<main id="main">\n' + BODY + foot, encoding="utf-8")
print("wrote %s (%d bytes)" % (OUT, OUT.stat().st_size))
