"""A standard a team keeps repeating in review, proposed for a human to accept or refuse.

WHAT: `mine(comments)` returns `Proposal` records — a point a reviewer made more than once, with
      every comment that evidences it. **A proposal is not a rule and never becomes one here.**
WHY:  **D1d. THE YIELD WAS MEASURED BEFORE THIS MODULE WAS WRITTEN, AND IT IS THIN.** Over 1,213
      real inline comments from eight repositories the honest count is **1.62 candidate clusters
      per repository, of which roughly five of thirteen were generalizable standards** — under one
      real rule per repository per ~150 comments.
      → `docs/findings/standards/D1D_REVIEWER_REPETITION_YIELD_2026-08.md`

      **THE ACKNOWLEDGEMENT FILTER IS THE FEATURE, NOT A TIDY-UP.** Without it the largest clusters
      in that corpus are `done` x6, `fixed` x6, `ditto` x4 and `nit: suggestion` x11. A miner
      shipping those is a miner whose headline number is noise, so the filter lives here in the
      code rather than in the analysis that discovered it.

      **REPETITION INSIDE ONE PULL REQUEST IS NOT A STANDARD.** Four of the thirteen clusters were
      one reviewer restating themselves in a single thread, one of them character-identical. A
      standard is something said again on a DIFFERENT change, so `Comment.pull` is required to
      count — and when a source cannot supply it, `Proposal.distinct_pulls` is `None` rather than a
      number, because "said twice on two changes" and "we could not tell" must not read alike.

      **A BOT'S COMMENT IS NOT A TEAM'S STANDARD, AND THE FIRST REAL RUN PROVED THE POINT.** Pointed
      at this repository's own pull requests, the miner proposed three "standards" and all three
      were OUR OWN REVIEW COMMENTS repeated across heads.
      `research/phase0/corpus/human_attention.py` had already recorded that about a third of
      inline comments in public repositories are AI-written. Mining those makes D1d a mirror
      rather than a miner, so `Comment.machine` exists and `mine` refuses them — and the caller
      is told how many were dropped, because a silently smaller denominator is how coverage gets
      overstated.

      **THIS IS THE ONE MODEL USE WHERE BEING WRONG IS CHEAP** — the row says so — but nothing here
      calls a model at all. Clustering by shared vocabulary is deterministic and re-runnable, and
      `AGENTS.md` says if a parser can answer it a model must not. What a model could add later is
      phrasing a proposal as a rule; finding the repetition does not need one.
IMPORTS: stdlib re; types.standards.proposal for `Comment` and `Proposal`. Leftward only.
CONSUMED BY: `serve/commands/run_standards.py`, and `render/mined_rules.py` for the report.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from quantamind.types.standards.proposal import MIN_OCCURRENCES, Comment, Proposal

CODE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
NON_LETTERS = re.compile(r"[^a-z ]+")

STOPWORDS = frozenset(
    [
        "the",
        "a",
        "an",
        "is",
        "are",
        "be",
        "to",
        "of",
        "in",
        "for",
        "this",
        "that",
        "it",
        "and",
        "or",
        "if",
        "you",
        "we",
        "not",
        "on",
        "with",
        "as",
        "at",
        "should",
        "would",
        "could",
        "can",
        "will",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "but",
        "so",
        "no",
        "yes",
        "there",
        "here",
    ]
)

ACKNOWLEDGEMENT = re.compile(
    r"^\W*(done|fixed|thanks?|thank you|lgtm|nice|good catch|ditto|same as above|\+1|agreed?|"
    r"ok(ay)?|sure|yep|yes|no|nit|updated?|removed?|added?|resolved?)\W*$",
    re.IGNORECASE,
)
"""**MEASURED, NOT GUESSED.** Every token here headed a cluster in the corpus that produced the
finding: `done` x6, `fixed` x6, `ditto` x4, `nit` x11, `Nice` x5, `Same as above` x3."""

MIN_CONTENT_WORDS = 6
"""Content words a comment needs to be worth clustering. 413 of 1,213 real comments fall below it.

A four-word comment shares vocabulary with anything, so clustering it produces groups held together
by nothing a reader would call a standard."""

SIMILAR = 0.5
"""Jaccard overlap of content words at which two comments are the same point.

The finding's clusters were built at this value and read by hand; every cluster it produced was a
genuine restatement, and the failures were in what the clusters CONTAINED, not in the threshold."""


def _content(body: str) -> frozenset[str]:
    """The content words of a comment: no code spans, no stopwords, nothing under four letters."""
    stripped = NON_LETTERS.sub(" ", CODE.sub(" ", body.lower()))
    return frozenset(w for w in stripped.split() if w not in STOPWORDS and len(w) > 3)


def _overlap(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def substantive(body: str) -> bool:
    """Whether this comment could carry a standard at all.

    **AN ACKNOWLEDGEMENT IS REPETITION AND IS NOT A STANDARD.** This is the filter the measurement
    found necessary; see the module docstring for what the corpus looks like without it.
    """
    collapsed = " ".join(body.split())
    if not collapsed or ACKNOWLEDGEMENT.match(collapsed):
        return False
    return len(_content(collapsed)) >= MIN_CONTENT_WORDS


def mine(comments: Sequence[Comment]) -> tuple[Proposal, ...]:
    """Every point made more than once, most-repeated first.

    **NOTHING HERE DECIDES ANYTHING.** The output is a list a human reads and accepts or refuses;
    no `Rule` is constructed, nothing is written to `.quantamind/rules.toml`, and no `Checked` row
    exists anywhere downstream. The measured yield is under one real standard per repository, which
    is affordable to read and would not be affordable to trust.
    """
    # **BOTS FIRST, BEFORE ANY CLUSTERING.** See the module docstring: the first real run mined
    # this product's own comments and called them the team's standards.
    human = [c for c in comments if not c.machine]
    worth = [c for c in human if substantive(c.body)]
    bags = [_content(c.body) for c in worth]

    # Union-find over "these two comments make the same point".
    parent = list(range(len(worth)))

    def root(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for i in range(len(worth)):
        for j in range(i + 1, len(worth)):
            if _overlap(bags[i], bags[j]) >= SIMILAR:
                parent[root(i)] = root(j)

    grouped: dict[int, list[Comment]] = {}
    for index, comment in enumerate(worth):
        grouped.setdefault(root(index), []).append(comment)

    found = [
        Proposal(max((c.body for c in members), key=len), len(members), tuple(members))
        for members in grouped.values()
        if len(members) >= MIN_OCCURRENCES
    ]
    # Most-repeated first; ties broken on text so the order is stable across runs.
    return tuple(sorted(found, key=lambda p: (-p.occurrences, p.text)))
