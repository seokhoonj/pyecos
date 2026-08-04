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

## Curated indicators

Reach the Bank of Korea's headline series **by name** instead of memorizing a stat
code. Each is `ecos.<group>.<indicator>.fetch()`, discoverable by editor autocomplete.

```python
with ECOS() as ecos:
    ecos.rate.base.fetch(start="202001", end="202412")   # base rate
    ecos.fx.usd.latest()                                 # latest KRW/USD
    ecos.trade.exports.semiconductor.value.fetch()       # semiconductor export value index
    ecos.stock.kospi.per.fetch()                         # KOSPI PER
```

Every indicator offers `.fetch(start, end)` and `.latest()`. Alongside the top-100
indicators, the tree includes frequently used series (semiconductor export/import
value/volume/price, reserve-asset components, KOSPI/KOSDAQ market metrics).

<details>
<summary>Full indicator list (125) </summary>

| Group | Accessor | Indicator |
|---|---|---|
| rate | `ecos.rate.base` | Bank of Korea Base Rate |
| rate | `ecos.rate.call` | Call Rate (Overnight) |
| rate | `ecos.rate.koribor_3m` | KORIBOR(3 month) |
| rate | `ecos.rate.cd_91d` | CD(91 day) |
| rate | `ecos.rate.msb_364d` | Monetary Stabilization Bonds(364 day) |
| rate | `ecos.rate.treasury_3y` | Treasury Bonds(3 year) |
| rate | `ecos.rate.treasury_5y` | Treasury Bonds(5 year) |
| rate | `ecos.rate.corporate_bond_3y` | Corporate Bonds(3 year, AA-) |
| rate | `ecos.rate.deposit` | Interest Rate on Time & Savings Deposits of CBs & SBs |
| rate | `ecos.rate.loan` | Interest Rate on Loans & Discounts of CBs & SBs |
| credit | `ecos.credit.total_deposits` | Total Deposits of CBs & SBs(Avg.) |
| credit | `ecos.credit.total_loans` | Loans of CBs & SBs(Avg.) |
| credit | `ecos.credit.household_credit` | Credit to Households |
| credit | `ecos.credit.household_delinquency_rate` | Household Loans Delinquency Rate |
| money | `ecos.money.m1` | M1(Narrow Money, Avg.) |
| money | `ecos.money.m2` | M2(Broad Money, Avg.) |
| money | `ecos.money.lf` | Lf(Avg.) |
| money | `ecos.money.l` | L(End of) |
| fx | `ecos.fx.usd` | KRW/USD(Closing Rate) |
| fx | `ecos.fx.jpy` | KRW/JPY(100 Yen) |
| fx | `ecos.fx.eur` | KRW/EURO |
| fx | `ecos.fx.cny` | KRW/CNY(Closing Rate) |
| stock | `ecos.stock.kospi.index` | KOSPI |
| stock | `ecos.stock.kosdaq.index` | KOSDAQ Index |
| stock | `ecos.stock.kosdaq.trading_value` | KOSDAQ's Trading Value |
| stock | `ecos.stock.kospi.trading_value` | KOSPI’s Trading Value |
| stock | `ecos.stock.kospi.market_cap` | KOSPI Market Capitalization |
| stock | `ecos.stock.kospi.volume` | KOSPI Trading Volume |
| stock | `ecos.stock.kospi.turnover` | KOSPI Turnover Ratio |
| stock | `ecos.stock.kospi.dividend_yield` | KOSPI Dividend Yield |
| stock | `ecos.stock.kospi.per` | KOSPI PER |
| stock | `ecos.stock.kosdaq.market_cap` | KOSDAQ Market Capitalization |
| stock | `ecos.stock.kosdaq.volume` | KOSDAQ Trading Volume |
| stock | `ecos.stock.kosdaq.turnover` | KOSDAQ Turnover Ratio |
| stock | `ecos.stock.investor_deposits` | Investor Deposits |
| bond | `ecos.bond.trading_value` | Bonds Trading Value |
| bond | `ecos.bond.treasury_issuance` | Issued Amount of Treasury Bonds |
| growth | `ecos.growth.gdp_growth` | GDP Growth Rate(S.A.) |
| growth | `ecos.growth.private_consumption_growth` | Private Consumption(S.A., % Change) |
| growth | `ecos.growth.facilities_investment_growth` | Facilities Investment(S.A.,% Change) |
| growth | `ecos.growth.construction_investment_growth` | Construction Investment(S.A.,% Change) |
| growth | `ecos.growth.exports_growth` | Exports of Goods and Services(S.A., % Change) |
| growth | `ecos.growth.gdp_nominal` | GDP(S.A.,at Current Price) |
| growth | `ecos.growth.gni_per_capita` | Per Capita GNI |
| growth | `ecos.growth.gross_saving_ratio` | Gross Saving Ratio |
| growth | `ecos.growth.gross_investment_ratio` | Gross Dom. Investment Ratio |
| growth | `ecos.growth.trade_to_gni_ratio` | Ratio of Exports and Imports to GNI |
| production | `ecos.production.all_industry` | Index of all industry production |
| production | `ecos.production.manufacturing.output` | Manufacturing Production Index |
| production | `ecos.production.manufacturing.shipment` | Manufacturing Shipment Index |
| production | `ecos.production.manufacturing.inventory` | Manufacturing Inventory Index |
| production | `ecos.production.manufacturing.utilization` | Index of manufacturing capacity utilization rate |
| production | `ecos.production.services` | index of Services Production |
| production | `ecos.production.retail_wholesale` | Wholesale and Retail Production Index |
| consumption | `ecos.consumption.retail_sales` | Retail Sales Index |
| consumption | `ecos.consumption.credit_card_spending` | Amount of Personal Credit Cards Use |
| consumption | `ecos.consumption.motor_vehicle_sales` | Motor Vehicle Sales Index |
| investment | `ecos.investment.equipment` | Estimated Index of Equipment Investment |
| investment | `ecos.investment.machinery_shipment` | Domestic Machinery Shipment Index |
| investment | `ecos.investment.machinery_orders` | Value of Dom. Machinery Orders Received |
| investment | `ecos.investment.construction_completed` | Value of Construction Completed |
| investment | `ecos.investment.building_permits` | Permits Authorized for Bldg. Construction |
| investment | `ecos.investment.construction_orders` | Value of Construction Orders Received |
| investment | `ecos.investment.construction_started` | Results of Construction Start |
| business_cycle | `ecos.business_cycle.coincident_index` | Cyclical Component of Coincident Index |
| business_cycle | `ecos.business_cycle.leading_index` | Cyclical Component of Leading Index |
| sentiment | `ecos.sentiment.business` | Composite Business Sentiment Index |
| sentiment | `ecos.sentiment.consumer` | Composite Consumer Sentiment Index |
| sentiment | `ecos.sentiment.economic` | Economic Sentiment Index |
| sentiment | `ecos.sentiment.manufacturing_bsi` | BSI(Manufact. Business Con., Tendency) |
| corporate | `ecos.corporate.manufacturing.sales_growth` | Growth Rate of Sales in Manufacturing |
| corporate | `ecos.corporate.manufacturing.profit_margin` | Ordinary Income to Sales in Manufacturing |
| corporate | `ecos.corporate.manufacturing.debt_ratio` | Debt Ratio in Manufacturing |
| household | `ecos.household.income` | Monthly Ave. Income of Households |
| household | `ecos.household.propensity_to_consume` | Average of Propensity to Consume |
| household | `ecos.household.gini` | Gini's Coefficient |
| household | `ecos.household.quintile_ratio` | Income of Highest Quintile/Income of Lowest Quintile(by quintile, ratio) |
| employment | `ecos.employment.unemployment_rate` | Unemployment Rate |
| employment | `ecos.employment.employment_rate` | Employment Rate |
| employment | `ecos.employment.active_population` | Economically Active Population |
| employment | `ecos.employment.employed_persons` | Employed Persons |
| employment | `ecos.employment.hourly_wage` | Hourly Nominal Wage Index |
| employment | `ecos.employment.labor_productivity` | Index of Labor Productivity |
| employment | `ecos.employment.unit_labor_cost` | Unit Labor Cost |
| population | `ecos.population.projected` | Population Projected |
| population | `ecos.population.elderly_ratio` | Elderly Population Ratio |
| population | `ecos.population.fertility_rate` | Total Fertility Rate |
| external | `ecos.external.current_account` | Current Account |
| external | `ecos.external.direct_investment_assets` | Direct Investment, Assets |
| external | `ecos.external.direct_investment_liabilities` | Direct Investment, Liabilities |
| external | `ecos.external.portfolio_investment_assets` | Portfolio Investment, Assets |
| external | `ecos.external.portfolio_investment_liabilities` | Portfolio Investment, Liabilities |
| external | `ecos.external.reserves.total` | International Reserves |
| external | `ecos.external.reserves.fx` | International Reserves: Foreign Exchange |
| external | `ecos.external.reserves.gold` | International Reserves: Gold |
| external | `ecos.external.reserves.sdr` | International Reserves: SDRs |
| external | `ecos.external.reserves.imf` | International Reserves: IMF Reserve Position |
| external | `ecos.external.debt` | External Debt |
| external | `ecos.external.claims` | External Claims |
| trade | `ecos.trade.exports.value` | Export value index |
| trade | `ecos.trade.imports.value` | Import value index |
| trade | `ecos.trade.exports.volume` | Export volume index |
| trade | `ecos.trade.imports.volume` | Import volume index |
| trade | `ecos.trade.terms_of_trade.net` | Net Barter Terms of Trade Index |
| trade | `ecos.trade.terms_of_trade.income` | Income Terms of Trade Index |
| trade | `ecos.trade.exports.price` | Export Price Index |
| trade | `ecos.trade.imports.price` | Import Price Index |
| trade | `ecos.trade.exports.semiconductor.value` | Semiconductor Export Value Index |
| trade | `ecos.trade.exports.semiconductor.volume` | Semiconductor Export Volume Index |
| trade | `ecos.trade.exports.semiconductor.price` | Semiconductor Export Price Index |
| trade | `ecos.trade.imports.semiconductor.value` | Semiconductor Import Value Index |
| trade | `ecos.trade.imports.semiconductor.volume` | Semiconductor Import Volume Index |
| trade | `ecos.trade.imports.semiconductor.price` | Semiconductor Import Price Index |
| price | `ecos.price.cpi` | Consumer Price Index |
| price | `ecos.price.core_cpi` | CPI Excluding Agricultural Products & Oils |
| price | `ecos.price.living_cpi` | CPI For Living Necessaries |
| price | `ecos.price.ppi` | Producer Price Index |
| price | `ecos.price.producer.dram` | DRAM Producer Price |
| price | `ecos.price.producer.nand` | NAND Flash Producer Price |
| price | `ecos.price.producer.system_semiconductor` | System Semiconductor Producer Price |
| real_estate | `ecos.real_estate.house_sales_price` | Housing Sales Price Index |
| real_estate | `ecos.real_estate.house_jeonse_price` | Housing Jeonse Price Index |
| real_estate | `ecos.real_estate.land_price_change` | Land Price Change Rates |
| commodity | `ecos.commodity.dubai_oil` | Dubai Crude Oil |
| commodity | `ecos.commodity.gold` | Gold Price(Spot) |

</details>

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
