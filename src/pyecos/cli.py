"""Command-line shell over ``ECOS`` -- ``pyecos series`` / ``tables`` / ``items`` / ...

The shell over the shell: it parses ``argv``, runs one library call, and renders the
returned rows as aligned text (or ``--json``). All request and parsing knowledge stays
in the library -- this only formats what the library returns -- and it is stdlib-only,
so the package's single runtime dependency (``httpx``) is not widened by having a CLI.

    $ export ECOS_API_KEY=...
    $ pyecos series 722Y001 --item 0101000 --cycle monthly --start 202001 --end 202412
    $ pyecos tables
    $ pyecos items 722Y001 --json
    $ pyecos key-stats
    $ pyecos glossary DSR
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence

from . import __version__
from .client import ECOS
from .exceptions import ECOSError
from .types import Cycle

# The --cycle words derive from the Cycle enum so the CLI never restates the
# taxonomy: the flag reads as words (monthly/daily), and Cycle[word.upper()] maps
# back. A cycle added to the enum becomes an accepted choice with no edit here.
_CYCLE_CHOICES = tuple(cycle.name.lower() for cycle in Cycle)

# How many of the most recent observations the text view of `series` prints; the full
# series is always available with --json.
_RECENT_OBS = 10

Row = Mapping[str, object]


def main(argv: Sequence[str] | None = None) -> int:
    """Parse ``argv``, run one call, and return a process exit code.

    A failure -- a missing API key, a rejected key, a vendor error, or a transport
    problem -- is printed as a one-line ``pyecos: <message>`` to stderr and returns 1,
    so a shell caller sees a clean error rather than a traceback. Argparse handles a
    bad flag or a missing subcommand itself (exit 2).
    """
    args = _make_parser().parse_args(argv)
    run: Callable[[argparse.Namespace], int] = args.run
    try:
        return run(args)
    except ECOSError as err:
        print(f"pyecos: {err}", file=sys.stderr)
        return 1


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyecos",
        description="Read the Bank of Korea ECOS API from the command line.")
    parser.add_argument("--version", action="version", version=f"pyecos {__version__}")
    commands = parser.add_subparsers(required=True)

    series = commands.add_parser(
        "series", help="a statistic's observations over time (StatisticSearch)")
    series.add_argument("stat_code", help="a statistic table code (e.g. 722Y001)")
    series.add_argument("--item", action="append", default=[], metavar="CODE",
                        help="an item code; repeat up to 4 to select a sub-series")
    series.add_argument("--cycle", choices=_CYCLE_CHOICES, default="monthly",
                        help="observation frequency (default: monthly)")
    series.add_argument("--start", default=None,
                        help="cycle-formatted period start (202001, 2020, 20200101)")
    series.add_argument("--end", default=None, help="cycle-formatted period end")
    _add_shared_flags(series)
    series.set_defaults(run=_run_series)

    tables = commands.add_parser(
        "tables", help="statistical tables, or a table's children (StatisticTableList)")
    tables.add_argument("--stat-code", default=None, metavar="CODE",
                        help="parent table code; omit for the top-level tables")
    _add_shared_flags(tables)
    tables.set_defaults(run=_run_tables)

    items = commands.add_parser(
        "items", help="a table's detail items (StatisticItemList)")
    items.add_argument("stat_code", help="a statistic table code (e.g. 722Y001)")
    _add_shared_flags(items)
    items.set_defaults(run=_run_items)

    key_stats = commands.add_parser(
        "key-stats", help="the top-100 headline indicators (KeyStatisticList)")
    _add_shared_flags(key_stats)
    key_stats.set_defaults(run=_run_key_stats)

    glossary = commands.add_parser(
        "glossary", help="a statistical term's definition (StatisticWord)")
    glossary.add_argument("word", help="the term to look up")
    _add_shared_flags(glossary)
    glossary.set_defaults(run=_run_glossary)

    meta = commands.add_parser(
        "meta", help="a meta-DB dataset by name (StatisticMeta)")
    meta.add_argument("dataset_name", help="the meta dataset name")
    _add_shared_flags(meta)
    meta.set_defaults(run=_run_meta)

    return parser


def _add_shared_flags(command: argparse.ArgumentParser) -> None:
    command.add_argument("--lang", choices=("kr", "en"), default=None,
                         help="response language (default: kr)")
    command.add_argument("--json", action="store_true",
                         help="emit JSON instead of text")


def _run_series(args: argparse.Namespace) -> int:
    if len(args.item) > 4:
        print("pyecos: at most 4 --item codes are allowed", file=sys.stderr)
        return 1
    items = (args.item + [None, None, None, None])[:4]
    with ECOS(lang=args.lang or "kr") as ecos:
        rows = ecos.get_series(
            args.stat_code, cycle=Cycle[args.cycle.upper()],
            start=args.start, end=args.end,
            item_code1=items[0], item_code2=items[1],
            item_code3=items[2], item_code4=items[3])
    print(_to_json(rows) if args.json else _render_series(rows, args.stat_code))
    return 0


def _run_tables(args: argparse.Namespace) -> int:
    with ECOS(lang=args.lang or "kr") as ecos:
        rows = ecos.get_tables(stat_code=args.stat_code)
    print(_to_json(rows) if args.json else _render_table(
        rows, [("code", "stat_code"), ("cycle", "cycle"),
               ("srch", "searchable"), ("name", "stat_name")]))
    return 0


def _run_items(args: argparse.Namespace) -> int:
    with ECOS(lang=args.lang or "kr") as ecos:
        rows = ecos.get_items(args.stat_code)
    print(_to_json(rows) if args.json else _render_table(
        rows, [("item", "item_code"), ("cycle", "cycle"), ("from", "start_time"),
               ("to", "end_time"), ("unit", "unit_name"), ("name", "item_name")]))
    return 0


def _run_key_stats(args: argparse.Namespace) -> int:
    with ECOS(lang=args.lang or "kr") as ecos:
        rows = ecos.get_key_statistics()
    print(_to_json(rows) if args.json else _render_table(
        rows, [("class", "class_name"), ("name", "keystat_name"),
               ("value", "data_value"), ("unit", "unit_name")]))
    return 0


def _run_glossary(args: argparse.Namespace) -> int:
    with ECOS(lang=args.lang or "kr") as ecos:
        rows = ecos.get_glossary(args.word)
    print(_to_json(rows) if args.json else _render_glossary(rows))
    return 0


def _run_meta(args: argparse.Namespace) -> int:
    with ECOS(lang=args.lang or "kr") as ecos:
        rows = ecos.get_meta(args.dataset_name)
    print(_to_json(rows) if args.json else _render_table(
        rows, [("lvl", "level"), ("code", "content_code"), ("name", "content_name")]))
    return 0


def _to_json(rows: Sequence[Row]) -> str:
    """The full row list as indented JSON, Korean names kept unescaped."""
    return json.dumps(list(rows), ensure_ascii=False, indent=2)


def _render_series(rows: Sequence[Row], stat_code: str) -> str:
    """A one-line summary, then the most recent observations (oldest-first)."""
    if not rows:
        return f"{stat_code}  (no observations in range)"
    unit = rows[-1].get("unit_name") or ""
    name = rows[-1].get("stat_name") or ""
    head = f"{stat_code}  {name}  {len(rows)} obs" + (f"  [{unit}]" if unit else "")
    lines = [head]
    for row in rows[-_RECENT_OBS:]:
        data_value = row.get("data_value")
        shown = "-" if data_value is None else f"{data_value:,}"
        lines.append(f"  {row.get('time', '-')!s:>10}  {shown:>16}")
    return "\n".join(lines)


def _render_glossary(rows: Sequence[Row]) -> str:
    """Each matched term as its word followed by the definition block."""
    if not rows:
        return "(no matching term)"
    blocks = []
    for row in rows:
        blocks.append(f"{row.get('word', '?')}\n  {row.get('content', '')}")
    return "\n\n".join(blocks)


def _render_table(rows: Sequence[Row], columns: list[tuple[str, str]]) -> str:
    """Rows as an aligned table over ``columns`` (label, key), one row per line.

    A missing or None cell prints as ``-``. A trailing count line follows so the reader
    sees how many rows came back when the table itself is empty.
    """
    if not rows:
        return "(no rows)"
    labels = [label for label, _ in columns]
    cells = [[_cell(row.get(key)) for _, key in columns] for row in rows]
    widths = [max(len(labels[i]), *(len(cell[i]) for cell in cells))
              for i in range(len(columns))]
    header = "  ".join(label.ljust(widths[i]) for i, label in enumerate(labels))
    body = "\n".join(
        "  ".join(cell[i].ljust(widths[i]) for i in range(len(columns)))
        for cell in cells)
    return f"{header}\n{body}\n({len(rows)} rows)"


def _cell(value: object) -> str:
    return "-" if value is None else str(value)


if __name__ == "__main__":
    raise SystemExit(main())
