"""Refuse a corpus whose events are too recent to have an outcome yet.

WHAT: `require_outcome_window()` rejects any pull request merged less than the outcome window ago,
      and `assert_corpus_age()` refuses a whole corpus if any member is too young.
WHY:  Twice in one session a corpus was drawn from the MOST RECENT items and then asked a question
      about what happened NEXT. The review-comment study sampled recent pages and measured project
      activity phase instead of review content. The pull-request corpus fetched newly merged PRs
      and made the defect-return check impossible -- median forward history 0.4 days against a
      90-day rule, zero of 14 usable.

      Both were caught after the fact by a reader, not by the code. A constraint that lives in a
      document is a wish; this makes it a precondition that fails loudly at fetch time, before the
      expensive run rather than after it.

      THE RULE IN ONE LINE: if the question is "what happened afterwards", the sample must have an
      afterwards. Draw from the past, never from the present.
IMPORTS: stdlib only (datetime).
CONSUMED BY: any corpus fetcher whose findings will be scored against a later outcome.
"""

from __future__ import annotations

import datetime

OUTCOME_WINDOW_DAYS = 90


class CorpusTooRecent(RuntimeError):
    """The corpus cannot answer a question about outcomes because it has no future."""


def days_since(iso: str, *, now: datetime.datetime | None = None) -> float:
    """Days between an ISO-8601 timestamp and now. Raises on an unparseable value."""
    when = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    ref = now or datetime.datetime.now(datetime.timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    return (ref - when).total_seconds() / 86400


def require_outcome_window(
    merged_at: str, *, window_days: int = OUTCOME_WINDOW_DAYS, now: datetime.datetime | None = None
) -> bool:
    """True when this event is old enough for a later outcome to exist. No exception -- a filter."""
    return days_since(merged_at, now=now) >= window_days


def assert_corpus_age(
    merged_dates: list[str],
    *,
    window_days: int = OUTCOME_WINDOW_DAYS,
    now: datetime.datetime | None = None,
) -> None:
    """Refuse the whole corpus if any member is too young to have an outcome.

    Fails loudly at fetch time. The alternative is what happened twice: a full run, an expensive
    adjudication, and only then the discovery that the question was unanswerable.
    """
    young = [
        d for d in merged_dates if not require_outcome_window(d, window_days=window_days, now=now)
    ]
    if young:
        ages = sorted(round(days_since(d, now=now), 1) for d in young)
        raise CorpusTooRecent(
            f"{len(young)} of {len(merged_dates)} events are younger than {window_days} days "
            f"(ages: {ages[:8]}...). A corpus drawn from the present cannot answer a question "
            f"about what happened next."
        )
