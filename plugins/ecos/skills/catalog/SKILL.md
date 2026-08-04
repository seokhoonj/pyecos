---
name: catalog
description: "Find ECOS statistic table codes and their item codes by browsing the Bank of Korea catalog. Holds no logic of its own -- it calls the pyecos package's CLI (`ecos tables` / `ecos items`) and shows the result to the user. Use this to turn a concept (기준금리, CPI) into the codes the series skill needs. Trigger phrases: ECOS 통계표 찾아, 통계 코드, 항목 코드, find ECOS table code, ECOS item code, what stat code is, 한은 통계 목록."
---

# ecos — catalog (tables and items)

Discover the codes a statistic is stored under. ECOS keys every series by a table code
plus an item code, and this skill finds them: `tables` lists statistical tables (or one
table's children), `items` lists a table's detail items. The listing and parsing live in
the pyecos package (on PyPI); this skill is a thin wrapper that calls its CLI and relays
the result.

## Prerequisite

This plugin calls the `ecos` CLI, so the package must be installed and an API key set:

```
pipx install pyecos          # or: pip install pyecos
export ECOS_API_KEY=...       # a free key from https://ecos.bok.or.kr/api/#/
```

The key can also be stored in `~/.config/pyecos/credentials.json` as
`{"ECOS_API_KEY": "..."}`. Without a key the CLI exits with
`ecos: no ECOS API key ...`; relay that and point the user at the ECOS site.

## Running

```
ecos tables [--stat-code CODE] [--lang kr|en] [--json]
ecos items "<STAT_CODE>" [--lang kr|en] [--json]
```

- `ecos tables` with no code lists the top-level tables; with `--stat-code` it lists
  that table's children (the catalog is a tree, so drill down a level at a time).
- `ecos items "<STAT_CODE>"` lists the detail items of one table -- these are the
  `--item` codes the **series** skill needs.
- `--json` emits the full rows; the text view shows aligned columns and a row count.

## Procedure

1. **Start broad, then drill.** From a concept, list `ecos tables` and scan the names
   for the matching area; take that table's `code` and either list its children
   (`ecos tables --stat-code CODE`) or its items (`ecos items CODE`).
2. **Run.**
   ```bash
   ecos tables
   ecos items "722Y001"
   ```
3. **Relay the result.** Show the CLI's stdout. When the goal is a single code, point out
   the one row the user needs (its `code` / `item`), then offer to hand it to the
   **series** skill.
4. **Error handling.** Relay the one-line `ecos: <message>` from stderr as-is. The same
   key and install errors as the series skill apply. An empty listing prints `(no rows)`.

## What this skill does not do

- It does not re-implement listing or parsing (the package does); it always calls the CLI.
- It finds codes only -- to fetch the observations for a code, use the **series** skill.
