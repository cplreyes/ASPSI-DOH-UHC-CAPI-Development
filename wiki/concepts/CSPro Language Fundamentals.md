---
type: concept
tags: [cspro, logic, proc, language, declarations, operators, expressions, special-values]
source_count: 1
---

# CSPro Language Fundamentals

The **CSPro Language** is the procedural scripting language that drives data entry, batch editing, and tabulation logic. Every dictionary item, record, form, and level can have logic attached to it; the language ties them together into an application. Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]] (CSPro Language section, pp. 123–180; also Statements & Functions Reference, pp. 448–end).

This page is the *fundamentals* — program structure, variables, expressions, operators. Event order (`preproc`, `onfocus`, etc.) lives in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Logic Events]]. Question text and fills live in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Question Text and Fills]].

## Program structure

A logic file is a sequence of **PROC** blocks. Every dictionary symbol — the application itself, levels, records, items, forms, blocks, fields — can have its own PROC. The first block is always `PROC GLOBAL`, where shared declarations live.

```cspro
PROC GLOBAL

    // Declaration section
    numeric eligible_count;
    alpha(20) current_household_head;

    function logical isAdult(numeric age)
        isAdult = age >= 18;
    end;

PROC HOUSEHOLD_FORM

    preproc
        eligible_count = 0;
    endlevel;

PROC AGE
    postproc
        if isAdult(AGE) then
            eligible_count = eligible_count + 1;
        endif;
```

Order of PROCs in the file does not affect execution order — the dictionary/form structure does. Order of declarations *within* `PROC GLOBAL` does matter (a function must be declared before it's called).

## Programming standards (book recommendations)

The guide gives 15 conventions; the high-value ones for this project:

- **UPPERCASE** for dictionary names (items, records, forms, value sets) — they appear in source as `AGE`, `PERSON_REC`.
- **mixedCase** for declared variables and user-defined functions — `eligibleCount`, `isAdult()`.
- Indent the body of every `if`, `for`, `while`, `do`, `function`, and `proc` block.
- Comment *why*, not *what* — the syntax is self-evident, the intent isn't.
- One statement per line. Don't pack assignments.
- Always parenthesize mixed-precedence expressions (`(a + b) * c`, not `a + b * c`).
- Use `select case` instead of long `if/elseif` chains.
- Prefer named constants (`define MAX_PERSONS 25`) over magic numbers.

## Logic versions: Original vs CSPro 8.0+

CSPro 8.0 introduced an opt-in language version. The new version cleans up several historical warts. Toggle in the dictionary's compiler mode setting.

| Feature | Original | CSPro 8.0+ |
|---|---|---|
| Block comment | `{ ... }` | `/* ... */` |
| Curly braces | comment delimiters | block delimiters (future use) |
| String escape sequences | none — `\n` is literal | C-style — `\n`, `\t`, `\\`, `\"`, etc. |
| Verbatim string literal | not available | `@"C:\path\with\backslashes"` |
| String comparison | padded (trailing blanks ignored) | exact (length matters) |

**For UHC Year 2: use CSPro 8.0+ language mode** on every new dictionary. The escape-sequence and verbatim-string improvements alone are worth it, and exact string comparison catches bugs.

## Declaration section

Goes inside `PROC GLOBAL` (or inside any function/proc to declare locals). Declares:

- **Variables** — `numeric x;`, `alpha(50) name;`, `logical isDone;`
- **Constants** — `define MAX_PERSONS 25`
- **User-defined functions** — `function ... end;`
- **Logic objects** — instances of CSPro's built-in classes (see below)
- **Aliases** — give a dictionary item a shorter name: `alias h = HOUSEHOLD_REC.HEAD_LINE_NO;`

Aliases are particularly handy when an item is buried deep in a record path. Once aliased, `h` behaves identically to the original symbol.

## User-defined functions

```cspro
function numeric monthsBetween(numeric startYM, numeric endYM)
    numeric sy, sm, ey, em;
    sy = int(startYM / 100);
    sm = startYM % 100;
    ey = int(endYM / 100);
    em = endYM % 100;
    monthsBetween = (ey - sy) * 12 + (em - sm);
end;
```

The return value is assigned by writing to the function name itself (no `return` keyword in original mode). Functions can be `numeric`, `alpha`, `logical`, or return nothing (`function void doThing()`). Parameters are pass-by-value for scalars, pass-by-reference for objects.

## Logic objects

CSPro logic is procedural at heart but ships a small set of built-in classes. Each is instantiated by declaring a variable of that type and then calling methods on it with dot syntax.

| Object | Purpose |
|---|---|
| **Array** | Multi-dimensional fixed-size collection. Declared with size: `array numeric counts(10, 5);` |
| **Audio** | Wraps an audio recording. Methods: `record()`, `play()`, `stop()`, `length()`. Used in binary items. |
| **Case** | Represents a whole questionnaire. Used to read/write cases programmatically (`open`, `forcase`, `getcase`, `writecase`). |
| **Document** | A binary item that wraps an arbitrary file (PDF, DOC, etc.). |
| **File** | Plain text file I/O — `open`, `read`, `write`, `close`. |
| **Freq** | Frequency table builder for batch editing — `add()`, `print()`. |
| **Geometry** | GPS point/line/polygon. Methods: `capture()`, `getLatitude()`, `getLongitude()`, `getAccuracy()`. |
| **HashMap** | Key-value store. `put(key, value)`, `get(key)`, `contains(key)`. |
| **Image** | Photo or static image. `takePhoto()`, `pickPhoto()`, `resample()`, `show()`. |
| **List** | Ordered, growable collection (unlike Array). |
| **Map** | Native map widget for displaying GPS layers in CAPI. |
| **Pff** | Read/write `.pff` parameter file fields from logic. |
| **SystemApp** | Launch external Android apps. |
| **ValueSet** | Build/modify value sets at runtime — feeds `setvalueset()`. |

Example — capturing a photo into a binary item:

```cspro
PROC ROOF_TYPE
    if accept("Take a photo of the roof?", "Yes", "No") = 1 then
        if ROOF_IMAGE.takePhoto() then
            ROOF_IMAGE.resample(maxWidth := 1200, maxHeight := 800);
        endif;
    endif;
```

For UHC Year 2: **HashMap** is the cleanest way to carry province/municipality lookup tables; **Geometry** is in scope if facility GPS is required; **Image** is available if facility photos are added later; **ValueSet** is what makes dynamic skip patterns work.

## Variables and constants

### Data items

Dictionary items act as global variables. Reading `AGE` reads the current case's `AGE` value; writing to `AGE` sets it. When the same item appears in multiple records or occurrences, CSPro infers the path from context — usually you mean "the current one".

`$` is shorthand for *the current item*, mostly used in conditional rules and consistency checks: `if $ in 1:5 then ... endif`.

### Subscripts

`PERSON_REC(3).AGE` = the AGE item on the third occurrence of the person record. `curocc()` returns the current occurrence number inside loops. `numocc(PERSON_REC)` returns how many occurrences exist.

### Numbers

Plain decimals: `42`, `3.14`, `-7`. No thousands separators. Hex/octal not supported.

### Boolean values

`yes` / `no` are the canonical literals. The language also accepts `true`/`false`. Tested with `=` (`if isDone = yes then ...`) — there's no `==`.

### Special values

Numeric items can hold one of four sentinel values, each with its own representation in the data file (typically `9...9`, `8...8`, etc., or blank, depending on item width).

| Special | Meaning | Common use |
|---|---|---|
| **missing** | Value is unknown / blank | Item never filled in |
| **refused** | Respondent declined to answer | Sensitive questions (income, HIV status) |
| **notappl** | Question doesn't apply | Skipped by routing logic |
| **default** | Item has its declared default | Working dictionaries |

Test with the keyword: `if AGE = missing then ...`. The function `special(AGE)` returns whether *any* special is set. **Always treat specials explicitly** in batch edits — arithmetic on a `notappl` item silently propagates the special.

CSPro 8.0+ adds the `OnRefused` override function — define it once globally and CSPro calls it whenever the user types the refusal value, letting you confirm or override per-item.

### String literals

Original mode: only `'single'` and `"double"` quoted, no escapes. CSPro 8.0+ adds C-style escapes:

| Escape | Meaning |
|---|---|
| `\'` `\"` `\\` | literal `'` `"` `\` |
| `\a` `\b` `\f` | bell, backspace, formfeed |
| `\n` `\r` `\t` `\v` | newline, return, tab, vtab |

Verbatim string literal: `@"C:\Users\analy\foo"` — backslashes are literal, no escapes processed. Use this for Windows paths and regex patterns.

## Expressions

Three flavors: **numeric**, **string**, **logical**. Type is inferred from context; no implicit numeric→string coercion (use `edit()` or `tonumber()`).

### Substring expressions

```cspro
alpha(20) name;
name = "Reyes, Carl Patrick";
name[8:4]              // → "Carl"
name[1:5]              // → "Reyes"
name[8:0]              // → "Carl Patrick" — length 0 means "to end"
```

Syntax is `STR[start:length]`, 1-indexed. Substrings are assignable on the left side: `name[1:5] = "REYES";`.

### Operators

| Category | Operators |
|---|---|
| **Arithmetic** | `+` `-` `*` `/` `%` (modulo) `^` (power) |
| **Relational** | `=` `<>` `<` `>` `<=` `>=` |
| **Set membership** | `in` (`AGE in 0:17`), `has` (string contains) |
| **Logical** | `and` `or` `not` `iff` (if-and-only-if / equivalence) |

Notes:
- `=` is both assignment and equality — context disambiguates. `if x = 5 then x = 10 endif` is legal.
- `in` accepts ranges *and* lists: `if SEX in 1, 2 then ...`, `if AGE in 0:4, 65:120 then ...`.
- `iff` is rarely used outside formal consistency checks but can clean up double-negation.
- No bitwise operators in standard logic.

Operator precedence follows mathematical convention (`^` > `* /` > `+ -` > relational > `not` > `and` > `or`). **Always parenthesize** when mixing — the book is emphatic about this and so is every CSPro veteran I've read.

## Logic preprocessor

CSPro 8.0+ supports compile-time conditionals via `#if`/`#elseif`/`#else`/`#endif`, evaluated before normal compilation. Useful predicates:

- `AppType()` — returns `"DataEntry"`, `"BatchEdit"`, `"Tabulation"`, etc. Lets one logic file branch by application type.
- `exists(SYMBOL)` — true if a symbol is defined in the dictionary. Lets one logic file work across two slightly different dictionaries.
- `#setProperty(name, value)` — set a compiler property at preprocessing time.

```cspro
#if AppType() = "DataEntry"
    // CAPI-only logic
#elseif AppType() = "BatchEdit"
    // batch-only consistency edits
#endif
```

For UHC Year 2: useful if F4 ends up sharing a single logic file between data entry and batch validation.

## Why this matters for UHC Year 2

- **PROC GLOBAL with `define MAX_PERSONS 25`** and a few helper functions (age-from-DOB, household head lookup) is the right starting structure for F4.
- **Compiler mode = CSPro 8.0+** on all four annexes — no reason to inherit Original Mode quirks.
- **Specials are mandatory** — every numeric item in F1/F3 with sensitive content needs an explicit `notappl` for skipped paths and `refused` for declined answers, otherwise tabulation will silently treat them as zero.
- **HashMap-based PSGC lookups** are cleaner than embedding the province/municipality list as a value set.
- **Aliases** are useful for F4's deeply-nested expenditure rosters where the full dotted path gets unwieldy.
- **`#if AppType()`** lets the F4 dictionary share logic between the CAPI app and the batch validation pass without duplicating files.
