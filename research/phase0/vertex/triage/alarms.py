"""Raise candidate defects with a sound analyzer, inside the units the ranker funded.

WHAT: Runs `ruff` over each changed file with defect-oriented rules only, and keeps the alarms
      whose line falls inside one of the top-3 funded units.
WHY:  Four fixes failed with the model generating candidates, at a 7.2% base rate no filter can
      exceed. Every system in the literature with strong measured precision inverts the roles --
      a sound analyzer finds, the model triages. This is the finder half of that inversion.

      RULES ARE RESTRICTED TO DEFECT CLASSES ON PURPOSE. F (pyflakes: undefined names, unused
      bindings), B (bugbear: mutable defaults, loop-variable capture), S (security), ASYNC, PLE
      (pylint errors), RUF. No line length, no import order, no formatting -- a style alarm is
      trivially real and trivially not a defect, and including them would inflate the promoted
      set with things nobody wants reported.
IMPORTS: stdlib only (json, subprocess, tempfile, os).
CONSUMED BY: `triage_run.py` in this package.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

RULES = "F,B,S,ASYNC,PLE,RUF"
RUFF = "/Users/dhanu/Documents/SaaS/quanta_mind/.venv/bin/ruff"


class AnalyzerFailed(RuntimeError):
    """ruff did not run. NOT the same as ruff finding nothing."""


def raise_alarms(path: str, source: str) -> list[dict[str, object]]:
    """Every defect-class alarm in `source`. [] means the analyzer found nothing.

    Raises AnalyzerFailed when ruff could not run at all, so an empty result always means
    "clean" and never "the tool broke" -- the distinction rule 3 exists to protect.
    """
    with tempfile.TemporaryDirectory() as tmp:
        # keep the original basename: some rules key on whether it is a test file
        f = os.path.join(tmp, os.path.basename(path) or "u.py")
        with open(f, "w") as fh:
            fh.write(source)
        p = subprocess.run(
            [
                RUFF,
                "check",
                "--select",
                RULES,
                "--no-fix",
                "--output-format",
                "json",
                "--isolated",
                f,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        # ruff exits 1 when it finds violations; anything else is a real failure
        if p.returncode not in (0, 1):
            raise AnalyzerFailed(f"{path}: ruff exited {p.returncode}: {p.stderr.strip()[:160]}")
        try:
            found = json.loads(p.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise AnalyzerFailed(f"{path}: ruff output did not parse: {exc}") from None

    out: list[dict[str, object]] = []
    for a in found:
        loc = a.get("location") or {}
        out.append(
            {
                "code": a.get("code"),
                "message": a.get("message"),
                "line": int(loc.get("row", 0)),
                "column": int(loc.get("column", 0)),
            }
        )
    return out


def in_units(
    alarms: list[dict[str, object]], units: list[dict[str, object]]
) -> list[dict[str, object]]:
    """Alarms falling inside a funded unit, tagged with which one."""
    kept: list[dict[str, object]] = []
    for a in alarms:
        for u in units:
            if int(u["lineno"]) <= int(a["line"]) <= int(u["end_lineno"]):
                kept.append(
                    {
                        **a,
                        "unit": u["name"],
                        "unit_lineno": u["lineno"],
                        "unit_end": u["end_lineno"],
                    }
                )
                break
    return kept
