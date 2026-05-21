from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import DEFAULT_RESOLVERS, Paths
from .pipeline import run_update


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update disposable email domain outputs.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root path.")
    parser.add_argument("--workers", type=int, default=64, help="Concurrent DNS scan workers.")
    parser.add_argument(
        "--resolver",
        action="append",
        dest="resolvers",
        help="Public resolver IP to query. Can be passed multiple times.",
    )
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(message)s")

    paths = Paths.from_root(args.root)
    resolvers = tuple(args.resolvers) if args.resolvers else DEFAULT_RESOLVERS
    summary = run_update(paths, resolvers=resolvers, workers=args.workers)

    print(
        "Update complete: "
        f"fetched={summary.fetched}, "
        f"allowlisted={summary.allowlisted}, "
        f"cached_inactive={summary.skipped_cached_inactive}, "
        f"active={summary.active}, "
        f"newly_inactive={summary.newly_inactive}, "
        f"unknown_kept={summary.unknown}, "
        f"output={summary.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
