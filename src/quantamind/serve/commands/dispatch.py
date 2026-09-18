"""Which implementation a parsed command runs, and nothing about parsing it.

WHAT: `run(args)` returns the exit code for a built command, or `None` when no branch matched so
      the caller can fall through to `config`.
WHY:  **`serve/cli.py` HIT THE 200-LINE CAP AND THE CHAIN IS THE HALF THAT KEEPS GROWING.** The
      parser changes once per command; this grows by a branch every time, and `reconcile` was the
      one that would not fit. Splitting on that seam leaves `cli.py` doing one thing — turning
      argv into a `Namespace` — and puts the command table where the next command goes.

      **EVERY IMPORT STAYS INSIDE ITS BRANCH, WHICH IS THE WHOLE POINT OF THE SHAPE.** `cli.py`
      imported each command's implementation lazily so `--version` and `config` still answer when
      a layer below is broken. Hoisting them here to tidy the file would quietly undo that: one
      bad import in `infer/` would take out `quantamind config`, the command an operator reaches
      for precisely when something is wrong.

      **`None` IS A VALUE, NOT A MISS.** "No branch matched" is how `config` is reached, and
      returning `0` for it would make an unknown command look like a successful one.
IMPORTS: stdlib argparse. Each command's module is imported inside its own branch.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

import argparse


def run(args: argparse.Namespace) -> int | None:
    """The exit code for a built command, or None when nothing matched."""
    if args.command == "serve":
        from quantamind.serve.commands.run_endpoint import run

        return run(args.port, args.host)

    if args.command == "review":
        from quantamind.serve.commands.run_commit import review_commit

        return review_commit(
            args.clone, args.repo, args.sha, deep_project=args.deep, as_json=args.as_json
        )

    if args.command == "scan":
        from quantamind.serve.commands.run_scan import run_scan

        return run_scan(args.clone, explain=args.explain)

    if args.command == "retrospective":
        from quantamind.serve.commands.run_retrospective import run_retrospective

        return run_retrospective(args.clone, args.repo)

    if args.command == "migrate":
        from quantamind.serve.commands.run_migrate import run_migrate

        return run_migrate()

    if args.command == "reconcile":
        from quantamind.serve.commands.run_reconcile import run_reconcile

        return run_reconcile(args.account)

    if args.command == "standards":
        from quantamind.serve.commands.run_standards import run_standards

        return run_standards(args.repo, args.pulls)

    if args.command == "compliance":
        from quantamind.serve.commands.run_report import run_compliance

        return run_compliance(args.repo, args.export)

    if args.command == "cost":
        from quantamind.serve.commands.run_report import run_cost

        return run_cost(args.repo)

    if args.command == "dashboard":
        from quantamind.serve.commands.run_report import run_dashboard

        return run_dashboard(args.repo, args.limit)

    return None
