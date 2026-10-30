from datetime import date, datetime

import pytest

from liuyao_card import cast, from_values
from liuyao_card.data import HEX_TABLE, TRIGRAMS
from liuyao_card.ganzhi import day_index, month_branch, sexagenary_name, void_branches


# ── 64괘 표 ────────────────────────────────────────────
def test_64_hexagrams_unique_and_complete():
    assert len(HEX_TABLE) == 64
    assert len({h.name_hanja for h in HEX_TABLE.values()}) == 64
    assert len({h.name_ko for h in HEX_TABLE.values()}) == 64


def test_names_match_trigram_images():
    """괘 이름의 첫 글자=외괘 상, 둘째 글자=내괘 상 (순괘 제외)."""
    for h in HEX_TABLE.values():
        if h.step == 0:
            continue
        assert h.name_hanja[0] == TRIGRAMS[h.upper].image, h.name_hanja
        assert h.name_hanja[1] == TRIGRAMS[h.lower].image, h.name_hanja


def test_shi_ying_pairs():
    for h in HEX_TABLE.values():
        assert (h.ying - h.shi) % 6 == 3


def test_known_palace_members():
    by_name = {h.name_ko: h for h in HEX_TABLE.values()}
    assert by_name["천풍구"].palace == "건" and by_name["천풍구"].shi == 1
    assert by_name["화지진"].step_label == "유혼괘" and by_name["화지진"].shi == 4
    assert by_name["화천대유"].step_label == "귀혼괘" and by_name["화천대유"].shi == 3
    assert by_name["지수사"].palace == "감" and by_name["지수사"].step_label == "귀혼괘"
    assert by_name["풍산점"].palace == "간"


# ── 납갑·육친 ──────────────────────────────────────────
def test_qian_pure_hexagram():
    r = from_values([7, 7, 7, 7, 7, 7], when=date(2024, 1, 1))  # 甲子일
    assert r.ben.name_ko == "건위천"
    assert [ln.branch for ln in r.ben.lines] == list("子寅辰午申戌")
    assert [ln.relative for ln in r.ben.lines] == ["자손", "처재", "부모", "관귀", "형제", "부모"]
    assert r.ben.lines[5].is_shi and r.ben.lines[2].is_ying
    assert "육충괘" in r.ben.tags


def test_tian_feng_gou_najia():
    r = from_values([8, 7, 7, 7, 7, 7], when=date(2024, 1, 1))
    assert r.ben.name_ko == "천풍구"
    assert [ln.stem + ln.branch for ln in r.ben.lines] == ["辛丑", "辛亥", "辛酉", "壬午", "壬申", "壬戌"]
    assert [ln.relative for ln in r.ben.lines] == ["부모", "자손", "형제", "관귀", "형제", "부모"]
    assert r.ben.lines[0].is_shi and r.ben.lines[3].is_ying


def test_six_clash_and_harmony_tags():
    clash = {h.name_hanja for h in HEX_TABLE.values()}
    from liuyao_card.engine import _hexagram
    got_clash, got_harmony = set(), set()
    for bits, info in HEX_TABLE.items():
        hx = _hexagram(bits, info.palace_element, [False] * 6, [None] * 6, set(), None)
        if "육충괘" in hx.tags:
            got_clash.add(info.name_hanja)
        if "육합괘" in hx.tags:
            got_harmony.add(info.name_hanja)
    assert got_clash == {"乾為天", "坤為地", "坎為水", "離為火", "震為雷", "巽為風", "艮為山", "兌為澤", "天雷无妄", "雷天大壯"}
    assert got_harmony == {"天地否", "地天泰", "澤水困", "水澤節", "山火賁", "火山旅", "雷地豫", "地雷復"}


# ── 동효·변괘 ──────────────────────────────────────────
def test_moving_lines_make_changed_hexagram():
    r = from_values([9, 7, 7, 7, 7, 7], when=date(2024, 1, 1))  # 건위천 초효 동
    assert r.moving == [1]
    assert r.bian.name_ko == "천풍구"
    assert r.bian.lines[0].branch == "丑"
    # 변효 육친은 본궁(건궁=金) 기준: 丑土 → 부모
    assert r.bian.lines[0].relative == "부모"


def test_no_moving_means_no_bian():
    r = from_values([7, 8, 7, 8, 7, 8])
    assert r.bian is None and r.moving == []


def test_invalid_values():
    with pytest.raises(ValueError):
        from_values([7, 7, 7, 7, 7])
    with pytest.raises(ValueError):
        from_values([7, 7, 7, 7, 7, 5])


# ── 일진·공망·육신 ─────────────────────────────────────
def test_day_pillar_reference_dates():
    assert sexagenary_name(day_index(date(2000, 1, 1)))[0] == "戊午"
    assert sexagenary_name(day_index(date(2024, 1, 1)))[0] == "甲子"


def test_void_branches():
    assert void_branches(0) == (10, 11)       # 甲子순: 戌亥
    assert void_branches(10) == (8, 9)        # 甲戌순: 申酉
    assert void_branches(54) == (0, 1)        # 甲寅순(50~59): 子丑


def test_spirits_by_day_stem():
    r = from_values([7] * 6, when=date(2024, 1, 1))  # 甲일 → 청룡 시작
    assert [ln.spirit for ln in r.ben.lines] == ["청룡", "주작", "구진", "등사", "백호", "현무"]
    r2 = from_values([7] * 6, when=date(2000, 1, 1))  # 戊일 → 구진 시작
    assert r2.ben.lines[0].spirit == "구진"


def test_void_flag_on_lines():
    r = from_values([7] * 6, when=date(2024, 1, 1))  # 甲子일 공망 戌亥
    assert [ln.void for ln in r.ben.lines] == [False, False, False, False, False, True]


def test_day_change_at_23():
    a = day_index(datetime(2024, 1, 1, 23, 30))
    b = day_index(datetime(2024, 1, 1, 23, 30), day_change_at_23=True)
    assert (b - a) % 60 == 1


# ── 월건 ───────────────────────────────────────────────
def test_month_branch():
    idx, _, _ = month_branch(date(2026, 10, 30))
    assert "子丑寅卯辰巳午未申酉戌亥"[idx] == "戌"
    idx, _, _ = month_branch(date(2026, 11, 20))
    assert "子丑寅卯辰巳午未申酉戌亥"[idx] == "亥"
    idx, _, _ = month_branch(date(2026, 1, 2))
    assert "子丑寅卯辰巳午未申酉戌亥"[idx] == "子"


def test_month_branch_out_of_range_note():
    r = from_values([7] * 6, when=date(1990, 5, 5))
    assert r.month_branch is None and r.notes
    r2 = from_values([7] * 6, when=date(1990, 5, 5), month_branch="巳")
    assert r2.month_branch == "巳"


# ── 복신 ───────────────────────────────────────────────
def test_hidden_spirit_for_missing_relative():
    # 천풍구(건궁 金): 처재(寅木)가 본괘에 없음 → 건위천 2효 寅에서 복신
    r = from_values([8, 7, 7, 7, 7, 7], when=date(2024, 1, 1))
    hidden = {h.relative: h for h in r.hidden}
    assert "처재" in hidden
    assert hidden["처재"].branch == "寅" and hidden["처재"].fly_pos == 2


# ── 카드 뽑기 ──────────────────────────────────────────
def test_cast_is_reproducible_with_seed():
    a = cast(seed=42, when=date(2026, 10, 30))
    b = cast(seed=42, when=date(2026, 10, 30))
    assert a.to_dict() == b.to_dict()


def test_cast_methods_and_text():
    for method in ("coin", "yarrow"):
        r = cast(seed=1, when=date(2026, 10, 30), method=method)
        assert len(r.cards) == 6
        assert r.ben.name_ko in {h.name_ko for h in HEX_TABLE.values()}
        assert r.to_text()
    with pytest.raises(ValueError):
        cast(method="nope")


def test_deck_distribution():
    from liuyao_card.cards import DECKS
    assert sorted(DECKS["coin"]).count(7) == 3 and len(DECKS["coin"]) == 8
    assert len(DECKS["yarrow"]) == 16
