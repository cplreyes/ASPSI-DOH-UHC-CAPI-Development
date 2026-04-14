---
type: concept
tags: [cspro, data-dictionary, dcf, schema, value-sets, records, items]
source_count: 1
---

# CSPro Data Dictionary

The **Data Dictionary** (`.dcf` file) is the schema for every CSPro application. It describes the physical layout of a data file *and* the semantic structure of the questionnaire it represents. Every CSPro application — data entry, batch edit, tabulation — is built on top of a dictionary; without one, nothing else works. Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]] (Data Dictionary Module, pp. 79–122).

## The dictionary mirrors the questionnaire

| Questionnaire term | Dictionary term |
|---|---|
| Form | File |
| Section | Record |
| Question | Item |
| Response options | Value set |
| Identification block (province, district, household no.) | ID items |

A *case* is the primary unit — usually one questionnaire. A case decomposes into one or more **levels** (max 3), each level into **records**, each record into **items**, each item into one or more **value sets**, each value set into **values**.

## File structure: single-record vs. multiple-record

**Single-record** — each line of the data file is one complete questionnaire, no record-type column needed. Example: a student survey where one row = one student.

**Multiple-record** — several lines per questionnaire, each line typed by a leading *record type* code. Example: a Housing & Population census with `1` = housing record, `2` = person record. ID columns repeat across the lines so the records can be regrouped into one questionnaire later.

```
11010011122122        ← housing line for household 101001 (record type 1)
2101001120109196138   ← person 1
2101001212105196732   ← person 2
2101001311707199207   ← person 3
```

For [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]: F1, F2, F3 each likely fit a single-record structure (one questionnaire = one respondent). F4 (household) is the canonical multiple-record case — household record + repeating person record + repeating expenditure rows.

## Levels (rare but powerful)

Default is one level. Use additional levels only when the questionnaire is genuinely hierarchical *and* the children must be grouped under their parents. The book example: a reproductive health survey with Level 1 = household, Level 2 = each woman of reproductive age, Level 3 = each child of each woman. Each woman's children stay tied to *their* mother automatically.

For UHC Year 2, **none of the four annexes need multiple levels** — F4's roster works inside a single level using repeating records. Add levels only if you can't get the grouping any other way; multi-level dictionaries complicate logic order-of-execution and form design (records from different levels must live on different forms).

## Records

A record is a group of related items, usually one section of the questionnaire. Key properties:

| Property | Meaning |
|---|---|
| **Label / Name** | Human-readable label, plus a CSPro-language identifier (UPPERCASE, no leading digit, no reserved words) |
| **Type Value** | The 1-or-2 char code that distinguishes this record from others in a multi-record file. Always alphanumeric. Case-sensitive. Blank is allowed. |
| **Required** | Yes = at least one occurrence must exist for the case to be considered complete. No = optional. |
| **Max** | Max occurrences in one questionnaire (1–9999). Keep this as low as is reasonable — large maxes inflate file size when occurrences go unused. |

Single-record dictionaries: set the record type's `start` and `length` to 0 to "remove" it.

Required examples for a census:
- Allow vacant housing → housing record required, person record not required
- Allow homeless persons → housing not required, person required
- Standard → both required

## Items

The atomic unit. An item is one question's response. Properties:

| Property | Notes |
|---|---|
| **Label / Name** | Label feeds default field text and tabulation titles. Name is the CSPro-language identifier. |
| **Start, Length** | Position in the record. Numeric items max 15 digits; alpha max 255 chars (alpha can go up to 999 in some contexts). |
| **Data Type** | Numeric (default) or Alpha. With Binary Items enabled: Audio, Document, Geometry, Image. |
| **Item Type** | Item or Subitem (a redefinition of part of an item). |
| **Occ** | Number of consecutive repetitions of the item in one record. Default 1. |
| **Dec / Dec Char** | Decimal places, and whether the decimal point is physically in the file or implied. |
| **Zero Fill** | Numeric only — `Yes` = stored with leading zeros (default), `No` = leading blanks. |

### ID items

Special items that uniquely identify the case. Defined at a level; appear on every record at *that* level and below. Each level needs at least 1 ID item, max 15. ID items cannot have decimals, multiple occurrences, or subitems. Convention: put the record-type column first, then ID items, then everything else.

### Subitems

Carve a parent item into pieces by overlaying smaller items at the same byte range. Classic use cases:

- **Date redefinition** — `DOB` (length 8, YYYYMMDD) → subitems `DOB_YEAR` (4), `DOB_MONTH` (2), `DOB_DAY` (2), all starting inside the parent's byte range.
- **Hierarchical codes** — `OCCUPATION` length 4 → `OCC_MAJOR` (1), `OCC_SUBMAJOR` (2), `OCC_MINOR` (3) for tabulating at major/minor breakdowns without re-entering data.

Constraints: a subitem's start position must lie inside its parent. ID items cannot have subitems. If a parent item has `Occ > 1`, its subitems cannot also have `Occ > 1` (and vice versa).

### Binary items (experimental in 8.0)

Items can wrap CSPro objects: **Audio**, **Document**, **Geometry**, **Image**. Cannot have value sets. Cannot be placed on forms — must be manipulated through logic only. Only work with `CSPro DB`, `Encrypted CSPro DB`, `JSON`, `None`, and `In-Memory` data sources (Text data source crashes at runtime). Synced via `syncdata` like any other item, but binary blobs can be slow.

Example logic — taking a photo and storing it on the case:

```cspro
PROC ROOF_TYPE
    if accept("Take a photo of the roof?", "Yes", "No") = 1 then
        if ROOF_IMAGE.takePhoto() then
            ROOF_IMAGE.resample(maxWidth := 1200, maxHeight := 800);
        endif;
    endif;
```

For UHC Year 2: relevant if the survey ever wants to capture facility documents (e.g., accreditation papers — the guide cites this exact use case) or roof photos for facility characterization. Not in current scope.

## Value Sets

A value set bounds an item's allowed values. Critical for numeric items — without one, a length-1 numeric item silently accepts 0–9 even when only 1/2 are meaningful. Uses:

- Restrict data entry to valid values
- Present a pick list to the enumerator
- Drive `setvalueset` for dynamic value-set switching ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Question Text and Fills]])
- Power `impute(...valueset...)` in batch editing
- Auto-generate column stubs in tabulation tables
- Generate codebooks for SPSS/Stata/R/SAS exports

**An item can have multiple value sets.** Common pattern: one "raw" value set for entry plus alternate value sets for different tabulation breakdowns.

```
Value Set         Item     Definition
AGE               AGE      0..98, 99 = Not Reported
AGE_5YRS          AGE      0–4, 5–9, 10–14, ..., 60+
AGE_CATEGORY      AGE      Infant=0, Child=1–12, Teenager=13–19, Adult=20–59, Senior=60+
```

### Values

A value is a single response or a range. Properties:

| Property | Meaning |
|---|---|
| **Value Label** | Display string. Used in tab stubs. |
| **From / To** | Single value (To blank) or range (To > From). |
| **Special** | One of `missing`, `refused`, `notappl`, `default`. Numeric items only. |
| **Image** | Image file shown next to the label in CAPI — useful for illiterate respondents or visual response sets. |

To make several disjoint ranges share one value label, leave the value-label blank on continuation rows. The lack of a notes box at the start of a row indicates it joined the row above.

### Linked value sets

Two items can share a value set via copy → "Paste Value Set Link". Linked value sets render in pink. Editing one updates all. Common case: country-of-residence and country-of-birth both pull from the same country list.

### Generate value set

`Generate Value Set` builds 0–99 (or any from/to/interval) automatically with a label template like `%s to %s years` — saves typing for things like single-year age breakdowns.

### Value set images

Each value can carry a `.jpg/.gif/.bmp/.png/.tif`. When deploying to a tablet, **bundle the images with the .pen file** by placing them in a *resource folder* — otherwise the device won't find them.

## Relations

Define joins between two repeating elements. Four linking types:

| Type | How linked |
|---|---|
| Occurrence to Occurrence | First-to-first, second-to-second, etc. |
| Item to Occurrence | Value of an item on the primary points to the secondary's occurrence number |
| Occurrence to Item | Reverse |
| Item to Item | Value-equality join (like a SQL JOIN ON) |

Used inside `for` statements in batch programs and in the Export Data tool. Example use: linking child records to mother records by `MOTHER_LINE_NUMBER`. For UHC Year 2 F4 (Household), relations could link expenditure rows back to specific household members if the design requires it.

## Modes: Relative vs. Absolute positioning

- **Relative mode** — CSPro auto-packs items consecutively. No gaps. As you add/insert/delete items, everything shifts. **Use this for new dictionaries.**
- **Absolute mode** — Items keep their explicit start positions. Gaps allowed. **Use this when reverse-engineering a dictionary from an existing legacy data file** so you can describe only the columns you care about and leave gaps for the rest.

Toggle: `Options → Relative Positions`.

## Dictionary types (when used as a secondary dictionary)

| Type | Use |
|---|---|
| **Main** | The primary dictionary the application was built on. Cannot change. |
| **External** | Must have an associated data file. Defaults to `notappl`. Used for lookup tables. |
| **Working** | No data file required. Defaults to blank/zero. Used for scratch storage. Consider `In-Memory` or `None` data sources as alternatives. |
| **Special Output** | Backward compatibility with ISSA Batch Edit Applications. Rarely used. |

## Multiple-language dictionaries

`Edit → Languages` adds languages. Each label, value label, and occurrence label gets a per-language string. If unset for a given language, falls back to the primary. Switch in the editor with `Ctrl+Alt+L`. For multi-language CAPI, the CAPI Languages must match — see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Multi-Language Applications]]. UHC Year 2 doesn't currently scope multilingual dictionaries (Filipino + English UI is on the CAPI side, not the dictionary).

## Dictionary macros (bulk operations)

`Edit → Dictionary Macros` exposes operations that would be tedious by hand:

- **Copy/Paste All names + labels** to/from clipboard in tab-delimited form — round-trips through Excel. Use this to hand the labels to a subject-matter specialist or to a translator without giving them the dictionary tool.
- **Bulk add items** to a record (`RECORD_NAME_ITEM001`, ...) — useful if a clerk will fill in names later.
- **Generate Random Data File** — synthesizes test data conforming to value sets with optional `% Not Applicable` and `% Invalid` to stress-test edits.
- **Sample Data File** — pull a random or sequential N% sample from an existing file.
- **Compact Data** — strips tilde-deleted rows from a Text data source.
- **Sort Data in ID Order** — runs Sort Data tool against the dictionary's ID hierarchy.
- **Create Notes Dictionary** — creates a sister dictionary that can read the `.csnot` notes file produced by data entry, enabling export of operator notes.

## Dictionary analysis (lint)

`View → Dictionary Analysis` — generates reports for:

- Items without value sets
- **Numeric** items without value sets (the high-priority ones)
- Numeric items with overlapping value sets
- Numeric items with mismatched ZeroFill or DecChar (you almost always want all items consistent)

Run this against every UHC Year 2 dictionary before bench testing — it's the cheapest way to catch missing value sets.

## Dictionary security

`Edit → Security Options`:

- *Allow exporting data to other formats* — gates Data Viewer / Export Data / `export` statement.
- **Encryption password caching** — for `Encrypted CSPro DB` data sources, controls how long a key (not the password itself) can be cached. Options: Never / Hour / Day / Week / Month / Year / Forever / Custom. The cached key is stored in secure OS storage. Clear via `CSPro Settings`.

For UHC Year 2: any dictionary that touches PHI (patient identifiers in F3, household identifiers in F4) should use the Encrypted CSPro DB data source with a short cache window — likely Never or One Hour for fieldwork tablets.

## Reconciling dictionary changes

When you edit a dictionary that an application depends on, CSPro reconciles automatically when the app is open. If the app is closed at edit time, reconciliation runs the next time you open it. **Some changes prompt for assistance** — e.g., renaming an item triggers a "rename or delete?" dialog because CSPro doesn't know whether the field on the form should be re-pointed or removed. Plan dictionary edits before re-opening the form designer.

## Practical workflow for building a dictionary

The book recommends, and Carl should follow:

1. Set level properties (rename "Level 1" to something meaningful).
2. Define the **ID items** — these will appear on every record; get them right first.
3. Create the **records** for the level. Set max occurrences and required flag.
4. Add the **dictionary items** for each record (1-to-1 with questions on the questionnaire).
5. Add **value sets and values** last. This is the step most often skipped — don't.
6. Run `View → Dictionary Analysis` before declaring the dictionary done.

## Why this matters for UHC Year 2

- **F1, F2, F3** — single-level, mostly single-record dictionaries. F1 already has a draft dictionary (see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Facility Head Data Dictionary and Value Sets]]) using `Q{n}_{DESCRIPTION}` naming.
- **F4 (Household)** — multi-record. Will need at minimum: `HOUSEHOLD_REC` (singly-occurring), `PERSON_REC` (multiply-occurring with `Max ≈ 25` and required = No until at least one person is recorded), `EXPENDITURE_REC` or repeating items inside `HOUSEHOLD_REC` for the consumption rosters.
- **Linked value sets** are worth using for region/province/municipality codes that appear across all four annexes.
- **Encryption** is non-negotiable for any dictionary holding PHI (F3 patient records).
- **Dictionary Macros → Generate Random Data File** is the fastest way to produce a test dataset for the Tranche 2 bench test if real pretested data is still blocked.
