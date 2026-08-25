"""Does telling the reviewer today's date stop it calling past dates future?

WHAT: Takes REAL diffs from live repositories whose added lines carry a date, and runs the shipped
      prompt over each twice -- once as it ships, once with today's date stated -- counting claims
      that a date is in the future. The same run also shows each diff with a date rewritten to be
      GENUINELY future, so the arm cannot pass by having gone quiet.
WHY:  **DATE ARITHMETIC IS 5 OF 45 REAL WRONG FINDINGS.** Blind raters recorded "the comment reads
      Aug 16 2026 and today is Aug 18 2026, so the date is past" four separate times. The model has
      no notion of the present; its training cut off before the diff was written, and a date after
      that cutoff reads as the future.

      **THE FUTURE ARM IS THE CONTROL AND WITHOUT IT THIS MEASURES NOTHING.** "Inject the date"
      could fix a false claim or simply silence the check, and those look identical if only past
      dates are tested. A genuinely future date is a real defect a reviewer should mention, so the
      treated arm must still mention it.

      **THE DIFFS ARE REAL AND FETCHED, NOT WRITTEN HERE.** A hand-made diff would measure the
      author's idea of what a dated change looks like.
IMPORTS: stdlib; local `bench_reviewer` and the Vertex `client`.
CONSUMED BY: read by a human; writes `results/date_grounding.json`.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "vertex"))
sys.path.insert(0, str(HERE.parent))

import bench_reviewer as br  # noqa: E402
from client import Client  # noqa: E402

OUT = HERE.parent / "results" / "date_grounding.json"
GH_TIMEOUT_S = 90
# **NO TRAILING `\b`.** `\b(20\d\d)-(\d\d)-(\d\d)\b` misses every ISO timestamp, because in
# `2026-08-10T09:39:18Z` the character after the day is `T` -- a word character, so there is no
# boundary. That silently skipped two of three real diffs and left this experiment at n = 1 while
# reporting "no dated line in the real diff", which reads like a property of the data.
DATE = re.compile(r"(?<!\d)(20\d\d)-(\d\d)-(\d\d)(?!\d)")
CLAIMS_FUTURE = re.compile(
    r"\b(in the future|future date|future-dated|has not (yet )?(occurred|happened)|"
    r"yet to (occur|happen)|later than (today|the current)|not yet (arrived|reached))\b",
    re.I,
)

# Repositories whose recent history actually carries dated lines, found by scanning rather than
# assumed. A repository with no dated change contributes nothing and is not padded in.
# **DATES NEAR TODAY, NOT ANY DATE.** Django's dated lines are 2012 test fixtures and the model
# knows 2012 has passed; they cannot reproduce the failure. The recorded failures were all about
# 2026 dates a few days old -- after the training cutoff, which is exactly when "the future" is a
# plausible reading. These three commits were found by scanning real history for that shape.
SOURCES = (
    ("pydantic/pydantic", "f7e30afbd959b3cf6401ebec3ed2a239aa1eaae8"),
    ("grafana/grafana", "dcc4743d8fc9aa9b8fc00ded713222a90dab072b"),
    ("hashicorp/terraform", "137cba0aea37d653711ec9e026760eda2b545795"),
)


def real_diff(repo: str, sha: str) -> str:
    """The commit's actual patch, from GitHub. Raises nothing; empty means unavailable."""
    done = subprocess.run(
        ["gh", "api", f"repos/{repo}/commits/{sha}", "--jq", '[.files[]?.patch] | join("\\n")'],
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_S,
    )
    return done.stdout if done.returncode == 0 else ""


def shift_to_future(diff: str, today: dt.date) -> tuple[str, int]:
    """(diff with every 2026-or-later date moved two years ahead, how many moved).

    Only dates at or after this year are moved. Shifting a 2012 test fixture to 2014 leaves it
    firmly in the past and would quietly put an unchanged diff in the FUTURE arm, which then reads
    as the treated arm correctly staying silent.
    """
    moved = 0

    def bump(m: re.Match[str]) -> str:
        nonlocal moved
        if int(m.group(1)) < today.year:
            return m.group(0)
        moved += 1
        return f"{int(m.group(1)) + 2}-{m.group(2)}-{m.group(3)}"

    return DATE.sub(bump, diff), moved


def dated_prompt(today: dt.date) -> str:
    """The shipped prompt with one sentence added. **Nothing else changes.**"""
    marker = "Report at most {max_issues} issues."
    if marker not in br.PROMPT:
        raise RuntimeError("the shipped prompt no longer contains the insertion point")
    return br.PROMPT.replace(
        marker,
        f"Today's date is {today.isoformat()}. Any date on or before that has already passed.\n\n"
        + marker,
    )


def main() -> int:
    client = Client("gemini-2.5-pro")
    today = dt.date.today()
    trials: list[dict[str, object]] = []

    for repo, sha in SOURCES:
        diff = real_diff(repo, sha)
        if not DATE.search(diff):
            print(f"  {repo}: no dated line in the real diff, skipped", flush=True)
            continue
        future, moved = shift_to_future(diff, today)
        for when, body in (("PAST", diff), ("FUTURE", future)):
            for arm, tmpl in (("SHIPPED", br.PROMPT), ("DATE_INJECTED", dated_prompt(today))):
                issues, finish = br.review(client, f"{repo} change", body, template=tmpl)
                said = [i for i in issues if CLAIMS_FUTURE.search(i)]
                trials.append(
                    {
                        "repo": repo,
                        "dates": when,
                        "arm": arm,
                        "moved": moved,
                        "issues": issues,
                        "future_claims": said,
                        "finish": finish,
                    }
                )
                print(
                    f"  {repo:<16} dates={when:<7} {arm:<14} "
                    f"{len(said)} future-claim(s) of {len(issues)} issue(s)",
                    flush=True,
                )

    OUT.write_text(json.dumps({"today": today.isoformat(), "trials": trials}, indent=1))
    print(f"\n  today is {today.isoformat()}")
    for when in ("PAST", "FUTURE"):
        for arm in ("SHIPPED", "DATE_INJECTED"):
            rows = [t for t in trials if t["dates"] == when and t["arm"] == arm]
            n = sum(len(t["future_claims"]) for t in rows)
            verdict = "FALSE claims" if when == "PAST" else "correct catches"
            print(f"    {when:<7} {arm:<14} {n} {verdict} over {len(rows)} diff(s)")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
