# AGENTS.md Progressive Disclosure (vs. Flat Index)

A structured document pattern for knowledge wikis and multi-folder projects, 
used as an alternative to a flat `index.md` catalog.

## Core Idea

Instead of a single `index.md` that lists every page, place an `AGENTS.md` in 
each folder that documents what lives there, the conventions that govern it, 
and how to interact with it. This is the same DOX pattern used at the project 
level — applied recursively at every folder depth.

## When to Use Which

| Factor | Flat `index.md` | AGENTS.md Progressive Disclosure |
|--------|-----------------|----------------------------------|
| Scale | Small wikis (<50 pages) | Any scale, especially growing wikis |
| Maintenance burden | One file to update on every change | Each folder's AGENTS.md updated only when that folder's structure changes |
| Discoverability | Single source of truth for all pages | Context at point of use; navigation via folder hierarchy |
| LLM-friendly | LLM reads one file | LLM walks the folder tree, reading only relevant AGENTS.md files |
| Redundancy risk | Drift between index.md and actual pages | AGENTS.md at the folder level stays accurate because it's local |

## Structure

```
wiki/
├── AGENTS.md            ← Root: what's in the wiki, page schema, links to wiki-schema.md
├── log.md               ← Append-only activity log (structured, parsable)
├── entities/
│   ├── AGENTS.md        ← Entity conventions: naming, when to create, tagging rules
│   ├── person-name.md
│   └── ...
├── topics/
│   ├── AGENTS.md        ← Topic conventions: merging, structure, cross-linking
│   └── ...
├── sources/
│   ├── AGENTS.md        ← Source summary conventions
│   └── ...
└── syntheses/
    ├── AGENTS.md        ← Synthesis conventions
    └── ...
```

## Frontmatter as Query Layer

Every page gets structured YAML frontmatter (`type`, `tags`, `sources`, 
`created`, `updated`). This replaces the need for a flat index for 
retrieval purposes — tags and type are what you query against:

```yaml
---
title: "Page Title"
type: entity | topic | source | synthesis
tags: [tag1, tag2]
sources: [source-ids-that-informed-this-page]
created: 2026-07-22
updated: 2026-07-22
---
```

Tools like Obsidian Dataview, grep, or `search_files` can query these 
directly: `search_files "type: entity" path="wiki/"`.

## Root AGENTS.md Template

```markdown
# Wiki — Knowledge Base

LLM-maintained wiki. Every page follows the schema defined in `wiki-schema.md`.

## Structure

| Directory | Contents | Conventions |
|-----------|----------|-------------|
| entities/ | Person, company, product, concept pages | One per named thing in >=2 sources |
| topics/   | Thematic area summaries | Merge 3+ related sources |
| sources/  | Single-source summaries | One per ingested source |
| syntheses/| Cross-cutting analysis | Q&A outputs worth keeping |
| log.md    | Append-only activity log | Structured, parsable entries |

## Page Rule

Every page MUST have frontmatter with `title`, `type`, `tags`, `sources`,
`created`, and `updated`. Without it, the page is invisible to query tools.
```

## How INGEST Works (vs. index.md)

With the flat index pattern, ingest requires:
1. Create page(s)
2. Add entry to `index.md`
3. Append to `log.md`

With AGENTS.md progressive disclosure:
1. Create page(s) with proper frontmatter
2. If a new entity type or subfolder emerged, update the relevant `AGENTS.md`
3. Append to `log.md`

No single index file to maintain. The frontmatter IS the index.

## How QUERY Works (vs. index.md)

With the flat index pattern:
1. Read `index.md` to find relevant pages
2. Read those pages

With AGENTS.md progressive disclosure:
1. Read `wiki/AGENTS.md` to understand structure
2. Read subfolder `AGENTS.md` to narrow which pages to check
3. Read those pages

The trade-off: one more read, but each read is smaller and more relevant.
