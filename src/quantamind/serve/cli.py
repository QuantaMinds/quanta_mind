"""The command line: the same pipeline, invoked locally, posting nothing.

WHAT: `main()` and the argument parser behind `uv run quantamind`. `config` prints the resolved
      settings, `retrospective` replays the ranker over a clone's own history, `serve` binds the
      webhook endpoint. `review` is the one command still unbuilt, and it says so and exits 2.
WHY:  The CLI is not a convenience. It runs the retrospective, it is how a sceptic verifies
      us before granting repository access, and it is what answers the ranker gate. So it is
      built first and stays. The App is this plus a webhook, a signature check and
      idempotency -- and the pipeline must not know which one called it, or what a customer
      verified here is not what runs there.
IMPORTS: stdlib (argparse, pathlib, tempfile) and types.settings at module scope. The heavier
      layers -- render.replay_report, serve.{run_endpoint,retrospective}, types.pooled_outcome --
      are imported inside the command that needs them, so `--version` and `config` still answer
      when a layer below is broken.
CONSUMED BY: the `quantamind` entry point in pyproject.toml, and tests/unit.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from quantamind import __version__
from quantamind.types.settings import Settings, SettingsError, load

# Commands named in AGENTS.md that have no implementation behind them yet. They parse and
# exit non-zero with the stage that will deliver them, rather than exiting 0 having done
# nothing -- a documented command that silently succeeds is how a runbook comes to report
# work it never did.
UNBUILT: dict[str, str] = {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantamind",
        description="A code reviewer that reports what it did not check.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("config", help="print the resolved configuration and exit")
    listen = subparsers.add_parser(
        "serve", help="authenticate and de-duplicate GitHub webhooks over HTTP"
    )
    listen.add_argument("--port", type=int, default=7331)
    look = subparsers.add_parser(
        "review", help="rank one change's files against history and print what we would say"
    )
    look.add_argument("clone", type=Path, help="a full clone; nothing is sent anywhere")
    look.add_argument("--repo", default="local/clone", help="owner/name, for the store key")
    look.add_argument(
        "--sha", required=True, help="the commit to review, scored against history BEFORE it"
    )
    # **SUPPRESSED FROM `--help`, NOT REMOVED, AND OFF UNLESS ASKED FOR BY NAME.**
    # `docs/product/QUANTAMIND.md` says the product publishes no model findings. A flag advertised
    # in `--help` contradicts that document, and a CLI quietly offering what the canonical document
    # says is not shipped is precisely the drift this project spends its time catching.
    #
    # It stays because the measurement half needs it: raw findings are **66.7-82.1% wrong** at
    # **0.013-0.037 correct per pull request**, and the parser gate in front of it has adjudicated
    # exactly ONE live finding — which it dropped. That is not a capability to put in front of a
    # customer; it is an instrument for finding out whether it could ever be one.
    look.add_argument("--deep", metavar="GCP_PROJECT", default="", help=argparse.SUPPRESS)
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
            # NO CAP. `SURVIVOR_CAP` stops one large repository dominating a pooled figure in the
            # RESEARCH, where the six were compared to each other. Here the customer's own history
            # is the answer, and capping would discard it and then report it short of the floor:
            # scrapy has 1,447 events and the capped run announced "132 short of 500".
            # owner/name is what store.touches requires; a colon or a bare directory is rejected.
            name = repo if len(clones) == 1 else f"{repo}/{clone.name}"
            outcomes.append(replay(clone, name, Path(scratch) / f"{index}.db"))
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

    if args.command == "serve":
        from quantamind.serve.run_endpoint import run

        return run(args.port)

    if args.command == "review":
        from quantamind.serve.run_review import review_commit

        return review_commit(args.clone, args.repo, args.sha, deep_project=args.deep)

    if args.command == "retrospective":
        return _retrospective(args.clone, args.repo)

    try:
        settings = load()
    except SettingsError as exc:
        print(f"configuration error: {exc}")
        return 1

    print(render_config(settings))
    return 0
