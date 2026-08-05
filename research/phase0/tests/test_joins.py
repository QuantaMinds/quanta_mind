"""Verification that a join cannot match nothing without saying so.

WHAT: Reproduces the string-versus-int key failure on real frames, and pins the two
      shapes it takes — an inner join collapsing to zero rows, and the more dangerous
      left join returning full rows with the joined columns all null.
WHY:  The bug shipped in an analysis script and returned "0 of 1,402 human PRs have
      commit data", which is a sentence we had independent reason to believe. Nothing
      raised. It was caught by arithmetic, and arithmetic is not a mechanism.

      The last test runs against the actual replication package when it is present,
      because that is the only version of this test asserting on bytes that really
      caused the failure rather than bytes constructed to resemble them.
IMPORTS: pandas, pytest, phase0.joins.
CONSUMED BY: `just test-phase0`.
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from phase0.joins import JoinError, checked_merge

PACKAGE = Path(__file__).resolve().parents[1] / "data" / "AIDev_BC_Analyser.zip"


def _pulls() -> pd.DataFrame:
    return pd.DataFrame({"id": [1, 2, 3], "title": ["a", "b", "c"]})


def test_string_against_int_key_raises_and_names_the_cast() -> None:
    """The actual bug. The message must send you to the cast, not to the data."""
    right = pd.DataFrame({"id": ["1", "2", "3"], "type": ["feat", "fix", "chore"]})
    with pytest.raises(JoinError) as caught:
        checked_merge(_pulls(), right, on="id", how="left", name="x", minimum_match_rate=0.9)
    message = str(caught.value)
    assert "int64" in message and "object" in message
    assert 'astype("int64")' in message


def test_left_join_with_no_matches_raises_instead_of_returning_nulls() -> None:
    """The dangerous shape: without the guard this returns 3 rows of null `type`.

    Downstream that becomes `not_structural = total` — an attrition count that looks
    computed and is not. Asserted here by showing what plain pandas does first.
    """
    right = pd.DataFrame({"id": [7, 8, 9], "type": ["feat", "fix", "chore"]})
    unguarded = _pulls().merge(right, on="id", how="left")
    assert len(unguarded) == 3 and unguarded["type"].isna().all()

    with pytest.raises(JoinError, match="below the declared floor"):
        checked_merge(_pulls(), right, on="id", how="left", name="x", minimum_match_rate=0.5)


def test_match_rate_comes_from_the_keys_not_the_merged_length() -> None:
    """A left join's length equals the left frame's whether or not anything matched."""
    right = pd.DataFrame({"id": [1, 99], "type": ["feat", "fix"]})
    merged, report = checked_merge(
        _pulls(), right, on="id", how="left", name="x", minimum_match_rate=0.3
    )
    assert len(merged) == 3  # length says 100%
    assert report.matched_rows == 1 and report.match_rate == pytest.approx(1 / 3)


def test_an_expected_empty_result_must_be_declared_not_discovered() -> None:
    """0.0 is legal and explicit: this join may match nothing, and that is a finding."""
    right = pd.DataFrame({"id": [7, 8], "type": ["feat", "fix"]})
    merged, report = checked_merge(
        _pulls(), right, on="id", how="inner", name="x", minimum_match_rate=0.0
    )
    assert merged.empty and report.matched_rows == 0


def test_report_records_both_dtypes_for_the_pilot() -> None:
    right = pd.DataFrame({"id": [1, 2, 3], "type": ["feat", "fix", "chore"]})
    _, report = checked_merge(
        _pulls(), right, on="id", how="left", name="pulls x tasks", minimum_match_rate=1.0
    )
    assert report.match_rate == 1.0
    assert "3/3" in report.describe() and "int64 -> int64" in report.describe()


def test_a_missing_key_column_names_the_side() -> None:
    with pytest.raises(JoinError, match="right frame has no column 'id'"):
        checked_merge(
            _pulls(),
            pd.DataFrame({"other": [1]}),
            on="id",
            how="left",
            name="x",
            minimum_match_rate=0.5,
        )


def test_an_out_of_range_floor_is_rejected() -> None:
    with pytest.raises(JoinError, match=r"must be in \[0, 1\]"):
        checked_merge(_pulls(), _pulls(), on="id", how="left", name="x", minimum_match_rate=1.5)


def test_an_empty_side_reports_zero_matches_rather_than_a_dtype_fault() -> None:
    """An empty frame's key column is object by default; that is not the cause."""
    empty = pd.DataFrame({"id": pd.Series([], dtype="object"), "type": []})
    _, report = checked_merge(
        _pulls(), empty, on="id", how="left", name="x", minimum_match_rate=0.0
    )
    assert report.matched_rows == 0 and report.right_rows == 0


@pytest.mark.skipif(not PACKAGE.is_file(), reason="replication package not downloaded")
def test_the_real_package_reproduces_the_failure_and_the_cast_fixes_it() -> None:
    """Against the bytes that actually caused it — 0% uncast, 94.5% cast.

    This is the assertion that matters: the guard raises on the real tables in their
    published dtypes, and the same join clears a high floor once `pr_id` is cast.
    """
    with zipfile.ZipFile(PACKAGE) as archive:
        read = lambda n: pd.read_parquet(  # noqa: E731
            BytesIO(archive.read(f"AIDev_BC_Analyser/{n}.parquet"))
        )
        prs = read("human_pr_python")[["id"]].rename(columns={"id": "pr_id"})
        commits = read("human_commit")[["pr_id", "sha"]].drop_duplicates("pr_id")

    assert prs["pr_id"].dtype.kind in "iu" and commits["pr_id"].dtype.kind == "O"

    with pytest.raises(JoinError, match="cannot intersect"):
        checked_merge(prs, commits, on="pr_id", how="left", name="human", minimum_match_rate=0.9)

    commits["pr_id"] = commits["pr_id"].astype("int64")
    _, report = checked_merge(
        prs, commits, on="pr_id", how="left", name="human", minimum_match_rate=0.9
    )
    assert report.matched_rows == 1325
    assert report.match_rate == pytest.approx(0.945, abs=0.001)
