# pyecos

[![check](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml/badge.svg)](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml)
[![PyPI](https://img.shields.io/pypi/v/pyecos)](https://pypi.org/project/pyecos/)
[![Python](https://img.shields.io/pypi/pyversions/pyecos)](https://pypi.org/project/pyecos/)
[![License](https://img.shields.io/pypi/l/pyecos)](https://github.com/seokhoonj/pyecos/blob/main/LICENSE)

**한국어** | [English](README.en.md)

한국은행 경제통계시스템 [ECOS Open API](https://ecos.bok.or.kr/api/#/)의 파이썬
클라이언트입니다. `ECOS` 객체 하나에 ECOS 6개 서비스와 1:1로 대응하는 메서드 여섯 개,
그리고 그대로 DataFrame이 되는 행(row)을 제공합니다.

## 설치

```bash
pip install pyecos
```

[ECOS Open API 사이트](https://ecos.bok.or.kr/api/#/)에서 무료 API 키를 발급받으세요.
`ECOS()`는 다음 순서로 키를 찾습니다.

1. `ECOS(...)`에 넘긴 `api_key` 인자,
2. `ECOS_API_KEY` 환경변수,
3. `~/.config/pyecos/credentials.json`의 `"ECOS_API_KEY"` (`$XDG_CONFIG_HOME` 존중).

```bash
export ECOS_API_KEY="발급받은-키"
# 또는 파일로 한 번만 저장:
mkdir -p ~/.config/pyecos
printf '{"ECOS_API_KEY": "발급받은-키"}' > ~/.config/pyecos/credentials.json
chmod 600 ~/.config/pyecos/credentials.json
```

## 사용법

```python
from pyecos import ECOS, Cycle

with ECOS() as ecos:
    # 통계 시계열 조회 (StatisticSearch).
    rows = ecos.fetch_series(
        "722Y001",              # 시장금리
        item_code1="0101000",   # 한국은행 기준금리
        cycle=Cycle.MONTHLY,
        start="202001",
        end="202412",
    )

    # 통계표 카탈로그 탐색.
    tables = ecos.fetch_tables()             # 최상위 통계표
    children = ecos.fetch_tables(stat_code="722Y001")
    items = ecos.fetch_items("722Y001")      # 통계표의 세부 항목

    # 100대 지표, 용어사전, 메타DB.
    key = ecos.fetch_key_statistics()        # 100대 통계지표
    word = ecos.fetch_glossary("DSR")
    meta = ecos.fetch_meta("경제심리지수")
```

모든 메서드는 평범한 `dict` 행의 `list`를 반환하므로, pandas는 한 줄이면 됩니다
(그리고 pandas는 필수 의존성이 아닙니다).

```python
import pandas as pd

frame = pd.DataFrame(rows)
```

`fetch_series`는 각 관측치의 `data_value`를 `float`로 반환하고(한국은행이 값을 비워 보낸
경우 `None`), 요청당 100건 제한을 알아서 넘겨 페이지네이션하므로 여러 해치 일별 시계열도
한 번의 호출로 돌아옵니다.

## 오프라인 카탈로그

어떤 통계표(`stat_code`)가 필요한지 찾을 때, 네트워크 없이 패키지에 동봉된 스냅샷에서
바로 검색할 수 있습니다 (API 키도 필요 없음).

```python
from pyecos import catalog

catalog.search("소비자물가")   # 이름·코드로 검색 -> [{stat_code, stat_name, cycle, searchable}, ...]
catalog.table("901Y009")      # 특정 표 한 줄, 없으면 None
catalog.tables()              # 전체 스냅샷 (834개 표)
```

스냅샷은 특정 시점 사본입니다. 실시간 목록이나 표의 세부 항목은
`ecos.fetch_tables()` / `ecos.fetch_items()`를 쓰세요.

## 큐레이션 지표

통계표 코드를 외우는 대신, **이름으로** 한국은행 주요 지표에 접근할 수 있습니다.
`ecos.<그룹>.<지표>.fetch()` 형태이며, 에디터 자동완성으로 탐색됩니다.

```python
with ECOS() as ecos:
    ecos.rate.base.fetch(start="202001", end="202412")   # 기준금리
    ecos.fx.usd.latest()                                 # 원/달러 최근값
    ecos.trade.exports.semiconductor.value.fetch()       # 반도체 수출금액지수
    ecos.stock.kospi.per.fetch()                         # 코스피 PER
```

각 지표는 `.fetch(start, end)`와 `.latest()`를 제공합니다. 한국은행 100대 지표에 더해,
자주 쓰는 지표(반도체 수출입 금액·물량·물가, 외환보유액 성분, 코스피·코스닥 시장지표)를
함께 담았습니다.

<details>
<summary>전체 지표 목록 (125개) 펼치기</summary>

| 그룹 | 경로 | 지표 |
|---|---|---|
| rate | `ecos.rate.base` | 한국은행 기준금리 |
| rate | `ecos.rate.call` | 콜금리(익일물) |
| rate | `ecos.rate.koribor_3m` | KORIBOR(3개월) |
| rate | `ecos.rate.cd_91d` | CD수익률(91일) |
| rate | `ecos.rate.msb_364d` | 통안증권수익률(364일) |
| rate | `ecos.rate.treasury_3y` | 국고채수익률(3년) |
| rate | `ecos.rate.treasury_5y` | 국고채수익률(5년) |
| rate | `ecos.rate.corporate_bond_3y` | 회사채수익률(3년,AA-) |
| rate | `ecos.rate.deposit` | 예금은행 수신금리 |
| rate | `ecos.rate.loan` | 예금은행 대출금리 |
| credit | `ecos.credit.total_deposits` | 예금은행총예금(말잔) |
| credit | `ecos.credit.total_loans` | 예금은행대출금(말잔) |
| credit | `ecos.credit.household_credit` | 가계신용 |
| credit | `ecos.credit.household_delinquency_rate` | 가계대출연체율 |
| money | `ecos.money.m1` | M1(협의통화, 평잔) |
| money | `ecos.money.m2` | M2(광의통화, 평잔) |
| money | `ecos.money.lf` | Lf(평잔) |
| money | `ecos.money.l` | L(말잔) |
| fx | `ecos.fx.usd` | 원/달러 환율(종가) |
| fx | `ecos.fx.jpy` | 원/엔(100엔) 환율(매매기준율) |
| fx | `ecos.fx.eur` | 원/유로 환율(매매기준율) |
| fx | `ecos.fx.cny` | 원/위안 환율(종가) |
| stock | `ecos.stock.kospi.index` | 코스피지수 |
| stock | `ecos.stock.kosdaq.index` | 코스닥지수 |
| stock | `ecos.stock.kosdaq.trading_value` | 주식거래대금(KOSDAQ) |
| stock | `ecos.stock.kospi.trading_value` | 주식거래대금(KOSPI) |
| stock | `ecos.stock.kospi.market_cap` | 코스피 시가총액 |
| stock | `ecos.stock.kospi.volume` | 코스피 거래량 |
| stock | `ecos.stock.kospi.turnover` | 코스피 회전율 |
| stock | `ecos.stock.kospi.dividend_yield` | 코스피 배당수익률 |
| stock | `ecos.stock.kospi.per` | 코스피 PER |
| stock | `ecos.stock.kosdaq.market_cap` | 코스닥 시가총액 |
| stock | `ecos.stock.kosdaq.volume` | 코스닥 거래량 |
| stock | `ecos.stock.kosdaq.turnover` | 코스닥 회전율 |
| stock | `ecos.stock.investor_deposits` | 투자자예탁금 |
| bond | `ecos.bond.trading_value` | 채권거래대금 |
| bond | `ecos.bond.treasury_issuance` | 국고채발행액 |
| growth | `ecos.growth.gdp_growth` | 경제성장률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.private_consumption_growth` | 민간소비증감률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.facilities_investment_growth` | 설비투자증감률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.construction_investment_growth` | 건설투자증감률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.exports_growth` | 재화의 수출 증감률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.gdp_nominal` | GDP(명목, 계절조정) |
| growth | `ecos.growth.gni_per_capita` | 1인당GNI |
| growth | `ecos.growth.gross_saving_ratio` | 총저축률 |
| growth | `ecos.growth.gross_investment_ratio` | 국내총투자율 |
| growth | `ecos.growth.trade_to_gni_ratio` | 수출입의 대 GNI 비율 |
| production | `ecos.production.all_industry` | 전산업생산지수 |
| production | `ecos.production.manufacturing.output` | 제조업생산지수 |
| production | `ecos.production.manufacturing.shipment` | 제조업출하지수 |
| production | `ecos.production.manufacturing.inventory` | 제조업재고지수 |
| production | `ecos.production.manufacturing.utilization` | 제조업가동률지수 |
| production | `ecos.production.services` | 서비스업생산지수 |
| production | `ecos.production.retail_wholesale` | 도소매업생산지수 |
| consumption | `ecos.consumption.retail_sales` | 소매판매액지수 |
| consumption | `ecos.consumption.credit_card_spending` | 개인신용카드사용액 |
| consumption | `ecos.consumption.motor_vehicle_sales` | 자동차판매액지수 |
| investment | `ecos.investment.equipment` | 설비투자지수 |
| investment | `ecos.investment.machinery_shipment` | 설비용 기계류내수출하지수 |
| investment | `ecos.investment.machinery_orders` | 국내기계수주액 |
| investment | `ecos.investment.construction_completed` | 건설기성액 |
| investment | `ecos.investment.building_permits` | 건축허가면적 |
| investment | `ecos.investment.construction_orders` | 건설수주액 |
| investment | `ecos.investment.construction_started` | 건축착공면적 |
| business_cycle | `ecos.business_cycle.coincident_index` | 동행지수순환변동치 |
| business_cycle | `ecos.business_cycle.leading_index` | 선행지수순환변동치 |
| sentiment | `ecos.sentiment.business` | 전산업 기업심리지수실적 |
| sentiment | `ecos.sentiment.consumer` | 소비자심리지수 |
| sentiment | `ecos.sentiment.economic` | 경제심리지수 |
| sentiment | `ecos.sentiment.manufacturing_bsi` | 제조업업황실적BSI |
| corporate | `ecos.corporate.manufacturing.sales_growth` | 제조업매출액증감률 |
| corporate | `ecos.corporate.manufacturing.profit_margin` | 제조업매출액세전순이익률 |
| corporate | `ecos.corporate.manufacturing.debt_ratio` | 제조업부채비율 |
| household | `ecos.household.income` | 가구당월평균소득 |
| household | `ecos.household.propensity_to_consume` | 평균소비성향 |
| household | `ecos.household.gini` | 지니계수 |
| household | `ecos.household.quintile_ratio` | 5분위배율 |
| employment | `ecos.employment.unemployment_rate` | 실업률 |
| employment | `ecos.employment.employment_rate` | 고용률 |
| employment | `ecos.employment.active_population` | 경제활동인구 |
| employment | `ecos.employment.employed_persons` | 취업자수 |
| employment | `ecos.employment.hourly_wage` | 시간당명목임금지수 |
| employment | `ecos.employment.labor_productivity` | 노동생산성지수 |
| employment | `ecos.employment.unit_labor_cost` | 단위노동비용지수 |
| population | `ecos.population.projected` | 추계인구 |
| population | `ecos.population.elderly_ratio` | 고령인구비율 |
| population | `ecos.population.fertility_rate` | 합계출산율 |
| external | `ecos.external.current_account` | 경상수지 |
| external | `ecos.external.direct_investment_assets` | 직접투자(자산) |
| external | `ecos.external.direct_investment_liabilities` | 직접투자(부채) |
| external | `ecos.external.portfolio_investment_assets` | 증권투자(자산) |
| external | `ecos.external.portfolio_investment_liabilities` | 증권투자(부채) |
| external | `ecos.external.reserves.total` | 외환보유액 |
| external | `ecos.external.reserves.fx` | 외환보유액(외환) |
| external | `ecos.external.reserves.gold` | 외환보유액(금) |
| external | `ecos.external.reserves.sdr` | 외환보유액(SDR) |
| external | `ecos.external.reserves.imf` | 외환보유액(IMF포지션) |
| external | `ecos.external.debt` | 대외채무 |
| external | `ecos.external.claims` | 대외채권 |
| trade | `ecos.trade.exports.value` | 수출금액지수 |
| trade | `ecos.trade.imports.value` | 수입금액지수 |
| trade | `ecos.trade.exports.volume` | 수출물량지수 |
| trade | `ecos.trade.imports.volume` | 수입물량지수 |
| trade | `ecos.trade.terms_of_trade.net` | 순상품교역조건지수 |
| trade | `ecos.trade.terms_of_trade.income` | 소득교역조건지수 |
| trade | `ecos.trade.exports.price` | 수출물가지수 |
| trade | `ecos.trade.imports.price` | 수입물가지수 |
| trade | `ecos.trade.exports.semiconductor.value` | 반도체 수출금액지수 |
| trade | `ecos.trade.exports.semiconductor.volume` | 반도체 수출물량지수 |
| trade | `ecos.trade.exports.semiconductor.price` | 반도체 수출물가지수 |
| trade | `ecos.trade.imports.semiconductor.value` | 반도체 수입금액지수 |
| trade | `ecos.trade.imports.semiconductor.volume` | 반도체 수입물량지수 |
| trade | `ecos.trade.imports.semiconductor.price` | 반도체 수입물가지수 |
| price | `ecos.price.cpi` | 소비자물가지수 |
| price | `ecos.price.core_cpi` | 농산물 및 석유류제외 소비자물가지수 |
| price | `ecos.price.living_cpi` | 생활물가지수 |
| price | `ecos.price.ppi` | 생산자물가지수 |
| price | `ecos.price.producer.dram` | DRAM 생산자물가 |
| price | `ecos.price.producer.nand` | NAND플래시 생산자물가 |
| price | `ecos.price.producer.system_semiconductor` | 시스템반도체 생산자물가 |
| real_estate | `ecos.real_estate.house_sales_price` | 주택매매가격지수 |
| real_estate | `ecos.real_estate.house_jeonse_price` | 주택전세가격지수 |
| real_estate | `ecos.real_estate.land_price_change` | 지가변동률(전기대비) |
| commodity | `ecos.commodity.dubai_oil` | Dubai유(현물) |
| commodity | `ecos.commodity.gold` | 금 |

</details>

<details>
<summary>접근자 트리 (구조) 펼치기</summary>

`name/` 은 네임스페이스, 나머지 leaf는 지표입니다. leaf에서 `.fetch(start, end)` 또는 `.latest()`를 호출합니다 (예: `ecos.rate.base.fetch(...)`).

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

</details>

## 커맨드라인

패키지를 설치하면 `pyecos` 명령이 PATH에 함께 올라가며, 서비스마다 서브커맨드가 하나씩
있습니다.

```bash
export ECOS_API_KEY="발급받은-키"

pyecos series 722Y001 --item 0101000 --cycle monthly --start 202001 --end 202412
pyecos tables                        # 최상위 통계표
pyecos items 722Y001                 # 통계표의 세부 항목
pyecos key-stats                     # 100대 통계지표
pyecos glossary DSR
pyecos meta 경제심리지수
```

플래그 (최종 근거는 `pyecos <command> --help`):

- `series <stat_code>` — `--item CODE`(최대 4회 반복), `--cycle annual|semiannual|quarterly|monthly|semimonthly|daily`(기본 `monthly`), `--start`, `--end`
- `tables` — `--stat-code CODE`로 하위 통계표(생략 시 최상위)
- `items <stat_code>` · `key-stats` · `glossary <word>` · `meta <dataset_name>`
- 모든 서브커맨드: `--lang kr|en`, `--json` · 최상위: `--version`

## 주기(cycle)

`fetch_series`는 `Cycle`(또는 그 코드 문자열)을 받습니다. 각 행의 `time` 필드는 주기에 맞춰
형식이 정해집니다.

| 주기 | 코드 | `time` 예시 |
|---|---|---|
| 연 | `A` | `2024` |
| 반기 | `S` | `2024S1` |
| 분기 | `Q` | `2024Q1` |
| 월 | `M` | `202401` |
| 반월 | `SM` | `202401S1` |
| 일 | `D` | `20240115` |

## 예외

모든 운영성 예외는 `ECOSError`에서 파생됩니다.

| 예외 | 발생 시점 |
|---|---|
| `ECOSConfigError` | API 키가 없을 때 |
| `ECOSAuthError` | ECOS가 키를 거부했을 때 |
| `ECOSRateLimitError` | ECOS가 호출을 제한할 때 (ERROR-602 · `ECOSResponseError`의 하위) |
| `ECOSResponseError` | ECOS가 에러 코드를 반환했을 때 (`.code` / `.message` 보유) |
| `ECOSNetworkError` | 요청이 끝내 완료되지 못했을 때 (일시적 타임아웃·5xx는 백오프 재시도 후) |

조회 결과가 단순히 없는 경우는 에러가 아니라 빈 리스트로 돌아옵니다. 잘못된 `cycle`·`lang`
인자는 표준 `ValueError`를 냅니다.

대량으로 조회할 때는 `ECOS(delay_seconds=0.6)`처럼 요청 간격을 두면 ECOS 레이트리밋(약 3분에
300회)을 넘지 않습니다.

## 라이선스

[MIT](LICENSE)
