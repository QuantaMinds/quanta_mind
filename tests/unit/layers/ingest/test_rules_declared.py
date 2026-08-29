"""A declaration that cannot become a rule comes back named, never dropped.

WHAT: Feeds malformed and duplicate declarations through `ingest/rules_file.read()` and asserts on
      the refusals it returns.
WHY:  **SPLIT FROM `test_rules_file.py` AT THE 200-LINE CAP, AND IT IS A REAL SEAM.** That file
      asks WHERE rules come from — from git, at a commit, in a clone with no working tree. This one
      asks whether a declaration is VALID. They broke apart when reading moved to git.

      **SKIPPING WHAT WE DO NOT UNDERSTAND NARROWS WHAT A CUSTOMER BELIEVES IS ENFORCED**, and it
      does so invisibly, inside the artefact built to make enforcement visible.
IMPORTS: ingest.rules_file, types.{rule,verdict}.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.standards.rules_file import RULES_PATH, read
from quantamind.types.rule import CheckKind, Rule, RuleRefused, Severity
from quantamind.types.verdict import Reason

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


BAD = {
    "no description": 'id = "x"\nseverity = "high"\ncheck = "forbid_call"\ntarget = "y"',
    "unknown severity": 'id = "x"\ndescription = "d"\nseverity = "urgent"\n'
    'check = "forbid_call"\ntarget = "y"',
    "unknown check": 'id = "x"\ndescription = "d"\nseverity = "high"\n'
    'check = "vibes"\ntarget = "y"',
    "no target": 'id = "x"\ndescription = "d"\nseverity = "high"\ncheck = "forbid_call"',
}


def _write(root: Path, text: str) -> Path:
    """A real git repository — the reader goes to git, so a loose file would test nothing."""
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


@pytest.mark.parametrize("why", sorted(BAD))
def test_a_declaration_that_cannot_become_a_rule_comes_back_named(tmp_path: Path, why: str) -> None:
    rules, refused = read(_write(tmp_path / why.replace(" ", "-"), "[[rule]]\n" + BAD[why]), "HEAD")

    assert rules == (), f"{why}: enforced a rule we could not read"
    assert len(refused) == 1, f"{why}: the declaration was dropped silently instead of returned"
    assert refused[0].reason is Reason.MALFORMED_DECLARATION


def test_one_bad_declaration_does_not_take_the_good_ones_with_it(tmp_path: Path) -> None:
    rules, refused = read(_write(tmp_path, GOOD + '\n[[rule]]\nid = "broken"\n'), "HEAD")

    assert [r.id for r in rules] == ["no-console-log-in-prod", "async-error-handling"]
    assert len(refused) == 1 and refused[0].site.path == "broken"


def test_every_declaration_sharing_a_duplicated_id_is_refused_including_the_first(
    tmp_path: Path,
) -> None:
    """**THIS TEST ASSERTED FIRST-ONE-WINS, AND THIS PRODUCT'S OWN REVIEWER CAUGHT IT.**

    On the first real run of the deep half, against the commit that added this module, the model
    said: accepting the first rule and rejecting the rest "can be misleading if the rule
    definitions differ; all rules with a duplicated ID should be rejected to avoid ambiguity about
    which rule is being enforced." It was right, and it was arguing against a comment of mine that
    claimed the refusal existed to prevent exactly the ambiguity the code then produced.

    If two declarations share an id and differ, enforcing whichever appeared first is arbitrary,
    and the audit row names a rule the reader cannot identify. Keeping none cannot be wrong.
    """
    rules, refused = read(_write(tmp_path, GOOD + GOOD), "HEAD")

    assert rules == (), (
        f"a duplicated id was still enforced: {[r.id for r in rules]}. Which of the two "
        "declarations that is, nobody reading the audit trail can tell"
    )
    assert len(refused) == 2, "one refusal per duplicated id, naming it"
    assert {u.site.path for u in refused} == {"no-console-log-in-prod", "async-error-handling"}


def test_a_unique_id_alongside_a_duplicated_one_still_survives(tmp_path: Path) -> None:
    """Refusing the duplicates must not take the well-formed rules with them."""
    extra = GOOD.replace("no-console-log-in-prod", "unique-rule").replace(
        "async-error-handling", "other-unique"
    )
    rules, refused = read(_write(tmp_path, GOOD + GOOD + extra), "HEAD")

    assert {r.id for r in rules} == {"unique-rule", "other-unique"}
    assert len(refused) == 2


def test_a_rule_with_no_description_is_refused_at_construction() -> None:
    """The description is what the developer reads beside the violation. A slug is not a reason."""
    with pytest.raises(RuleRefused, match="cannot be acted on"):
        Rule(id="x", description="  ", severity=Severity.LOW, check=CheckKind.MODEL_JUDGED)
