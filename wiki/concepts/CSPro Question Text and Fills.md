---
type: concept
tags: [cspro, capi, question-text, fills, html, conditional]
source_count: 2
---

# CSPro Question Text and Fills

CAPI applications display customized question text in the top half of the entry window. CSPro lets you embed dynamic content — values, computed strings, even formatted HTML — into that text using **fills**.

## Entering question text

In the Forms Designer, with a CAPI application open:

1. `View → Question View` (or `Ctrl+Q`) — the question editor appears.
2. Pick an item in the tree on the left.
3. Type the text in the right-hand editor. Format with the toolbar or the `Question Text` menu.

The editor supports paste of formatted text from other documents.

## Fills — substitution syntax

A **fill** is a CSPro logic expression embedded in question text by surrounding it with **pairs of tilde characters** (`~~`):

```
Can I speak with ~~FIRST_NAME~~ now?
```

becomes, at runtime:

```
Can I speak with Marjorie now?
Can I speak with Allyson now?
```

> **Version note:** The 16-page CSPro Android CAPI Getting Started tutorial (written against CSPro 6.1) shows the older `%item%` syntax. **For CSPro 8.0 and the UHC project, always use `~~item~~`.**

A fill may be any valid CSPro logic expression that resolves to a string or number — dictionary items, variables, occurrence labels, user-defined functions, built-in functions, operators.

## Common fill patterns

### Dictionary item value
```
Can I speak with ~~FIRST_NAME~~ now?
```

### Numeric value via its label (use `getvaluelabel`)
By default a numeric fill uses the value *code*. To use the value *label* (e.g., "Female" instead of `2`):

```
How old was ~~FIRST_NAME~~ when they completed
~~getvaluelabel(HIGHEST_GRADE_COMPLETED)~~?
```

### Occurrence labels (`getocclabel`)
For repeated items, fill the label of the current occurrence:

```
How much did you spend on ~~getocclabel()~~ in the last month?
```

### User-defined function
The function can return numeric or string. Example — pronoun selection based on sex:

```
function string SexPronoun()
    recode SEX -> SexPronoun;
        1 -> "his";
          -> "her";
    endrecode;
end;
```

```
Thinking now about ~~FIRST_NAME~~, what is ~~SexPronoun()~~ age?
```

### HTML in fills (use **three** tildes)

To produce dynamically formatted HTML in the question text, surround the fill with **three** tildes (`~~~`) instead of two. Three tildes tells CSPro **not** to escape the HTML tags, so the formatted result is rendered. Two tildes will substitute the literal HTML as text.

```
You have entered the following household members:
~~~householdMembers~~~
```

with logic:

```
householdMembers = "<ul><li>Bouba</li><li>Frank</li><li>Chen</li></ul>";
```

renders the bulleted list.

## Conditional question text

Beyond fills, the application can present **entirely different question text** based on conditions — e.g., reword a question depending on household size or respondent age. The mechanism is documented under "Create Conditional Questions" in the Complete User's Guide.

## Question text styling

CSPro ships customizable styles so the designer can color text differently:

- Black for what the interviewer reads aloud to the respondent.
- Blue (or another color) for instructions to the interviewer.

This visual distinction is critical in long interviews where the interviewer is parsing the screen quickly.

## Project relevance

- **Personalization across F1, F3, F4** — every interview that captures a respondent name will use a fill (`~~RESPONDENT_NAME~~`, `~~FIRST_NAME~~`, etc.) in subsequent questions.
- **F4 household roster** — `~~getocclabel()~~` is the cleanest way to put "Person 1", "Person 2", or the actual name into per-person questions.
- **Interviewer-vs-respondent text colors** — apply the standard styling so DOH/SJREB reviewers can immediately see which text is read aloud and which is an enumerator instruction.
- **Filipino translation** — fills travel with the language switch automatically since they reference dictionary items, not hard-coded strings. The translator only changes the surrounding text.
- **MyCAPI walkthrough patterns** — the `setvalueset` switching of male/female relationship value sets in the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android CAPI Getting Started|Android CAPI Getting Started]] is the same pattern that F3 outpatient/inpatient routing and F4 household-conditional questions will use.

## Sources

- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro Android CAPI Getting Started]])
