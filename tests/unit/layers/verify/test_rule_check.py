"""A rule that could not be checked must never read as a rule that passed.

WHAT: Runs `verify/rule_check.check()` over REAL source strings — Python that violates, Python that
      does not, Python that will not parse, and a language we have no parser for.
WHY:  **THIS IS THE CLEAN-ZERO FAILURE IN ITS NEWEST COSTUME.** Only Python is parsed, because
      `AGENTS.md` states tree-sitter is not a dependency. If a JavaScript file returned "no
      violations found", a compliance rate over a JS repository would read 100% while nothing was
      ever checked — and the dashboard would be reporting our parser coverage as the customer's
      code quality.

      **AND THE DENOMINATOR IS ASSERTED, NOT THE NUMERATOR.** Tests that only check violations get
      caught fire to leave the "how many did we actually decide" question to whoever reads the
      percentage later.
IMPORTS: types.{checked,rule,verdict}, verify.rule_check.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.types.checked import Checked, Outcome
from quantamind.types.rule import CheckKind, Rule, Severity
from quantamind.types.verdict import Reason, Site
from quantamind.verify.rule_check import check, check_all

NO_SUBPROCESS = Rule(
    id="no-subprocess-run",
    description="Shelling out bypasses the timeout policy every call site is required to carry.",
    severity=Severity.HIGH,
    check=CheckKind.FORBID_CALL,
    target="subprocess.run",
)
NO_PICKLE = Rule(
    id="no-pickle",
    description="Deserialising pickle from any untrusted source is remote code execution.",
    severity=Severity.HIGH,
    check=CheckKind.FORBID_IMPORT,
    target="pickle",
)
JUDGED = Rule(
    id="async-error-handling",
    description="An awaited call with no handler fails silently.",
    severity=Severity.MEDIUM,
    check=CheckKind.MODEL_JUDGED,
)


def test_a_forbidden_call_is_caught_and_points_at_the_line() -> None:
    source = "import subprocess\n\n\ndef go():\n    return subprocess.run(['ls'])\n"

    row = check(NO_SUBPROCESS, "src/a.py", source)

    assert row.outcome is Outcome.VIOLATED
    assert row.site.line == 5, f"the violation points at line {row.site.line}, not the call site"
    assert "subprocess.run" in row.evidence


def test_a_similar_name_does_not_fire_the_rule() -> None:
    """`runner.run` is not `subprocess.run`. A substring match here would be a false accusation."""
    source = "def go(runner):\n    return runner.run()\n"

    assert check(NO_SUBPROCESS, "src/a.py", source).outcome is Outcome.PASSED


def test_a_forbidden_import_covers_everything_beneath_it() -> None:
    beneath = check(NO_PICKLE, "src/a.py", "from pickle import loads\n")
    exact = check(NO_PICKLE, "src/b.py", "import pickle\n")
    unrelated = check(NO_PICKLE, "src/c.py", "import pickletools_lookalike\n")

    assert beneath.outcome is Outcome.VIOLATED, "forbidding a module must forbid what is under it"
    assert exact.outcome is Outcome.VIOLATED
    assert unrelated.outcome is Outcome.PASSED, "a name that merely starts the same is not a match"


def test_a_language_we_cannot_parse_is_uncheckable_and_never_a_pass() -> None:
    """**THE ONE THAT MATTERS.** Reporting a JS repository as compliant with checks that never ran
    would make the dashboard a picture of our parser coverage, not of their code."""
    row = check(NO_SUBPROCESS, "src/app.ts", "subprocess.run('rm -rf /')\n")

    assert row.outcome is not Outcome.PASSED, (
        "a TypeScript file was reported as passing a Python-only check. Every rule would read as "
        "satisfied on a repository we cannot parse at all"
    )
    assert row.outcome is Outcome.UNCHECKABLE
    assert row.why is Reason.LANGUAGE_UNSUPPORTED
    assert row.counts_toward_compliance is False


def test_python_that_will_not_parse_is_uncheckable_and_never_a_pass() -> None:
    row = check(NO_SUBPROCESS, "src/broken.py", "def go(:\n")

    assert row.outcome is Outcome.UNCHECKABLE
    assert row.why is Reason.UNPARSEABLE_SYNTAX
    assert row.counts_toward_compliance is False


def test_a_model_judged_rule_is_deferred_rather_than_skipped() -> None:
    row = check(JUDGED, "src/a.py", "async def go():\n    await thing()\n")

    assert row.outcome is Outcome.DEFERRED, "a parser did not decide it, and the row must say so"
    assert row.counts_toward_compliance is False


def test_every_rule_produces_exactly_one_row() -> None:
    """The count is the denominator of any compliance rate over this file."""
    rows = check_all([NO_SUBPROCESS, NO_PICKLE, JUDGED], "src/a.py", "import pickle\n")

    assert len(rows) == 3, f"{len(rows)} rows for 3 rules — the denominator is not observable"
    assert {r.rule_id for r in rows} == {"no-subprocess-run", "no-pickle", "async-error-handling"}
    assert sum(r.counts_toward_compliance for r in rows) == 2, "the deferred row is not decidable"


def test_a_violation_without_evidence_cannot_be_constructed() -> None:
    with pytest.raises(ValueError, match="accusation"):
        Checked("r", Site("a.py", 3), Outcome.VIOLATED)


def test_an_unchecked_row_without_a_reason_cannot_be_constructed() -> None:
    with pytest.raises(ValueError, match="indistinguishable from one that passed"):
        Checked("r", Site("a.py"), Outcome.UNCHECKABLE)
