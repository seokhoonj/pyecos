# pyecos

[![check](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml/badge.svg)](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml)
[![PyPI](https://img.shields.io/pypi/v/pyecos)](https://pypi.org/project/pyecos/)
[![Python](https://img.shields.io/pypi/pyversions/pyecos)](https://pypi.org/project/pyecos/)
[![License](https://img.shields.io/pypi/l/pyecos)](https://github.com/seokhoonj/pyecos/blob/main/LICENSE)

**English** | [한국어](README.md)

Read economic and financial statistics from the Bank of Korea's **ECOS** (Economic
Statistics System).

Policy and market interest rates, exchange rates, money supply and bank deposits / loans,
the KOSPI and KOSDAQ, consumer and producer prices, GDP and growth, production /
consumption / investment, business and consumer sentiment, employment and wages,
population and households, the balance of payments, reserves and external debt, export /
import prices and volumes, housing / land prices, and the policy and market rates of
major economies (US, Japan, China, euro area, UK, Korea, Canada, India, and more).

Frequently-used indicators are reached through an **accessor** (like `ecos.rate.base`);
everything else is fetched by its statistic-table code.

## 1. Install

```bash
pip install pyecos
```

Get a free API key at <https://ecos.bok.or.kr/api/>. There are two ways to give it to pyecos.

**Option 1 — pass it in code** (to try it once)

```python
from pyecos import ECOS

ecos = ECOS(api_key="your-key")
```

**Option 2 — save it to a file** (recommended — save once, never pass it again)

Create `~/.config/pyecos/credentials.json` with:

```json
{ "ECOS_API_KEY": "your-key" }
```

After that, a bare `ECOS()` finds this key on its own.

> Prefer an environment variable? On macOS/Linux, in the terminal:
> `export ECOS_API_KEY="your-key"`. On Windows, in PowerShell:
> `setx ECOS_API_KEY "your-key"`.

## 2. Quickstart

```python
from pyecos import ECOS

ecos = ECOS()                                              # finds your saved key
rows = ecos.rate.base.fetch(start="202001", end="202412")  # base rate, monthly 2020-2024
```

Returns are a `list` of `dict`, so a table (DataFrame) is one line away (pandas optional).

```python
import pandas as pd

pd.DataFrame(rows)   # or polars.DataFrame(rows)
```

## 3. Curated indicators (149)

Instead of memorizing table codes, reach the frequently-used indicators as `ecos.group.indicator`.
Type `ecos.` and follow the dots with editor autocomplete. Every indicator offers two calls.

- `.fetch(start, end)` — the whole series over a period
- `.latest()` — just the most recent value

```python
ecos.rate.base.fetch(start="202001", end="202412")  # base rate
ecos.fx.usd.latest()                                # latest KRW/USD
ecos.trade.exports.semiconductor.value.fetch()      # semiconductor export value index
ecos.price.producer.dram.fetch()                    # DRAM producer price
ecos.price.producer.nand.fetch()                    # NAND flash producer price
ecos.stock.kospi.per.fetch()                        # KOSPI P/E
ecos.world.rate.policy.us.latest()                  # US policy rate, latest
```

In the tree below, **a line ending in `/` is just a grouping** (e.g. `rate/`, `stock/`);
**a line without `/` is an actual indicator**. Join the dots to call one — e.g. `base`
under `rate/` is `ecos.rate.base`.

```
ecos
├── rate/
│   ├── base                              # Bank of Korea Base Rate
│   ├── call                              # Call Rate (Overnight)
│   ├── koribor_3m                        # KORIBOR(3 month)
│   ├── cd_91d                            # CD(91 day)
│   ├── msb_364d                          # Monetary Stabilization Bonds(364 day)
│   ├── treasury_3y                       # Treasury Bonds(3 year)
│   ├── treasury_5y                       # Treasury Bonds(5 year)
│   ├── corporate_bond_3y                 # Corporate Bonds(3 year, AA-)
│   ├── deposit                           # Interest Rate on Time & Savings Deposits of CBs & SBs
│   └── loan                              # Interest Rate on Loans & Discounts of CBs & SBs
├── credit/
│   ├── total_deposits                    # Total Deposits of CBs & SBs(Avg.)
│   ├── total_loans                       # Loans of CBs & SBs(Avg.)
│   ├── household_credit                  # Credit to Households
│   └── household_delinquency_rate        # Household Loans Delinquency Rate
├── money/
│   ├── m1                                # M1(Narrow Money, Avg.)
│   ├── m2                                # M2(Broad Money, Avg.)
│   ├── lf                                # Lf(Avg.)
│   └── l                                 # L(End of)
├── fx/
│   ├── usd                               # KRW/USD(Closing Rate)
│   ├── jpy                               # KRW/JPY(100 Yen)
│   ├── eur                               # KRW/EURO
│   └── cny                               # KRW/CNY(Closing Rate)
├── stock/
│   ├── kospi/
│   │   ├── index                         # KOSPI
│   │   ├── trading_value                 # KOSPI’s Trading Value
│   │   ├── market_cap                    # KOSPI Market Capitalization
│   │   ├── volume                        # KOSPI Trading Volume
│   │   ├── turnover                      # KOSPI Turnover Ratio
│   │   ├── dividend_yield                # KOSPI Dividend Yield
│   │   └── per                           # KOSPI PER
│   ├── kosdaq/
│   │   ├── index                         # KOSDAQ Index
│   │   ├── trading_value                 # KOSDAQ's Trading Value
│   │   ├── market_cap                    # KOSDAQ Market Capitalization
│   │   ├── volume                        # KOSDAQ Trading Volume
│   │   └── turnover                      # KOSDAQ Turnover Ratio
│   └── investor_deposits                 # Investor Deposits
├── bond/
│   ├── trading_value                     # Bonds Trading Value
│   └── treasury_issuance                 # Issued Amount of Treasury Bonds
├── growth/
│   ├── gdp_growth                        # GDP Growth Rate(S.A.)
│   ├── private_consumption_growth        # Private Consumption(S.A., % Change)
│   ├── facilities_investment_growth      # Facilities Investment(S.A.,% Change)
│   ├── construction_investment_growth    # Construction Investment(S.A.,% Change)
│   ├── exports_growth                    # Exports of Goods and Services(S.A., % Change)
│   ├── gdp_nominal                       # GDP(S.A.,at Current Price)
│   ├── gni_per_capita                    # Per Capita GNI
│   ├── gross_saving_ratio                # Gross Saving Ratio
│   ├── gross_investment_ratio            # Gross Dom. Investment Ratio
│   └── trade_to_gni_ratio                # Ratio of Exports and Imports to GNI
├── production/
│   ├── all_industry                      # Index of all industry production
│   ├── manufacturing/
│   │   ├── output                        # Manufacturing Production Index
│   │   ├── shipment                      # Manufacturing Shipment Index
│   │   ├── inventory                     # Manufacturing Inventory Index
│   │   └── utilization                   # Index of manufacturing capacity utilization rate
│   ├── services                          # index of Services Production
│   └── retail_wholesale                  # Wholesale and Retail Production Index
├── consumption/
│   ├── retail_sales                      # Retail Sales Index
│   ├── credit_card_spending              # Amount of Personal Credit Cards Use
│   └── motor_vehicle_sales               # Motor Vehicle Sales Index
├── investment/
│   ├── equipment                         # Estimated Index of Equipment Investment
│   ├── machinery_shipment                # Domestic Machinery Shipment Index
│   ├── machinery_orders                  # Value of Dom. Machinery Orders Received
│   ├── construction_completed            # Value of Construction Completed
│   ├── building_permits                  # Permits Authorized for Bldg. Construction
│   ├── construction_orders               # Value of Construction Orders Received
│   └── construction_started              # Results of Construction Start
├── business_cycle/
│   ├── coincident_index                  # Cyclical Component of Coincident Index
│   └── leading_index                     # Cyclical Component of Leading Index
├── sentiment/
│   ├── business                          # Composite Business Sentiment Index
│   ├── consumer                          # Composite Consumer Sentiment Index
│   ├── economic                          # Economic Sentiment Index
│   └── manufacturing_bsi                 # BSI(Manufact. Business Con., Tendency)
├── corporate/
│   └── manufacturing/
│       ├── sales_growth                  # Growth Rate of Sales in Manufacturing
│       ├── profit_margin                 # Ordinary Income to Sales in Manufacturing
│       └── debt_ratio                    # Debt Ratio in Manufacturing
├── household/
│   ├── income                            # Monthly Ave. Income of Households
│   ├── apc                               # Average of Propensity to Consume
│   ├── gini                              # Gini's Coefficient
│   └── quintile_ratio                    # Income of Highest Quintile/Income of Lowest Quintile(by quintile, ratio)
├── employment/
│   ├── unemployment_rate                 # Unemployment Rate
│   ├── employment_rate                   # Employment Rate
│   ├── active_population                 # Economically Active Population
│   ├── employed_persons                  # Employed Persons
│   ├── hourly_wage                       # Hourly Nominal Wage Index
│   ├── labor_productivity                # Index of Labor Productivity
│   └── unit_labor_cost                   # Unit Labor Cost
├── population/
│   ├── projected                         # Population Projected
│   ├── elderly_ratio                     # Elderly Population Ratio
│   └── fertility_rate                    # Total Fertility Rate
├── external/
│   ├── current_account                   # Current Account
│   ├── direct_investment_assets          # Direct Investment, Assets
│   ├── direct_investment_liabilities     # Direct Investment, Liabilities
│   ├── portfolio_investment_assets       # Portfolio Investment, Assets
│   ├── portfolio_investment_liabilities  # Portfolio Investment, Liabilities
│   ├── reserves/
│   │   ├── total                         # International Reserves
│   │   ├── fx                            # International Reserves: Foreign Exchange
│   │   ├── gold                          # International Reserves: Gold
│   │   ├── sdr                           # International Reserves: SDRs
│   │   └── imf                           # International Reserves: IMF Reserve Position
│   ├── debt                              # External Debt
│   └── claims                            # External Claims
├── trade/
│   ├── exports/
│   │   ├── value                         # Export value index
│   │   ├── volume                        # Export volume index
│   │   ├── price                         # Export Price Index
│   │   └── semiconductor/
│   │       ├── value                     # Semiconductor Export Value Index
│   │       ├── volume                    # Semiconductor Export Volume Index
│   │       └── price                     # Semiconductor Export Price Index
│   ├── imports/
│   │   ├── value                         # Import value index
│   │   ├── volume                        # Import volume index
│   │   ├── price                         # Import Price Index
│   │   └── semiconductor/
│   │       ├── value                     # Semiconductor Import Value Index
│   │       ├── volume                    # Semiconductor Import Volume Index
│   │       └── price                     # Semiconductor Import Price Index
│   └── terms_of_trade/
│       ├── net                           # Net Barter Terms of Trade Index
│       └── income                        # Income Terms of Trade Index
├── price/
│   ├── cpi                               # Consumer Price Index
│   ├── core_cpi                          # CPI Excluding Agricultural Products & Oils
│   ├── living_cpi                        # CPI For Living Necessaries
│   ├── ppi                               # Producer Price Index
│   └── producer/
│       ├── dram                          # DRAM Producer Price
│       ├── nand                          # NAND Flash Producer Price
│       └── logic                         # System Semiconductor Producer Price
├── real_estate/
│   ├── house_sales_price                 # Housing Sales Price Index
│   ├── house_jeonse_price                # Housing Jeonse Price Index
│   └── land_price_change                 # Land Price Change Rates
├── commodity/
│   ├── dubai_oil                         # Dubai Crude Oil
│   └── gold                              # Gold Price(Spot)
└── world/
    └── rate/
        ├── policy/
        │   ├── us                        # US Policy Rate
        │   ├── jp                        # Japan Policy Rate
        │   ├── cn                        # China Policy Rate
        │   ├── euro                      # Euro Area Policy Rate
        │   ├── uk                        # UK Policy Rate
        │   ├── kr                        # Korea Policy Rate
        │   ├── ca                        # Canada Policy Rate
        │   └── india                     # India Policy Rate
        └── market/                       # no euro-area market series in ECOS; Germany (de) proxies it
            ├── us/
            │   ├── long                  # US Long-term Rate
            │   └── short                 # US Short-term Rate
            ├── jp/
            │   ├── long                  # Japan Long-term Rate
            │   └── short                 # Japan Short-term Rate
            ├── cn/
            │   ├── long                  # China Long-term Rate
            │   └── short                 # China Short-term Rate
            ├── uk/
            │   ├── long                  # UK Long-term Rate
            │   └── short                 # UK Short-term Rate
            ├── kr/
            │   ├── long                  # Korea Long-term Rate
            │   └── short                 # Korea Short-term Rate
            ├── ca/
            │   ├── long                  # Canada Long-term Rate
            │   └── short                 # Canada Short-term Rate
            ├── india/
            │   ├── long                  # India Long-term Rate
            │   └── short                 # India Short-term Rate
            └── de/
                ├── long                  # Germany Long-term Rate
                └── short                 # Germany Short-term Rate
```

The full list:

| Group | Call | Indicator |
|---|---|---|
| rate | `ecos.rate.base` | Bank of Korea Base Rate |
| rate | `ecos.rate.call` | Call Rate (Overnight) |
| rate | `ecos.rate.cd_91d` | CD(91 day) |
| rate | `ecos.rate.corporate_bond_3y` | Corporate Bonds(3 year, AA-) |
| rate | `ecos.rate.deposit` | Interest Rate on Time & Savings Deposits of CBs & SBs |
| rate | `ecos.rate.koribor_3m` | KORIBOR(3 month) |
| rate | `ecos.rate.loan` | Interest Rate on Loans & Discounts of CBs & SBs |
| rate | `ecos.rate.msb_364d` | Monetary Stabilization Bonds(364 day) |
| rate | `ecos.rate.treasury_3y` | Treasury Bonds(3 year) |
| rate | `ecos.rate.treasury_5y` | Treasury Bonds(5 year) |
| credit | `ecos.credit.household_credit` | Credit to Households |
| credit | `ecos.credit.household_delinquency_rate` | Household Loans Delinquency Rate |
| credit | `ecos.credit.total_deposits` | Total Deposits of CBs & SBs(Avg.) |
| credit | `ecos.credit.total_loans` | Loans of CBs & SBs(Avg.) |
| money | `ecos.money.l` | L(End of) |
| money | `ecos.money.lf` | Lf(Avg.) |
| money | `ecos.money.m1` | M1(Narrow Money, Avg.) |
| money | `ecos.money.m2` | M2(Broad Money, Avg.) |
| fx | `ecos.fx.cny` | KRW/CNY(Closing Rate) |
| fx | `ecos.fx.eur` | KRW/EURO |
| fx | `ecos.fx.jpy` | KRW/JPY(100 Yen) |
| fx | `ecos.fx.usd` | KRW/USD(Closing Rate) |
| stock | `ecos.stock.investor_deposits` | Investor Deposits |
| stock | `ecos.stock.kosdaq.index` | KOSDAQ Index |
| stock | `ecos.stock.kosdaq.market_cap` | KOSDAQ Market Capitalization |
| stock | `ecos.stock.kosdaq.trading_value` | KOSDAQ's Trading Value |
| stock | `ecos.stock.kosdaq.turnover` | KOSDAQ Turnover Ratio |
| stock | `ecos.stock.kosdaq.volume` | KOSDAQ Trading Volume |
| stock | `ecos.stock.kospi.dividend_yield` | KOSPI Dividend Yield |
| stock | `ecos.stock.kospi.index` | KOSPI |
| stock | `ecos.stock.kospi.market_cap` | KOSPI Market Capitalization |
| stock | `ecos.stock.kospi.per` | KOSPI PER |
| stock | `ecos.stock.kospi.trading_value` | KOSPI’s Trading Value |
| stock | `ecos.stock.kospi.turnover` | KOSPI Turnover Ratio |
| stock | `ecos.stock.kospi.volume` | KOSPI Trading Volume |
| bond | `ecos.bond.trading_value` | Bonds Trading Value |
| bond | `ecos.bond.treasury_issuance` | Issued Amount of Treasury Bonds |
| growth | `ecos.growth.construction_investment_growth` | Construction Investment(S.A.,% Change) |
| growth | `ecos.growth.exports_growth` | Exports of Goods and Services(S.A., % Change) |
| growth | `ecos.growth.facilities_investment_growth` | Facilities Investment(S.A.,% Change) |
| growth | `ecos.growth.gdp_growth` | GDP Growth Rate(S.A.) |
| growth | `ecos.growth.gdp_nominal` | GDP(S.A.,at Current Price) |
| growth | `ecos.growth.gni_per_capita` | Per Capita GNI |
| growth | `ecos.growth.gross_investment_ratio` | Gross Dom. Investment Ratio |
| growth | `ecos.growth.gross_saving_ratio` | Gross Saving Ratio |
| growth | `ecos.growth.private_consumption_growth` | Private Consumption(S.A., % Change) |
| growth | `ecos.growth.trade_to_gni_ratio` | Ratio of Exports and Imports to GNI |
| production | `ecos.production.all_industry` | Index of all industry production |
| production | `ecos.production.manufacturing.inventory` | Manufacturing Inventory Index |
| production | `ecos.production.manufacturing.output` | Manufacturing Production Index |
| production | `ecos.production.manufacturing.shipment` | Manufacturing Shipment Index |
| production | `ecos.production.manufacturing.utilization` | Index of manufacturing capacity utilization rate |
| production | `ecos.production.retail_wholesale` | Wholesale and Retail Production Index |
| production | `ecos.production.services` | index of Services Production |
| consumption | `ecos.consumption.credit_card_spending` | Amount of Personal Credit Cards Use |
| consumption | `ecos.consumption.motor_vehicle_sales` | Motor Vehicle Sales Index |
| consumption | `ecos.consumption.retail_sales` | Retail Sales Index |
| investment | `ecos.investment.building_permits` | Permits Authorized for Bldg. Construction |
| investment | `ecos.investment.construction_completed` | Value of Construction Completed |
| investment | `ecos.investment.construction_orders` | Value of Construction Orders Received |
| investment | `ecos.investment.construction_started` | Results of Construction Start |
| investment | `ecos.investment.equipment` | Estimated Index of Equipment Investment |
| investment | `ecos.investment.machinery_orders` | Value of Dom. Machinery Orders Received |
| investment | `ecos.investment.machinery_shipment` | Domestic Machinery Shipment Index |
| business_cycle | `ecos.business_cycle.coincident_index` | Cyclical Component of Coincident Index |
| business_cycle | `ecos.business_cycle.leading_index` | Cyclical Component of Leading Index |
| sentiment | `ecos.sentiment.business` | Composite Business Sentiment Index |
| sentiment | `ecos.sentiment.consumer` | Composite Consumer Sentiment Index |
| sentiment | `ecos.sentiment.economic` | Economic Sentiment Index |
| sentiment | `ecos.sentiment.manufacturing_bsi` | BSI(Manufact. Business Con., Tendency) |
| corporate | `ecos.corporate.manufacturing.debt_ratio` | Debt Ratio in Manufacturing |
| corporate | `ecos.corporate.manufacturing.profit_margin` | Ordinary Income to Sales in Manufacturing |
| corporate | `ecos.corporate.manufacturing.sales_growth` | Growth Rate of Sales in Manufacturing |
| household | `ecos.household.apc` | Average of Propensity to Consume |
| household | `ecos.household.gini` | Gini's Coefficient |
| household | `ecos.household.income` | Monthly Ave. Income of Households |
| household | `ecos.household.quintile_ratio` | Income of Highest Quintile/Income of Lowest Quintile(by quintile, ratio) |
| employment | `ecos.employment.active_population` | Economically Active Population |
| employment | `ecos.employment.employed_persons` | Employed Persons |
| employment | `ecos.employment.employment_rate` | Employment Rate |
| employment | `ecos.employment.hourly_wage` | Hourly Nominal Wage Index |
| employment | `ecos.employment.labor_productivity` | Index of Labor Productivity |
| employment | `ecos.employment.unemployment_rate` | Unemployment Rate |
| employment | `ecos.employment.unit_labor_cost` | Unit Labor Cost |
| population | `ecos.population.elderly_ratio` | Elderly Population Ratio |
| population | `ecos.population.fertility_rate` | Total Fertility Rate |
| population | `ecos.population.projected` | Population Projected |
| external | `ecos.external.claims` | External Claims |
| external | `ecos.external.current_account` | Current Account |
| external | `ecos.external.debt` | External Debt |
| external | `ecos.external.direct_investment_assets` | Direct Investment, Assets |
| external | `ecos.external.direct_investment_liabilities` | Direct Investment, Liabilities |
| external | `ecos.external.portfolio_investment_assets` | Portfolio Investment, Assets |
| external | `ecos.external.portfolio_investment_liabilities` | Portfolio Investment, Liabilities |
| external | `ecos.external.reserves.fx` | International Reserves: Foreign Exchange |
| external | `ecos.external.reserves.gold` | International Reserves: Gold |
| external | `ecos.external.reserves.imf` | International Reserves: IMF Reserve Position |
| external | `ecos.external.reserves.sdr` | International Reserves: SDRs |
| external | `ecos.external.reserves.total` | International Reserves |
| trade | `ecos.trade.exports.price` | Export Price Index |
| trade | `ecos.trade.exports.semiconductor.price` | Semiconductor Export Price Index |
| trade | `ecos.trade.exports.semiconductor.value` | Semiconductor Export Value Index |
| trade | `ecos.trade.exports.semiconductor.volume` | Semiconductor Export Volume Index |
| trade | `ecos.trade.exports.value` | Export value index |
| trade | `ecos.trade.exports.volume` | Export volume index |
| trade | `ecos.trade.imports.price` | Import Price Index |
| trade | `ecos.trade.imports.semiconductor.price` | Semiconductor Import Price Index |
| trade | `ecos.trade.imports.semiconductor.value` | Semiconductor Import Value Index |
| trade | `ecos.trade.imports.semiconductor.volume` | Semiconductor Import Volume Index |
| trade | `ecos.trade.imports.value` | Import value index |
| trade | `ecos.trade.imports.volume` | Import volume index |
| trade | `ecos.trade.terms_of_trade.income` | Income Terms of Trade Index |
| trade | `ecos.trade.terms_of_trade.net` | Net Barter Terms of Trade Index |
| price | `ecos.price.core_cpi` | CPI Excluding Agricultural Products & Oils |
| price | `ecos.price.cpi` | Consumer Price Index |
| price | `ecos.price.living_cpi` | CPI For Living Necessaries |
| price | `ecos.price.ppi` | Producer Price Index |
| price | `ecos.price.producer.dram` | DRAM Producer Price |
| price | `ecos.price.producer.logic` | System Semiconductor Producer Price |
| price | `ecos.price.producer.nand` | NAND Flash Producer Price |
| real_estate | `ecos.real_estate.house_jeonse_price` | Housing Jeonse Price Index |
| real_estate | `ecos.real_estate.house_sales_price` | Housing Sales Price Index |
| real_estate | `ecos.real_estate.land_price_change` | Land Price Change Rates |
| commodity | `ecos.commodity.dubai_oil` | Dubai Crude Oil |
| commodity | `ecos.commodity.gold` | Gold Price(Spot) |
| world | `ecos.world.rate.market.ca.long` | Canada Long-term Rate |
| world | `ecos.world.rate.market.ca.short` | Canada Short-term Rate |
| world | `ecos.world.rate.market.cn.long` | China Long-term Rate |
| world | `ecos.world.rate.market.cn.short` | China Short-term Rate |
| world | `ecos.world.rate.market.de.long` | Germany Long-term Rate |
| world | `ecos.world.rate.market.de.short` | Germany Short-term Rate |
| world | `ecos.world.rate.market.india.long` | India Long-term Rate |
| world | `ecos.world.rate.market.india.short` | India Short-term Rate |
| world | `ecos.world.rate.market.jp.long` | Japan Long-term Rate |
| world | `ecos.world.rate.market.jp.short` | Japan Short-term Rate |
| world | `ecos.world.rate.market.kr.long` | Korea Long-term Rate |
| world | `ecos.world.rate.market.kr.short` | Korea Short-term Rate |
| world | `ecos.world.rate.market.uk.long` | UK Long-term Rate |
| world | `ecos.world.rate.market.uk.short` | UK Short-term Rate |
| world | `ecos.world.rate.market.us.long` | US Long-term Rate |
| world | `ecos.world.rate.market.us.short` | US Short-term Rate |
| world | `ecos.world.rate.policy.ca` | Canada Policy Rate |
| world | `ecos.world.rate.policy.cn` | China Policy Rate |
| world | `ecos.world.rate.policy.euro` | Euro Area Policy Rate |
| world | `ecos.world.rate.policy.india` | India Policy Rate |
| world | `ecos.world.rate.policy.jp` | Japan Policy Rate |
| world | `ecos.world.rate.policy.kr` | Korea Policy Rate |
| world | `ecos.world.rate.policy.uk` | UK Policy Rate |
| world | `ecos.world.rate.policy.us` | US Policy Rate |

## 4. Everything else

Statistics outside this set are fetched by table code. pyecos exposes ECOS's six queries
as-is; each returns a `list` of `dict`.

| Call | What it does |
|---|---|
| `ecos.fetch_series(stat_code, ...)` | One statistic's values over time |
| `ecos.fetch_tables()` | The table list (children via `stat_code=`) |
| `ecos.fetch_items(stat_code)` | A table's detail items |
| `ecos.fetch_key_statistics()` | The top-100 headline indicators |
| `ecos.fetch_glossary(word)` | A statistical term's definition |
| `ecos.fetch_meta(dataset_name)` | Dataset metadata |

```python
rows = ecos.fetch_series(
    "722Y001",             # the market-rates table
    item_code1="0101000",  # its 'BOK base rate' item
    cycle="M",             # monthly
    start="202001", end="202412",
)
```

Empty periods come back with `data_value` set to `None`. Long series that ECOS pages 100
rows at a time are stitched together and returned in one call.

## 5. Command line

Installing pyecos puts the `ecos` command on PATH (the package is `pyecos`, the command
is `ecos`) — the same six queries from the terminal.

```bash
ecos series 722Y001 --item 0101000 --start 202001 --end 202412  # base-rate series
ecos tables                                                     # the table list
ecos items 722Y001                                              # a table's detail items
ecos key-statistics                                             # the top-100 indicators
ecos glossary DSR                                               # a term's definition
ecos meta 경제심리지수                                          # dataset metadata (name is Korean)
```

| Command | What it does |
|---|---|
| `series <stat_code>` | Values over time. `--item` (up to 4), `--cycle`, `--start` / `--end` |
| `tables` | The table list; `--stat-code` for a table's children |
| `items <stat_code>` | A table's detail items |
| `key-statistics` | The top-100 indicators |
| `glossary <word>` | A term's definition |
| `meta <dataset_name>` | Dataset metadata |

Every command takes `--lang en` and `--json`; `ecos --version` prints the version. See
`ecos <command> --help` for the rest.

## 6. AI coding agents

This repo doubles as a plugin marketplace for Claude Code and Codex — it ships `series`,
`catalog`, and `key-statistics` as skills that call the `ecos` command. Install the
package and set an API key first (above).

### 6.1. Claude Code

```
/plugin marketplace add seokhoonj/pyecos
/plugin install ecos@pyecos
```

Then just ask ("show the base-rate series", "find the table code for the CPI"), or call a
skill directly — `/ecos:series 722Y001 --item 0101000`, `/ecos:key-statistics`.

### 6.2. Codex

```
codex plugin marketplace add seokhoonj/pyecos
codex plugin add ecos@pyecos
```

The `series`, `catalog`, and `key-statistics` skills react to a request for an economic
statistic, and you can always run `ecos <command>` directly.

Prefer not to install the plugin? Symlink a skill into your skills directory and call it
without the `ecos:` prefix, as `/series`:

```sh
ln -s "$PWD/plugins/ecos/skills/series" ~/.claude/skills/series   # Claude Code -> /series
ln -s "$PWD/plugins/ecos/skills/series" ~/.codex/skills/series    # Codex -> $ecos:series
```

Claude Code picks it up immediately; Codex needs a restart to load it.

## 7. Cycles

The observation cycle taken by `fetch_series` and the `series` command. The library uses
the code (`"M"`), the command uses the word (`monthly`). Each row's `time` is formatted to
match.

| Cycle | Code | Command word | `time` example |
|---|---|---|---|
| Annual | `A` | `annual` | `2024` |
| Semiannual | `S` | `semiannual` | `2024S1` |
| Quarterly | `Q` | `quarterly` | `2024Q1` |
| Monthly | `M` | `monthly` | `202401` |
| Semimonthly | `SM` | `semimonthly` | `202401S1` |
| Daily | `D` | `daily` | `20240115` |

## 8. Errors

| Exception | When |
|---|---|
| `ECOSConfigError` | No API key was found |
| `ECOSAuthError` | ECOS rejected the key |
| `ECOSRateLimitError` | Called too often and throttled (ERROR-602) |
| `ECOSResponseError` | ECOS returned an error code (carries `.code` / `.message`) |
| `ECOSNetworkError` | The request never completed (after retrying transient errors) |

All derive from `ECOSError`. A query that simply has no data is not an error — it returns
an empty list. For heavy use, `ECOS(delay_seconds=0.6)` paces requests under the limit
(about 300 per 3 minutes).

## 9. Offline indicator search

To find the code of a table outside this set — with no API key and no network, searched
straight from a table snapshot bundled with the package.

```python
from pyecos import catalog

catalog.search("소비자물가")
# -> [{"stat_code": "901Y009", "stat_name": "4.2.1. 소비자물가지수", "cycle": "M", "searchable": True}, ...]

catalog.table("901Y009")   # that one row (None if absent)
catalog.tables()           # the whole snapshot (834 tables)
```

Table names are Korean, so search by a Korean keyword or a code. For the live list or a
table's detail items, use `ecos.fetch_tables()` / `ecos.fetch_items()`.

## License

[MIT](LICENSE)
