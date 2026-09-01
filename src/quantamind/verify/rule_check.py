"""Apply one repository's declared rules to one file, and record what happened to each.

WHAT: `check(rule, path, source)` returns exactly one `Checked`; `check_all(rules, path, source)`
      returns one per rule. Never fewer, including for rules that found nothing.
WHY:  **A RULE THAT CANNOT BE CHECKED MUST NOT READ AS A RULE THAT PASSED.** Only Python is
      PARSED here: `AGENTS.md` states plainly that tree-sitter is not a dependency and
      `pyproject.toml` declares `dependencies = []`. A JavaScript file therefore yields
      `UNCHECKABLE` with
      `LANGUAGE_UNSUPPORTED`, and a compliance rate computed over those rows would otherwise
      report a JS repository as fully compliant with checks that never ran. That is the clean zero
      this project has now found four times.

      **MODEL-JUDGED RULES ARE `DEFERRED`, NOT SKIPPED.** A parser did not decide them, and the row
      says so. Dropping them would make the audit trail quietly narrower than the standard it
      claims to enforce.

      **A VIOLATION CARRIES THE NAME AND THE LINE.** `Checked` refuses to be constructed without
      evidence for a reason: a developer who cannot find what fired cannot fix it, and a reviewer
      who cannot check it has to take our word.

      **`HARDCODED_SECRET` IS THE ONE KIND THAT IS NOT PYTHON-ONLY, AND THE SENTENCE ABOVE USED TO
      SAY OTHERWISE WITHOUT QUALIFICATION.** A credential is a string, not syntax, so it is found in
      a `.env`, a `.tf` or a CI workflow exactly as well as in a module — and those are the files
      that leak one most often, and the files the language gate refuses. It therefore dispatches
      BEFORE that gate. This is the first rule kind to widen the enforceable surface past `.py`,
      which `docs/product/unit-economics.md` names as the honest limit of the standards engine.

      **EXACT MATCH ON DOTTED NAMES, NOT A SUBSTRING.** `subprocess.run` must not fire on
      `runner.run`. An import matches its target or anything beneath it, so forbidding `subprocess`
      also forbids `subprocess.run`, which is what somebody writing that rule means.
IMPORTS: ingest.{blob,standards.rules_file}, parse.{python_names,secret_scan},
      store.rule_checks, types.{change,checked,rule,verdict}, and its sibling
      `verify.judged_rule` for the model half. Leftward only; nothing from `infer`.
CONSUMED BY: the audit trail and the compliance dashboard (D4, D5).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from quantamind.ingest.blob import at
from quantamind.ingest.standards import rules_file
from quantamind.parse.python_names import Mention, Names, UnparseableSource, names_in
from quantamind.parse.secret_scan import secrets_in
from quantamind.store.rule_checks import persist
from quantamind.types.change import Language, language_of
from quantamind.types.standards.checked import Checked, Outcome
from quantamind.types.standards.judged import Judged
from quantamind.types.standards.rule import CheckKind, Rule
from quantamind.types.verdict import Reason, Site
from quantamind.verify.judged_rule import Ask, judge_change


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
    # **THE SECRET CHECK RUNS BEFORE THE LANGUAGE GATE, AND THAT IS THE POINT OF IT.** Every other
    # kind needs an AST and is Python-only; a credential is a string, and the files that leak one
    # most often — `.env`, `.tf`, a CI workflow — are exactly the ones the gate below refuses.
    # This is the first rule kind that widens the enforceable surface past `.py`.
    if rule.check is CheckKind.HARDCODED_SECRET:
        found = secrets_in(source)
        if not found:
            return Checked(rule.id, Site(path), Outcome.PASSED)
        first = found[0]
        return Checked(rule.id, Site(path, first.line), Outcome.VIOLATED, evidence=first.render())
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
    # A rule that does not govern this path produces no row: there is no question to answer, and
    # a PASSED row would inflate the denominator with a pair nobody agreed to.
    return tuple(check(rule, path, source) for rule in rules if rule.applies_to(path))


def check_change(
    rules: Sequence[Rule], clone: Path, sha: str, paths: Sequence[str]
) -> tuple[Checked, ...]:
    """Every rule against every changed file, read AS THE CHANGE LEAVES IT.

    **A PATH THE CHANGE DELETED PRODUCES NO ROWS, AND THAT IS NOT A SKIP.** There is no code left
    for a standard to apply to, so there is no question to answer — unlike a file we could not
    parse, which IS a question we failed to answer and gets an `UNCHECKABLE` row. `ingest/blob.at`
    distinguishes the two: absent returns `None`, and anything else raises rather than pretending
    a broken clone is a repository full of deletions.

    **THE COST IS ONE `git show` PER CHANGED FILE AND NO MODEL CALL AT ALL.** That is the point of
    doing the deterministic half first: it is affordable on every pull request, and its verdicts
    are reproducible, which is what makes an audit row worth reading.
    """
    rows: list[Checked] = []
    for path in paths:
        source = at(clone, sha, path)
        if source is None:
            continue
        rows.extend(check_all(rules, path, source))
    return tuple(rows)


def enforce(
    clone: Path,
    sha: str,
    paths: Sequence[str],
    store: Path,
    repo: str,
    number: int,
    ask: Ask | None = None,
) -> tuple[tuple[Checked, ...], tuple[Judged, ...]]:
    """Read this repository's declared rules, check the change, and put the result on the record.

    **THE TWO HALVES COME BACK SEPARATELY BECAUSE THEY ARE NOT THE SAME KIND OF CLAIM.** The
    `Checked` rows are reproducible and go to the audit trail. The `Judged` records are a model's
    opinion, go only to the comment, and **are never persisted** — `persist` below is given the
    checks and nothing else. `ask=None` produces an empty second half and leaves the first
    byte-identical to what this returned before D1c.

    **APPLYING A STANDARD AND RECORDING THAT YOU APPLIED IT ARE ONE JOB.** Separating them is how a
    trail comes to hold fewer checks than ran: the second half is easy to forget at a call site and
    impossible to notice afterwards, because a missing row and a check that never happened look the
    same. Doing both here makes them fail together or not at all.

    **A REFUSED DECLARATION IS REPORTED, NOT DROPPED**, and a recording failure does not take the
    review with it — the comment is already worth posting whether or not the trail accepted it.
    """
    declared, unreadable = rules_file.read(clone, sha)
    if unreadable:
        print(f"[rules] {len(unreadable)} declaration(s) could not be read", flush=True)
    if not declared:
        return (), ()
    rows = check_change(declared, clone, sha, paths)
    landed = persist(store, repo, number, sha, rows, declared)
    if landed != len(rows):
        print(f"[rules] audit trail took {landed} of {len(rows)} check(s)", flush=True)
    # **THE JUDGED HALF IS NOT PASSED TO `persist`, AND THAT IS THE WHOLE DESIGN.** A model's
    # opinion does not enter the audit trail or the compliance rate; it travels to the comment
    # and stops there. See `types/judged.py`.
    judged = judge_change(declared, clone, sha, paths, ask)
    return rows, judged
