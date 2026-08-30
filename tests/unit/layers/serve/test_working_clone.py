"""The repository name arrives from the network, so the path built from it is checked.

WHAT: Feeds `path_for` the shapes a hostile or malformed payload would carry, and requires a
      refusal rather than a path outside the root. Also proves `sweep` returns what it removed.
WHY:  **THE NAME IS AUTHENTICATED BY HMAC, WHICH IS NOT THE SAME AS WELL-FORMED.** A signature
      proves who sent the payload, not that `repo` is `owner/name`. A path assembled from it
      without a check is the kind of defect only ever noticed afterwards, and it would be reached
      by anyone holding the webhook secret -- including a compromised integration.

      **`sweep` IS TESTED FOR ITS RETURN VALUE, NOT FOR NOT RAISING.** Its predecessor in this
      project claimed in a comment that a leftover was caught on the next attempt; nothing checked,
      and 1.6 GB accumulated. A cleanup asserted rather than counted is rule 14's example.
IMPORTS: stdlib, pytest, quantamind.serve.working_clone.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.serve.working_clone import CloneFailed, path_for, sweep

HOSTILE = [
    "../../etc",
    "owner/../../etc",
    "../owner/name",
    "owner/name/extra",
    "owner",
    "",
    "/name",
    "owner/",
    "-upload-pack=touch/name",
    "owner/-x",
]


@pytest.mark.parametrize("repo", HOSTILE)
def test_refuses_anything_that_is_not_owner_slash_name(repo: str) -> None:
    with pytest.raises(CloneFailed):
        path_for(repo, Path("/tmp/root"))


def test_a_good_name_stays_under_the_root() -> None:
    """The control. Without it the check could pass by refusing everything."""
    where = path_for("calcom/cal.com", Path("/tmp/root"))
    assert where == Path("/tmp/root/calcom/cal.com")
    assert Path("/tmp/root") in where.parents


def test_sweep_returns_how_many_it_removed(tmp_path: Path) -> None:
    for i in range(5):
        (tmp_path / "owner" / f"repo{i}" / ".git").mkdir(parents=True)
    removed = sweep(tmp_path, keep=2)
    assert removed == 3, "the count must be the number actually deleted"
    left = [p for p in (tmp_path / "owner").iterdir() if (p / ".git").is_dir()]
    assert len(left) == 2, "sweep reported 3 removed; the filesystem must agree"


def test_sweep_on_a_missing_root_is_zero_not_an_error(tmp_path: Path) -> None:
    assert sweep(tmp_path / "never-created") == 0


# **`DEFAULT_KEEP` WAS FREELY MUTABLE.** The test above passes `keep=2`, so the shipped default
# was never exercised: setting it to 0 deletes every clone on the next sweep and setting it to 17
# lets the disk fill, and both left the suite green. Eight is written out rather than imported,
# because `DEFAULT_KEEP + 1` reads the value under test and passes at any value.

KEEP = 8


def test_the_default_keeps_eight_clones(tmp_path: Path) -> None:
    """Ten clones, swept with no explicit keep: two go, eight stay."""
    for i in range(10):
        (tmp_path / "owner" / f"repo{i}" / ".git").mkdir(parents=True)

    removed = sweep(tmp_path)

    assert removed == 2
    assert len([p for p in (tmp_path / "owner").iterdir() if (p / ".git").is_dir()]) == KEEP


def test_the_default_deletes_nothing_when_there_is_nothing_spare(tmp_path: Path) -> None:
    """Fewer clones than the budget is not a reason to delete any. Catches DEFAULT_KEEP = 0."""
    for i in range(KEEP):
        (tmp_path / "owner" / f"repo{i}" / ".git").mkdir(parents=True)

    assert sweep(tmp_path) == 0
    assert len([p for p in (tmp_path / "owner").iterdir() if (p / ".git").is_dir()]) == KEEP
