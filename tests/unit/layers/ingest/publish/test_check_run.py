"""C2: what may be written onto somebody's diff, and what may never be.

WHAT: `ingest/publish/check_run.py` — the annotations, the severity mapping, the cap, and the
      rehearsal contract.
WHY:  **AN ANNOTATION IS RENDERED BY GITHUB AS A FACT AGAINST A LINE.** There is no room for "we
      think" on a diff, and our raw model findings measure 66.7-82.1% wrong across four blind
      pools. The surface where being wrong is loudest gets only the reproducible half, and the
      tests below are what make that true rather than intended.

      **AND IT IS NOT THE COMMIT STATUS D1f BUILT.** That posts one line with one state and no
      location. Ticking C2 on it would have counted one build twice.
IMPORTS: quantamind.ingest.publish.check_run, quantamind.types.standards.*, types.verdict.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

from quantamind.ingest.publish.check_run import MAX_ANNOTATIONS, inline, publish, summary
from quantamind.types.standards.checked import Checked, Outcome
from quantamind.types.standards.rule import CheckKind, Rule, Severity
from quantamind.types.verdict import Reason, Site

HIGH = Rule("no-eval", "eval turns data into code.", Severity.HIGH, CheckKind.FORBID_CALL, "eval")
MED = Rule("no-print", "Use the logger.", Severity.MEDIUM, CheckKind.FORBID_CALL, "print")
LOW = Rule("naming", "Name things well.", Severity.LOW, CheckKind.NAMING_PATTERN, "^[a-z_]+$")
JUDGED = Rule("prose", "Explain why.", Severity.HIGH, CheckKind.MODEL_JUDGED)
RULES = [HIGH, MED, LOW, JUDGED]


def _violation(rule_id: str, path: str = "src/a.py", line: int = 7) -> Checked:
    return Checked(
        rule_id, Site(path, line), Outcome.VIOLATED, evidence=f"{rule_id} at line {line}"
    )


def test_a_violation_becomes_an_annotation_at_its_line() -> None:
    """**THE POINT OF THE ROW.** A status says pass or fail; this says where."""
    shown, dropped = inline([_violation("no-eval")], RULES)

    assert dropped == 0
    assert len(shown) == 1
    assert shown[0]["path"] == "src/a.py"
    assert shown[0]["start_line"] == 7
    assert shown[0]["end_line"] == 7
    assert shown[0]["title"] == "no-eval"
    assert "no-eval at line 7" in str(shown[0]["message"])


def test_the_customers_severity_decides_the_level() -> None:
    """**NOT OURS.** Deciding which of a team's standards blocks a merge would override the
    judgement the standards file exists to record."""
    shown, _ = inline([_violation("no-eval"), _violation("no-print"), _violation("naming")], RULES)
    levels = {a["title"]: a["annotation_level"] for a in shown}

    assert levels == {"no-eval": "failure", "no-print": "warning", "naming": "notice"}


def test_a_deferred_model_judged_row_is_never_annotated() -> None:
    """**A MODEL VERDICT MUST NOT REACH A DIFF.** D1c keeps model-judged rules at DEFERRED, and
    this is the surface where that mattering is easiest to break."""
    deferred = Checked("prose", Site("src/a.py", 3), Outcome.DEFERRED)
    assert inline([deferred], RULES) == ([], 0)


def test_passed_and_uncheckable_are_never_annotated() -> None:
    """`PASSED` on every line trains a reviewer to dismiss the column; `UNCHECKABLE` is a statement
    about OUR coverage, not about their code."""
    rows = [
        Checked("no-eval", Site("src/a.py"), Outcome.PASSED),
        Checked("no-eval", Site("web/x.ts"), Outcome.UNCHECKABLE, why=Reason.LANGUAGE_UNSUPPORTED),
    ]
    assert inline(rows, RULES) == ([], 0)


def test_a_rule_we_cannot_find_is_skipped_not_given_a_default_level() -> None:
    """Inventing a severity would put a level on somebody's diff that nobody chose."""
    assert inline([_violation("a-rule-not-declared")], RULES) == ([], 0)


def test_the_cap_is_enforced_and_the_overflow_is_counted() -> None:
    """**A TRUNCATED LIST THAT DOES NOT SAY SO READS AS A COMPLETE ONE.**"""
    many = [_violation("no-eval", line=n + 1) for n in range(MAX_ANNOTATIONS + 12)]
    shown, dropped = inline(many, RULES)

    assert len(shown) == MAX_ANNOTATIONS
    assert dropped == 12
    assert f"{dropped} more are not shown" in summary(len(shown), dropped, 60)


def test_the_summary_names_the_denominator_and_the_parser_only_rule() -> None:
    """The reader must see what was checked, and that nothing a model said is on their diff."""
    text = summary(2, 0, 40)
    assert "40 decided check(s)" in text
    assert "nothing a model judged is annotated" in text


def test_a_clean_run_still_says_what_it_checked() -> None:
    """**AN EMPTY RESULT IS A DOCUMENT.** "No violations" over no denominator is a boast."""
    text = summary(0, 0, 31)
    assert "31 check(s) decided" in text
    assert "No violations" in text


def test_rehearsal_writes_nothing_and_reports_the_conclusion() -> None:
    """**`POSTING_ENABLED=0` REHEARSES**, the same contract as everywhere else in the product."""
    said = publish("acme/app", "a" * 40, [_violation("no-eval")], RULES, enabled=False)

    assert "rehearsed" in said
    assert "would be failure" in said


def test_only_a_high_severity_violation_fails_the_check() -> None:
    """A warning that failed the build would make every `LOW` rule a merge blocker."""
    assert "would be success" in publish("a/b", "s", [_violation("no-print")], RULES, enabled=False)
    assert "would be failure" in publish("a/b", "s", [_violation("no-eval")], RULES, enabled=False)
