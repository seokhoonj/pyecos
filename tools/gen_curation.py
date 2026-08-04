"""Generate src/pyecos/curation/_generated.py from curation_design.tsv.

Reads the worksheet (one row per curated indicator, with a dotted ``path``) and
emits a tree of typed namespace classes: one class per interior path node, an
``Indicator`` at each leaf, and a ``_CurationGroups`` base that ``ECOS`` inherits
so ``ecos.<group>...`` resolves with autocomplete and under mypy. Each top-level
group is a ``cached_property``, so a client builds only the branches it touches.

Run:  uv run python tools/gen_curation.py
"""

from __future__ import annotations

import csv
import keyword
import subprocess
from collections.abc import Iterable
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TSV = _HERE / "curation_design.tsv"
_OUT = _HERE.parent / "src" / "pyecos" / "curation" / "_generated.py"

_MEMBER_BY_CODE = {
    "A": "ANNUAL",
    "S": "SEMIANNUAL",
    "Q": "QUARTERLY",
    "M": "MONTHLY",
    "SM": "SEMIMONTHLY",
    "D": "DAILY",
}


class _Node:
    """One node of the path trie: either a namespace (children) or a leaf (spec)."""

    def __init__(self) -> None:
        self.children: dict[str, _Node] = {}
        self.spec: dict[str, str] | None = None


def _pascal(segment: str) -> str:
    return "".join(part.capitalize() for part in segment.split("_"))


def _class_name(prefix: tuple[str, ...]) -> str:
    return "_" + "".join(_pascal(seg) for seg in prefix)


def _check_identifier(segment: str) -> None:
    # Note: single-char l/O/I pass on purpose -- `money.l` is the Bank of Korea's
    # own name for the L monetary aggregate, a deliberate member of the m1/m2/lf/l set.
    if not segment.isidentifier():
        raise ValueError(f"path segment {segment!r} is not a valid identifier")
    if keyword.iskeyword(segment):
        raise ValueError(f"path segment {segment!r} is a Python keyword")


def _build_tree(rows: Iterable[dict[str, str]]) -> _Node:
    """Build the path trie from worksheet rows, rejecting duplicate/ambiguous paths.

    Raises ``ValueError`` on a duplicate path, a path that is simultaneously a leaf
    and a namespace prefix, or a segment that is not a usable Python attribute --
    so a malformed worksheet fails loudly here rather than silently dropping a leaf.
    """
    root = _Node()
    seen: set[str] = set()
    for row in rows:
        path = row["path"].strip()
        if not path or not row["stat_code"].strip():
            continue
        if path in seen:
            raise ValueError(f"duplicate path {path!r} in worksheet")
        seen.add(path)
        node = root
        segments = path.split(".")
        for depth, seg in enumerate(segments):
            _check_identifier(seg)
            node = node.children.setdefault(seg, _Node())
            if depth == len(segments) - 1:
                if node.children:
                    raise ValueError(f"path {path!r} is both a leaf and a namespace")
                node.spec = row
            elif node.spec is not None:
                prefix = ".".join(segments[: depth + 1])
                raise ValueError(f"path {prefix!r} is both a leaf and a namespace")
    return root


def _load_tree() -> _Node:
    with _TSV.open(encoding="utf-8") as f:
        return _build_tree(csv.DictReader(f, delimiter="\t"))


def _spec_literal(row: dict[str, str]) -> str:
    def opt(col: str) -> str:
        value = row.get(col, "").strip()
        return repr(value) if value else "None"

    member = _MEMBER_BY_CODE[row["cycle"].strip()]
    return (
        "IndicatorSpec("
        f"path={row['path'].strip()!r}, "
        f"name_ko={row['name_ko'].strip()!r}, "
        f"name_en={row['name_en'].strip()!r}, "
        f"stat_code={row['stat_code'].strip()!r}, "
        f"cycle=Cycle.{member}, "
        f"item_code1={opt('item_code1')}, "
        f"item_code2={opt('item_code2')}, "
        f"item_code3={opt('item_code3')})"
    )


def _emit_class(prefix: tuple[str, ...], node: _Node, out: list[str]) -> None:
    """Emit interior classes bottom-up, so a child is defined before its parent."""
    for seg, child in node.children.items():
        if child.children:
            _emit_class(prefix + (seg,), child, out)

    name = _class_name(prefix)
    out.append(f"class {name}:")
    out.append(f'    """Curated indicators under ``{".".join(prefix)}``."""')
    out.append("")
    out.append("    def __init__(self, client: _SeriesClient) -> None:")
    for seg, child in node.children.items():
        if child.children:
            out.append(f"        self.{seg} = {_class_name(prefix + (seg,))}(client)")
        else:
            assert child.spec is not None
            out.append(
                f"        self.{seg} = Indicator(client, {_spec_literal(child.spec)})"
            )
    out.append("")
    out.append("")


def _emit_groups_base(root: _Node, out: list[str]) -> None:
    groups = list(root.children)
    out.append("class _CurationGroups:")
    out.append(
        '    """Curated indicators, grouped, reached as ``ecos.<group>.<indicator>``.'
    )
    out.append("")
    out.append(
        "    ``ECOS`` inherits this and sets :attr:`_series_client` to itself, so each"
    )
    out.append(
        "    group builds lazily on first access and stays bound to that client."
    )
    out.append('    """')
    out.append("")
    out.append("    _series_client: _SeriesClient")
    out.append("")
    for group in groups:
        cls = _class_name((group,))
        out.append("    @cached_property")
        out.append(f"    def {group}(self) -> {cls}:")
        out.append(f"        return {cls}(self._series_client)")
        out.append("")


def main() -> None:
    root = _load_tree()
    out: list[str] = [
        '"""Curated-indicator namespaces, grouped by theme.',
        "",
        "Generated by tools/gen_curation.py from tools/curation_design.tsv -- do not",
        "edit by hand. Each interior class mirrors one level of an indicator's dotted",
        "path; leaves are :class:`Indicator` objects.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from functools import cached_property",
        "",
        "from ..types import Cycle",
        "from ._indicator import Indicator, IndicatorSpec, _SeriesClient",
        "",
        '__all__ = ["_CurationGroups"]',
        "",
        "",
    ]
    for seg, child in root.children.items():
        _emit_class((seg,), child, out)
    _emit_groups_base(root, out)

    _OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    # The one-line-per-spec emission blows past the line length on purpose; let the
    # formatter wrap it so the checked-in file passes ruff like everything else.
    subprocess.run(["ruff", "format", str(_OUT)], check=True)
    n_indicators = sum(1 for _ in _walk_leaves(root))
    rel = _OUT.relative_to(_HERE.parent)
    print(f"wrote {rel} -- {len(root.children)} groups, {n_indicators} indicators")


def _walk_leaves(node: _Node) -> Iterable[_Node]:
    for child in node.children.values():
        if child.children:
            yield from _walk_leaves(child)
        else:
            yield child


if __name__ == "__main__":
    main()
