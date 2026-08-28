"""A blind labelling pack for the correctness of PUBLISHED model findings.

WHAT: `draw(findings)` returns a `Pack` -- a shuffled sheet of items the labeller reads, and
      a sealed key saying which were real findings and which were planted controls.
WHY:  `draw.py` samples PRs to ask whether a PR broke something. This asks a different
      question of a different unit: of the findings the pipeline PUBLISHED, after the anchor
      gate and the refutation pass, what share are actually true of the code they point at?
      A6 measured 0.686 findings published per change and could not say how many were right.

      **THE CONTROL ARM EXISTS BECAUSE A ONE-ARMED SHEET CANNOT DETECT AN INATTENTIVE
      LABELLER.** Marking everything TRUE would score 100%. Half the pack is therefore a
      genuine claim shown beside code it is not about, so a constant answer scores 50%.

      **FALSITY IS ESTABLISHED BY CONSTRUCTION, NOT BY OPINION.** A planted claim must name
      something -- an identifier, a dotted attribute -- that is ABSENT from the code shown.
      A claim generic enough to be accidentally true of its host would mark a CORRECT labeller
      wrong and withhold a real result. The cost is stated where it is measured: a control
      built this way tests whether the labeller read, not how well they judged.

      Three leaks were found by auditing the first build of this pack, all of which handed the
      labeller the key: one claim reused three times, six claims appearing in BOTH arms (once
      beside their own diff and once beside a foreign one), and repeated diffs that were
      homogeneous by arm. Every one came from drawing donors out of a pool that still held the
      real items. `findings_audit.py` refuses a pack exhibiting any of them.
IMPORTS: stdlib only.
CONSUMED BY: `findings/audit.py`; tests/findings/test_pack_leaks.py.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

REAL_DEFAULT = PLANTED_DEFAULT = 12


class NotEnoughFindings(RuntimeError):
    """The harvested pool cannot fill the pack. Carries what was available and what was needed."""


@dataclass(frozen=True, slots=True)
class Finding:
    """One published finding and the change it points at."""

    sha: str
    path: str
    claim: str
    quote: str
    diff: str

    def judgeable(self) -> bool:
        """Whether the line the claim anchors to is inside the diff the labeller will see.

        `diff_for` truncates. An item whose quoted line fell outside would be labelled FALSE
        for the pack's fault rather than the finding's, which is a fabricated error rate.
        """
        return bool(self.quote.strip()) and self.quote.strip() in self.diff


@dataclass(frozen=True, slots=True)
class Item:
    """One row of the blind sheet. Carries NO indication of which arm it is in, by type."""

    label_id: int
    claim: str
    diff: str
    path: str


@dataclass(frozen=True, slots=True)
class Pack:
    """A completed draw: what the labeller sees, and what is sealed away."""

    blind: tuple[Item, ...]
    key: tuple[tuple[int, str], ...]  # (label_id, "REAL" | "PLANTED")
    seed: int
    considered: int
    # Findings excluded because their quoted line fell outside the truncated diff. Returned
    # rather than dropped: a pack that silently passed over them would look identical to one
    # that met none, and the count is the instrument reporting on itself.
    unjudgeable: int = 0

    def arm_of(self, label_id: int) -> str:
        """The sealed arm for one row. Reading this is opening the key."""
        return dict(self.key)[label_id]


def named(text: str) -> set[str]:
    """Everything in a claim that could name code: backticked spans and identifier words.

    **BACKTICKS ARE NOT ALWAYS IDENTIFIERS.** An earlier version matched only identifier-shaped
    backticks, so a claim quoting `len(args) == 1` yielded nothing and was skipped by a filter
    that then reported success over the items it had looked at. Spans are tokenised instead.
    """
    out: set[str] = set()
    for span in re.findall(r"`([^`]+)`", text):
        out |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", span))
    out |= set(re.findall(r"\b([a-z]+_[a-z_]+|[A-Za-z]+\.[A-Za-z_]+)\b", text))
    return out


def overlap(claim: str, diff: str) -> float:
    """Share of a claim's named entities appearing in `diff`, or -1.0 when it names nothing.

    **UNTESTABLE IS ITS OWN VALUE.** Returning 0.0 for a claim naming nothing would make
    "checked and absent" and "never checked" the same number, which is the whole defect this
    module was rewritten to remove.
    """
    tokens = named(claim)
    if not tokens:
        return -1.0
    return sum(t.split(".")[-1] in diff for t in tokens) / len(tokens)


def _split_by_kind(pool: list[Finding], count: int) -> tuple[list[Finding], list[Finding]]:
    """Take `count` findings, keeping tests and source represented. Returns (taken, left).

    Neither arm may be identifiable by file kind: putting every test-file diff in one arm is
    a rule a labeller can learn instead of reading the code.
    """
    tests = [f for f in pool if "test" in f.path]
    source = [f for f in pool if "test" not in f.path]
    share = min(len(tests) // 2, count)
    taken = tests[:share] + source[: count - share]
    ids = {id(f) for f in taken}
    return taken, [f for f in pool if id(f) not in ids]


def draw(
    findings: list[Finding],
    *,
    real: int = REAL_DEFAULT,
    planted: int = PLANTED_DEFAULT,
    seed: int = 20260826,
) -> Pack:
    """Build a balanced, blind pack. Raises rather than quietly returning a smaller one."""
    judgeable = [f for f in findings if f.judgeable()]
    if findings and not judgeable:
        raise NotEnoughFindings(
            f"all {len(findings)} findings quote a line outside their own diff. A filter "
            f"admitting NOTHING is a statement about the two populations -- the quotes and "
            f"the diff text -- not about the findings. Check `diff_for`'s truncation."
        )

    # One finding per distinct diff: showing a diff twice tells the labeller that the repeat
    # group shares an answer, which is worth more to them than the second finding is to us.
    by_diff: dict[tuple[str, str], Finding] = {}
    for f in judgeable:
        by_diff.setdefault((f.sha, f.path), f)
    pool = list(by_diff.values())
    rng = random.Random(seed)
    rng.shuffle(pool)
    if len(pool) < real + planted:
        raise NotEnoughFindings(
            f"{len(pool)} distinct diffs available, {real + planted} needed. Harvest more "
            f"commits rather than shrinking the pack, which would change what is measured."
        )

    chosen, left = _split_by_kind(pool, real)
    hosts, _ = _split_by_kind(left, planted)

    # **DONORS COME FROM OUTSIDE THE REAL ARM.** Drawing them from the whole pool put six
    # claims into the pack twice -- once beside their own diff as a real item, once beside a
    # foreign one as a control. The identical sentence hands over both answers at once.
    real_claims = {f.claim for f in chosen}
    donors: list[Finding] = []
    seen: set[str] = set()
    for f in judgeable:
        if f.claim not in real_claims and f.claim not in seen:
            seen.add(f.claim)
            donors.append(f)

    rows: list[tuple[Finding | None, str, str, str]] = [
        (f, f.claim, f.diff, f.path) for f in chosen
    ]
    spent: set[str] = set()
    for host in hosts:
        # A donor naming nothing checkable cannot be SHOWN false of the host, so it is not a
        # control -- it is an unverified item wearing a control's label.
        able = [
            f
            for f in donors
            if f.path != host.path and f.claim not in spent and overlap(f.claim, host.diff) >= 0.0
        ]
        if not able:
            raise NotEnoughFindings(
                f"no verifiable-false donor claim left for {host.path}: every remaining claim "
                f"is already spent, shares the host's file, or names nothing checkable."
            )
        best = min(able, key=lambda f: (overlap(f.claim, host.diff), f.claim))
        spent.add(best.claim)
        rows.append((None, best.claim, host.diff, host.path))

    rng.shuffle(rows)
    blind = tuple(Item(i, claim, diff, path) for i, (_, claim, diff, path) in enumerate(rows, 1))
    key = tuple(
        (i, "REAL" if src is not None else "PLANTED") for i, (src, *_) in enumerate(rows, 1)
    )
    return Pack(blind, key, seed, len(findings), len(findings) - len(judgeable))
