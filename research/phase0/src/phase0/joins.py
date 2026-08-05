"""Joins that cannot fail silently.

WHAT: One wrapper around `DataFrame.merge` that refuses to return a result until the
      caller has declared, in the call itself, how much of the left frame is expected
      to find a match. Reports the realised rate; raises when it is below the floor.
WHY:  A join that matches nothing is either a bug or a finding, and the two are
      indistinguishable at the call site unless somebody says which. Ours matched
      nothing: `pr_id` is a string in the replication package's commit tables and
      `int64` in its PR table, so the key sets could not intersect. The result was
      zero rows, no exception, no warning — and it read exactly like "AIDev has no
      commit data for the human arm", which is a true fact we had independent reason
      to expect. It was caught by noticing that 1,325 distinct `pr_id` values against
      1,402 PRs cannot yield zero, i.e. by arithmetic, not by the pipeline.

      This is the fourth instance of the same class in this harness — an absence that
      is not typed, so it reads as a result. The others: an uncomputable negative
      control scoring as a pass, `Unresolved` versus no edge, and a hunk that fails to
      parse counting as "no breaking change". AGENTS.md rule 3 exists for exactly this
      and had no mechanism on the analysis side until now.

      Two failure shapes, not one. An inner join collapses to zero rows, which is at
      least visible downstream. A LEFT join returns the full frame with the joined
      columns all null — so `extract_prs._filter` would drop every row for a missing
      `language` and the attrition counter would report `not_python = total`. Same
      cause, and the more dangerous presentation, because the count looks computed.
IMPORTS: pandas. No phase0 modules — this sits below all of them.
CONSUMED BY: extract_prs.py; tests/test_joins.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# dtype.kind for the numeric families. A key that is object on one side and any of
# these on the other cannot intersect: '123' != 123, and pandas says nothing.
_NUMERIC_KINDS = frozenset("iuf")


class JoinError(RuntimeError):
    """A join matched less of the left frame than the caller declared it must.

    Carries the join's name and the realised report, so the message names the
    specific join rather than leaving the reader to find it.
    """

    def __init__(self, *, name: str, reason: str, report: JoinReport | None = None) -> None:
        super().__init__(f"join {name!r}: {reason}")
        self.name = name
        self.reason = reason
        self.report = report


@dataclass(frozen=True, slots=True)
class JoinReport:
    """What a join actually did, whether or not it cleared its floor."""

    name: str
    left_rows: int
    right_rows: int
    matched_rows: int
    left_dtype: str
    right_dtype: str

    @property
    def match_rate(self) -> float:
        """Fraction of left rows that found a key in the right frame."""
        return self.matched_rows / self.left_rows if self.left_rows else 0.0

    def describe(self) -> str:
        """One line for the pilot's shape metrics."""
        return (
            f"{self.name}: {self.matched_rows:,}/{self.left_rows:,} left rows matched "
            f"({self.match_rate:.1%}) against {self.right_rows:,} right rows "
            f"[{self.left_dtype} -> {self.right_dtype}]"
        )


def _dtype_mismatch(left: pd.Series, right: pd.Series) -> str | None:
    """The cast instruction, if the key dtypes cannot possibly intersect.

    Checked before the match rate so the error names the cause rather than the
    symptom. "0 of 1,402 matched" sends you looking for missing data; "object vs
    int64" sends you to the cast, which is where the bug is.
    """
    left_kind, right_kind = left.dtype.kind, right.dtype.kind
    if left_kind == right_kind:
        return None
    has_object = "O" in (left_kind, right_kind)
    has_numeric = bool({left_kind, right_kind} & _NUMERIC_KINDS)
    if has_object and has_numeric:
        object_side = "left" if left_kind == "O" else "right"
        return (
            f"key dtypes cannot intersect: left={left.dtype}, right={right.dtype}. "
            f"The {object_side} key holds strings and the other holds numbers, so no "
            f"value can be equal to any other. Cast before joining, e.g. "
            f'frame["{left.name}"] = frame["{left.name}"].astype("int64").'
        )
    return None


def checked_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    on: str,
    how: str,
    name: str,
    minimum_match_rate: float,
) -> tuple[pd.DataFrame, JoinReport]:
    """Merge two frames, refusing to hide a join that matched too little.

    `minimum_match_rate` has no default on purpose. Every call site must state what
    fraction of the left frame it expects to match, which converts "this join returned
    nothing" from something you discover later into something the author already had
    to have an opinion about. Passing 0.0 is legal and is the explicit declaration that
    an empty result is a finding rather than a bug — it is three characters, and it is
    visible in review, which a silent empty result is not.

    The match rate is computed from the key sets, not from the merged frame's length,
    because a left join's length tells you nothing: it equals the left frame's length
    whether every key matched or none did.

    Raises:
        JoinError: on incompatible key dtypes, or a realised rate below the floor.
    """
    if not 0.0 <= minimum_match_rate <= 1.0:
        raise JoinError(
            name=name,
            reason=f"minimum_match_rate must be in [0, 1], got {minimum_match_rate!r}",
        )
    for side, frame in (("left", left), ("right", right)):
        if on not in frame.columns:
            raise JoinError(name=name, reason=f"{side} frame has no column {on!r}")

    left_key, right_key = left[on], right[on]
    # Skip the dtype check when either side is empty: an empty frame's key column is
    # often object by default, which would report a mismatch that is not the cause.
    if len(left_key) and len(right_key):
        mismatch = _dtype_mismatch(left_key, right_key)
        if mismatch is not None:
            raise JoinError(name=name, reason=mismatch)

    matched = int(left_key.isin(set(right_key)).sum())
    report = JoinReport(
        name=name,
        left_rows=len(left),
        right_rows=len(right),
        matched_rows=matched,
        left_dtype=str(left_key.dtype),
        right_dtype=str(right_key.dtype),
    )
    if report.match_rate < minimum_match_rate:
        raise JoinError(
            name=name,
            reason=(
                f"matched {matched:,} of {len(left):,} left rows "
                f"({report.match_rate:.1%}), below the declared floor of "
                f"{minimum_match_rate:.1%}. Either the keys are wrong or this is a "
                f"finding — if it is a finding, say so by lowering the floor at the "
                f"call site."
            ),
            report=report,
        )
    return left.merge(right, on=on, how=how), report
