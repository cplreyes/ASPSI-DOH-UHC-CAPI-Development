# Supervisor App — Field Supervisor SOP (Facility Visit Log)

**What it is:** the app you use to log every facility touchpoint with automatic GPS +
timestamp. One record per facility, built up across the engagement (courtesy-call day,
patient-listing day, interview days).

## Install (once, on your own account)

1. CSEntry → ⋮ → **Add Application → From server** → enter the project server → sign in with
   **your own FS username/password** (do not share credentials).
2. Install **SupervisorApp** (alongside the survey instruments you monitor).
3. To refresh after an update: **remove the app, then Add Application → From server again**
   (the ⋮ "Update Installed Applications" is unreliable).

## At each facility

1. Open **SupervisorApp** → add a case (or open the existing case for this facility) and enter
   the **9-digit facility code** (RRPPMMMFF — the same facility portion as the survey case key)
   + facility name + your operator id.
2. **Log each touchpoint as it happens** on the Touchpoint screen: add a row and pick the type
   (Arrival when you arrive, Courtesy call, Endorsement delivery, Workstation, Focal person,
   HCW-list, **Departure** when you leave; Other + a note for anything else). The **time and GPS
   stamp automatically** — you don't type them, and they lock read-only.
3. On the first visit, fill the **Courtesy-Call** screen: endorsement obtained, focal person,
   discharge cutoff, scheduled interview/patient-listing dates, workstation, QR poster, and the
   **HCW master-list** count (tick "captured" and take the optional photo of the printed list).
4. The visit log saves as you go (partial save is on) — you can stop and resume the same case.

## Sync

Sync to the server **nightly** (and at each facility if you have signal), same as the
instruments: tap Synchronize → wait for "Successfully synced". Your visit log uploads to CSWeb
where it can be reconciled against the planned visit schedule.
