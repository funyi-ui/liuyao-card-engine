"""명령줄 사용: python -m liuyao_card [옵션]"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import List, Optional

from .engine import cast, from_values


def _parse_when(date_s: Optional[str], time_s: Optional[str]) -> Optional[datetime]:
    if not date_s:
        return None
    text = date_s if not time_s else f"{date_s} {time_s}"
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise SystemExit(f"날짜 형식이 올바르지 않습니다: {text!r} (예: 2026-10-30, 시각은 14:30)")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="liuyao-card", description="육효카드 엔진 — 카드 6장으로 점괘를 만듭니다.")
    p.add_argument("--values", help="직접 입력: 1효→6효 값 6개 (6노음 7소양 8소음 9노양), 예: 7,8,8,9,7,6")
    p.add_argument("--seed", type=int, help="같은 결과를 다시 뽑고 싶을 때 난수 시드")
    p.add_argument("--method", choices=["coin", "yarrow"], default="coin", help="덱 확률 (기본: coin)")
    p.add_argument("--date", help="점친 날짜 YYYY-MM-DD (생략 시 지금)")
    p.add_argument("--time", help="점친 시각 HH:MM")
    p.add_argument("--month-branch", help="월건 지지를 직접 지정 (예: 戌)")
    p.add_argument("--day-change-at-23", action="store_true", help="23시 이후를 다음 날 일진으로 계산")
    p.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = p.parse_args(argv)

    when = _parse_when(args.date, args.time)
    common = dict(month_branch=args.month_branch, day_change_at_23=args.day_change_at_23)
    try:
        if args.values:
            values = [int(v) for v in args.values.replace(" ", "").split(",")]
            reading = from_values(values, when=when or datetime.now(), **common)
        else:
            reading = cast(seed=args.seed, when=when, method=args.method, **common)
    except ValueError as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(reading.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(reading.to_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
