# pyecos

[![check](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml/badge.svg)](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml)
[![PyPI](https://img.shields.io/pypi/v/pyecos)](https://pypi.org/project/pyecos/)
[![Python](https://img.shields.io/pypi/pyversions/pyecos)](https://pypi.org/project/pyecos/)
[![License](https://img.shields.io/pypi/l/pyecos)](https://github.com/seokhoonj/pyecos/blob/main/LICENSE)

**한국어** | [English](README.en.md)

한국은행 경제통계시스템 [ECOS Open API](https://ecos.bok.or.kr/api/#/)의 파이썬 클라이언트입니다.
자주 쓰는 지표 125개는 **이름으로** 바로 가져오고, 그 밖의 통계는 ECOS 6개 서비스로 조회합니다.

## 설치

```bash
pip install pyecos
```

[ECOS Open API 사이트](https://ecos.bok.or.kr/api/#/)에서 무료 API 키를 발급받아, 아래 중 한 가지로 등록합니다.

**① 코드에서 직접 넘기기**

```python
from pyecos import ECOS

ecos = ECOS(api_key="발급받은-키")
```

**② 저장해두고 `ECOS()`가 자동으로 찾게 하기** — 환경변수나 파일에 두면 인자 없이 `ECOS()`만 쓰면 됩니다.

```bash
# 환경변수로
export ECOS_API_KEY="발급받은-키"

# 또는 파일에 한 번만 저장
mkdir -p ~/.config/pyecos
printf '{"ECOS_API_KEY": "발급받은-키"}' > ~/.config/pyecos/credentials.json
chmod 600 ~/.config/pyecos/credentials.json
```

키는 ① 인자 → ② 환경변수 `ECOS_API_KEY` → ③ 파일 `~/.config/pyecos/credentials.json` 순으로 찾습니다.

## 빠른 시작

```python
from pyecos import ECOS

ecos = ECOS()                                              # 키를 자동으로 찾아 클라이언트 생성
rows = ecos.rate.base.fetch(start="202001", end="202412")  # 기준금리 월별 시계열을 조회
```

반환값은 평범한 `dict`의 `list`라, pandas DataFrame으로 한 줄에 바뀝니다 (pandas는 필수 의존성이 아닙니다).

```python
import pandas as pd

frame = pd.DataFrame(rows)
```

## 큐레이션 지표 (125개)

통계표 코드를 외울 필요 없이, 자주 쓰는 **125개** 지표를 `ecos.<그룹>.<지표>` 경로로 가져옵니다.
`ecos.` 뒤를 타고 들어가면 **에디터 자동완성**으로 탐색되고, 모든 지표가 `.fetch(start, end)`와 `.latest()`를 제공합니다.

```python
ecos = ECOS()

ecos.rate.base.fetch(start="202001", end="202412")  # 기준금리
ecos.fx.usd.latest()                                # 원/달러 최근값
ecos.trade.exports.semiconductor.value.fetch()      # 반도체 수출금액지수
ecos.stock.kospi.per.fetch()                        # 코스피 PER
```

전체 지표 트리 — `name/`은 그룹(네임스페이스), 나머지 leaf가 지표입니다.

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

## 6개 서비스

큐레이션에 없는 통계는 `ECOS`의 서비스 메서드로 직접 조회합니다. ECOS 6개 서비스와 1:1로 대응하며, 모두 `list[dict]`을 반환합니다.

| 메서드 | 무엇을 조회 | ECOS 서비스 |
|---|---|---|
| `fetch_series(stat_code, ...)` | 통계 시계열 | StatisticSearch |
| `fetch_tables(stat_code=None)` | 통계표 목록 | StatisticTableList |
| `fetch_items(stat_code)` | 표의 세부 항목 | StatisticItemList |
| `fetch_key_statistics()` | 100대 통계지표 | KeyStatisticList |
| `fetch_glossary(word)` | 용어사전 | StatisticWord |
| `fetch_meta(dataset_name)` | 메타DB | StatisticMeta |

```python
ecos = ECOS()

rows = ecos.fetch_series(
    "722Y001",             # 시장금리 통계표
    item_code1="0101000",  # 한국은행 기준금리
    cycle="M",
    start="202001",
    end="202412",
)
```

`fetch_series`는 값이 비면 `data_value`가 `None`으로 오고, 요청당 100건 제한을 알아서 페이지네이션하므로 여러 해치 일별 시계열도 한 번의 호출로 돌아옵니다.

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

## 오프라인 카탈로그

큐레이션 125개에 없는 통계표의 `stat_code`를 찾을 때 — API 키도 네트워크도 없이, 패키지에 동봉된 통계표 스냅샷에서 검색합니다.

```python
from pyecos import catalog

catalog.search("소비자물가")
# -> [{"stat_code": "901Y009", "stat_name": "4.2.1. 소비자물가지수", "cycle": "M", "searchable": True}, ...]

catalog.table("901Y009")   # 그 표 한 줄, 없으면 None
catalog.tables()           # 전체 스냅샷 (834개 표)
```

통계표 이름은 한국어라 한글 키워드나 코드로 검색합니다. 실시간 목록이나 표의 세부 항목은 `ecos.fetch_tables()` / `ecos.fetch_items()`를 쓰세요.

## 라이선스

[MIT](LICENSE)
