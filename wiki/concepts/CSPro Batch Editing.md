---
type: concept
tags: [cspro, batch, edits, imputation, hot-deck, csbatch, errmsg, consistency]
source_count: 1
---

# CSPro Batch Editing

**Batch editing** is the post-collection cleaning pass: a separate CSPro application reads raw data files, runs structure/validity/consistency checks, optionally imputes missing or invalid values, and writes a corrected file plus reports. Built in the **Batch Edit Designer**, run by **CSBatch**. Source: [[wiki/sources/Source - CSPro 8.0 Complete Users Guide]] (Batch Editing section, pp. 273–301).

This is the *back-end* counterpart to data entry: you cannot fully validate during entry without slowing the enumerator, so most consistency edits run here. Built on the same dictionary, the same logic language, and the same logic events as CAPI ([[wiki/concepts/CSPro Language Fundamentals]], [[wiki/concepts/CSPro Logic Events]]).

## Application files

A batch edit application is a small bundle of files:

| File | Purpose |
|---|---|
| `.bch` | Application file (links the rest together) |
| `.ord` | Edit order file (one per app, references the primary `.dcf`) |
| `.apc` | Logic file (CSPro language statements — `PROC GLOBAL`, `PROC ITEM_NAME`, etc.) |
| `.mgf` | Optional message file — numbered messages used by `errmsg(...)` |
| Secondary `.dcf` | Optional lookup or output dictionaries |

Run with `CSBatch.exe MyEdits.pff`. The PFF is just a text file pointing to all the inputs/outputs:

```
[Run Information]
Version=CSPro 8.0
AppType=Batch

[Files]
Application=.\MyEdits.bch
InputData=.\MyInputData.dat
OutputData=.\MyOutputData.dat
Listing=.\MyEdits.lst
Freqs=.\MyEdits.tbw
ImputeFreqs=.\MyEdits.impute_freq.lst
SaveArray=.\MyEdits.bch.sva

[ExternalFiles]
LOOKUP_DICT=.\LookupFile.dat

[Parameters]
ViewListing=Always
InputOrder=Sequential
```

`InputOrder=Indexed` re-runs the file in case-ID order; this matters when using lookups that depend on prior cases (hot decks).

## Order of execution

Batch logic walks the case in dictionary order — application → level → record → item — with `preproc` and `postproc` at every node. For a 2-level app:

```
PROC application      preproc
  PROC level1         preproc
    PROC record1      preproc
      PROC item11     preproc → postproc
      PROC item12     preproc → postproc
      ...
    PROC record1      postproc
    PROC record2      preproc → ... → postproc
  PROC level1         postproc
  PROC level2         preproc → record → postproc      (repeated per node)
PROC application      postproc
```

**Recommendations from the book**:
- For BatchEdit *items*, write only `postproc` (the default — don't even type the keyword). Pre/post on items is meaningless because no other code runs in between.
- Logic on a *repeating record itself* runs **once per case**, not once per occurrence. Per-occurrence logic must go on the first item of the record.
- Logic on the application file's `preproc` is the *only* place to initialize global hot-deck arrays.
- Logic on Level 1 runs once per case; Level 2/3 logic runs once per node within the case.

You can re-order edits via *Custom Order* (Options menu) — drag items in the batch edit tree without touching the dictionary. Useful when an edit depends on another edit having already been completed (e.g., RELATIONSHIP must be cleaned before SEX).

## Types of edits

The book groups edits into four buckets:

1. **Structure checks** — every required record present, no extras, no duplicate occurrences.
2. **Validity checks** — values fall inside the value set's defined ranges.
3. **Consistency checks** — cross-item logic (a 5-year-old female reporting children, a male with fertility data, etc.).
4. **Automatic modification (imputation)** — replacing invalid/missing values.

The team should run **two separate batch passes** in serious projects: one for structure (cases that fail are quarantined and manually inspected), then a second for validity + consistency on the survivors.

## Reporting: errmsg, write, freq

### `errmsg` — message-based reporting

Hard-coded messages clutter the source. Define them once in the `.mgf` file:

```
100001 Current age after imputation is %d
```

Then call by number:

```cspro
errmsg(100001, AGE);
```

CSBatch automatically tallies how many times each numbered message fired and prints a summary. The default listing shows messages per-case AND per-summary; the `ErrmsgOverride` PFF parameter restricts output to one or the other.

### `write` — custom report rows

When the subject-matter team needs a "human-readable" report, use `write` instead of `errmsg`:

```cspro
PROC QUEST
preproc
    write("***************");
    write("Province: %3d", PROVINCE);
    write("District: %3d", DISTRICT);
    write("Village : %3d", VILLAGE);
    write("EA      : %3d", EA);
    write("***************");
    write(" ");
```

`write` output goes to the `.wrt` file specified in the PFF (or to the listing if none).

### `freq` — frequency tables

Builds tabulations on the fly during the batch run, captured in the `.tbw` (or `.frq`) file.

## Imputation

Imputation = filling in missing/invalid values. Three flavors:

### Hard-coded (toggle)

```cspro
PROC GLOBAL
numeric sexToggle = 1;

PROC SEX
    if not SEX in 1:2 then
        SEX = sexToggle;
        sexToggle = 3 - sexToggle;
    endif;
```

50/50 random within the case order. Crude — doesn't account for any other case characteristics. Avoid except as a last resort.

### Cold deck (static lookup table)

A predefined table of "most likely" values keyed by other variables. Doesn't change during the run. Acceptable when (a) the population is homogeneous and (b) imputation is rare.

### Hot deck (dynamic) — the recommended approach

Same idea as cold deck, but the lookup table is *updated continuously* during the run from valid cases. Each time a case has a valid set of values, the corresponding cell in the table is overwritten with that case's value. When an invalid case is encountered, the current cell value is used.

```cspro
PROC GLOBAL
Array HD_Age_SexRel(SEX_VS, REL_VS) save;   // saved between runs

PROC AGE
    if AGE = notappl then
        impute(AGE, HD_Age_SexRel());        // pull from hot deck
    else
        HD_Age_SexRel() = AGE;               // refresh hot deck
    endif;
```

The `save` keyword writes the array to a `.sva` file at end-of-run and reads it back at start. **Run the program twice**: the first run primes the hot deck (output discarded); the second uses a fully-warmed deck (output kept).

### DeckArrays — value-set-driven hot decks

Declare the array dimensions using value set names instead of integers:

```cspro
Array HD_HeadAgeFromHHSize(SEX_VS, 10);
Array HD_HeadAgeFromSpouse(SEX_VS, AGE_VS);
```

The size auto-tracks the value set. `getdeck(...)` and `putdeck(...)` handle the recoding from raw value to array index automatically — no manual recode logic needed. Use `(+)` after a value-set name to add a "leftover" row for values not in the value set:

```cspro
Array housingTypeHD(H8_VS1(+), H9_VS1(+), H10_VS1(+)) save;
```

When the dependent variables themselves haven't been edited yet, the leftover row catches them. With three `(+)` dimensions, one DeckArray effectively packs eight hot decks into one — a falls-through cascade from "all valid" down to "use the previous valid HH".

## Universe filter

```cspro
PROC AGE
    universe RELATIONSHIP = 1;   // only edit head-of-household here
    ...
```

`universe` short-circuits the procedure when the condition fails — equivalent to wrapping the whole proc body in an `if`, but cleaner.

## Run output and interpreting reports

After CSBatch runs, Text Viewer opens the `.lst` listing automatically (controlled by `ViewListing`). The header is the **CSPro Process Summary**:

- Records read / records written / records ignored
- Cases with bad structure
- Total messages broken down into user-defined / system warnings / system errors

Per-case message blocks look like:

```
*** Case (010705802820460191) has 12 messages (8 E / 2 W / 2 U)
W 88870 Value '01' out of range — check P16_IND(1)
U   -69 Household tenure is vacant, but there are 5 person records.
E 88212 ... H07_RENT should be blank (currently '000')
```

Codes: `E` = system error, `W` = system warning, `U` = user-defined `errmsg`.

## Practical workflow (book recommendation)

1. **Review edit specs** with subject-matter specialists. Pseudo-code first, CSPro second.
2. **Define coding standards** — variable name prefixes per item, hot-deck naming convention `HD_<imputed>_<key1>_<key2>`, indentation, message numbering scheme.
3. **Write the simple edits first**. Junior team members on validity, senior on consistency and imputation.
4. **Build a comprehensive test file** — synthetic cases that exercise every edit path.
5. **Test on the synthetic file**, fix all syntax errors, verify imputation rates are sane.
6. **Re-run the program on its own output**. Second pass should produce zero corrections — if not, your logic is contradictory.
7. **Test on live data** (~2,000–3,000 cases). Subject-matter specialists review imputation rates — anything unexpectedly high is suspect.
8. **Production run** — re-edit *all* prior batches whenever the program changes (always from the original input, never from prior output).

## Why this matters for UHC Year 2

- **Two-pass design**: F4 (Household) needs a structure pass (housing record present, at least one person record) before consistency edits can run. F1/F3 are simpler — one pass each.
- **Consistency checks**: F4 has the largest surface — sex × relationship × age × parity, household head uniqueness, expenditure totals must reconcile against per-item rows. These are the canonical hot-deck candidates.
- **Hot decks for missing age/sex**: standard hot deck pattern keyed on relationship — straight from the book example.
- **DeckArrays**: cleaner than raw arrays for our value sets; province/region/age-group hot decks should use them.
- **Numbered `errmsg` + .mgf**: gives the DOH validation team a clean report grouped by message ID. Should be designed at the same time as the dictionary.
- **`InputOrder=Indexed`**: probably not needed for UHC Year 2 since cases will be processed in collection order.
- **Two-pass run for hot deck warming**: when F4 batch validation hits production, the `save`-array/two-run pattern is the right approach.
- **`universe` for routed sections**: F3's outpatient vs inpatient split can use `universe VISIT_TYPE = 1` at the top of each routed proc rather than wrapping each rule in an if.
