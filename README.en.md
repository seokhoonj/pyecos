# pyecos

[![check](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml/badge.svg)](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml)
[![PyPI](https://img.shields.io/pypi/v/pyecos)](https://pypi.org/project/pyecos/)
[![Python](https://img.shields.io/pypi/pyversions/pyecos)](https://pypi.org/project/pyecos/)
[![License](https://img.shields.io/pypi/l/pyecos)](https://github.com/seokhoonj/pyecos/blob/main/LICENSE)

**English** | [한국어](README.md)

A Python client for the [ECOS Open API](https://ecos.bok.or.kr/api/#/) — the
Bank of Korea's Economic Statistics System. One `ECOS` object, six methods that
map to the six ECOS services, and rows that drop straight into a DataFrame.

## Install

```bash
pip install pyecos
```

Get a free API key from the [ECOS Open API site](https://ecos.bok.or.kr/api/#/).
`ECOS()` resolves it from, in order:

1. the `api_key` you pass to `ECOS(...)`,
2. the `ECOS_API_KEY` environment variable,
3. `"ECOS_API_KEY"` in `~/.config/pyecos/credentials.json` (honoring `$XDG_CONFIG_HOME`).

```bash
export ECOS_API_KEY="your-key"
# or, to store it once:
mkdir -p ~/.config/pyecos
printf '{"ECOS_API_KEY": "your-key"}' > ~/.config/pyecos/credentials.json
chmod 600 ~/.config/pyecos/credentials.json
```

## Usage

```python
from pyecos import ECOS, Cycle

with ECOS() as ecos:
    # A statistic's observations (StatisticSearch).
    rows = ecos.fetch_series(
        "722Y001",              # 시장금리
        item_code1="0101000",   # 한국은행 기준금리
        cycle=Cycle.MONTHLY,
        start="202001",
        end="202412",
    )

    # Browse the catalog.
    tables = ecos.fetch_tables()             # top-level statistical tables
    children = ecos.fetch_tables(stat_code="722Y001")
    items = ecos.fetch_items("722Y001")      # a table's detail items

    # Headline indicators, glossary, meta-DB.
    key = ecos.fetch_key_statistics()        # top-100 indicators
    word = ecos.fetch_glossary("DSR")
    meta = ecos.fetch_meta("경제심리지수")
```

Every method returns a `list` of plain `dict` rows, so pandas is one line away
(and never a required dependency):

```python
import pandas as pd

frame = pd.DataFrame(rows)
```

`fetch_series` returns each observation's `data_value` as a `float` (`None` when the
Bank reported it blank) and pages past the API's 100-row-per-request limit for
you, so a multi-year daily series comes back in a single call.

## Command line

Installing the package also puts a `pyecos` command on your PATH, with one subcommand
per service:

```bash
export ECOS_API_KEY="your-key"

pyecos series 722Y001 --item 0101000 --cycle monthly --start 202001 --end 202412
pyecos tables                        # top-level statistical tables
pyecos items 722Y001                 # a table's detail items
pyecos key-stats                     # the top-100 headline indicators
pyecos glossary DSR
pyecos meta 경제심리지수
```

Flags (`pyecos <command> --help` is the source of truth):

- `series <stat_code>` — `--item CODE` (repeat up to 4), `--cycle annual|semiannual|quarterly|monthly|semimonthly|daily` (default `monthly`), `--start`, `--end`
- `tables` — `--stat-code CODE` for a table's children (omit for the top level)
- `items <stat_code>` · `key-stats` · `glossary <word>` · `meta <dataset_name>`
- every subcommand: `--lang kr|en`, `--json` · top level: `--version`

## Cycles

`fetch_series` takes a `Cycle` (or its bare code). The `time` field of each row is
formatted to match:

| Cycle | Code | `time` example |
|---|---|---|
| Annual | `A` | `2024` |
| Semiannual | `S` | `2024S1` |
| Quarterly | `Q` | `2024Q1` |
| Monthly | `M` | `202401` |
| Semimonthly | `SM` | `202401S1` |
| Daily | `D` | `20240115` |

## Errors

All operational errors derive from `ECOSError`:

| Exception | Raised when |
|---|---|
| `ECOSConfigError` | no API key was provided |
| `ECOSAuthError` | ECOS rejected the key |
| `ECOSRateLimitError` | ECOS is rate-limiting the key (ERROR-602 · subclass of `ECOSResponseError`) |
| `ECOSResponseError` | ECOS returned an error code (carries `.code` / `.message`) |
| `ECOSNetworkError` | the request never completed (after a transient timeout/5xx is retried) |

A query that simply matches no data returns an empty list, not an error. An invalid
`cycle` or `lang` argument raises the standard `ValueError`.

When fetching in bulk, space out requests with `ECOS(delay_seconds=0.6)` to stay under
the ECOS rate cap (~300 calls in three minutes).

## License

[MIT](LICENSE)
