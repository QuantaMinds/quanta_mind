"""D6c: whose data may cross which boundary, and the direction the default points.

WHAT: `ingest/context/egress.py` against real git repositories carrying real consent files.
WHY:  **"EGRESS IS A DECISION, NOT A DETAIL."** Quoting a private Slack thread into a pull request
      makes it visible to everyone who can read the repository, who are not the people who could
      read the channel. Every test here checks the DENY direction as hard as the grant, because the
      two mistakes do not cost the same.

      **A CONSENT FILE IS READ FROM GIT, NOT FROM DISK**, like every other file this product reads
      from a customer's repository — `serve/working_clone.ensure()` clones with `--no-checkout`, so
      a filesystem read finds nothing and would return "no consent" for everyone, forever. That is
      the safe direction here, which is exactly why it needs a test: a bug pointing the safe way is
      invisible until the day somebody grants a source and it does not take effect.
IMPORTS: quantamind.ingest.context.egress; stdlib subprocess, pathlib.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.ingest.context.egress import ALWAYS, Source, allowed, quotable


def _repo(root: Path, consent: str | None) -> str:
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    if consent is not None:
        (root / ".quantamind").mkdir()
        (root / ".quantamind" / "context.toml").write_text(consent, encoding="utf-8")
    (root / "app.py").write_text("x = 1\n", encoding="utf-8")
    for command in (
        ["git", "-C", str(root), "config", "user.email", "t@e.com"],
        ["git", "-C", str(root), "config", "user.name", "t"],
        ["git", "-C", str(root), "add", "-A"],
        ["git", "-C", str(root), "commit", "-qm", "one"],
    ):
        subprocess.run(command, check=True, timeout=30)
    done = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return done.stdout.strip()


def test_no_consent_file_grants_github_and_nothing_else(tmp_path: Path) -> None:
    """**THE DEFAULT, AND IT IS THE ONE THAT CANNOT LEAK.**"""
    clone = tmp_path / "repo"
    sha = _repo(clone, None)

    granted = allowed(clone, sha)
    assert granted == ALWAYS
    assert quotable(Source.GITHUB, granted) is True
    assert quotable(Source.JIRA, granted) is False
    assert quotable(Source.SLACK, granted) is False


def test_granting_jira_says_nothing_about_slack(tmp_path: Path) -> None:
    """**PER SOURCE.** One switch for "external context" would let a ticket title agree to a
    private channel."""
    clone = tmp_path / "repo"
    sha = _repo(clone, "[context]\nquote_jira = true\n")

    granted = allowed(clone, sha)
    assert quotable(Source.JIRA, granted) is True
    assert quotable(Source.SLACK, granted) is False, "granting Jira granted Slack"


def test_both_can_be_granted_together_when_both_are_named(tmp_path: Path) -> None:
    """The positive path must be reachable, or the tests above only prove nothing works."""
    clone = tmp_path / "repo"
    sha = _repo(clone, "[context]\nquote_jira = true\nquote_slack = true\n")

    granted = allowed(clone, sha)
    assert granted == frozenset({Source.GITHUB, Source.JIRA, Source.SLACK})


@pytest.mark.parametrize(
    "consent",
    [
        '[context]\nquote_slack = "yes"\n',
        "[context]\nquote_slack = 1\n",
        "[context]\nquote_slack = false\n",
        "[context]\nquote_everything = true\n",
        "[wrong_table]\nquote_slack = true\n",
        "this is not toml {{{\n",
        "",
    ],
    ids=[
        "string-yes",
        "number-one",
        "explicit-false",
        "wrong-key",
        "wrong-table",
        "broken",
        "empty",
    ],
)
def test_nothing_but_a_literal_true_grants_a_source(tmp_path: Path, consent: str) -> None:
    """**A TYPO MUST NOT OPEN AN EGRESS PATH.**

    A broken consent file is the absence of consent. This is the one place in the product where
    "we could not tell" and "no" are deliberately the same answer, because the cost of the two
    mistakes is not symmetric.
    """
    clone = tmp_path / "repo"
    sha = _repo(clone, consent)

    assert quotable(Source.SLACK, allowed(clone, sha)) is False


def test_github_needs_no_consent_and_cannot_be_revoked(tmp_path: Path) -> None:
    """The comment is posted to GitHub quoting GitHub. Nothing crosses a boundary."""
    clone = tmp_path / "repo"
    sha = _repo(clone, "[context]\nquote_github = false\n")

    assert quotable(Source.GITHUB, allowed(clone, sha)) is True
