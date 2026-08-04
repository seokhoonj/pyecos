---
name: series
description: "Fetch a Bank of Korea economic statistic as a time series from ECOS. Holds no logic of its own -- it calls the pyecos package's CLI (`ecos series`) and shows the result to the user. Needs a stat table code and usually an item code (find them with the catalog skill). Trigger phrases: 기준금리 시계열, 환율 추이, ECOS 통계 가져와, economic statistic time series, Bank of Korea interest rate, CPI series, 한은 통계."
---

# ecos — statistic time series

Take an ECOS statistic table code (and usually an item code) and print its observations
over time. The fetching, pagination, and parsing live in the pyecos package (on PyPI);
this skill is a thin wrapper that calls its CLI and relays the result. A rejected key or a
vendor error comes back from the CLI as a one-line `ecos: <message>` -- relay it as-is
rather than throwing a stack trace at the user. (A missing or malformed argument is caught
earlier by argparse, which prints usage and exits 2.)

## Prerequisite

This plugin calls the `ecos` CLI, so the package must be installed and an API key set:

```
pipx install pyecos          # or: pip install pyecos
export ECOS_API_KEY=...       # a free key from https://ecos.bok.or.kr/api/#/
```

That puts the `ecos` command on PATH. The key can also be stored in
`~/.config/pyecos/credentials.json` as `{"ECOS_API_KEY": "..."}`. Without a key the
CLI exits with `ecos: no ECOS API key ...`; relay that and point the user at the
ECOS site.

## Running

```
ecos series "<STAT_CODE>" [--item CODE] [--cycle ...] [--start ...] [--end ...] [options]
```

Options (`ecos series --help` is the source of truth):
- `--item CODE` — an item code selecting a sub-series; repeat up to 4 times.
- `--cycle annual|semiannual|quarterly|monthly|semimonthly|daily` — frequency (default: monthly).
- `--start` / `--end` — cycle-formatted period bounds: `202401` (monthly), `2024`
  (annual), `2024Q1` (quarterly), `20240115` (daily). ECOS usually requires both.
- `--lang kr|en` — response language (default: kr).
- `--json` — the full series as JSON instead of the text summary.

The text output is a one-line summary (code, name, observation count, unit) plus the
most recent observations. Use `--json` when the user wants the whole series or machine-
readable data.

## Procedure

1. **Get the code.** You need a `stat_code` and usually an `item_code`. If the user gave
   a concept ("기준금리", "원/달러 환율") but no code, use the **catalog** skill first to
   look it up, then come back here.
2. **Run.** Call the CLI. Add `--start`/`--end`/`--cycle` for the window and frequency
   the user asked for; add `--json` when they want the full series.
   ```bash
   ecos series "722Y001" --item 0101000 --cycle monthly --start 202001 --end 202412
   ```
3. **Relay the result.** Show the CLI's stdout. You may trim a long series, but keep the
   summary line.
4. **Error handling.** When the CLI exits non-zero, relay the one-line `ecos: <message>`
   from stderr as-is. Common ones:
   - `command not found: ecos` -> not installed; point the user at `pipx install pyecos`.
   - `no ECOS API key ...` -> no key was found (env var and config file both empty).
   - a "rejected key" / authentication message -> the key was rejected (vendor code INFO-100).
   - `[ERROR-...] ...` -> a vendor error, often a missing period or a wrong item code.
   An empty series (no rows in range) is not an error -- the summary line says so.

## What this skill does not do

- It does not re-implement fetching or parsing (the package does); it always calls the CLI.
- It is the observation series only -- to discover table and item codes, use the
  **catalog** skill; for the headline indicator snapshot, use **key-statistics**.
