"""육효(六爻) 기초 데이터: 팔괘, 납갑, 팔궁 64괘, 오행·육친 규칙."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ── 간지 ────────────────────────────────────────────────
STEMS = "甲乙丙丁戊己庚辛壬癸"
STEMS_KO = "갑을병정무기경신임계"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
BRANCHES_KO = "자축인묘진사오미신유술해"

BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}
ELEMENT_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}

# 오행 상생·상극
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 육합(六合)·육충(六沖) 지지 쌍
SIX_HARMONY = {frozenset(p) for p in ["子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未"]}
SIX_CLASH = {frozenset(p) for p in ["子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"]}

# 육신: 일간별 1효에서 시작하는 위치
SPIRITS = ["청룡", "주작", "구진", "등사", "백호", "현무"]
SPIRIT_START_BY_STEM = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5}

RELATIVES = ["형제", "자손", "부모", "처재", "관귀"]


# ── 팔괘 ────────────────────────────────────────────────
@dataclass(frozen=True)
class Trigram:
    key: str            # 한글 이름
    hanja: str
    symbol: str
    image: str          # 괘상 한자 (天澤火雷風水山地)
    lines: Tuple[int, int, int]   # 아래→위, 1=양
    element: str        # 궁 오행
    inner_stem: str     # 내괘 납갑 천간
    inner_branches: str  # 내괘 1·2·3효 지지
    outer_stem: str     # 외괘 납갑 천간
    outer_branches: str  # 외괘 4·5·6효 지지


# 팔궁 순서: 건 태 리 진 손 감 간 곤
TRIGRAMS: Dict[str, Trigram] = {
    t.key: t
    for t in [
        Trigram("건", "乾", "☰", "天", (1, 1, 1), "金", "甲", "子寅辰", "壬", "午申戌"),
        Trigram("태", "兌", "☱", "澤", (1, 1, 0), "金", "丁", "巳卯丑", "丁", "亥酉未"),
        Trigram("리", "離", "☲", "火", (1, 0, 1), "火", "己", "卯丑亥", "己", "酉未巳"),
        Trigram("진", "震", "☳", "雷", (1, 0, 0), "木", "庚", "子寅辰", "庚", "午申戌"),
        Trigram("손", "巽", "☴", "風", (0, 1, 1), "木", "辛", "丑亥酉", "辛", "未巳卯"),
        Trigram("감", "坎", "☵", "水", (0, 1, 0), "水", "戊", "寅辰午", "戊", "申戌子"),
        Trigram("간", "艮", "☶", "山", (0, 0, 1), "土", "丙", "辰午申", "丙", "戌子寅"),
        Trigram("곤", "坤", "☷", "地", (0, 0, 0), "土", "乙", "未巳卯", "癸", "丑亥酉"),
    ]
}
TRIGRAM_BY_LINES = {t.lines: k for k, t in TRIGRAMS.items()}
PALACE_ORDER = list(TRIGRAMS.keys())

# ── 팔궁 64괘 이름 (본궁→1세→2세→3세→4세→5세→유혼→귀혼) ──
STEP_LABELS = ["본궁(순괘)", "1세괘", "2세괘", "3세괘", "4세괘", "5세괘", "유혼괘", "귀혼괘"]
STEP_SHI = [6, 1, 2, 3, 4, 5, 4, 3]

PALACE_NAMES_HANJA = {
    "건": ["乾為天", "天風姤", "天山遯", "天地否", "風地觀", "山地剝", "火地晉", "火天大有"],
    "태": ["兌為澤", "澤水困", "澤地萃", "澤山咸", "水山蹇", "地山謙", "雷山小過", "雷澤歸妹"],
    "리": ["離為火", "火山旅", "火風鼎", "火水未濟", "山水蒙", "風水渙", "天水訟", "天火同人"],
    "진": ["震為雷", "雷地豫", "雷水解", "雷風恒", "地風升", "水風井", "澤風大過", "澤雷隨"],
    "손": ["巽為風", "風天小畜", "風火家人", "風雷益", "天雷无妄", "火雷噬嗑", "山雷頤", "山風蠱"],
    "감": ["坎為水", "水澤節", "水雷屯", "水火既濟", "澤火革", "雷火豐", "地火明夷", "地水師"],
    "간": ["艮為山", "山火賁", "山天大畜", "山澤損", "火澤睽", "天澤履", "風澤中孚", "風山漸"],
    "곤": ["坤為地", "地雷復", "地澤臨", "地天泰", "雷天大壯", "澤天夬", "水天需", "水地比"],
}
PALACE_NAMES_KO = {
    "건": ["건위천", "천풍구", "천산돈", "천지비", "풍지관", "산지박", "화지진", "화천대유"],
    "태": ["태위택", "택수곤", "택지췌", "택산함", "수산건", "지산겸", "뇌산소과", "뇌택귀매"],
    "리": ["이위화", "화산려", "화풍정", "화수미제", "산수몽", "풍수환", "천수송", "천화동인"],
    "진": ["진위뢰", "뇌지예", "뇌수해", "뇌풍항", "지풍승", "수풍정", "택풍대과", "택뢰수"],
    "손": ["손위풍", "풍천소축", "풍화가인", "풍뢰익", "천뢰무망", "화뢰서합", "산뢰이", "산풍고"],
    "감": ["감위수", "수택절", "수뢰둔", "수화기제", "택화혁", "뇌화풍", "지화명이", "지수사"],
    "간": ["간위산", "산화비", "산천대축", "산택손", "화택규", "천택리", "풍택중부", "풍산점"],
    "곤": ["곤위지", "지뢰복", "지택림", "지천태", "뇌천대장", "택천쾌", "수천수", "수지비"],
}


@dataclass(frozen=True)
class HexInfo:
    name_ko: str
    name_hanja: str
    palace: str          # 궁 (건·태·리·…)
    palace_element: str  # 궁 오행
    step: int            # 0=본궁 … 7=귀혼
    step_label: str
    shi: int             # 세효 위치 (1~6)
    ying: int            # 응효 위치 (1~6)
    lower: str           # 내괘
    upper: str           # 외괘
    lines: Tuple[int, ...]


def _palace_sequence(pure: Tuple[int, ...]) -> List[Tuple[int, ...]]:
    """순괘에서 시작해 팔궁 8괘를 생성한다."""
    seq: List[List[int]] = [list(pure)]
    cur = list(pure)
    for i in range(5):  # 1효~5효를 차례로 변
        cur = cur.copy()
        cur[i] ^= 1
        seq.append(cur)
    yuhon = seq[5].copy()
    yuhon[3] ^= 1                 # 유혼: 5세괘에서 4효를 되돌림
    seq.append(yuhon)
    guihon = yuhon.copy()
    guihon[0:3] = pure[0:3]       # 귀혼: 내괘를 본궁 내괘로 복귀
    seq.append(guihon)
    return [tuple(s) for s in seq]


def _build_table() -> Dict[Tuple[int, ...], HexInfo]:
    table: Dict[Tuple[int, ...], HexInfo] = {}
    for palace in PALACE_ORDER:
        tri = TRIGRAMS[palace]
        pure = tri.lines + tri.lines
        for step, bits in enumerate(_palace_sequence(pure)):
            shi = STEP_SHI[step]
            table[bits] = HexInfo(
                name_ko=PALACE_NAMES_KO[palace][step],
                name_hanja=PALACE_NAMES_HANJA[palace][step],
                palace=palace,
                palace_element=tri.element,
                step=step,
                step_label=STEP_LABELS[step],
                shi=shi,
                ying=(shi + 2) % 6 + 1,   # 세+3 (6효 기준 순환)
                lower=TRIGRAM_BY_LINES[bits[:3]],
                upper=TRIGRAM_BY_LINES[bits[3:]],
                lines=bits,
            )
    return table


HEX_TABLE = _build_table()
