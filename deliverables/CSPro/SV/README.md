# SupervisorApp — Facility Visit Log (Phase 3)

The DOH-Manual-named **Supervisor App**: a standalone CSEntry data-capture app the Field
Supervisor (FS) runs to log every facility touchpoint (arrival → courtesy-call → … →
departure) with **auto GPS + timestamp**, syncing to CSWeb. Spec:
`docs/superpowers/specs/2026-06-23-supervisor-app-phase3-facility-visit-log-design.md`.
(The QA review layer — coverage/partials/flags — is a *separate* tool at
`deliverables/CSWeb/supervisor-app/`, not this.)

## Iron rule

Never hand-edit `SupervisorApp.dcf` / `.ent.apc` / `.generated.fmf` / `.ent.qsf` — edit the
generators and rerun. (`SupervisorApp.fmf` is the bound copy of `.generated.fmf`.)

## Data model (one case per facility, keyed by 9-digit FACILITY_CODE = RRPPMMMFF)

- **VISIT_HEADER** — facility name, FS operator id.
- **COURTESY_CALL** (once) — endorsement obtained, head-interview date, focal person,
  discharge cutoff, HCW-list captured + count (+ optional photo), QR poster, patient-listing
  date, workstation arranged.
- **TOUCHPOINT** (repeating, max 30) — type (Arrival / Courtesy call / Endorsement delivery /
  Workstation / Focal person / HCW-list / Departure / Other) + **auto** timestamp + **auto**
  GPS (lat/long/alt/accuracy/satellites/readtime) + outcome note. GPS+timestamp are captured
  once per row in `TP_TYPE`'s postproc (via the shared `Capture-Helpers.apc` `ReadGPSReading`)
  and `protect()`ed (tamper-evident). The binary HCW photo (`VERIFICATION_PHOTO_IMAGE`) is
  off-form and syncs to CSWeb (#713 pattern).

## Build / deploy

```
cd deliverables/CSPro/SV
python generate_dcf.py            # -> SupervisorApp.dcf
python generate_apc.py            # -> SupervisorApp.ent.apc  (inlines Capture-Helpers into PROC GLOBAL)
python generate_fmf.py            # -> SupervisorApp.generated.fmf
python generate_qsf.py            # -> SupervisorApp.ent.qsf
python -m pytest -q               # generator structural tests (6)

# bind + compile + strict publish (from automation/):
python cspro_compile_driver.py SV --build --save     # regen -> bind -> compile (Ctrl+L/Ctrl+K)
#   read shots/SV_compile.png -> "Compile Successful"
# strict gate: open in Designer, File -> Publish Entry Application (.pen) [F7] -> SupervisorApp.pen
# CSWeb: File -> Publish and Deploy (needs the .pff + a CSWeb admin login the FIRST time to
#   register the SupervisorApp package); thereafter auto_deploy.py SV --deploy.
```

Registered in `automation/cspro_compile_driver.py` `SPECS["SV"]` (has_fmf_gen=True) and
`automation/auto_deploy.py` `INSTRUMENTS["SV"]` (CSWeb Package name `SupervisorApp`).

## v1 scope (per spec)

Facility log only (no household Visit Sheet); typed FACILITY_CODE (no PSGC cascade);
one optional HCW-list photo per case; EN-only labels; reconciliation report = fast-follow.
