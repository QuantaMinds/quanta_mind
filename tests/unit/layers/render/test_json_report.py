"""The review as data — and the three keys an agent would act on wrongly if they lied.

WHAT: Parses `render/json_report.report()` and asserts on the object a tool receives.
WHY:  **AN AGENT ACTS UNATTENDED, SO AMBIGUITY COSTS MORE HERE THAN IN PROSE.** A human reading
      "cannot tell" hesitates; a tool reading `false` merges. The three that matter:

      **`unread` IS ALWAYS PRESENT.** An absent key and an empty list must not be the same answer,
      or an agent reports a partial review as a whole one.

      **`breaks: null` IS NEVER `false`.** Null is "we could not tell"; false is "we checked the
      callers". Collapsing them merges on a check that never ran.

      **`provenance` SURVIVES, THOUGH IT LEFT THE COMMENT.** A developer does not act on which
      component produced a line; an agent deciding whether to apply a fix unattended must weigh a
      parser's verdict differently from a model's reading.
IMPORTS: render.json_report, types.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import json

from quantamind.rank.order import rank
from quantamind.render.json_report import SCHEMA, report
from quantamind.types.checked import Checked, Outcome
from quantamind.types.finding import Finding
from quantamind.types.verdict import Provenance, Reason, Site


class _Verdicts:
    """The shape `infer.change_summary.Summary` presents, with `breaks` deliberately undecided."""

    what_changed = "It adds a table."
    achieves_goal = True
    reasoning = "The table is present."
    impact = "Callers unaffected."
    breaks: bool | None = None
    breaks_why = "No importer of the changed file could be found."
    convention = ""
    dependents: tuple[str, ...] = ()


def test_unread_is_present_even_when_nothing_was_skipped() -> None:
    """An absent key and an empty list must not be the same answer."""
    body = json.loads(report(rank({"a.py": 5})))

    assert "unread" in body["files"], (
        "the residual key was omitted. An agent that cannot see it reports a partial review as a "
        "whole one, and an omission is indistinguishable from 'nothing was skipped'"
    )
    assert body["files"]["unread"] == []


def test_unread_names_the_files_nobody_looked_at() -> None:
    body = json.loads(report(rank({f"f{i}.py": 10 - i for i in range(6)})))

    assert body["files"]["reviewed"], "nothing was reported as reviewed"
    assert body["files"]["unread"], "a six-file change reported nothing unread"
    assert set(body["files"]["reviewed"]) & set(body["files"]["unread"]) == set(), (
        "a file was reported as both reviewed and unread"
    )


def test_undecided_never_becomes_false() -> None:
    """**THE ONE THAT MERGES BAD CODE.** `null` is "could not tell"; `false` is "we checked".

    The whole verdicts object is compared rather than one key: a tool reads all of it, and a
    field that quietly changed shape would be as damaging as one that lied.
    """
    body = json.loads(report(rank({"a.py": 1}), summary=_Verdicts()))

    assert body["verdicts"] == {
        "what_changed": "It adds a table.",
        "achieves_goal": True,
        "reasoning": "The table is present.",
        "impact": "Callers unaffected.",
        "breaks": None,
        "breaks_why": "No importer of the changed file could be found.",
        "convention_broken": None,
        "dependents": [],
    }, "an undecided break verdict changed shape; a tool reading false would merge on no check"


def test_provenance_survives_into_the_data() -> None:
    body = json.loads(
        report(
            rank({"a.py": 1}),
            findings=[Finding(path="a.py", quote="x", claim="leaks", line=4)],
            checks=[Checked("no-print", Site("a.py", 4), Outcome.VIOLATED, evidence="print")],
        )
    )

    assert body["findings"][0]["provenance"] == Provenance.MODEL.value
    assert body["rule_checks"][0]["outcome"] == "violated"


def test_an_undecided_check_is_excluded_from_the_compliance_count() -> None:
    body = json.loads(
        report(
            rank({"a.py": 1}),
            checks=[
                Checked("r", Site("x.ts"), Outcome.UNCHECKABLE, why=Reason.LANGUAGE_UNSUPPORTED)
            ],
        )
    )

    row = body["rule_checks"][0]
    assert row["counts_toward_compliance"] is False
    assert row["undecided_because"] == "language_unsupported"


def test_the_schema_is_versioned_so_a_consumer_can_refuse() -> None:
    """A tool built on these keys outlives this file; unversioned it mis-reads silently."""
    assert json.loads(report(rank({"a.py": 1})))["schema"] == SCHEMA
