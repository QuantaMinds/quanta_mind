"""A committer identity for every test that builds a real git repository.

WHAT: An autouse session fixture setting `GIT_AUTHOR_*` and `GIT_COMMITTER_*`, so any
      test that commits does so without consulting the machine's global git config.
WHY:  Several tests build real repositories and commit to them, because asserting on a
      faked history would test the fake. Those commits were taking their identity from
      whatever `git config --global` happened to hold, which every developer machine has
      and a fresh CI runner does not. `test_merge_commit_resolves_to_first_parent` passed
      locally for everyone and failed on CI with "empty ident name".

      That is a test whose result depended on ambient state it never declared. The
      environment variables are set here rather than per-fixture so a new repo-building
      test cannot forget them and re-acquire the same hidden dependency --
      `tests/pipeline/conftest.py` configures its own repo, and the tests outside that
      directory had nothing.
IMPORTS: pytest, monkeypatch.
CONSUMED BY: every test under research/phase0/tests; autouse, so nothing requests it.
"""

from __future__ import annotations

import pytest

IDENTITY = {
    "GIT_AUTHOR_NAME": "phase0 tests",
    "GIT_AUTHOR_EMAIL": "tests@phase0.invalid",
    "GIT_COMMITTER_NAME": "phase0 tests",
    "GIT_COMMITTER_EMAIL": "tests@phase0.invalid",
}


@pytest.fixture(autouse=True, scope="session")
def _git_identity() -> object:
    """Set the identity for the session, undoing it afterwards.

    `.invalid` is the reserved TLD from RFC 2606: it can never resolve, so an address
    escaping into a fixture's committed history cannot name a real person.
    """
    patcher = pytest.MonkeyPatch()
    for name, value in IDENTITY.items():
        patcher.setenv(name, value)
    yield None
    patcher.undo()
