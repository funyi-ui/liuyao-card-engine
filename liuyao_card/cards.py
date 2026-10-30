"""효 카드(爻 card): 동전 던지기를 카드 뽑기로 대신하는 덱."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Card:
    value: int      # 6 노음 / 7 소양 / 8 소음 / 9 노양
    name: str
    hanja: str
    yang: bool
    moving: bool    # 동효(변하는 효) 여부


LINE_CARDS: Dict[int, Card] = {
    6: Card(6, "노음", "老陰", False, True),
    7: Card(7, "소양", "少陽", True, False),
    8: Card(8, "소음", "少陰", False, False),
    9: Card(9, "노양", "老陽", True, True),
}

# 덱 구성(카드 장수) — 한 효마다 새로 섞은 덱에서 한 장을 뽑는다.
#   coin   : 동전 3개 확률과 같음 (노음 1 : 소양 3 : 소음 3 : 노양 1)
#   yarrow : 시초(蓍草) 점 확률 (노음 1 : 소양 5 : 소음 7 : 노양 3)
DECKS: Dict[str, List[int]] = {
    "coin": [6, 7, 7, 7, 8, 8, 8, 9],
    "yarrow": [6] + [7] * 5 + [8] * 7 + [9] * 3,
}


def card_from_value(value: int) -> Card:
    try:
        return LINE_CARDS[int(value)]
    except (KeyError, ValueError):
        raise ValueError(f"효 값은 6(노음)·7(소양)·8(소음)·9(노양) 중 하나여야 합니다: {value!r}")


def draw_cards(
    method: str = "coin",
    seed: Optional[int] = None,
    rng: Optional[random.Random] = None,
) -> List[Card]:
    """1효→6효 순서로 카드 6장을 뽑는다. seed를 주면 재현 가능."""
    if method not in DECKS:
        raise ValueError(f"method는 {sorted(DECKS)} 중 하나여야 합니다: {method!r}")
    if rng is None:
        rng = random.Random(seed) if seed is not None else random.SystemRandom()
    deck = DECKS[method]
    return [LINE_CARDS[rng.choice(deck)] for _ in range(6)]
