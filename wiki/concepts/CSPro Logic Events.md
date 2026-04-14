---
type: concept
tags: [cspro, logic, procedural, events, blocks, consistency-edits]
source_count: 1
---

# CSPro Logic Events

CSPro data entry applications execute logic at well-defined points in the data entry lifecycle. Understanding the order of these events is essential for writing correct skip logic, validations, and prefills — and for placing each piece of code in the right procedure so it fires at the right time.

## The procedural sections

Every dictionary element (form file, level, form, roster, record, item, block) can have one or more procedural sections attached. The available sections, in firing order:

| Section | Fires |
|---|---|
| `preproc` | **Before** entering the element. Use for initialization, prefills, conditional skips. |
| `onfocus` | When the cursor arrives on the element. Use for value-set switching, dynamic question text setup. |
| `onoccchange` | When the current occurrence of a repeated element changes (rosters). |
| `killfocus` | When the cursor leaves the element. Use for cross-field validations that should fire as the operator moves on. |
| `postproc` | **After** the element is fully entered. Use for end-of-block consistency edits. |

For data entry, **`preproc`, `onfocus`, `onoccchange`, `killfocus`, and `postproc` are all executed in the order in which they're encountered.**

## Default event order

For a two-level data entry application with no skip/advance statements, the natural flow is:

```
Form File preproc
    Level 1 preproc
        Form 1 preproc
        Form 1 onfocus
            Field 1.1 preproc
            Field 1.1 onfocus
            (entry of Field 1.1)
            Field 1.1 killfocus
            Field 1.1 postproc
            ...
            Field 1.N preproc
            Field 1.N onfocus
            (entry of Field 1.N)
            Field 1.N killfocus
            Field 1.N postproc
        Form 1 killfocus
        Form 1 postproc
        Form 2 preproc
        ...
    Level 2 preproc
        Form 3 preproc
        ...
```

This is the same for both system-controlled and operator-controlled applications. (See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Entry Modes]].)

## Blocks

A **block** is a way to group several fields from the same group into a related unit. Blocks have two main purposes:

1. **On mobile**, all fields in a block can be displayed on the **same screen**, allowing the operator to enter them in any order. This is the only way to put multiple questions on one Android screen.
2. **Logic** can be defined at the block level — a single place to write checks that apply to multiple fields.

To create a block: Ctrl-click multiple fields in the Forms Tree → right-click → `Add Block`. The block's icon is red. Blocks can contain only fields from the *same group* (e.g., all population-record items).

### Event order with blocks

For a block containing `FIELD1` and `FIELD2`:

```
BLOCK (preproc, onfocus)
FIELD1 (preproc, onfocus, killfocus, postproc)
FIELD2 (preproc, onfocus, killfocus, postproc)
BLOCK (killfocus, postproc)
```

Block-level logic should hold cross-field checks; field-level logic should be minimal. Use block names (not field names) in `advance`, `ask`, `move`, `reenter`, `skip` statements — this lets you reorder fields inside the block without rewriting movement logic.

### Example: validating a date-of-birth block

```
PROC DOB_BLOCK
preproc
    // only ask date of birth in conventional households
    ask if HH_TYPE = 1;

postproc
    numeric dob_mm = DOB_MONTH;
    if dob_mm = missing then dob_mm = 1; endif;

    numeric dob_dd = DOB_DAY;
    if dob_dd = missing then dob_dd = 1; endif;

    numeric dob_yyyymmdd = DOB_YEAR * 10000 + dob_mm * 100 + dob_dd;

    if not datevalid(dob_yyyymmdd) then
        errmsg("The date of birth is not valid");
        reenter;
    elseif dob_yyyymmdd > sysdate("YYYYMMDD") then
        errmsg("The date of birth cannot be in the future");
        reenter;
    endif;
```

A "no field" block can also exist — useful as a control anchor for orienting skips.

## Consistency edits at data entry

CSPro distinguishes:

- **Structure edits** — verify the case has the right records in the right order, correct counts of household members, etc. Typically run as batch edits after entry, but can run during entry too.
- **Consistency edits** — verify item-to-item logical consistency (e.g., a 9-year-old should not have completed secondary school).

Both can be written as logic in the data entry application using the same `errmsg`, `reenter`, and movement statements. The same logic can later be re-run as a batch edit pass over the saved data, either interactively or in batch mode.

The Census Bureau guidance is that for **complex surveys with smaller volumes** (Household Surveys, Income & Expenditure Surveys), running consistency checks at entry time is desirable — errors get resolved while the questionnaire (and respondent) are still at hand. For censuses, batch edits after the fact are preferred.

For UHC Survey Year 2 — small-volume, complex survey — **all consistency checks should run at entry**.

## Other entry-time controls

| Mechanism | Purpose |
|---|---|
| `errmsg(...)` | Display a custom error message at entry time. |
| `reenter` | Force the operator back to the field that triggered the error. |
| `skip`, `advance`, `endgroup`, `endlevel` | Control flow movement. |
| `OnStop` | Trap attempts to exit the interview (Stop button, Alt+F4). Block, redirect, or save partial case. |
| `ispartial` | Test whether the current case is a partial save. |
| `putnote`, `getnote`, `editnote` | Field-level enumerator notes. |
| `accept`, `showarray` | Pop up a window of valid values for operator selection. |
| `loadcase`, `retrieve`, `selcase` | Read from external dictionaries / files. |
| `visualvalue`, `highlighted` | Examine the value being entered before it's committed. |

## Project relevance

- **Block usage for date entry** — F1, F3, F4 all collect dates (interview date, birth date, last visit). Use a block per date so all three fields appear on one tablet screen and the validation runs in the block's `postproc`.
- **`onfocus` for value-set switching** — F3 outpatient/inpatient routing and F4 person-conditional questions both follow the MyCAPI walkthrough's `setvalueset` in `onfocus` pattern.
- **`postproc` for cross-field consistency** — every "if A, then B" check in the F1/F3/F4 questionnaires (e.g., facility type vs services offered, age vs fertility questions) should live in the `postproc` of the field that triggers the check, with `errmsg` + `reenter` for blocking corrections.
- **`OnStop` for partial save** — every CAPI app should override `OnStop` to confirm the operator's intent, save the partial case, and offer to schedule a callback (per the Census Bureau's CAPI strategies).
- **Run consistency at entry, not in batch** — UHC Year 2 is the survey-not-census case, so all checks belong in entry-time logic.

## Sources

- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
