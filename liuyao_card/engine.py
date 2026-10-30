"""육효 엔진: 카드 6장 → 본괘·변괘, 납갑, 육친, 세응, 육신, 공망, 복신."""
from __future__ import annotations

import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Sequence, Union

from . import ganzhi
from .cards import Card, card_from_value, draw_cards
from .data import (
    BRANCH_ELEMENT, BRANCHES, BRANCHES_KO, CONTROLS, ELEMENT_KO, GENERATES,
    HEX_TABLE, RELATIVES, SIX_CLASH, SIX_HARMONY, SPIRIT_START_BY_STEM, SPIRITS,
    STEMS, TRIGRAMS, HexInfo,
)

When = Union[date, datetime]


# ── 결과 모델 ───────────────────────────────────────────
@dataclass
class Line:
    pos: int                 # 1(초효) ~ 6(상효)
    yang: bool
    moving: bool
    card_value: Optional[int]  # 본괘 효만 해당 (6~9), 변괘는 None
    stem: str
    branch: str
    element: str
    relative: str            # 육친 (항상 본궁 오행 기준)
    is_shi: bool
    is_ying: bool
    void: bool = False       # 공망 여부
    spirit: Optional[str] = None  # 육신 (본괘만)


@dataclass
class HiddenSpirit:
    """복신(伏神): 본괘에 없는 육친을 본궁 순괘에서 빌려 온 것."""
    relative: str
    fly_pos: int   # 이 복신이 숨어 있는 본괘 효 위치 (비신)
    stem: str
    branch: str
    element: str
    void: bool = False


@dataclass
class Hexagram:
    name_ko: str
    name_hanja: str
    palace: str
    palace_element: str
    step_label: str
    shi: int
    ying: int
    upper: str
    lower: str
    tags: List[str]
    lines: List[Line]


@dataclass
class Reading:
    cards: List[dict]
    ben: Hexagram                      # 본괘
    bian: Optional[Hexagram]           # 변괘 (동효가 없으면 None)
    moving: List[int]                  # 동효 위치
    hidden: List[HiddenSpirit]
    when: Optional[str] = None
    day_pillar: Optional[str] = None
    day_pillar_ko: Optional[str] = None
    void_branches: Optional[List[str]] = None
    month_branch: Optional[str] = None
    month_term: Optional[str] = None
    month_uncertain: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_text(self) -> str:
        return _render_text(self)


# ── 내부 계산 ───────────────────────────────────────────
def relative_of(palace_element: str, line_element: str) -> str:
    """궁 오행 기준 육친."""
    if line_element == palace_element:
        return "형제"
    if GENERATES[palace_element] == line_element:
        return "자손"
    if GENERATES[line_element] == palace_element:
        return "부모"
    if CONTROLS[palace_element] == line_element:
        return "처재"
    return "관귀"  # CONTROLS[line_element] == palace_element


def _make_lines(
    info: HexInfo,
    palace_element: str,
    moving: Sequence[bool],
    values: Sequence[Optional[int]],
    void_set: set,
    spirits: Optional[List[str]],
) -> List[Line]:
    lower, upper = TRIGRAMS[info.lower], TRIGRAMS[info.upper]
    out: List[Line] = []
    for i in range(6):
        if i < 3:
            stem, branch = lower.inner_stem, lower.inner_branches[i]
        else:
            stem, branch = upper.outer_stem, upper.outer_branches[i - 3]
        element = BRANCH_ELEMENT[branch]
        out.append(Line(
            pos=i + 1,
            yang=bool(info.lines[i]),
            moving=moving[i],
            card_value=values[i],
            stem=stem,
            branch=branch,
            element=element,
            relative=relative_of(palace_element, element),
            is_shi=(i + 1 == info.shi),
            is_ying=(i + 1 == info.ying),
            void=BRANCHES.index(branch) in void_set,
            spirit=spirits[i] if spirits else None,
        ))
    return out


def _tags(info: HexInfo, lines: List[Line]) -> List[str]:
    tags = []
    pairs = [frozenset((lines[i].branch, lines[i + 3].branch)) for i in range(3)]
    if all(p in SIX_CLASH for p in pairs):
        tags.append("육충괘")
    if all(p in SIX_HARMONY for p in pairs):
        tags.append("육합괘")
    return tags


def _hexagram(
    bits: Sequence[int],
    palace_element: str,
    moving: Sequence[bool],
    values: Sequence[Optional[int]],
    void_set: set,
    spirits: Optional[List[str]],
) -> Hexagram:
    info = HEX_TABLE[tuple(bits)]
    lines = _make_lines(info, palace_element, moving, values, void_set, spirits)
    return Hexagram(
        name_ko=info.name_ko, name_hanja=info.name_hanja,
        palace=info.palace, palace_element=info.palace_element,
        step_label=info.step_label, shi=info.shi, ying=info.ying,
        upper=info.upper, lower=info.lower,
        tags=_tags(info, lines), lines=lines,
    )


def _hidden_spirits(ben_lines: List[Line], palace: str, palace_element: str, void_set: set) -> List[HiddenSpirit]:
    present = {ln.relative for ln in ben_lines}
    pure = HEX_TABLE[TRIGRAMS[palace].lines * 2]
    pure_lines = _make_lines(pure, palace_element, [False] * 6, [None] * 6, void_set, None)
    result = []
    for rel in RELATIVES:
        if rel in present:
            continue
        for pl in pure_lines:
            if pl.relative == rel:
                result.append(HiddenSpirit(rel, pl.pos, pl.stem, pl.branch, pl.element, pl.void))
    return result


def from_values(
    values: Sequence[int],
    *,
    when: Optional[When] = None,
    month_branch: Optional[str] = None,
    day_change_at_23: bool = False,
) -> Reading:
    """효 값 6개(1효→6효, 각 6·7·8·9)로 점괘를 만든다."""
    if len(values) != 6:
        raise ValueError("효 값은 정확히 6개(1효→6효)여야 합니다.")
    cards = [card_from_value(v) for v in values]
    return _build(cards, when, month_branch, day_change_at_23)


def cast(
    *,
    seed: Optional[int] = None,
    when: Optional[When] = None,
    method: str = "coin",
    month_branch: Optional[str] = None,
    day_change_at_23: bool = False,
) -> Reading:
    """카드 6장을 뽑아 점괘를 만든다. when을 생략하면 지금 시각을 쓴다."""
    cards = draw_cards(method=method, seed=seed)
    if when is None:
        when = datetime.now()
    return _build(cards, when, month_branch, day_change_at_23)


def _build(
    cards: List[Card],
    when: Optional[When],
    month_branch_override: Optional[str],
    day_change_at_23: bool,
) -> Reading:
    notes: List[str] = []
    ben_bits = [int(c.yang) for c in cards]
    moving = [c.moving for c in cards]
    bian_bits = [b ^ int(m) for b, m in zip(ben_bits, moving)]
    info = HEX_TABLE[tuple(ben_bits)]
    palace_element = info.palace_element

    # 날짜 정보
    day_pillar = day_pillar_ko = None
    void_set: set = set()
    void_names: Optional[List[str]] = None
    spirits: Optional[List[str]] = None
    m_branch = m_term = None
    m_uncertain = False
    when_text = None
    if when is not None:
        when_text = when.isoformat()
        idx = ganzhi.day_index(when, day_change_at_23)
        day_pillar, day_pillar_ko = ganzhi.sexagenary_name(idx)
        void_set = set(ganzhi.void_branches(idx))
        void_names = [BRANCHES[i] for i in sorted(void_set)]
        start = SPIRIT_START_BY_STEM[idx % 10]
        spirits = [SPIRITS[(start + i) % 6] for i in range(6)]
        if month_branch_override:
            if month_branch_override not in BRANCHES:
                raise ValueError(f"month_branch는 지지 한 글자여야 합니다: {month_branch_override!r}")
            m_branch = month_branch_override
        else:
            try:
                b_idx, m_uncertain, m_term = ganzhi.month_branch(when)
                m_branch = BRANCHES[b_idx]
                if m_uncertain:
                    notes.append(f"{m_term} 절기 경계 근처라 월건이 하루 정도 어긋날 수 있습니다. 필요하면 month_branch로 직접 지정하세요.")
            except ValueError as exc:
                notes.append(str(exc))

    ben = _hexagram(ben_bits, palace_element, moving, [c.value for c in cards], void_set, spirits)
    bian = None
    if any(moving):
        bian = _hexagram(bian_bits, palace_element, [False] * 6, [None] * 6, void_set, None)

    return Reading(
        cards=[asdict(c) for c in cards],
        ben=ben,
        bian=bian,
        moving=[i + 1 for i, m in enumerate(moving) if m],
        hidden=_hidden_spirits(ben.lines, info.palace, palace_element, void_set),
        when=when_text,
        day_pillar=day_pillar,
        day_pillar_ko=day_pillar_ko,
        void_branches=void_names,
        month_branch=m_branch,
        month_term=m_term,
        month_uncertain=m_uncertain,
        notes=notes,
    )


# ── 텍스트 출력 ─────────────────────────────────────────
def _width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def _pad(s: str, width: int) -> str:
    return s + " " * max(0, width - _width(s))


def _art(yang: bool) -> str:
    return "━━━━━━━" if yang else "━━━ ━━━"


def _mark(card_value: Optional[int]) -> str:
    return {9: "○", 6: "×"}.get(card_value, " ") if card_value else " "


def _cell(ln: Line) -> str:
    return f"{ln.relative} {ln.stem}{ln.branch}{ELEMENT_KO[ln.element]}"


def _render_text(r: Reading) -> str:
    out: List[str] = []
    ben, bian = r.ben, r.bian
    if r.when:
        head = f"{r.when} · 일진 {r.day_pillar}({r.day_pillar_ko})일"
        if r.month_branch:
            head += f" · 월건 {r.month_branch}월"
        head += f" · 공망 {''.join(r.void_branches or [])}"
        out.append(head)
    out.append(f"본괘  {ben.name_ko} ({ben.name_hanja}) — {ben.palace}궁({ELEMENT_KO[ben.palace_element]}) {ben.step_label}"
               + (f" [{', '.join(ben.tags)}]" if ben.tags else ""))
    if bian:
        out.append(f"변괘  {bian.name_ko} ({bian.name_hanja}) — {bian.palace}궁({ELEMENT_KO[bian.palace_element]}) {bian.step_label}"
                   + (f" [{', '.join(bian.tags)}]" if bian.tags else ""))
    else:
        out.append("변괘  없음 (동효 없음)")
    out.append("")
    for pos in range(6, 0, -1):
        b = ben.lines[pos - 1]
        parts = [
            _pad(b.spirit or "", 4),
            f"{pos}효 ",
            _art(b.yang),
            _mark(b.card_value),
            " ",
            _pad(_cell(b), 14),
            ("世" if b.is_shi else "應" if b.is_ying else "　"),
            ("空" if b.void else " "),
        ]
        if bian:
            c = bian.lines[pos - 1]
            parts += ["  →  ", _art(c.yang), " ", _pad(_cell(c), 14),
                      ("世" if c.is_shi else "應" if c.is_ying else "　"), ("空" if c.void else " ")]
        out.append(" ".join(parts).rstrip())
    if r.hidden:
        out.append("")
        for h in r.hidden:
            out.append(f"복신  {h.relative} {h.stem}{h.branch}{ELEMENT_KO[h.element]} — 본괘 {h.fly_pos}효 아래 숨음" + (" (공망)" if h.void else ""))
    for n in r.notes:
        out.append(f"※ {n}")
    return "\n".join(out)
