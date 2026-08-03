---
name: key-statistics
description: "Show the Bank of Korea's top-100 headline economic indicators in one shot from ECOS. Holds no logic of its own -- it calls the pyecos package's CLI (`pyecos key-stats`) and shows the result to the user. Use for a quick snapshot without needing any table code. Trigger phrases: 100대 지표, 주요 경제지표, 한은 핵심 지표, top-100 indicators, key Korean economic indicators, ECOS headline stats."
---

# pyecos — key statistics (top-100 indicators)

Print the Bank of Korea's curated top-100 indicators -- base rate, CPI, GDP growth,
exchange rate, and the rest -- each with its latest value, cycle, and unit. No table code
is needed; it is one call. The fetching and parsing live in the pyecos package (on PyPI);
this skill is a thin wrapper that calls its CLI and relays the result.

## Prerequisite

This plugin calls the `pyecos` CLI, so the package must be installed and an API key set:

```
pipx install pyecos          # or: pip install pyecos
export ECOS_API_KEY=...       # a free key from https://ecos.bok.or.kr/api/#/
```

The key can also be stored in `~/.config/pyecos/credentials.json` as
`{"ECOS_API_KEY": "..."}`. Without a key the CLI exits with
`pyecos: no ECOS API key ...`; relay that and point the user at the ECOS site.

## Running

```
pyecos key-stats [--lang kr|en] [--json]
```

Options (`pyecos key-stats --help` is the source of truth):
- `--lang kr|en` — response language (default: kr).
- `--json` — the full list as JSON instead of the text table.

The text output is an aligned table (class, indicator name, latest value, unit) with a
row count.

## Procedure

1. **Run.** No arguments are required.
   ```bash
   pyecos key-stats
   ```
2. **Relay the result.** Show the CLI's stdout. If the user asked about one indicator,
   point out its row; the list is grouped by class (interest rates, prices, ...), so you
   can filter to the group they asked for.
3. **Follow up.** For a full time series of any one indicator rather than just its latest
   value, hand off to the **series** skill (find its code first with **catalog**).
4. **Error handling.** Relay the one-line `pyecos: <message>` from stderr as-is -- the
   same key and install errors as the other pyecos skills apply.

## What this skill does not do

- It does not re-implement fetching or parsing (the package does); it always calls the CLI.
- It shows latest values only -- for a full time series, use the **series** skill.
