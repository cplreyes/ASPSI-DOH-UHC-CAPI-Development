---
type: concept
tags: [cspro, tabulation, cstab, cross-tab, area-processing, weights, value-sets]
source_count: 1
---

# CSPro Tabulation

**Tabulation applications** turn one or more CSPro data files into frequency distributions and cross-tabulations. Built in the **Tabulation Designer**, run by **CSTab**. The point-and-click interface produces most tables without writing logic; the procedural language is reserved for the most complex tables. Source: [[wiki/sources/Source - CSPro 8.0 Complete Users Guide]] (Tabulation section, pp. 302–426).

Tabulation is the *third* CSPro application type after Data Entry ([[wiki/concepts/CSPro CAPI Strategies]]) and Batch Editing ([[wiki/concepts/CSPro Batch Editing]]) — same dictionary, different purpose.

## Application files

| File | Purpose |
|---|---|
| `.xtb` | Tabulation application file |
| `.xts` | Table specifications (variables, tally attributes, formatting) |
| `.dcf` | The data dictionary describing the input data |

Output table file: `.tbw` (CSPro Table Viewer format). Tables can also be exported to RTF, HTML, or tab-delimited.

## Anatomy of a table

| Part | What it is |
|---|---|
| **Title** / **Subtitle** | Auto-generated from variable labels; editable |
| **Spanner** | Text box covering several columns |
| **Stub** | Row label |
| **Stub Head** | Header text describing the stub column |
| **Column Head** | Header text for each data column |
| **Caption** | Text rows interspersed between stubs but with no data |
| **Page Note / End Note** | Footnotes (per-page or end-of-table) |
| **Boxhead** | Union of stub heads + spanners + column heads |
| **Tally** | The numbers themselves (counts, %, mean, median, etc.) |
| **Subtable** | A self-contained section within a larger table — own universe, weight, value, unit of tabulation |

## Building tables: drag and drop

The basic workflow:

1. **Select Dictionary tab** → expand to find the items.
2. **Drag an item onto the table workspace.** Position determines whether it's a row or column variable — below the diagonal = row, above = column.
3. **Drop next to** an existing item (`+` cursor) → adds it as a *sibling* (creates a sub-table).
4. **Drop on top of** an existing item (`x` cursor) → *crosses* the two items (nested categories).
5. **To delete** a row/column variable, drag it back onto the dictionary tree.

A table can have any number of rows; column count is effectively unlimited but harder to read past 6–8 columns. Maximum **2 row variables and 2 column variables** per subtable. The first dragged becomes the **independent (major)** variable; the second becomes the **dependent (minor)**, nested within the categories of the first.

## Multiple value sets per item

Critical leverage point. Recall that items can have multiple value sets ([[wiki/concepts/CSPro Data Dictionary]]):

```
AGE              0..98, 99 = Not Reported
AGE_5YRS         0–4, 5–9, 10–14, ..., 60+
AGE_CATEGORY     Infant, Child, Teenager, Adult, Senior
```

In Tabulation, dragging the **item itself** uses its first value set. Dragging a **specific value set** uses that one instead. So a single dictionary item drives multiple table breakdowns without re-coding the data.

Notes on counting:
- Counts are **only** made for values defined in the value set. Values in the data file that don't fall into any value set bucket are silently dropped (unless Special Values are tally-included).
- Median, mode, and N-tiles are *calculated from the value set buckets* by default — wide ranges = inaccurate stats. Use single values or small uniform ranges for continuous variables when you need accurate central-tendency stats.
- Alphanumeric items **cannot be tallied** in 8.0.

## Counts vs percents

Tally attributes (per table or per subtable) control what's displayed:

- **Counts** (default)
- **Percent of row total**
- **Percent of column total**
- **Percent of table total**
- **Percent only** (suppress raw counts — useful for small samples to avoid identifying individual cases)

## Weights and values

Two distinct concepts that can be combined:

- **Weight** — a multiplier applied to each case before adding to the cell. Set with the Weight attribute. Default = 1. Use this for survey sampling weights.
- **Value** — a quantity to *add* to the cell instead of incrementing by 1. Set with the Value attribute. Default = 1. Use this when you want to tally totals (e.g., total children born) rather than counts of cases (women with N children born).

If both are set, `weight × value` is added to the cell. For UHC Year 2 (sample survey, not census): both are in scope. F4 expenditure tables almost certainly need value-tallying *and* sampling weights.

## Universe

Per-table or per-subtable filter — only cases matching the universe expression contribute. Equivalent to a `WHERE` clause in SQL. A universe defined at the table level can be propagated to all tables in the application.

## Summary statistics

Beyond counts and percents, each variable can request:

- **Mean** — average
- **Mode** — most common value
- **Median** — 50th percentile
- **Min**, **Max**
- **Standard Deviation**, **Variance**
- **N-tiles** — quartiles, deciles, percentiles, etc.

Disable for nominal items where the stats have no meaning (sex, religion).

## Area processing

The killer feature for census/survey work: tabulate the same set of tables broken down by *geographic area*, automatically.

How it works:
1. Create an **area names file** (CSV-like) that maps geographic codes to names — e.g., region/province/municipality.
2. Set the application's Area item(s) to the corresponding ID variables.
3. Run tabulation. CSPro produces the same table set repeated once per area at every level of the hierarchy, with the area names automatically substituted as captions.

The area item(s) must live in the case ID block or on a singly-occurring record (so there's exactly one value per case).

For UHC Year 2: tables broken down by region → province → municipality are exactly the kind of routine output the project needs to deliver. **Build the area names file early** from the PSGC reference data.

## Subtables

Side-by-side mini-tables sharing a single table window. Useful for "this set of variables under one independent, that set under a different independent" without making two separate tables. Each subtable has its own universe / weight / value / unit-of-tabulation, so they're surprisingly flexible.

## Unit of tabulation

When a table mixes items from two record types (e.g., person + housing), CSPro asks which record's *occurrence count* drives the tally. For most simple tables this is automatic — single record types have only one option. Cross-record tables (Householder Tenure × Person Age) need an explicit choice and may need a **relation** defined in the dictionary to link the records correctly.

## Items with multiple occurrences

Drag the **parent** item → all occurrences are tabulated together (no parentheses on the column name).
Drag a **specific occurrence** → only that one is tabulated (parentheses around the index).

## Run output and export formats

Run with `CSTab.exe MyApp.pff` (or from the IDE). Output is a `.tbw` file viewable in CSPro Table Viewer. From there:

- **Save as RTF** → opens in Word with native table formatting
- **Save as HTML** → web embed
- **Save as tab-delimited** → opens in Excel as a proper grid
- **Copy/paste** to a word processor or spreadsheet — selection-aware

## Formatting and preferences

Per-table format controls: font, color, alignment, indentation, borders, number format, headers/footers, margins. CSPro ships defaults; custom defaults can be saved as **Preferences** and shared across the team for consistent table styling — important for publication-quality output.

## Why this matters for UHC Year 2

- **Multiple value sets per item** are the right way to deliver age breakdowns at single-year, 5-year, and category levels from one dictionary item.
- **Area processing** with a PSGC area names file gives DOH the regional breakdown tables for free — no per-region table specs needed. Build the area names file as part of the initial dictionary work.
- **Weights**: F4 is a sample survey — sampling weights must be on every table. Add a `WEIGHT` item to the household record.
- **Value tallying**: F4 expenditure totals are values, not counts — drag the expenditure amount as the Value attribute, not as a row variable.
- **Subtables**: useful for "demographics under one universe, health-seeking under another" within a single output table.
- **Tabulation as edit verification**: per the book, run the same tables on pre- and post-edit data to confirm imputation hasn't distorted the distribution. Worth doing for the F4 expenditure batch edits.
- **Output to RTF**: easiest path to "DOH-ready report" without manual reformatting.
