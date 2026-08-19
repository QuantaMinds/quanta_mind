"""The command line: the same pipeline, invoked locally, posting nothing.

WHAT: `main()` and the argument parser behind `uv run quantamind`. Today it reports version
      and resolved configuration; the review and retrospective commands arrive with the
      layers they need.
WHY:  The CLI is not a convenience. It runs the retrospective, it is how a sceptic verifies
      us before granting repository access, and it is what answers the ranker gate. So it is
      built first and stays. The App is this plus a webhook, a signature check and
      idempotency -- and the pipeline must not know which one called it, or what a customer
      verified here is not what runs there.
IMPORTS: stdlib only (argparse, sys), and types.settings. No layer to the left is skipped;
      there is simply no pipeline to call yet.
CONSUMED BY: the `quantamind` entry point in pyproject.toml, and tests/unit.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from quantamind import __version__
from quantamind.types.settings import Settings, SettingsError, load

# Large enough that no real history reaches it; not None, so the type stays one thing.
UNCAPPED = 10**9

# Commands named in AGENTS.md that have no implementation behind them yet. They parse and
# exit non-zero with the stage that will deliver them, rather than exiting 0 having done
# nothing -- a documented command that silently succeeds is how a runbook comes to report
# work it never did.
UNBUILT: dict[str, str] = {
    "review": "the reader, ranker and render stages",
    "serve": "the serve stage",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantamind",
        description="A code reviewer that reports what it did not check.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("config", help="print the resolved configuration and exit")
    walk = subparsers.add_parser(
        "retrospective", help="replay the ranker over a clone's own history and report"
    )
    walk.add_argument(
        "clone", type=Path, nargs="+", help="one or more full clones; nothing is sent anywhere"
    )
    walk.add_argument("--repo", default="local/clone", help="owner/name, for the report heading")
    for name, stage in UNBUILT.items():
        subparsers.add_parser(name, help=f"NOT BUILT — arrives with {stage}")
    return parser


def render_config(settings: Settings) -> str:
    """The resolved configuration, so a misconfiguration is visible before a run, not after."""
    lines = [
        f"database_path              {settings.database_path}",
        f"max_requests               {settings.max_requests}",
        f"threshold_percentile       {settings.threshold_percentile}",
        f"inference_enabled          {settings.inference_enabled}",
        f"model                      {settings.model}",
        f"subprocess_timeout_seconds {settings.subprocess_timeout_seconds}",
        "",
        f"runs a model on a review:  {settings.runs_model}",
    ]
    return "\n".join(lines)


def _retrospective(clones: list[Path], repo: str) -> int:
    """Replay one clone and print the report. The index is scratch and is thrown away.

    Imported here rather than at module scope so `quantamind config` and `--version` do not pay
    for the ranker, and so a broken layer below cannot stop the CLI reporting its own version.
    """
    from quantamind.render.replay_report import report
    from quantamind.serve.retrospective import replay
    from quantamind.types.pooled_outcome import pool

    for clone in clones:
        if not (clone / ".git").exists():
            print(f"{clone} is not a git clone; a retrospective reads history and nothing else")
            return 1
    outcomes = []
    with TemporaryDirectory() as scratch:
        for index, clone in enumerate(clones):
            # NO CAP. `MAX_EVENTS` stops one large repository dominating a pooled figure in the
            # RESEARCH, where the six were compared to each other. Here the customer's own history
            # is the answer, and capping would discard it and then report it short of the floor:
            # scrapy has 1,447 events and the capped run announced "132 short of 500".
            # owner/name is what store.touches requires; a colon or a bare directory is rejected.
            name = repo if len(clones) == 1 else f"{repo}/{clone.name}"
            outcomes.append(replay(clone, name, Path(scratch) / f"{index}.db", cap=UNCAPPED))
    print(report(outcomes, pool(outcomes) if len(outcomes) > 1 else None))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns an exit code rather than calling sys.exit, so tests can assert it."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command in UNBUILT:
        print(
            f"`quantamind {args.command}` is not built yet — it arrives with "
            f"{UNBUILT[args.command]}.\n"
            "See docs/plans/implementation.md for the stage and its gate."
        )
        return 2

    if args.command == "retrospective":
        return _retrospective(args.clone, args.repo)

    try:
        settings = load()
    except SettingsError as exc:
        print(f"configuration error: {exc}")
        return 1

    print(render_config(settings))
    return 0
