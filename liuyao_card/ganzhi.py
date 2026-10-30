"""일진·월건·순공(공망) 계산.

월건은 절기(節) 날짜를 공식으로 근사하므로 2001~2100년, 날짜 단위(±1일)까지만 믿을 수 있다.
절기 당일 전후는 `uncertain=True`로 표시하며, 정확한 값이 필요하면 엔진에 month_branch를 직접 넘긴다.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Tuple, Union

from .data import BRANCHES, BRANCHES_KO, STEMS, STEMS_KO

_REF_DATE = date(2000, 1, 1)
_REF_INDEX = 54  # 2000-01-01 = 戊午일 (갑자=0 기준 60갑자 번호)

# 21세기 절(節) 계수 (월 → C). 월건이 바뀌는 12절만 사용.
_TERM_C = {
    1: 5.4055,   # 소한
    2: 3.87,     # 입춘
    3: 5.63,     # 경칩
    4: 4.81,     # 청명
    5: 5.52,     # 입하
    6: 5.678,    # 망종
    7: 7.108,    # 소서
    8: 7.5,      # 입추
    9: 7.646,    # 백로
    10: 8.318,   # 한로
    11: 7.438,   # 입동
    12: 7.18,    # 대설
}
TERM_NAMES = {1: "소한", 2: "입춘", 3: "경칩", 4: "청명", 5: "입하", 6: "망종",
              7: "소서", 8: "입추", 9: "백로", 10: "한로", 11: "입동", 12: "대설"}


def sexagenary_name(idx: int) -> Tuple[str, str]:
    """60갑자 번호 → (한자 간지, 한글 간지)."""
    idx %= 60
    return STEMS[idx % 10] + BRANCHES[idx % 12], STEMS_KO[idx % 10] + BRANCHES_KO[idx % 12]


def day_index(when: Union[date, datetime], day_change_at_23: bool = False) -> int:
    """일진의 60갑자 번호. day_change_at_23=True면 23시 이후를 다음 날로 본다(야자시 구분)."""
    if isinstance(when, datetime):
        d = when.date()
        if day_change_at_23 and when.hour >= 23:
            d += timedelta(days=1)
    else:
        d = when
    return ((d - _REF_DATE).days + _REF_INDEX) % 60


def void_branches(day_idx: int) -> Tuple[int, int]:
    """일진이 속한 순(旬)의 공망 지지 번호 두 개."""
    start = day_idx - day_idx % 10
    return (start + 10) % 12, (start + 11) % 12


def _term_day(year: int, month: int) -> int:
    y = year % 100
    leap = (y - 1) // 4 if month in (1, 2) else y // 4
    return int(y * 0.2422 + _TERM_C[month]) - leap


def month_branch(when: Union[date, datetime]) -> Tuple[int, bool, str]:
    """(월건 지지 번호, 절기 경계 근처라 불확실한지, 기준 절기 이름)."""
    d = when.date() if isinstance(when, datetime) else when
    if not 2001 <= d.year <= 2100:
        raise ValueError("월건 자동 계산은 2001~2100년만 지원합니다. month_branch를 직접 지정하세요.")
    td = _term_day(d.year, d.month)
    term_month = d.month if d.day >= td else (d.month - 1 or 12)
    uncertain = abs(d.day - td) <= 1
    # 절 월 → 지지: 1월 소한=丑(1), 2월 입춘=寅(2) … 11월 입동=亥(11), 12월 대설=子(0)
    return term_month % 12, uncertain, TERM_NAMES[term_month]
