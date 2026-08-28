"""Apply one repository's declared rules to one file, and record what happened to each.

WHAT: `check(rule, path, source)` returns exactly one `Checked`; `check_all(rules, path, source)`
      returns one per rule. Never fewer, including for rules that found nothing.
WHY:  **A RULE THAT CANNOT BE CHECKED MUST NOT READ AS A RULE THAT PASSED.** Only Python is parsed
      here: `AGENTS.md` states plainly that tree-sitter is not a dependency and `pyproject.toml`
      declares `dependencies = []`. A JavaScript file therefore yields `UNCHECKABLE` with
      `LANGUAGE_UNSUPPORTED`, and a compliance rate computed over those rows would otherwise
      report a JS repository as fully compliant with checks that never ran. That is the clean zero
      this project has now found four times.

      **MODEL-JUDGED RULES ARE `DEFERRED`, NOT SKIPPED.** A parser did not decide them, and the row
      says so. Dropping them would make the audit trail quietly narrower than the standard it
      claims to enforce.

      **A VIOLATION CARRIES THE NAME AND THE LINE.** `Checked` refuses to be constructed without
      evidence for a reason: a developer who cannot find what fired cannot fix it, and a reviewer
      who cannot check it has to take our word.

      **EXACT MATCH ON DOTTED NAMES, NOT A SUBSTRING.** `subprocess.run` must not fire on
      `runner.run`. An import matches its target or anything beneath it, so forbidding `subprocess`
      also forbids `subprocess.run`, which is what somebody writing that rule means.
IMPORTS: parse.python_names, types.{change,checked,rule,verdict}. Leftward only.
CONSUMED BY: the audit trail and the compliance dashboard (D4, D5).
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from quantamind.parse.python_names import Mention, Names, UnparseableSource, names_in
from quantamind.types.change import Language, language_of
from quantamind.types.checked import Checked, Outcome
from quantamind.types.rule import CheckKind, Rule
from quantamind.types.verdict import Reason, Site


def _unchecked(rule: Rule, path: str, why: Reason) -> Checked:
    return Checked(rule.id, Site(path), Outcome.UNCHECKABLE, why=why)


def _violation(rule: Rule, path: str, hit: Mention) -> Checked:
    return Checked(
        rule.id,
        Site(path, hit.line),
        Outcome.VIOLATED,
        evidence=f"{hit.name} at line {hit.line}",
    )


def _forbidden_call(rule: Rule, names: Names) -> Mention | None:
    return next((m for m in names.calls if m.name == rule.target), None)


def _forbidden_import(rule: Rule, names: Names) -> Mention | None:
    beneath = rule.target + "."
    return next(
        (m for m in names.imports if m.name == rule.target or m.name.startswith(beneath)), None
    )


def _misnamed(rule: Rule, names: Names) -> Mention | None:
    """The first definition whose name does not match the required pattern."""
    pattern = re.compile(rule.target)
    return next((m for m in names.defined if not pattern.fullmatch(m.name)), None)


def check(rule: Rule, path: str, source: str) -> Checked:
    """One rule against one file. Exactly one row, whatever happened."""
    if rule.check is CheckKind.MODEL_JUDGED:
        return Checked(rule.id, Site(path), Outcome.DEFERRED)
    if language_of(path) is not Language.PYTHON:
        # **NOT A PASS.** The only parser here is Python's; every other language is undecided.
        return _unchecked(rule, path, Reason.LANGUAGE_UNSUPPORTED)
    try:
        names = names_in(source)
    except UnparseableSource:
        return _unchecked(rule, path, Reason.UNPARSEABLE_SYNTAX)

    try:
        finders = {
            CheckKind.FORBID_CALL: _forbidden_call,
            CheckKind.FORBID_IMPORT: _forbidden_import,
            CheckKind.NAMING_PATTERN: _misnamed,
        }
        hit = finders[rule.check](rule, names)
    except re.error:
        # A pattern that will not compile is a rule we cannot apply, not a file that passed it.
        return _unchecked(rule, path, Reason.MALFORMED_DECLARATION)
    return _violation(rule, path, hit) if hit else Checked(rule.id, Site(path), Outcome.PASSED)


def check_all(rules: Sequence[Rule], path: str, source: str) -> tuple[Checked, ...]:
    """One row per rule. **The count is the denominator of any compliance rate over this file.**"""
    return tuple(check(rule, path, source) for rule in rules)
