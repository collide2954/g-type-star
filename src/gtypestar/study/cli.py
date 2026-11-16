"""Command line interface of the style study."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gtypestar-study",
        description="Build the style study: check the tables and write the report.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("report", help="write docs/style-study.md from the tables")
    commands.add_parser("check", help="check the tables for errors")
    commands.add_parser("all", help="do check and report")
    args = parser.parse_args(argv)

    if args.command in ("check", "all"):
        from . import report

        problems = report.check()
        for problem in problems:
            print(f"problem: {problem}")
        if problems:
            return 1
        print("tables: no problems")
    if args.command in ("report", "all"):
        from . import report

        print(f"report: {report.write()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
