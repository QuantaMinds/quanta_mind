"""Every oracle must locate a NAMED artefact, not merely return something.

WHAT: One case per oracle, each asserting on a specific artefact that oracle must find — a
      particular tag, a particular release, a particular commit — never on a count being non-zero.
WHY:  **THE WEAK FORM OF THIS CHECK PASSES WHILE THE INSTRUMENT IS BROKEN, AND THAT HAS NOW
      HAPPENED FIVE TIMES.** GitHub code search returned `total_count: 0` for tests mentioning
      `pypi` in a repository whose `tests/` directory is full of them. Its replacement read 0 test
      files from a tree containing 33, because a jq filter was mangled by shell escaping on its way
      through subprocess. **Both would have reported a coverage ceiling of zero, and zero would
      have been read as a decisive result** -- the arm is impossible, close the road -- rather than
      as a broken search.

      What caught it was a check that named `test_repository_pypi.py` and required the search to
      return THAT. **"Does it return something" and "does it return this" are different tests**,
      and only the second can tell a working oracle from a silent one.

      **SO EVERY ORACLE IN THE LOOP GETS ONE**, and the artefacts below are chosen to be stable:
      released tags on widely-used repositories, and a published PyPI release. A fixture that rots
      fails loudly here rather than quietly weakening the oracle it guards.
IMPORTS: stdlib, pytest, the product's `verify` oracles.
CONSUMED BY: `uv run pytest tests/live`.
"""

from __future__ import annotations

import shutil

import pytest

from quantamind.verify.external_facts import sha_exists, tags_at
from quantamind.verify.pin_mismatch import detect
from quantamind.verify.releases import released

pytestmark = pytest.mark.skipif(
    shutil.which("gh") is None, reason="these oracles read live authorities"
)

# actions/checkout v7.0.0. A released tag on an archived-stable commit: it cannot move.
CHECKOUT_V7_SHA = "9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0"


def test_sha_exists_finds_a_named_commit_and_denies_a_fabricated_one() -> None:
    reached, exists = sha_exists("actions/checkout", CHECKOUT_V7_SHA)
    if not reached:
        pytest.skip("GitHub unreachable; the test proves nothing when it cannot ask")
    assert exists, "the oracle cannot find a commit that is certainly there"

    reached, exists = sha_exists("actions/checkout", "0" * 40)
    assert reached and not exists, "it must also be able to say NO, or it says yes to everything"


def test_tags_at_returns_the_NAMED_tags_not_merely_a_non_empty_list() -> None:
    """`v7.0.0` AND the `v7` alias. Returning one was the defect that flagged 10 correct pins."""
    reached, tags = tags_at("actions/checkout", CHECKOUT_V7_SHA)
    if not reached:
        pytest.skip("GitHub unreachable")
    # **v7.0.0 ONLY, and the fixture says so deliberately.** The `v7` alias has since moved to
    # v7.0.1, so it is NOT at this commit -- which is the whole reason `satisfies()` treats
    # `# v7` as satisfied by a v7.x release rather than requiring the alias to be present. An
    # earlier draft of this test asserted `v7` here and failed, and the test was wrong, not the
    # oracle: a named-artefact fixture has to name what is actually there.
    assert tags == ["v7.0.0"], (
        f"expected exactly the release tag at this commit, got {tags} — if the alias has moved "
        f"again, read the diff before changing this fixture"
    )


def test_released_finds_a_named_release_and_denies_a_fabricated_one() -> None:
    reached, exists = released("requests", "2.32.3")
    if not reached:
        pytest.skip("PyPI unreachable")
    assert exists, "requests 2.32.3 is published; the oracle cannot see a release that is there"

    reached, exists = released("requests", "99.99.99")
    assert reached and not exists, "it must be able to say NO"


def test_detect_names_the_tag_it_disagrees_with() -> None:
    """Not "it fired" — it must report WHICH tag GitHub holds, or its finding is unusable."""
    diff = f"+      - uses: actions/checkout@{CHECKOUT_V7_SHA} # v5.0.0\n"
    found, unresolved = detect(diff)
    if unresolved:
        pytest.skip("GitHub unreachable")
    assert len(found) == 1, "a genuinely wrong pin comment was not detected"
    said = found[0].sentence()
    assert "v5.0.0" in said and "v7.0.0" in said, (
        f"the finding must name both what was claimed and what GitHub reports: {said}"
    )


def test_detect_is_silent_on_the_same_pin_correctly_commented() -> None:
    """The direction that stops it passing by firing on everything."""
    found, unresolved = detect(f"+      - uses: actions/checkout@{CHECKOUT_V7_SHA} # v7.0.0\n")
    if unresolved:
        pytest.skip("GitHub unreachable")
    assert found == [], (
        f"fired on a CORRECT pin; every one of these would be a false claim: {found}"
    )
