# pyecos

[![check](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml/badge.svg)](https://github.com/seokhoonj/pyecos/actions/workflows/check.yml)
[![PyPI](https://img.shields.io/pypi/v/pyecos)](https://pypi.org/project/pyecos/)
[![Python](https://img.shields.io/pypi/pyversions/pyecos)](https://pypi.org/project/pyecos/)
[![License](https://img.shields.io/pypi/l/pyecos)](https://github.com/seokhoonj/pyecos/blob/main/LICENSE)

[English](README.en.md) | **한국어**

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
