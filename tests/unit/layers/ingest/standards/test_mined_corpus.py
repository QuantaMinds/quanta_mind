"""D1d against the REAL corpus, whose numbers were fixed before the code existed.

WHAT: `mine` over `research/phase0/results/oss_review_comments.json` — 1,213 real inline review
      comments from eight public repositories.
WHY:  **THE FINDING STATED ITS OWN REFUTATION CONDITIONS IN ADVANCE**, and these are them:
      a miner proposing more than ~2 per repository is finding noise, and one proposing nothing on
      `huggingface/transformers` is missing the clearest true positive in the corpus.
      → `docs/findings/standards/D1D_REVIEWER_REPETITION_YIELD_2026-08.md`

      **A THRESHOLD NOBODY RE-MEASURES DRIFTS.** Pinning the yield here means a later change to the
      filter, the similarity floor or the word length has to face the number it moves.
IMPORTS: quantamind.ingest.standards.mined, quantamind.types.standards.proposal; stdlib.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

import pytest

from quantamind.ingest.standards.mined import mine
from quantamind.types.standards.proposal import Comment

CORPUS = Path(__file__).resolve().parents[5] / "research/phase0/results/oss_review_comments.json"


@pytest.mark.skipif(not CORPUS.exists(), reason="the research corpus is not present")
def test_the_yield_on_the_real_corpus_stays_in_the_measured_range() -> None:
    """**A MINER PROPOSING MANY RULES PER REPOSITORY IS FINDING NOISE.**

    The finding fixed this bar before the code existed: ~1.6 candidate clusters per repository, and
    "more than ~2 per repository is noise". This asserts the shipped code lands there — if it ever
    proposes far more, the filter has stopped working and the report has become a wall.
    """
    raw = json.loads(CORPUS.read_text(encoding="utf-8"))
    by_repo: dict[str, list[Comment]] = collections.defaultdict(list)
    for item in raw:
        by_repo[item["repo"]].append(Comment(item["body"], item.get("path", "")))

    per_repo = {repo: len(mine(comments)) for repo, comments in by_repo.items()}
    average = sum(per_repo.values()) / len(per_repo)

    assert 0.5 <= average <= 2.0, f"yield left the measured range: {per_repo}"


@pytest.mark.skipif(not CORPUS.exists(), reason="the research corpus is not present")
def test_the_clearest_true_positive_in_the_corpus_is_found() -> None:
    """**NAMES ITS ARTEFACT.** transformers' dependency standard, said of three libraries.

    The finding calls this the clearest true positive in the corpus and says a miner that misses it
    is broken. Asserting a count alone would not catch a miner that found two other things instead.
    """
    raw = json.loads(CORPUS.read_text(encoding="utf-8"))
    comments = [
        Comment(item["body"], item.get("path", ""))
        for item in raw
        if item["repo"] == "huggingface/transformers"
    ]
    proposals = mine(comments)

    assert len(proposals) == 3, f"yield moved: {[p.text[:60] for p in proposals]}"
    dependency = [p for p in proposals if "required dependencies" in p.text]
    assert len(dependency) == 2, (
        "missed the dependency standard, which the finding names as the clearest true positive "
        f"in the corpus; proposed instead: {[p.text[:60] for p in proposals]}"
    )
    assert all(p.occurrences == 2 for p in dependency)
    # The corpus carries no pull numbers, so recurrence across changes is UNKNOWN, not claimed.
    assert all(p.distinct_pulls is None for p in dependency)


def test_a_bot_comment_is_never_mined() -> None:
    """**THE FIRST REAL RUN OF THE COMMAND PROPOSED THIS PRODUCT'S OWN COMMENTS AS STANDARDS.**

    Three proposals, all of them our own review text repeated across heads, on a repository whose
    every comment was machine-written. The tests were green throughout: they used hand-built
    comments, and no hand-built comment had an author. This is that gap closed.
    """
    machine = [
        Comment(
            "Consider extracting this into a helper so the retry policy is stated in one place.",
            "src/a.py",
            pull=n,
            author="quanminds[bot]",
            machine=True,
        )
        for n in (1, 2, 3)
    ]
    assert mine(machine) == ()


def test_a_human_saying_the_same_thing_is_still_mined() -> None:
    """The other half: an author filter that dropped everything would pass the test above."""
    people = [
        Comment(
            "Consider extracting this into a helper so the retry policy is stated in one place.",
            "src/a.py",
            pull=n,
            author="a-reviewer",
        )
        for n in (1, 2, 3)
    ]
    found = mine(people)

    assert len(found) == 1
    assert found[0].occurrences == 3
    assert found[0].distinct_pulls == 3


def test_bots_are_excluded_before_clustering_not_after() -> None:
    """**A BOT MUST NOT SWELL A HUMAN'S CLUSTER.**

    Filtering after clustering would leave a proposal saying "said 4 times" when a person said it
    twice, which overstates exactly the evidence this feature sells.
    """
    mixed = [
        Comment("Prefer the logger over print for anything a user will see.", pull=1, author="p"),
        Comment("Prefer the logger over print for anything a user will see.", pull=2, author="p"),
        Comment(
            "Prefer the logger over print for anything a user will see.",
            pull=3,
            author="bot[bot]",
            machine=True,
        ),
    ]
    only = mine(mixed)[0]

    assert only.occurrences == 2, "a bot was counted into a human's evidence"
    assert all(not c.machine for c in only.evidence)
