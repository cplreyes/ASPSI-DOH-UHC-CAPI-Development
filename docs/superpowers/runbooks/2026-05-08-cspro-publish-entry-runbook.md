---
title: CSPro 8.0 Publish Entry Application — manual F7 step
type: runbook
date: 2026-05-08
status: active
applies_to: UHC Survey System build (Plan 1+)
---

# CSPro 8.0 Publish Entry Application — manual F7 step

## Why this exists

CSPro 8.0 has **no documented headless CLI** for compiling `.ent` source to `.pen` binary application files. This is the only step in the UHC Survey build pipeline that requires CSPro Designer GUI.

Investigation confirmed:
- `CSDeploy.exe` — GUI Deploy Application wizard (post-publish bundling, not compile)
- `CSPack.exe` — packages already-compiled `.pen` files via `.cspack` spec (also post-publish)
- `CSPro.exe /publish <ent>` — opens GUI Designer, does not run headlessly
- `CSPro.exe` `/?` `--help` etc. — no documented CLI flags

The only canonical compile path is **File → Publish Entry Application** (or **F7**) inside CSPro Designer GUI, per the CSPro 8.0 Users Guide and Khurshid Arshad's tutorials.

This runbook covers that one manual step. Everything around it (generators, splice, package, upload) is automated.

## When to run this

After every successful `python build_all.py --env=<env>` that emits new or modified source files. The script ends with a checklist of `.ent` files to compile.

## Steps

### 1. Open CSPro Designer

Run: `& 'C:\Program Files (x86)\CSPro 8.0\CSPro.exe'`

### 2. For each `.ent` listed by `build_all.py`:

1. **File → Open Application** (or **Ctrl+O**) → navigate to the `.ent` path printed by the script.
2. Wait for Designer to load (a few seconds for large dictionaries like F1 with 671 items).
3. Press **F7** (or **File → Publish Entry Application**).
4. In the dialog: confirm the output `.pen` path (default = same folder, same basename) → **Save**.
5. **File → Close** to release the file before opening the next one.

### 3. Verify

After compiling all instruments, confirm the `.pen` files exist alongside their `.ent`:

```powershell
Get-ChildItem deliverables/CSPro/UHC-Survey-System -Recurse -Include *.pen | Select-Object FullName, Length
```

Expected: one `.pen` per instrument, sized roughly proportional to its `.fmf` complexity (login ~1 KB, F1 several MB).

### 4. Continue the build

After compile, run the next stage of the pipeline (CSWeb upload, CSPack, etc.). These are scriptable.

## Time budget

Per-instrument compile click: ~5-10 seconds (open → F7 → save → close).

Phase 1 has 3 instruments (login + menu + F1) → ~30 seconds per build cycle.
Phase 2 will add 4 more (PLF + F3 + F4_listing + F4) → ~60 seconds total per build cycle.

Cumulative across a multi-day build: still less manual time than a single Designer FMF layout pass would have been.

## Failure modes

### Designer reports compile error
The `.ent`'s referenced `.dcf`/`.fmf`/`.apc` files have a syntax issue. Designer's error pane points to the line; fix in the corresponding `generate_*.py` and re-run `build_all.py` to regenerate the source.

### F7 grays out
The `.ent` isn't focused as the active document, or it's a `.bat` (batch app) not an `.ent` (entry app). Click the `.ent` tab to focus it; only entry apps publish to `.pen`.

### Designer hangs on Open
Likely a previous Designer session is still holding the file. Close all Designer windows; check Task Manager for orphan `CSPro.exe` processes; restart Designer.

## Future work

- **Spike: AutoHotkey wrapper** — drive Designer GUI programmatically. Fragile but achievable.
- **Spike: CSPack with .cspack spec** — investigate whether `.cspack` includes a compile directive. Some forum threads hint at this; not confirmed.
- **Watch CSPro 8.x release notes** — the JSON-format migration in 8.0 was specifically for tooling integration; future versions may add a CLI publish.

## Related

- Plan 1: `docs/superpowers/plans/2026-05-08-uhc-survey-system-build-phase-1.md`
- Spec: `docs/superpowers/specs/2026-05-08-uhc-survey-system-build-design.md`
- Mentor: Khurshid Arshad, [Tutorial 4: Deploy Application @ 00:09](https://www.youtube.com/watch?v=hil_SpX_fsA)
- Mentor: Khurshid Arshad, "Publish entry application (.pen) and Deploy Application packaging" technique card (in `2022-04-24_using-html-dialogs-...` video)
