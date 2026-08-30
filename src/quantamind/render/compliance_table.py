"""The compliance table a buyer asks for, with what we could not check printed beside what we could.

WHAT: `table(standing, repo)` renders a `store.compliance.Standing` as text: every declared rule
      with all four outcomes, the files violations concentrate in, and the instrument's own limit
      first when the sample is too small to read as a rate.
WHY:  **THE UNCHECKABLE COLUMN IS THE PRODUCT.** Every competitor's compliance screen shows a
      pass rate. A rule that could not be evaluated is not a rule that passed, and folding the two
      together is how a dashboard reports a standard as met when nobody looked. This table prints
      `uncheckable` and `deferred` as their own columns and computes the rate over DECIDED checks
      only, so the denominator is the honest one.

      **THE CAVEAT GOES ABOVE THE TABLE, NOT UNDER IT.** A limit printed after the numbers is read
      second or not at all — the same choice `render/dashboard.py` made for the same reason.

      **A RULE WITH NOTHING DECIDED SHOWS `-`, NOT `0%`.** Zero per cent violated reads as
      compliance; it is silence. The two must not print the same characters.

      **PER REPOSITORY.** No developer is named anywhere in this file, deliberately.
IMPORTS: store.compliance. Left of serve, right of store.
CONSUMED BY: `serve/commands/run_report.py` behind `quantamind compliance`.
SEE ALSO: named for its
      artefact, not its subject — `store/compliance.py` is the read model, and `AGENTS.md` rule 13
      forbids two modules sharing a name, as `store/lifecycle.py` and `render/dashboard.py` do.
"""

from __future__ import annotations

from quantamind.store.compliance import Standing

HEAD = "| rule | passed | violated | uncheckable | deferred | violation rate |"
RULE = "|---|---:|---:|---:|---:|---:|"


def _rate(value: float | None) -> str:
    """A rate, or `-` when nothing was decided. Never `0%` for an absence."""
    return f"{value:.0%}" if value is not None else "-"


def table(standing: Standing, repo: str) -> str:
    """The whole report for one repository, newest facts first, limits before numbers."""
    lines = [f"## Rule compliance — `{repo}`", ""]

    caveat = standing.thin()
    if caveat is not None:
        lines += [f"**{caveat}**", ""]

    if not standing.rules:
        lines += [
            "No rule has been checked on this repository yet. That is not compliance: it is an",
            "absence of evidence, and it stays labelled as one until a review runs.",
            "",
        ]
        return "\n".join(lines)

    decided = sum(rule.decided for rule in standing.rules)
    withheld = sum(rule.uncheckable + rule.deferred for rule in standing.rules)
    lines += [
        f"{len(standing.rules)} declared rule(s) over {standing.reviews} reviewed change(s). "
        f"**{decided} check(s) decided, {withheld} not.**",
        "",
        HEAD,
        RULE,
    ]
    for rule in sorted(standing.rules, key=lambda r: (-r.violated, r.rule_id)):
        lines.append(
            f"| `{rule.rule_id}` | {rule.passed} | {rule.violated} | {rule.uncheckable} "
            f"| {rule.deferred} | {_rate(rule.violation_rate)} |"
        )

    if standing.hotspots:
        lines += ["", "**Where violations concentrate**", ""]
        lines += [f"- `{path}` — {count}" for path, count in standing.hotspots]
        if standing.other_hotspots:
            lines.append(f"- and {standing.other_hotspots} more file(s) with at least one")

    lines += [
        "",
        "The rate is violations over checks that could be DECIDED. Uncheckable and deferred are "
        "counted separately and never folded in: a rule nobody could evaluate did not pass.",
    ]
    return "\n".join(lines)
