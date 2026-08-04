# pyecos

[![check](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml/badge.svg)](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml)
[![PyPI](https://img.shields.io/pypi/v/pyecos)](https://pypi.org/project/pyecos/)
[![Python](https://img.shields.io/pypi/pyversions/pyecos)](https://pypi.org/project/pyecos/)
[![License](https://img.shields.io/pypi/l/pyecos)](https://github.com/seokhoonj/pyecos/blob/main/LICENSE)

[한국어](README.md) | **English**

A Python client for the Bank of Korea's [ECOS Open API](https://ecos.bok.or.kr/api/#/).
Reach 125 headline indicators **by name**, hit the rest through six service methods.

## Install

```bash
pip install pyecos
```

Get a free API key from the [ECOS Open API site](https://ecos.bok.or.kr/api/#/), then register it one of two ways.

**① Pass it directly**

```python
from pyecos import ECOS

ecos = ECOS(api_key="your-key")
```

**② Save it and let `ECOS()` find it** — set an env var or a file, then call `ECOS()` with no argument.

```bash
# an env var
export ECOS_API_KEY="your-key"

# or a file, once
mkdir -p ~/.config/pyecos
printf '{"ECOS_API_KEY": "your-key"}' > ~/.config/pyecos/credentials.json
chmod 600 ~/.config/pyecos/credentials.json
```

The key is resolved ① argument → ② `ECOS_API_KEY` env var → ③ `~/.config/pyecos/credentials.json`.

## Quickstart

```python
from pyecos import ECOS

ecos = ECOS()                                              # finds the key automatically
rows = ecos.rate.base.fetch(start="202001", end="202412")  # the base rate, monthly
```

Rows are plain `dict`s, so they drop into a DataFrame in one line (pandas is not a required dependency).

```python
import pandas as pd

frame = pd.DataFrame(rows)
```

## Curated indicators (125)

No stat codes to memorize — reach **125** headline indicators by their `ecos.<group>.<indicator>` path.
Walking `ecos.` gives editor **autocomplete**, and every indicator offers `.fetch(start, end)` and `.latest()`.

```python
ecos = ECOS()

ecos.rate.base.fetch(start="202001", end="202412")  # base rate
ecos.fx.usd.latest()                                # latest KRW/USD
ecos.trade.exports.semiconductor.value.fetch()      # semiconductor export value index
ecos.stock.kospi.per.fetch()                        # KOSPI PER
```

The full tree — `name/` is a namespace (group), every leaf is an indicator.

```
ecos
├── rate/
│   ├── base
│   ├── call
│   ├── koribor_3m
│   ├── cd_91d
│   ├── msb_364d
│   ├── treasury_3y
│   ├── treasury_5y
│   ├── corporate_bond_3y
│   ├── deposit
│   └── loan
├── credit/
│   ├── total_deposits
│   ├── total_loans
│   ├── household_credit
│   └── household_delinquency_rate
├── money/
│   ├── m1
│   ├── m2
│   ├── lf
│   └── l
├── fx/
│   ├── usd
│   ├── jpy
│   ├── eur
│   └── cny
├── stock/
│   ├── kospi/
│   │   ├── index
│   │   ├── trading_value
│   │   ├── market_cap
│   │   ├── volume
│   │   ├── turnover
│   │   ├── dividend_yield
│   │   └── per
│   ├── kosdaq/
│   │   ├── index
│   │   ├── trading_value
│   │   ├── market_cap
│   │   ├── volume
│   │   └── turnover
│   └── investor_deposits
├── bond/
│   ├── trading_value
│   └── treasury_issuance
├── growth/
│   ├── gdp_growth
│   ├── private_consumption_growth
│   ├── facilities_investment_growth
│   ├── construction_investment_growth
│   ├── exports_growth
│   ├── gdp_nominal
│   ├── gni_per_capita
│   ├── gross_saving_ratio
│   ├── gross_investment_ratio
│   └── trade_to_gni_ratio
├── production/
│   ├── all_industry
│   ├── manufacturing/
│   │   ├── output
│   │   ├── shipment
│   │   ├── inventory
│   │   └── utilization
│   ├── services
│   └── retail_wholesale
├── consumption/
│   ├── retail_sales
│   ├── credit_card_spending
│   └── motor_vehicle_sales
├── investment/
│   ├── equipment
│   ├── machinery_shipment
│   ├── machinery_orders
│   ├── construction_completed
│   ├── building_permits
│   ├── construction_orders
│   └── construction_started
├── business_cycle/
│   ├── coincident_index
│   └── leading_index
├── sentiment/
│   ├── business
│   ├── consumer
│   ├── economic
│   └── manufacturing_bsi
├── corporate/
│   └── manufacturing/
│       ├── sales_growth
│       ├── profit_margin
│       └── debt_ratio
├── household/
│   ├── income
│   ├── propensity_to_consume
│   ├── gini
│   └── quintile_ratio
├── employment/
│   ├── unemployment_rate
│   ├── employment_rate
│   ├── active_population
│   ├── employed_persons
│   ├── hourly_wage
│   ├── labor_productivity
│   └── unit_labor_cost
├── population/
│   ├── projected
│   ├── elderly_ratio
│   └── fertility_rate
├── external/
│   ├── current_account
│   ├── direct_investment_assets
│   ├── direct_investment_liabilities
│   ├── portfolio_investment_assets
│   ├── portfolio_investment_liabilities
│   ├── reserves/
│   │   ├── total
│   │   ├── fx
│   │   ├── gold
│   │   ├── sdr
│   │   └── imf
│   ├── debt
│   └── claims
├── trade/
│   ├── exports/
│   │   ├── value
│   │   ├── volume
│   │   ├── price
│   │   └── semiconductor/
│   │       ├── value
│   │       ├── volume
│   │       └── price
│   ├── imports/
│   │   ├── value
│   │   ├── volume
│   │   ├── price
│   │   └── semiconductor/
│   │       ├── value
│   │       ├── volume
│   │       └── price
│   └── terms_of_trade/
│       ├── net
│       └── income
├── price/
│   ├── cpi
│   ├── core_cpi
│   ├── living_cpi
│   ├── ppi
│   └── producer/
│       ├── dram
│       ├── nand
│       └── system_semiconductor
├── real_estate/
│   ├── house_sales_price
│   ├── house_jeonse_price
│   └── land_price_change
└── commodity/
    ├── dubai_oil
    └── gold
```

## The six services

For anything not curated, call the service methods on `ECOS`. They map one-to-one to the six ECOS services and all return `list[dict]`.

| Method | Returns | ECOS service |
|---|---|---|
| `fetch_series(stat_code, ...)` | a statistic's series | StatisticSearch |
| `fetch_tables(stat_code=None)` | the table list | StatisticTableList |
| `fetch_items(stat_code)` | a table's items | StatisticItemList |
| `fetch_key_statistics()` | the top-100 indicators | KeyStatisticList |
| `fetch_glossary(word)` | a glossary term | StatisticWord |
| `fetch_meta(dataset_name)` | a meta-DB dataset | StatisticMeta |

```python
ecos = ECOS()

rows = ecos.fetch_series(
    "722Y001",             # the market-rates table
    item_code1="0101000",  # Bank of Korea base rate
    cycle="M",
    start="202001",
    end="202412",
)
```

`fetch_series` returns `data_value` as `None` when the Bank left it blank, and pages past the 100-row-per-request limit for you, so a multi-year daily series comes back in one call.

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

## Offline catalog

To find the `stat_code` for a table that isn't among the 125 curated indicators — with no key and no network — search the snapshot bundled in the package.

```python
from pyecos import catalog

# Table names are Korean, so search by a Korean keyword or a code prefix.
catalog.search("소비자물가")   # or catalog.search("901Y")
catalog.table("901Y009")      # one table's row, or None
catalog.tables()              # the whole snapshot (834 tables)
```

For the live hierarchy or a table's items, use `ecos.fetch_tables()` / `ecos.fetch_items()`.

## License

[MIT](LICENSE)
