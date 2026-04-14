# LLM Wiki Schema

This vault is a **knowledge base for the ASPSI-DOH CAPI CSPro Development project**: Computer-Assisted Personal Interviewing (CAPI) system development for ASPSI | DOH using CSPro and CSEntry, covering survey questionnaire design through CSWeb deployment.

The scope covers everything related to this project:
- **Survey design** — questionnaire structure, skip logic, validation rules, multi-language support
- **CSPro/CSEntry** — data dictionaries, CAPI application development, form design, tablet optimization
- **CSWeb** — server setup, deployment, data synchronization, user management
- **DOH surveys** — Facility Head, Healthcare Worker, Patient, and Community survey instruments
- **ASPSI operations** — fieldwork logistics, enumerator training, data collection workflows
- **Data quality** — consistency checks, range validation, completeness rules

The human curates sources, directs analysis, and asks questions. The LLM does all writing, cross-referencing, and maintenance.

## Directory Structure

```
/raw/              — INPUT: Source documents to be ingested. Immutable. The LLM reads but NEVER modifies these.
/wiki/             — KNOWLEDGE: LLM-generated markdown pages. The LLM owns this entirely.
  /wiki/sources/   — Source summary pages (one per ingested source).
  /wiki/entities/  — Entity pages (people, orgs, places, products).
  /wiki/concepts/  — Concept pages (ideas, theories, frameworks, patterns).
  /wiki/analyses/  — Analysis pages (comparisons, syntheses, explorations).
/deliverables/     — OUTPUT: Work products authored by the user (often with LLM help).
                     CAPI applications, documentation, training materials, reports.
                     The LLM may create or edit files here when asked to produce deliverables.
/templates/        — REUSABLE: CSV templates, email drafts, checklists for repeated use.
/index.md          — Content catalog of all wiki pages, organized by category.
/log.md            — Chronological record of all operations (ingests, queries, lints).
/CLAUDE.md         — This file. The schema and operating rules.
```

## How the Zones Relate to PARA

This project lives inside a PARA vault (`1_Projects/ASPSI-DOH-CAPI-CSPro-Development/`). The zones above map to the PARA workflow:

| PARA Step | LLM Wiki Zone | Flow |
|---|---|---|
| User drops a file in `0_Inbox/` | — | File lands in vault inbox for triage |
| User moves it to `raw/` | `/raw/` | File is now a source, ready for ingestion |
| LLM ingests the source | `/wiki/` | Knowledge extracted into wiki pages |
| User asks LLM to produce work | `/deliverables/` | Authored outputs go here |
| Wiki knowledge informs deliverables | `/wiki/analyses/` → `/deliverables/` | Analyses feed into reports, SRS, etc. |

**Key rule**: Never put authored outputs in `/raw/`. Never put dropped/received files directly in `/deliverables/`. Use `0_Inbox/` as the staging area when unsure.

## Page Types

Wiki pages live in `/wiki/` and use one of these types, specified in YAML frontmatter:

### Source Summary
One per ingested source. Links back to the raw file.
```yaml
---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/filename.md]]"
date_ingested: YYYY-MM-DD
tags: []
---
```

### Entity Page
A person, organization, place, product, or any other distinct noun that appears across multiple sources.
```yaml
---
type: entity
tags: []
source_count: N
---
```

### Concept Page
An idea, theory, framework, pattern, or theme that spans sources.
```yaml
---
type: concept
tags: []
source_count: N
---
```

### Analysis Page
Generated from queries — comparisons, syntheses, explorations. Filed back into the wiki so they compound.
```yaml
---
type: analysis
date_created: YYYY-MM-DD
tags: []
---
```

### Overview Page
High-level summary of the entire wiki or a major section. Updated as the wiki evolves.
```yaml
---
type: overview
last_updated: YYYY-MM-DD
---
```

## Conventions

- **Links**: Use Obsidian `[[wikilinks]]` for all cross-references between wiki pages. Use `[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/filename]]` to cite sources.
- **Tags**: Add relevant tags in frontmatter. Use lowercase, hyphenated (e.g., `capi`, `survey-design`, `cspro`).
- **Headings**: H1 is the page title (matches filename). H2 for major sections. H3 for subsections.
- **Citations**: When a claim comes from a specific source, cite it inline: `(Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Title]])`.
- **Contradictions**: When sources disagree, note it explicitly with a `> [!warning] Contradiction` callout and link to both sources.
- **Filenames**: Use descriptive names. Source summaries: `Source - Title.md`. Entities: `Entity Name.md`. Concepts: `Concept Name.md`.
- **No orphans**: Every wiki page must be linked from at least one other page or from index.md.

## Operations

### Ingest Workflow

When the user adds a source to `/raw/` and asks to ingest it:

1. **Read** the source completely.
2. **Discuss** key takeaways with the user. Ask what to emphasize if unclear.
3. **Create** a source summary page in `/wiki/sources/`.
4. **Update or create** entity pages for people, organizations, and other nouns mentioned.
5. **Update or create** concept pages for ideas, frameworks, and themes.
6. **Cross-reference**: Add `[[wikilinks]]` between the new pages and all relevant existing pages.
7. **Check for contradictions** with existing wiki content. Flag them with callouts.
8. **Update** `index.md` — add entries for all new pages.
9. **Update** `log.md` — append an entry for this ingest.
10. **Report** to the user: what was created, what was updated, any contradictions found.

### Query Workflow

When the user asks a question:

1. **Read** `index.md` to identify relevant pages.
2. **Read** the relevant wiki pages.
3. **Synthesize** an answer with citations to wiki pages (and through them, to sources).
4. **Optionally file** the answer as an analysis page if the user confirms it's worth keeping.

### Lint Workflow

When the user asks to lint the wiki (or periodically suggest it):

1. Check for **contradictions** between pages.
2. Check for **stale claims** that newer sources have superseded.
3. Check for **orphan pages** with no inbound links.
4. Check for **mentioned but missing pages** — concepts or entities referenced but lacking their own page.
5. Check for **missing cross-references** between related pages.
6. Check for **data gaps** — suggest sources to look for.
7. Report findings and fix issues with user approval.

## Rules

- NEVER modify files in `/raw/`. They are immutable source documents.
- ALWAYS update `index.md` and `log.md` after any wiki operation.
- ALWAYS use the frontmatter format specified above for new pages.
- ALWAYS cross-reference aggressively — links are what make the wiki valuable.
- When in doubt about emphasis or interpretation, ASK the user.
- Prefer updating existing pages over creating new ones when the content overlaps.
- Keep source summaries factual. Keep analysis pages clearly marked as interpretation.
- The wiki should be browsable in Obsidian without the LLM — links, structure, and writing should all make sense to a human reader.
