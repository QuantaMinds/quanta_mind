"""Known-answer and sabotage tests for the retrospective's leakage bound.

WHAT: Builds a real repository whose answer flips if the bound is removed, replays it, and asserts
      the honest answer. Then removes the bound and requires the flip.
WHY:  **A retrospective that leaks looks brilliant and no customer can audit it.** It is the
      strongest incentive in this project to produce a wrong number, so the bound gets a known
      answer rather than a plausible one.

      **THE FIXTURE IS BUILT SO THAT LEAKING CHANGES THE OUTCOME, NOT JUST THE SCORES.** The first
      attempt had every file changing together, so every event was flat-scored and dropped: the
      sabotage ran, altered nothing, and the test correctly reported that it could not detect
      leakage. Here `f4` is the file a later fix returns to, it has NO history before the event,
      and it is heavily touched afterwards. Bounded, it ranks last and the top three misses it.
      Unbounded, the future makes it rank first and the miss becomes a hit -- one event, hits 0
      against 1, which is the signature of leakage and not a shift in an average.
IMPORTS: quantamind.rank.baseline, quantamind.serve.retrospective, quantamind.store.touches.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from quantamind.rank.baseline import chance_hit
from quantamind.serve import retrospective
from quantamind.store import schema
from quantamind.store import touches as touch_store
from quantamind.types.touch import Touch

DAY = 86400
BASE = 1_577_836_800  # 2020-01-01, so every stamp below is a real date git will accept
EVENT_AT = BASE + 150 * DAY


def _commit(repo: Path, when: int, files: dict[str, str], message: str) -> None:
    stamp = f"{when} +0000"
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
        "GIT_AUTHOR_DATE": stamp,
        "GIT_COMMITTER_DATE": stamp,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        "HOME": "/tmp",
    }
    for name, body in files.items():
        (repo / name).write_text(body)
    for args in (["add", "-A"], ["commit", "-q", "-m", message]):
        done = subprocess.run(
            ["git", *args], cwd=repo, env=env, capture_output=True, text=True, timeout=60
        )
        assert done.returncode == 0, f"git {args[0]} failed: {done.stderr}"


@pytest.fixture
def leaky_repo(tmp_path: Path) -> Path:
    """One admissible event whose verdict depends entirely on the bound."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, capture_output=True, timeout=60)

    # BEFORE: f1 and f2 accumulate history. f4 has none.
    for i in range(5):
        _commit(repo, BASE + i * DAY, {"f1.py": f"a{i}", "f2.py": f"b{i}"}, f"work {i}")

    # THE EVENT: five files change together. Bounded, only f1 and f2 have any history.
    _commit(
        repo,
        EVENT_AT,
        {f"f{n}.py": f"event{n}" for n in range(1, 6)},
        "the change under test",
    )
    # The return: a fix comes back to f4 alone, inside the ninety-day window.
    _commit(repo, EVENT_AT + 10 * DAY, {"f4.py": "repaired"}, "fix the fourth file")

    # AFTER: f4 becomes the busiest file in the repository. Only a leak can see this.
    for i in range(20):
        _commit(
            repo,
            EVENT_AT + (120 + i) * DAY,
            {"f4.py": f"later{i}", "f5.py": f"later{i}"},
            f"update {i}",
        )
    return repo


def test_the_bounded_replay_misses_the_file_only_the_future_would_have_ranked(
    leaky_repo: Path, tmp_path: Path
) -> None:
    """The known answer: one event, and the top three does NOT contain the returned-to file."""
    outcome = retrospective.replay(leaky_repo, "t/t", tmp_path / "honest.db")

    assert outcome.whole.events == 1, (
        f"expected exactly one admissible event, got {outcome.whole.events} "
        f"(rejected: {outcome.rejected})"
    )
    assert outcome.informative.events == 1, "a five-file change belongs in the informative stratum"
    assert outcome.whole.hits == 0, (
        "the ranker hit a file that had no history before the change — the bound is leaking"
    )


def test_removing_the_bound_turns_the_miss_into_a_hit(
    leaky_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The sabotage. Every count now sees the end of history, which is what leaking means."""
    honest = retrospective.replay(leaky_repo, "t/t", tmp_path / "a.db")
    real = touch_store.counts
    reached: list[int] = []

    def unbounded(conn: Any, repo_id: int, paths: Any, as_of: int, **kw: Any) -> Any:
        # BOTH halves of the bound, or the sabotage is a no-op: the window is 365 days WIDE, so
        # moving `as_of` alone to 2038 just slides an empty window past the end of history. That
        # first attempt reported "changed nothing" and was right to.
        reached.append(as_of)
        kw.pop("window", None)
        return real(conn, repo_id, paths, as_of=2**31 - 1, window=2**31 - 1, **kw)

    monkeypatch.setattr(touch_store, "counts", unbounded)
    leaked = retrospective.replay(leaky_repo, "t/t", tmp_path / "b.db")

    assert reached, "the sabotage never ran; replay() does not score through touches.counts"
    assert honest.whole.hits == 0 and leaked.whole.hits == 1, (
        f"the bound is not what decides this: honest hits {honest.whole.hits}, "
        f"leaked hits {leaked.whole.hits}. A sabotage that changes nothing is not a gate."
    )


def test_the_window_is_half_open_so_a_change_cannot_see_itself(tmp_path: Path) -> None:
    """`counts(as_of=t)` must exclude a touch AT t, or every change raises its own score."""
    conn = schema.open_store(tmp_path / "b.db")
    repo_id = touch_store.ensure_repo(conn, "github.com", "t/t")
    touch_store.index(conn, repo_id, [Touch(path="a.py", committed_at=1_000)])
    at_the_moment = dict(touch_store.counts(conn, repo_id, ["a.py"], as_of=1_000))
    one_second_later = dict(touch_store.counts(conn, repo_id, ["a.py"], as_of=1_001))
    conn.close()

    assert at_the_moment == {"a.py": 0}, "a touch AT as_of leaked into its own ranking"
    assert one_second_later == {"a.py": 1}, "the touch vanished entirely, so nothing is counted"


def test_chance_matches_hand_computed_values() -> None:
    """The baseline the headline is quoted against, checked against arithmetic done by hand."""
    assert chance_hit(3, 1, 3) == 1.0  # budget covers the change: a hit is certain
    assert chance_hit(4, 1, 3) == pytest.approx(0.75)  # miss = C(3,3)/C(4,3) = 1/4
    assert chance_hit(6, 2, 3) == pytest.approx(0.8)  # miss = C(4,3)/C(6,3) = 4/20
    with pytest.raises(ValueError):
        chance_hit(2, 3, 3)


def test_a_history_that_runs_backwards_end_to_end_refuses_to_measure() -> None:
    """Reversed, the scan admits almost nothing — the same output as a repo with rare fixes."""
    from quantamind.rank.events import ReversedHistory, admissible
    from quantamind.types.commit import Commit

    backwards = [
        Commit(committed_at=2_000, subject="later", paths=frozenset({"a.py", "b.py"})),
        Commit(committed_at=1_000, subject="fix earlier", paths=frozenset({"a.py", "b.py"})),
    ]
    with pytest.raises(ReversedHistory) as caught:
        list(admissible(backwards))
    assert "newest-first" in str(caught.value)


def test_a_locally_out_of_order_commit_is_counted_not_raised() -> None:
    """Every real repository has these. Raising would make us stricter than the validated policy.

    `defect_return.py` breaks out of the ninety-day scan at the first commit past the window and
    truncates on exactly the same inversions, so the product must too or gate 2b stops holding.
    Measured on the pinned corpus: 1 to 64 inversions per repository, worst a 56-day jump.
    """
    from quantamind.rank.events import OUT_OF_ORDER, Rejections, admissible
    from quantamind.types.commit import Commit

    dipped = [
        Commit(committed_at=1_000, subject="first", paths=frozenset({"a.py", "b.py"})),
        Commit(committed_at=900, subject="clock went backwards", paths=frozenset({"a.py"})),
        Commit(committed_at=2_000, subject="fix it", paths=frozenset({"a.py", "b.py"})),
    ]
    rejections = Rejections()
    list(admissible(dipped, rejections))

    assert rejections.counts[OUT_OF_ORDER] == 1, (
        f"the inversion was not counted: {dict(rejections.counts)} — it would be absorbed into "
        f"a smaller target set with nothing saying so"
    )
