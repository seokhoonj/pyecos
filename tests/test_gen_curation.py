"""The curation code generator's tree builder and its guard rails."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_GEN_PATH = Path(__file__).resolve().parent.parent / "tools" / "gen_curation.py"
_spec = importlib.util.spec_from_file_location("gen_curation", _GEN_PATH)
assert _spec is not None and _spec.loader is not None
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def _row(path: str) -> dict[str, str]:
    return {
        "path": path,
        "stat_code": "999Y999",
        "name_ko": "가",
        "name_en": "a",
        "cycle": "M",
        "item_code1": "X",
        "item_code2": "",
        "item_code3": "",
    }


def test_build_tree_places_leaves_and_namespaces():
    root = gen._build_tree([_row("rate.base"), _row("trade.exports.value")])
    assert root.children["rate"].children["base"].spec is not None
    assert root.children["trade"].children["exports"].children["value"].spec is not None


def test_rows_without_a_stat_code_are_skipped():
    blank = _row("rate.base")
    blank["stat_code"] = ""
    root = gen._build_tree([blank])
    assert "rate" not in root.children


def test_duplicate_path_raises():
    with pytest.raises(ValueError, match="duplicate path"):
        gen._build_tree([_row("rate.base"), _row("rate.base")])


def test_leaf_then_namespace_collision_raises():
    # A leaf at rate.base, then a deeper path turning rate.base into a namespace.
    with pytest.raises(ValueError, match="both a leaf and a namespace"):
        gen._build_tree([_row("rate.base"), _row("rate.base.overnight")])


def test_namespace_then_leaf_collision_raises():
    # The same clash discovered in the other order.
    with pytest.raises(ValueError, match="both a leaf and a namespace"):
        gen._build_tree([_row("rate.base.overnight"), _row("rate.base")])


def test_keyword_segment_raises():
    with pytest.raises(ValueError, match="Python keyword"):
        gen._build_tree([_row("trade.import.value")])


def test_single_char_l_is_allowed():
    # money.l is the Bank of Korea's own name for the L aggregate -- keep it.
    root = gen._build_tree([_row("money.l")])
    assert root.children["money"].children["l"].spec is not None


def test_non_identifier_segment_raises():
    with pytest.raises(ValueError, match="not a valid identifier"):
        gen._build_tree([_row("trade.2nd.value")])


def test_empty_path_row_is_skipped():
    blank = _row("")
    root = gen._build_tree([blank])
    assert not root.children


def test_class_name_pascalizes_each_segment():
    got = gen._class_name(("trade", "exports", "semiconductor"))
    assert got == "_TradeExportsSemiconductor"
    assert gen._class_name(("business_cycle",)) == "_BusinessCycle"


def test_spec_literal_emits_all_three_item_codes():
    row = _row("corporate.manufacturing.profit_margin") | {
        "cycle": "A", "item_code1": "C", "item_code2": "A", "item_code3": "6091"
    }
    lit = gen._spec_literal(row)
    assert "cycle=Cycle.ANNUAL" in lit
    assert "item_code1='C'" in lit
    assert "item_code2='A'" in lit
    assert "item_code3='6091'" in lit


def test_spec_literal_blank_item_codes_become_none():
    lit = gen._spec_literal(_row("rate.base") | {"item_code2": "", "item_code3": ""})
    assert "item_code2=None" in lit
    assert "item_code3=None" in lit


def test_spec_literal_rejects_an_unknown_cycle_code():
    with pytest.raises(KeyError):
        gen._spec_literal(_row("rate.base") | {"cycle": "Z"})


def test_generated_tree_matches_the_worksheet():
    """Every worksheet leaf must resolve in the shipped tree with identical codes.

    Guards against a stale _generated.py -- a TSV edit that was never regenerated.
    """
    import httpx

    from pyecos import ECOS

    ecos = ECOS(
        "K",
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"StatisticSearch": {"row": []}})
        ),
    )

    def leaves(node: object, prefix: tuple[str, ...]) -> list[tuple[str, dict]]:
        out: list[tuple[str, dict]] = []
        for seg, child in node.children.items():  # type: ignore[attr-defined]
            here = prefix + (seg,)
            if child.children:
                out.extend(leaves(child, here))
            elif child.spec is not None:
                out.append((".".join(here), child.spec))
        return out

    for path, spec in leaves(gen._load_tree(), ()):
        obj: object = ecos
        for seg in path.split("."):
            obj = getattr(obj, seg)
        assert obj.spec.stat_code == spec["stat_code"], path  # type: ignore[attr-defined]
        assert (obj.spec.item_code1 or "") == spec["item_code1"], path  # type: ignore[attr-defined]
