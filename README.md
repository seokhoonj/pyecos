# pyecos

[![check](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml/badge.svg)](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml)
[![PyPI](https://img.shields.io/pypi/v/pyecos)](https://pypi.org/project/pyecos/)
[![Python](https://img.shields.io/pypi/pyversions/pyecos)](https://pypi.org/project/pyecos/)
[![License](https://img.shields.io/pypi/l/pyecos)](https://github.com/seokhoonj/pyecos/blob/main/LICENSE)

**한국어** | [English](README.en.md)

한국은행 경제통계시스템 **ECOS**의 경제·금융 통계를 읽어옵니다.

기준금리와 시장금리, 환율, 통화량과 예금·대출, 코스피·코스닥, 소비자·생산자 물가,
GDP와 성장률, 생산·소비·투자, 기업경기와 소비심리, 고용과 임금, 인구와 가계,
국제수지·외환보유액·대외채권채무, 수출입 물가·물량, 주택·토지 가격까지 다룹니다.

자주 쓰는 지표 125개는 `ecos.rate.base`처럼 **이름으로** 바로 꺼내고, 그 밖의 통계는
통계표 코드로 조회합니다.

## 1. 설치

```bash
pip install pyecos
```

무료 API 키는 <https://ecos.bok.or.kr/api/> 에서 발급받으세요. 키를 넣는 방법은 두 가지입니다.

**방법 1 — 코드에서 직접 넣기** (바로 한 번 써볼 때)

```python
from pyecos import ECOS

ecos = ECOS(api_key="발급받은-키")
```

**방법 2 — 파일에 저장해서 계속 쓰기** (권장 — 한 번 저장하면 매번 안 넣어도 됩니다)

`~/.config/pyecos/credentials.json` 파일을 만들고 아래를 넣으세요.

```json
{ "ECOS_API_KEY": "발급받은-키" }
```

그러면 이후로는 인자 없이 `ECOS()`만 써도 이 키를 자동으로 찾습니다.

> 환경변수를 선호하면, macOS·Linux는 터미널에서 `export ECOS_API_KEY="발급받은-키"`,
> Windows는 PowerShell에서 `setx ECOS_API_KEY "발급받은-키"`.

## 2. 빠른 시작

```python
from pyecos import ECOS

ecos = ECOS()                                              # 저장해둔 키를 자동으로 찾습니다
rows = ecos.rate.base.fetch(start="202001", end="202412")  # 기준금리, 2020~2024년 월별
```

결과는 `dict`의 목록(`list`)이라, 표(DataFrame)로 한 줄에 바뀝니다. (pandas는 필수가 아닙니다.)

```python
import pandas as pd

pd.DataFrame(rows)   # 또는 polars.DataFrame(rows)
```

## 3. 이름으로 가져오는 지표 125개

통계표 코드를 외우지 않고, 자주 쓰는 지표 125개를 `ecos.그룹.지표` 형태로 바로 꺼냅니다.
편집기에서 `ecos.` 뒤를 점(`.`)으로 타고 들어가면 자동완성으로 찾을 수 있고, 어느 지표든
두 가지를 제공합니다.

- `.fetch(start, end)` — 기간을 정해 시계열 전체를 가져옵니다
- `.latest()` — 가장 최근 값 하나만 가져옵니다

```python
ecos.rate.base.fetch(start="202001", end="202412")  # 기준금리
ecos.fx.usd.latest()                                # 원/달러 최근값
ecos.trade.exports.semiconductor.value.fetch()      # 반도체 수출금액지수
ecos.stock.kospi.per.fetch()                        # 코스피 PER
```

아래 트리에서 **끝에 `/`가 붙은 줄은 묶음**(예: `rate/`, `stock/`)일 뿐이고, **`/`가 없는
줄이 실제 지표**입니다. 지표 줄을 점으로 이어 부르면 됩니다 — 예: `rate/` 안의 `base` →
`ecos.rate.base`.

```
ecos
├── rate/
│   ├── base                              # 한국은행 기준금리
│   ├── call                              # 콜금리(익일물)
│   ├── koribor_3m                        # KORIBOR(3개월)
│   ├── cd_91d                            # CD수익률(91일)
│   ├── msb_364d                          # 통안증권수익률(364일)
│   ├── treasury_3y                       # 국고채수익률(3년)
│   ├── treasury_5y                       # 국고채수익률(5년)
│   ├── corporate_bond_3y                 # 회사채수익률(3년,AA-)
│   ├── deposit                           # 예금은행 수신금리
│   └── loan                              # 예금은행 대출금리
├── credit/
│   ├── total_deposits                    # 예금은행총예금(말잔)
│   ├── total_loans                       # 예금은행대출금(말잔)
│   ├── household_credit                  # 가계신용
│   └── household_delinquency_rate        # 가계대출연체율
├── money/
│   ├── m1                                # M1(협의통화, 평잔)
│   ├── m2                                # M2(광의통화, 평잔)
│   ├── lf                                # Lf(평잔)
│   └── l                                 # L(말잔)
├── fx/
│   ├── usd                               # 원/달러 환율(종가)
│   ├── jpy                               # 원/엔(100엔) 환율(매매기준율)
│   ├── eur                               # 원/유로 환율(매매기준율)
│   └── cny                               # 원/위안 환율(종가)
├── stock/
│   ├── kospi/
│   │   ├── index                         # 코스피지수
│   │   ├── trading_value                 # 주식거래대금(KOSPI)
│   │   ├── market_cap                    # 코스피 시가총액
│   │   ├── volume                        # 코스피 거래량
│   │   ├── turnover                      # 코스피 회전율
│   │   ├── dividend_yield                # 코스피 배당수익률
│   │   └── per                           # 코스피 PER
│   ├── kosdaq/
│   │   ├── index                         # 코스닥지수
│   │   ├── trading_value                 # 주식거래대금(KOSDAQ)
│   │   ├── market_cap                    # 코스닥 시가총액
│   │   ├── volume                        # 코스닥 거래량
│   │   └── turnover                      # 코스닥 회전율
│   └── investor_deposits                 # 투자자예탁금
├── bond/
│   ├── trading_value                     # 채권거래대금
│   └── treasury_issuance                 # 국고채발행액
├── growth/
│   ├── gdp_growth                        # 경제성장률(실질, 계절조정 전기대비)
│   ├── private_consumption_growth        # 민간소비증감률(실질, 계절조정 전기대비)
│   ├── facilities_investment_growth      # 설비투자증감률(실질, 계절조정 전기대비)
│   ├── construction_investment_growth    # 건설투자증감률(실질, 계절조정 전기대비)
│   ├── exports_growth                    # 재화의 수출 증감률(실질, 계절조정 전기대비)
│   ├── gdp_nominal                       # GDP(명목, 계절조정)
│   ├── gni_per_capita                    # 1인당GNI
│   ├── gross_saving_ratio                # 총저축률
│   ├── gross_investment_ratio            # 국내총투자율
│   └── trade_to_gni_ratio                # 수출입의 대 GNI 비율
├── production/
│   ├── all_industry                      # 전산업생산지수
│   ├── manufacturing/
│   │   ├── output                        # 제조업생산지수
│   │   ├── shipment                      # 제조업출하지수
│   │   ├── inventory                     # 제조업재고지수
│   │   └── utilization                   # 제조업가동률지수
│   ├── services                          # 서비스업생산지수
│   └── retail_wholesale                  # 도소매업생산지수
├── consumption/
│   ├── retail_sales                      # 소매판매액지수
│   ├── credit_card_spending              # 개인신용카드사용액
│   └── motor_vehicle_sales               # 자동차판매액지수
├── investment/
│   ├── equipment                         # 설비투자지수
│   ├── machinery_shipment                # 설비용 기계류내수출하지수
│   ├── machinery_orders                  # 국내기계수주액
│   ├── construction_completed            # 건설기성액
│   ├── building_permits                  # 건축허가면적
│   ├── construction_orders               # 건설수주액
│   └── construction_started              # 건축착공면적
├── business_cycle/
│   ├── coincident_index                  # 동행지수순환변동치
│   └── leading_index                     # 선행지수순환변동치
├── sentiment/
│   ├── business                          # 전산업 기업심리지수실적
│   ├── consumer                          # 소비자심리지수
│   ├── economic                          # 경제심리지수
│   └── manufacturing_bsi                 # 제조업업황실적BSI
├── corporate/
│   └── manufacturing/
│       ├── sales_growth                  # 제조업매출액증감률
│       ├── profit_margin                 # 제조업매출액세전순이익률
│       └── debt_ratio                    # 제조업부채비율
├── household/
│   ├── income                            # 가구당월평균소득
│   ├── average_propensity_to_consume     # 평균소비성향
│   ├── gini                              # 지니계수
│   └── quintile_ratio                    # 5분위배율
├── employment/
│   ├── unemployment_rate                 # 실업률
│   ├── employment_rate                   # 고용률
│   ├── active_population                 # 경제활동인구
│   ├── employed_persons                  # 취업자수
│   ├── hourly_wage                       # 시간당명목임금지수
│   ├── labor_productivity                # 노동생산성지수
│   └── unit_labor_cost                   # 단위노동비용지수
├── population/
│   ├── projected                         # 추계인구
│   ├── elderly_ratio                     # 고령인구비율
│   └── fertility_rate                    # 합계출산율
├── external/
│   ├── current_account                   # 경상수지
│   ├── direct_investment_assets          # 직접투자(자산)
│   ├── direct_investment_liabilities     # 직접투자(부채)
│   ├── portfolio_investment_assets       # 증권투자(자산)
│   ├── portfolio_investment_liabilities  # 증권투자(부채)
│   ├── reserves/
│   │   ├── total                         # 외환보유액
│   │   ├── fx                            # 외환보유액(외환)
│   │   ├── gold                          # 외환보유액(금)
│   │   ├── sdr                           # 외환보유액(SDR)
│   │   └── imf                           # 외환보유액(IMF포지션)
│   ├── debt                              # 대외채무
│   └── claims                            # 대외채권
├── trade/
│   ├── exports/
│   │   ├── value                         # 수출금액지수
│   │   ├── volume                        # 수출물량지수
│   │   ├── price                         # 수출물가지수
│   │   └── semiconductor/
│   │       ├── value                     # 반도체 수출금액지수
│   │       ├── volume                    # 반도체 수출물량지수
│   │       └── price                     # 반도체 수출물가지수
│   ├── imports/
│   │   ├── value                         # 수입금액지수
│   │   ├── volume                        # 수입물량지수
│   │   ├── price                         # 수입물가지수
│   │   └── semiconductor/
│   │       ├── value                     # 반도체 수입금액지수
│   │       ├── volume                    # 반도체 수입물량지수
│   │       └── price                     # 반도체 수입물가지수
│   └── terms_of_trade/
│       ├── net                           # 순상품교역조건지수
│       └── income                        # 소득교역조건지수
├── price/
│   ├── cpi                               # 소비자물가지수
│   ├── core_cpi                          # 농산물 및 석유류제외 소비자물가지수
│   ├── living_cpi                        # 생활물가지수
│   ├── ppi                               # 생산자물가지수
│   └── producer/
│       ├── dram                          # DRAM 생산자물가
│       ├── nand                          # NAND플래시 생산자물가
│       └── system                        # 시스템반도체 생산자물가
├── real_estate/
│   ├── house_sales_price                 # 주택매매가격지수
│   ├── house_jeonse_price                # 주택전세가격지수
│   └── land_price_change                 # 지가변동률(전기대비)
└── commodity/
    ├── dubai_oil                         # Dubai유(현물)
    └── gold                              # 금
```

전체 목록:

| 그룹 | 불러오기 | 지표명 |
|---|---|---|
| rate | `ecos.rate.base` | 한국은행 기준금리 |
| rate | `ecos.rate.call` | 콜금리(익일물) |
| rate | `ecos.rate.cd_91d` | CD수익률(91일) |
| rate | `ecos.rate.corporate_bond_3y` | 회사채수익률(3년,AA-) |
| rate | `ecos.rate.deposit` | 예금은행 수신금리 |
| rate | `ecos.rate.koribor_3m` | KORIBOR(3개월) |
| rate | `ecos.rate.loan` | 예금은행 대출금리 |
| rate | `ecos.rate.msb_364d` | 통안증권수익률(364일) |
| rate | `ecos.rate.treasury_3y` | 국고채수익률(3년) |
| rate | `ecos.rate.treasury_5y` | 국고채수익률(5년) |
| credit | `ecos.credit.household_credit` | 가계신용 |
| credit | `ecos.credit.household_delinquency_rate` | 가계대출연체율 |
| credit | `ecos.credit.total_deposits` | 예금은행총예금(말잔) |
| credit | `ecos.credit.total_loans` | 예금은행대출금(말잔) |
| money | `ecos.money.l` | L(말잔) |
| money | `ecos.money.lf` | Lf(평잔) |
| money | `ecos.money.m1` | M1(협의통화, 평잔) |
| money | `ecos.money.m2` | M2(광의통화, 평잔) |
| fx | `ecos.fx.cny` | 원/위안 환율(종가) |
| fx | `ecos.fx.eur` | 원/유로 환율(매매기준율) |
| fx | `ecos.fx.jpy` | 원/엔(100엔) 환율(매매기준율) |
| fx | `ecos.fx.usd` | 원/달러 환율(종가) |
| stock | `ecos.stock.investor_deposits` | 투자자예탁금 |
| stock | `ecos.stock.kosdaq.index` | 코스닥지수 |
| stock | `ecos.stock.kosdaq.market_cap` | 코스닥 시가총액 |
| stock | `ecos.stock.kosdaq.trading_value` | 주식거래대금(KOSDAQ) |
| stock | `ecos.stock.kosdaq.turnover` | 코스닥 회전율 |
| stock | `ecos.stock.kosdaq.volume` | 코스닥 거래량 |
| stock | `ecos.stock.kospi.dividend_yield` | 코스피 배당수익률 |
| stock | `ecos.stock.kospi.index` | 코스피지수 |
| stock | `ecos.stock.kospi.market_cap` | 코스피 시가총액 |
| stock | `ecos.stock.kospi.per` | 코스피 PER |
| stock | `ecos.stock.kospi.trading_value` | 주식거래대금(KOSPI) |
| stock | `ecos.stock.kospi.turnover` | 코스피 회전율 |
| stock | `ecos.stock.kospi.volume` | 코스피 거래량 |
| bond | `ecos.bond.trading_value` | 채권거래대금 |
| bond | `ecos.bond.treasury_issuance` | 국고채발행액 |
| growth | `ecos.growth.construction_investment_growth` | 건설투자증감률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.exports_growth` | 재화의 수출 증감률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.facilities_investment_growth` | 설비투자증감률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.gdp_growth` | 경제성장률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.gdp_nominal` | GDP(명목, 계절조정) |
| growth | `ecos.growth.gni_per_capita` | 1인당GNI |
| growth | `ecos.growth.gross_investment_ratio` | 국내총투자율 |
| growth | `ecos.growth.gross_saving_ratio` | 총저축률 |
| growth | `ecos.growth.private_consumption_growth` | 민간소비증감률(실질, 계절조정 전기대비) |
| growth | `ecos.growth.trade_to_gni_ratio` | 수출입의 대 GNI 비율 |
| production | `ecos.production.all_industry` | 전산업생산지수 |
| production | `ecos.production.manufacturing.inventory` | 제조업재고지수 |
| production | `ecos.production.manufacturing.output` | 제조업생산지수 |
| production | `ecos.production.manufacturing.shipment` | 제조업출하지수 |
| production | `ecos.production.manufacturing.utilization` | 제조업가동률지수 |
| production | `ecos.production.retail_wholesale` | 도소매업생산지수 |
| production | `ecos.production.services` | 서비스업생산지수 |
| consumption | `ecos.consumption.credit_card_spending` | 개인신용카드사용액 |
| consumption | `ecos.consumption.motor_vehicle_sales` | 자동차판매액지수 |
| consumption | `ecos.consumption.retail_sales` | 소매판매액지수 |
| investment | `ecos.investment.building_permits` | 건축허가면적 |
| investment | `ecos.investment.construction_completed` | 건설기성액 |
| investment | `ecos.investment.construction_orders` | 건설수주액 |
| investment | `ecos.investment.construction_started` | 건축착공면적 |
| investment | `ecos.investment.equipment` | 설비투자지수 |
| investment | `ecos.investment.machinery_orders` | 국내기계수주액 |
| investment | `ecos.investment.machinery_shipment` | 설비용 기계류내수출하지수 |
| business_cycle | `ecos.business_cycle.coincident_index` | 동행지수순환변동치 |
| business_cycle | `ecos.business_cycle.leading_index` | 선행지수순환변동치 |
| sentiment | `ecos.sentiment.business` | 전산업 기업심리지수실적 |
| sentiment | `ecos.sentiment.consumer` | 소비자심리지수 |
| sentiment | `ecos.sentiment.economic` | 경제심리지수 |
| sentiment | `ecos.sentiment.manufacturing_bsi` | 제조업업황실적BSI |
| corporate | `ecos.corporate.manufacturing.debt_ratio` | 제조업부채비율 |
| corporate | `ecos.corporate.manufacturing.profit_margin` | 제조업매출액세전순이익률 |
| corporate | `ecos.corporate.manufacturing.sales_growth` | 제조업매출액증감률 |
| household | `ecos.household.average_propensity_to_consume` | 평균소비성향 |
| household | `ecos.household.gini` | 지니계수 |
| household | `ecos.household.income` | 가구당월평균소득 |
| household | `ecos.household.quintile_ratio` | 5분위배율 |
| employment | `ecos.employment.active_population` | 경제활동인구 |
| employment | `ecos.employment.employed_persons` | 취업자수 |
| employment | `ecos.employment.employment_rate` | 고용률 |
| employment | `ecos.employment.hourly_wage` | 시간당명목임금지수 |
| employment | `ecos.employment.labor_productivity` | 노동생산성지수 |
| employment | `ecos.employment.unemployment_rate` | 실업률 |
| employment | `ecos.employment.unit_labor_cost` | 단위노동비용지수 |
| population | `ecos.population.elderly_ratio` | 고령인구비율 |
| population | `ecos.population.fertility_rate` | 합계출산율 |
| population | `ecos.population.projected` | 추계인구 |
| external | `ecos.external.claims` | 대외채권 |
| external | `ecos.external.current_account` | 경상수지 |
| external | `ecos.external.debt` | 대외채무 |
| external | `ecos.external.direct_investment_assets` | 직접투자(자산) |
| external | `ecos.external.direct_investment_liabilities` | 직접투자(부채) |
| external | `ecos.external.portfolio_investment_assets` | 증권투자(자산) |
| external | `ecos.external.portfolio_investment_liabilities` | 증권투자(부채) |
| external | `ecos.external.reserves.fx` | 외환보유액(외환) |
| external | `ecos.external.reserves.gold` | 외환보유액(금) |
| external | `ecos.external.reserves.imf` | 외환보유액(IMF포지션) |
| external | `ecos.external.reserves.sdr` | 외환보유액(SDR) |
| external | `ecos.external.reserves.total` | 외환보유액 |
| trade | `ecos.trade.exports.price` | 수출물가지수 |
| trade | `ecos.trade.exports.semiconductor.price` | 반도체 수출물가지수 |
| trade | `ecos.trade.exports.semiconductor.value` | 반도체 수출금액지수 |
| trade | `ecos.trade.exports.semiconductor.volume` | 반도체 수출물량지수 |
| trade | `ecos.trade.exports.value` | 수출금액지수 |
| trade | `ecos.trade.exports.volume` | 수출물량지수 |
| trade | `ecos.trade.imports.price` | 수입물가지수 |
| trade | `ecos.trade.imports.semiconductor.price` | 반도체 수입물가지수 |
| trade | `ecos.trade.imports.semiconductor.value` | 반도체 수입금액지수 |
| trade | `ecos.trade.imports.semiconductor.volume` | 반도체 수입물량지수 |
| trade | `ecos.trade.imports.value` | 수입금액지수 |
| trade | `ecos.trade.imports.volume` | 수입물량지수 |
| trade | `ecos.trade.terms_of_trade.income` | 소득교역조건지수 |
| trade | `ecos.trade.terms_of_trade.net` | 순상품교역조건지수 |
| price | `ecos.price.core_cpi` | 농산물 및 석유류제외 소비자물가지수 |
| price | `ecos.price.cpi` | 소비자물가지수 |
| price | `ecos.price.living_cpi` | 생활물가지수 |
| price | `ecos.price.ppi` | 생산자물가지수 |
| price | `ecos.price.producer.dram` | DRAM 생산자물가 |
| price | `ecos.price.producer.nand` | NAND플래시 생산자물가 |
| price | `ecos.price.producer.system` | 시스템반도체 생산자물가 |
| real_estate | `ecos.real_estate.house_jeonse_price` | 주택전세가격지수 |
| real_estate | `ecos.real_estate.house_sales_price` | 주택매매가격지수 |
| real_estate | `ecos.real_estate.land_price_change` | 지가변동률(전기대비) |
| commodity | `ecos.commodity.dubai_oil` | Dubai유(현물) |
| commodity | `ecos.commodity.gold` | 금 |

## 4. 그 밖의 모든 통계

위 125개에 없는 통계는 통계표 코드로 직접 조회합니다. ECOS가 제공하는 6가지 조회를 그대로
쓰며, 모두 `dict`의 목록을 돌려줍니다.

| 불러오기 | 하는 일 |
|---|---|
| `ecos.fetch_series(통계표코드, ...)` | 한 통계의 기간별 값(시계열) |
| `ecos.fetch_tables()` | 통계표 목록 (하위표는 `stat_code=`로) |
| `ecos.fetch_items(통계표코드)` | 그 표에 딸린 세부 항목 |
| `ecos.fetch_key_statistics()` | 한눈에 보는 100대 지표 |
| `ecos.fetch_glossary(용어)` | 통계 용어 뜻풀이 |
| `ecos.fetch_meta(자료명)` | 자료 설명(메타데이터) |

```python
rows = ecos.fetch_series(
    "722Y001",             # 시장금리 통계표
    item_code1="0101000",  # 그 표 안의 '한국은행 기준금리' 항목
    cycle="M",             # 월별
    start="202001", end="202412",
)
```

값이 없는 구간은 `data_value`가 `None`으로 옵니다. 100건씩 나눠 오는 긴 시계열도 알아서
이어 붙여 한 번에 돌려줍니다.

## 5. 커맨드라인

설치하면 `ecos` 명령이 함께 깔립니다 (설치는 `pip install pyecos`, 명령은 `ecos`).
터미널에서 6가지 조회를 바로 할 수 있습니다.

```bash
ecos series 722Y001 --item 0101000 --start 202001 --end 202412  # 기준금리 시계열
ecos tables                                                     # 통계표 목록
ecos items 722Y001                                              # 한 표의 세부 항목
ecos key-stats                                                  # 100대 지표
ecos glossary DSR                                               # 용어 뜻풀이
ecos meta 경제심리지수                                          # 자료 설명
```

| 명령 | 하는 일 |
|---|---|
| `series <통계표코드>` | 기간별 값. `--item` 세부 항목(최대 4개), `--cycle` 주기, `--start`·`--end` 기간 |
| `tables` | 통계표 목록. `--stat-code`를 주면 그 표의 하위표 |
| `items <통계표코드>` | 그 표의 세부 항목 |
| `key-stats` | 100대 지표 |
| `glossary <용어>` | 용어 뜻풀이 |
| `meta <자료명>` | 자료 설명 |

모든 명령에 `--lang en`(영어)·`--json`(JSON 출력)을 붙일 수 있고, `ecos --version`으로
버전을 봅니다. 더 자세히는 `ecos <명령> --help`.

## 6. 조회 주기

`fetch_series`와 `series` 명령이 받는 조회 주기입니다. 라이브러리에서는 코드(`"M"`),
명령에서는 단어(`monthly`)를 씁니다. 각 행의 `time` 값이 주기에 맞춰 표기됩니다.

| 주기 | 코드 | 명령 단어 | `time` 예시 |
|---|---|---|---|
| 연 | `A` | `annual` | `2024` |
| 반기 | `S` | `semiannual` | `2024S1` |
| 분기 | `Q` | `quarterly` | `2024Q1` |
| 월 | `M` | `monthly` | `202401` |
| 반월 | `SM` | `semimonthly` | `202401S1` |
| 일 | `D` | `daily` | `20240115` |

## 7. 오류

| 예외 | 언제 |
|---|---|
| `ECOSConfigError` | API 키를 찾지 못했을 때 |
| `ECOSAuthError` | ECOS가 키를 거부했을 때 |
| `ECOSRateLimitError` | 너무 자주 불러 제한됐을 때 (ERROR-602) |
| `ECOSResponseError` | ECOS가 오류 코드를 돌려줬을 때 (`.code`·`.message` 포함) |
| `ECOSNetworkError` | 네트워크가 끝내 안 됐을 때 (일시적 오류는 재시도 후) |

모두 `ECOSError`의 하위입니다. 조회 결과가 없을 뿐이면 오류가 아니라 빈 목록으로 옵니다.
많이 조회할 때는 `ECOS(delay_seconds=0.6)`으로 간격을 두면 제한(약 3분에 300회)을 넘지
않습니다.

## 8. 오프라인 지표 검색

125개에 없는 통계표의 코드를 찾을 때 — API 키도 인터넷도 없이, 패키지에 들어 있는 통계표
목록에서 바로 검색합니다.

```python
from pyecos import catalog

catalog.search("소비자물가")
# -> [{"stat_code": "901Y009", "stat_name": "4.2.1. 소비자물가지수", "cycle": "M", "searchable": True}, ...]

catalog.table("901Y009")   # 그 표 한 줄 (없으면 None)
catalog.tables()           # 전체 목록 (834개)
```

통계표 이름이 한국어라 한글 키워드나 코드로 찾습니다. 최신 목록이나 세부 항목이 필요하면
`ecos.fetch_tables()`·`ecos.fetch_items()`를 쓰세요.

## 라이선스

[MIT](LICENSE)
