"""The standards a repository declares for itself, read from its own tree.

WHAT: `read(clone)` returns `(rules, refused)` — every well-formed rule in `.quantamind/rules.toml`
      and a typed `Unresolved` for every declaration that could not become one.
WHY:  **NO FILE AND A BROKEN FILE MUST NOT PRODUCE THE SAME ANSWER.** A repository with no rules
      has declared none; a repository whose file will not parse has declared some and we cannot
      read them. Both yield zero enforceable rules, and treating them alike would report a
      customer as fully compliant at the exact moment their standards stopped being checked. The
      first returns no refusals; the second returns one naming the file.

      **A MALFORMED RULE IS RETURNED, NOT SKIPPED.** Dropping the entries we do not understand
      would silently narrow what a customer believes is enforced, and the narrowing would be
      invisible in precisely the artefact — the audit trail — that exists to make it visible.
      Every rejected declaration comes back as `Unresolved(site, reason, construct)`, which is the
      same shape the resolver layer uses for a call site it cannot place.

      **`tomllib`, NOT YAML.** It is stdlib on 3.11+, so this costs no dependency, and rule 11
      bans `pyyaml` from `src/` outright. TOML also has no significant whitespace and no
      surprising type coercion, which for a file a customer hand-edits is worth more than the
      terseness YAML buys.

      **THE PATH IS FIXED AND NOT CONFIGURABLE.** A rules file that could live anywhere is a rules
      file an auditor has to be told the location of, and a second place for it is a second place
      to disagree with the first.
IMPORTS: stdlib (pathlib, tomllib), `ingest.blob` to read from git, `types.{rule,verdict}`.
CONSUMED BY: the checks that enforce these (D1b in docs/plans/product/product-build.md).
"""

from __future__ import annotations

import tomllib
from collections import Counter
from pathlib import Path

from quantamind.ingest.blob import BlobUnreadable, at
from quantamind.types.rule import CheckKind, Rule, RuleRefused, Severity
from quantamind.types.verdict import Construct, Reason, Site, Unresolved

RULES_PATH = Path(".quantamind") / "rules.toml"
TABLE = "rule"


def _refusal(where: str, reason: Reason) -> Unresolved:
    return Unresolved(site=Site(where), reason=reason, construct=Construct.FILE)


def _one(entry: object, index: int, where: str) -> tuple[Rule | None, Unresolved | None]:
    """One declaration into a rule, or a refusal naming where it was. Never both, never neither."""
    if not isinstance(entry, dict):
        return None, _refusal(f"{where}[{index}]", Reason.MALFORMED_DECLARATION)
    try:
        return (
            Rule(
                id=str(entry.get("id", "")),
                description=str(entry.get("description", "")),
                severity=Severity(str(entry.get("severity", "")).lower()),
                check=CheckKind(str(entry.get("check", "")).lower()),
                target=str(entry.get("target", "")),
                paths=tuple(str(p) for p in entry.get("paths", []) if str(p).strip()),
            ),
            None,
        )
    except (RuleRefused, ValueError):
        # ValueError covers an unknown Severity or CheckKind: a member we do not have is a rule
        # we cannot enforce, and enforcing a DIFFERENT one because it looked close is worse.
        named = str(entry.get("id", "")) or f"{where}[{index}]"
        return None, _refusal(named, Reason.MALFORMED_DECLARATION)


def read(clone: Path, sha: str = "HEAD") -> tuple[tuple[Rule, ...], tuple[Unresolved, ...]]:
    """Every rule this repository declares at `sha`, and every declaration that could not be read.

    **READ FROM GIT, NOT FROM THE WORKING TREE, BECAUSE THERE IS NO WORKING TREE.**
    `serve/working_clone.ensure()` clones with `--no-checkout`, so the customer's files exist only
    as objects. This read the filesystem, found nothing, and returned "no rules declared" — for
    EVERY repository, forever, indistinguishable from one that had declared none. The module's
    whole argument is that those two answers must differ, and it was defeated by looking in a
    directory that has no files in it. Caught before a delivery, by asking what the clone actually
    contains rather than assuming a checkout.

    **AND AT THE COMMIT UNDER REVIEW, NOT AT THE DEFAULT BRANCH.** A pull request that ADDS or
    changes a rule must be checked against the rule as it stands in that change, or the first
    review of a new standard would silently apply the old one.
    """
    where = str(RULES_PATH)
    try:
        raw = at(clone, sha, RULES_PATH.as_posix())
    except BlobUnreadable:
        # **A CLONE WE CANNOT READ IS NOT A REPOSITORY WITH NO RULES.** That is the same confusion
        # this module exists to prevent, one level up: git failing and a customer declaring nothing
        # would otherwise produce the same answer, and the compliance view would show a clean sheet.
        return (), (_refusal(where, Reason.UNPARSEABLE_SYNTAX),)
    if raw is None:
        return (), ()
    try:
        document = tomllib.loads(raw)
    except (tomllib.TOMLDecodeError, ValueError):
        return (), (_refusal(where, Reason.UNPARSEABLE_SYNTAX),)

    declared = document.get(TABLE, [])
    if not isinstance(declared, list):
        return (), (_refusal(where, Reason.MALFORMED_DECLARATION),)

    parsed: list[Rule] = []
    refused: list[Unresolved] = []
    for index, entry in enumerate(declared):
        rule, refusal = _one(entry, index, where)
        if refusal is not None:
            refused.append(refusal)
            continue
        assert rule is not None  # _one returns exactly one of the two; mypy cannot see it
        parsed.append(rule)

    # **EVERY DECLARATION SHARING A DUPLICATED ID IS REFUSED, INCLUDING THE FIRST.** This kept the
    # first and rejected the rest, which is the same ambiguity the refusal exists to prevent: if
    # two declarations share an id and differ, enforcing whichever appeared first is arbitrary, and
    # the audit row would name a rule the reader cannot identify. Keeping none is the only answer
    # that cannot be wrong. Found by this product's own deep review on its first real run, against
    # a comment of mine that asserted the property the code did not have.
    counts = Counter(rule.id for rule in parsed)
    rules = [rule for rule in parsed if counts[rule.id] == 1]
    refused.extend(
        _refusal(rule_id, Reason.MALFORMED_DECLARATION)
        for rule_id in sorted(counts)
        if counts[rule_id] > 1
    )
    return tuple(rules), tuple(refused)
