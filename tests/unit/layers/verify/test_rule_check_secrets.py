"""The secret rule as a `CheckKind`, and the language gate it is the first to pass.

WHAT: Drives `verify.rule_check.check()` with `CheckKind.HARDCODED_SECRET` over files in several
      languages, and pins that it reaches the audit trail as a PARSER verdict.
WHY:  **EVERY OTHER RULE KIND IS PYTHON-ONLY, AND THE FILES THAT LEAK A CREDENTIAL USUALLY ARE
      NOT.** `.env`, `.tf`, a CI workflow and a `.ts` config are exactly the files
      `LANGUAGE_UNSUPPORTED` refuses, and exactly where a key ends up. This kind therefore
      dispatches BEFORE the language gate — the first widening of the enforceable surface past
      `.py`, which `docs/product/unit-economics.md` names as the honest limit of the engine.

      **IT MUST BE A PARSER VERDICT OR IT CANNOT BLOCK.** `verify/blocking.py` gates the status
      check on `Provenance.PARSER`, so a secret rule that derived `MODEL` would be recorded,
      rendered, and unable to stop the merge it exists to stop.

      **AND IT NEEDS NO TARGET.** The other three kinds ask "is this identifier here" and are
      refused without one; this asks "does any line look like an issued credential", so `Rule`
      must not demand a target it would have nothing to do with.
IMPORTS: quantamind.types.standards.{rule,checked}, quantamind.verify.rule_check.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.types.standards.checked import Outcome
from quantamind.types.standards.rule import CheckKind, Rule, Severity
from quantamind.types.verdict import Provenance, Reason

SECRET_RULE = Rule(
    id="no-hardcoded-secrets",
    description="Credentials belong in the environment, never in the repository.",
    severity=Severity.HIGH,
    check=CheckKind.HARDCODED_SECRET,
)
# Assembled, never spelled: GitHub's push protection rejects a file containing a real-shaped key,
# which is the correct behaviour and the reason a detector's fixtures must be built at runtime.
LEAK = 'AWS_SECRET_ACCESS_KEY = "' + "AKIA" + 'IOSFODNN7EXAMPLE"\n'


def _check(path: str, source: str) -> object:
    from quantamind.verify.rule_check import check

    return check(SECRET_RULE, path, source)


@pytest.mark.parametrize(
    "path", [".env", "deploy/main.tf", ".github/workflows/ci.yml", "app.ts", "config.json"]
)
def test_a_credential_is_caught_in_files_no_other_rule_can_read(path: str) -> None:
    """**THE POINT OF THE WHOLE KIND.** Every other rule returns LANGUAGE_UNSUPPORTED here."""
    got = _check(path, LEAK)

    assert got.outcome is Outcome.VIOLATED
    assert "AWS access key" in got.evidence


def test_a_python_file_with_no_credential_passes() -> None:
    got = _check("src/app.py", "import os\nKEY = os.environ['K']\n")

    assert got.outcome is Outcome.PASSED
    assert got.why is None


def test_a_non_python_file_with_no_credential_passes_rather_than_being_unchecked() -> None:
    """**NOT `UNCHECKABLE`.** We really did read this file and really did decide; reporting it as
    undecided would understate coverage exactly where this kind adds it."""
    got = _check("deploy/main.tf", 'variable "region" { default = "us-east-1" }\n')

    assert got.outcome is Outcome.PASSED


def test_another_rule_kind_still_refuses_the_same_non_python_file() -> None:
    """The contrast that makes the widening real, asserted rather than described."""
    from quantamind.verify.rule_check import check

    other = Rule(
        id="no-print",
        description="Use the logger.",
        severity=Severity.LOW,
        check=CheckKind.FORBID_CALL,
        target="print",
    )
    got = check(other, "app.ts", LEAK)

    assert got.outcome is Outcome.UNCHECKABLE
    assert got.why is Reason.LANGUAGE_UNSUPPORTED


def test_the_verdict_is_a_parser_verdict_so_it_can_block() -> None:
    """`verify/blocking.py` gates on `Provenance.PARSER`. A secret rule deriving MODEL would be
    recorded, rendered, and unable to stop the merge it exists to stop."""
    assert SECRET_RULE.provenance is Provenance.PARSER
    assert SECRET_RULE.reproducible is True


def test_the_rule_needs_no_target() -> None:
    """The other kinds are refused without one. This asks a question that has no target."""
    assert SECRET_RULE.target == ""


def test_the_violation_carries_a_line_a_developer_can_open() -> None:
    got = _check(".env", "CLEAN=1\n" + LEAK)

    assert got.site.line == 2
    body = "AKIA" + "IOSFODNN7EXAMPLE"

    assert body not in got.evidence, "the secret must not reach the audit row"
