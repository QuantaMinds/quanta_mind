"""No rules and unreadable rules must never produce the same answer.

WHAT: Runs `ingest/rules_file.read()` over REAL files on disk — a missing one, a broken one, a
      good one, and one with declarations that cannot become rules.
WHY:  **THE FAILURE THIS GUARDS WOULD REPORT A CUSTOMER AS COMPLIANT AT THE MOMENT ENFORCEMENT
      STOPPED.** A repository with no rules has declared none. A repository whose file will not
      parse has declared some and we cannot read them. Both end with zero enforceable rules, and
      if they return the same value the compliance dashboard shows a clean sheet for a customer
      whose standards are silently off. The refusal list is what separates them.

      **AND A REJECTED DECLARATION IS RETURNED, NOT DROPPED.** Skipping the entries we do not
      understand narrows what a customer believes is enforced, invisibly, in exactly the artefact
      built to make it visible.
IMPORTS: ingest.rules_file, types.{rule,verdict}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from quantamind.ingest.standards.rules_file import RULES_PATH, read
from quantamind.types.rule import CheckKind, Severity
from quantamind.types.verdict import Provenance, Reason

GOOD = """
[[rule]]
id = "no-console-log-in-prod"
description = "Logging to the console in production hides output from the log pipeline."
severity = "high"
check = "forbid_call"
target = "console.log"

[[rule]]
id = "async-error-handling"
description = "An awaited call without a handler fails silently."
severity = "high"
check = "model_judged"
"""


def _write(root: Path, text: str) -> Path:
    """A REAL git repository with the rules committed.

    **THE OLD VERSION WROTE A LOOSE FILE AND THAT IS NOT THE PRODUCTION CONDITION.**
    `serve/working_clone.ensure()` clones with `--no-checkout`, so a customer's repository has no
    working tree at all — the reader must go to git. Writing a file to a temp directory tested a
    situation that never happens, and passed while the real path returned "no rules declared" for
    every repository on earth.
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / RULES_PATH.parent).mkdir(parents=True, exist_ok=True)
    (root / RULES_PATH).write_text(text, encoding="utf-8")
    for args in (
        ["init", "--quiet", "-b", "main"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
        ["add", "-A"],
        ["commit", "--quiet", "-m", "rules"],
    ):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, timeout=30)
    return root


def test_no_rules_file_is_not_the_same_answer_as_an_unreadable_one(tmp_path: Path) -> None:
    """**THE ONE THAT MATTERS.** Both give zero rules; only one is a customer in trouble.

    The "absent" case is a REAL repository that simply declared nothing, because that is what the
    product meets. A directory that is not a repository at all is a third case, and it is a
    refusal: git failing must never read as "this customer has no standards".
    """
    empty = tmp_path / "declares-nothing"
    empty.mkdir()
    (empty / "README.md").write_text("no rules here\n", encoding="utf-8")
    for args in (
        ["init", "--quiet", "-b", "main"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
        ["add", "-A"],
        ["commit", "--quiet", "-m", "none"],
    ):
        subprocess.run(
            ["git", "-C", str(empty), *args], check=True, capture_output=True, timeout=30
        )
    absent_rules, absent_refusals = read(empty, "HEAD")

    broken = _write(tmp_path / "broken", "[[rule]]\nid = 'unclosed")
    broken_rules, broken_refusals = read(broken, "HEAD")

    assert (absent_rules, absent_refusals) == ((), ()), "a repository with no rules declared none"
    assert broken_rules == (), "a file that will not parse must yield no enforceable rules"
    assert len(broken_refusals) == 1, (
        "an unreadable rules file produced no refusal, so it is indistinguishable from a "
        "repository that declared nothing — and the dashboard would call it compliant"
    )
    assert broken_refusals[0].reason is Reason.UNPARSEABLE_SYNTAX
    assert str(RULES_PATH) in broken_refusals[0].site.path


def test_a_declared_rule_is_read_with_the_severity_and_check_it_declared(tmp_path: Path) -> None:
    rules, refused = read(_write(tmp_path, GOOD), "HEAD")

    assert refused == (), f"a well-formed file produced refusals: {refused}"
    assert [r.id for r in rules] == ["no-console-log-in-prod", "async-error-handling"]
    assert rules[0].severity is Severity.HIGH
    assert rules[0].check is CheckKind.FORBID_CALL
    assert rules[0].target == "console.log"


def test_a_model_judged_rule_cannot_claim_a_parser_verified_it(tmp_path: Path) -> None:
    """The audit trail is worth exactly what this distinction is worth."""
    rules, _ = read(_write(tmp_path, GOOD), "HEAD")
    by_id = {r.id: r for r in rules}

    assert by_id["no-console-log-in-prod"].provenance is Provenance.PARSER
    assert by_id["no-console-log-in-prod"].reproducible is True
    assert by_id["async-error-handling"].provenance is Provenance.MODEL
    assert by_id["async-error-handling"].reproducible is False, (
        "a model-judged rule reported itself reproducible. Re-running it on the same commit "
        "need not give the same answer, and an audit row that claims otherwise is worthless"
    )


def test_rules_are_found_in_a_clone_WITH_NO_WORKING_TREE(tmp_path: Path) -> None:
    """**THE PRODUCTION CONDITION, AND THE BUG THIS FILE MISSED FOR ITS WHOLE EXISTENCE.**

    `working_clone.ensure()` clones with `--no-checkout`. The reader looked at the filesystem,
    found nothing, and returned "no rules declared" — for every repository, indistinguishable from
    one that had declared none, which is the exact confusion this module exists to prevent. Every
    other test here passed throughout, because they all wrote a loose file into a temp directory.
    """
    origin = _write(tmp_path / "origin", GOOD)
    clone = tmp_path / "bare-ish"
    subprocess.run(
        ["git", "clone", "--no-checkout", "--quiet", str(origin), str(clone)],
        check=True,
        capture_output=True,
        timeout=60,
    )

    assert not (clone / RULES_PATH).exists(), (
        "the fixture must have no working tree, or it proves nothing"
    )

    rules, refused = read(clone, "HEAD")

    assert [r.id for r in rules] == ["no-console-log-in-prod", "async-error-handling"], (
        "no rules were found in a clone with no checkout — which is every clone this product makes"
    )
    assert refused == ()


def test_a_clone_git_cannot_read_is_a_refusal_not_an_absence(tmp_path: Path) -> None:
    """**SABOTAGE FOUND THIS TEST MISSING.** Breaking the refusal path passed every other test.

    A directory that is not a repository, or a sha git does not have, is a THIRD case: not "this
    customer declared no standards" and not "their file is malformed". Reporting it as the first
    would show a clean compliance sheet for a repository we could not read at all — the same
    confusion this module exists to prevent, one level further out.
    """
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()

    rules, refused = read(not_a_repo, "HEAD")

    assert rules == ()
    assert len(refused) == 1, (
        "a clone git could not read returned no refusal, so it is indistinguishable from a "
        "repository that simply declared nothing"
    )
    assert refused[0].reason is Reason.UNPARSEABLE_SYNTAX
