"""Whether a repository qualifies for the free tier, checked rather than advertised.

WHAT: `facts_for(repo)` reads what GitHub says about a repository. `qualifies(facts, taken, total)`
      turns that into a `Verdict` naming EVERY rule that failed, not the first.
WHY:  **EVERY RULE HERE IS CHECKABLE AT INSTALL TIME, SO IT IS ENFORCED RATHER THAN ADVERTISED.**
      A published eligibility list nobody checks is a promise; this is a decision the endpoint can
      make before provisioning anything.

      **AND THE CRITERIA SELECT FOR REPOSITORIES WHERE THE PRODUCT ACTUALLY WORKS.** The ranker
      needs fix history: fifty contributors over six months is exactly what produces it. A
      repository failing these would have received a weak review, so refusing it is honest rather
      than arbitrary — and `rank/firing.estimate()` can tell a prospect the same thing from their
      own history before they install.

      **EVERY FAILING RULE IS RETURNED, NEVER JUST THE FIRST.** A prospect told "not eligible"
      once, then again after fixing one thing, learns the list by attrition. The verdict carries
      all of them.

      **A RULE WE COULD NOT CHECK IS NOT A RULE THAT PASSED.** `facts_for` raises rather than
      defaulting a count to zero, because a contributors call that failed would otherwise read as
      "fewer than fifty contributors" and refuse a repository on the strength of an outage.
IMPORTS: stdlib, `ingest.github_api` for the reads — the same reach `verify/pin_check.py` makes.
CONSUMED BY: `serve/listener.py` at installation, and onboarding before an install exists.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from quantamind.ingest.github_api import ApiFailed, call

MIN_STARS = 1_000
STAR_CEILING: int | None = None
"""Upper bound on stars, or None for "and above".

**THE PLAN RECORDS THIS AS UNRESOLVED** — `docs/plans/roadmap/product-build.md` B8 asks "is 5K a
ceiling or just 'and above'?" and does not answer. It ships as None because the section's own
justification argues against a ceiling: the criteria exist to select repositories the ranker can
serve, and more history is not worse history. If a ceiling is wanted it is a COST control, which
is a different rule with a different reason, and it belongs beside the clone budget rather than
here. Set to an integer to enforce one; `qualifies` reports it as a named failure either way.
"""

MIN_CONTRIBUTORS = 50
MIN_ACTIVE_DAYS = 180
MAX_PUSHED_DAYS_AGO = 30
"""How stale `pushed_at` may be. **The plan says "recent" and does not define it**; thirty days is
written here so the number is arguable rather than implicit. Both this and `MIN_ACTIVE_DAYS` are
required, because either alone passes a repository that was busy once and stopped."""

FREE_REPOS_TOTAL = 40
CONTRIBUTOR_PAGE = 100


@dataclass(frozen=True, slots=True)
class Facts:
    """What GitHub says. Every field was read; none is defaulted on a failed call."""

    repo: str
    private: bool
    stars: int
    contributors: int
    active_days: int
    pushed_days_ago: int


@dataclass(frozen=True, slots=True)
class Verdict:
    """Eligible, or every reason it is not. `reasons` is empty exactly when `eligible` is True."""

    eligible: bool
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.eligible and self.reasons:
            raise ValueError(f"eligible with reasons is not a verdict: {self.reasons}")
        if not self.eligible and not self.reasons:
            raise ValueError("refused without a reason; a prospect cannot act on that")


def _days_since(stamp: str, now: datetime) -> int:
    return max(0, (now - datetime.fromisoformat(stamp.replace("Z", "+00:00"))).days)


def facts_for(repo: str, *, now: datetime | None = None) -> Facts:
    """Read the repository, its contributors and its oldest recent commit. Raises on any failure.

    **NOTHING IS DEFAULTED.** A contributors call that failed would otherwise read as "too few
    contributors" and refuse a repository because GitHub had an outage.
    """
    moment = now or datetime.now(UTC)
    meta = json.loads(call(repo, f"repos/{repo}"))
    if not isinstance(meta, dict):
        raise ApiFailed("GET", f"repos/{repo}", "repository metadata was not an object")

    people = json.loads(call(repo, f"repos/{repo}/contributors?per_page={CONTRIBUTOR_PAGE}"))
    if not isinstance(people, list):
        raise ApiFailed("GET", f"repos/{repo}/contributors", "the reply was not a list")

    commits = json.loads(call(repo, f"repos/{repo}/commits?per_page=1&page=2"))
    oldest = json.loads(call(repo, f"repos/{repo}/commits?per_page=1&until={moment.isoformat()}"))
    if not isinstance(commits, list) or not isinstance(oldest, list) or not oldest:
        raise ApiFailed("GET", f"repos/{repo}/commits", "commit history could not be read")

    created = str(meta.get("created_at") or "")
    pushed = str(meta.get("pushed_at") or "")
    if not created or not pushed:
        raise ApiFailed("GET", f"repos/{repo}", "metadata lacked created_at or pushed_at")

    return Facts(
        repo=repo,
        private=bool(meta.get("private", True)),
        stars=int(meta.get("stargazers_count", 0)),
        contributors=len(people),
        active_days=_days_since(created, moment) - _days_since(pushed, moment),
        pushed_days_ago=_days_since(pushed, moment),
    )


def qualifies(facts: Facts, *, owner_already_free: bool, repos_taken: int) -> Verdict:
    """Every rule, with every failure named. The offer closes at `FREE_REPOS_TOTAL`."""
    reasons: list[str] = []
    if facts.private:
        reasons.append("the repository is private; the free tier is public repositories only")
    if facts.stars < MIN_STARS:
        reasons.append(f"{facts.stars} stars, and the free tier needs at least {MIN_STARS}")
    if STAR_CEILING is not None and facts.stars > STAR_CEILING:
        reasons.append(f"{facts.stars} stars is above the {STAR_CEILING} ceiling for the free tier")
    if facts.contributors < MIN_CONTRIBUTORS:
        reasons.append(
            f"{facts.contributors} contributor(s), and the ranker needs the fix history that at "
            f"least {MIN_CONTRIBUTORS} produces"
        )
    if facts.active_days < MIN_ACTIVE_DAYS:
        reasons.append(
            f"{facts.active_days} days of history, and at least {MIN_ACTIVE_DAYS} is needed"
        )
    if facts.pushed_days_ago > MAX_PUSHED_DAYS_AGO:
        reasons.append(
            f"last pushed {facts.pushed_days_ago} days ago; the free tier needs activity within "
            f"{MAX_PUSHED_DAYS_AGO}"
        )
    if owner_already_free:
        reasons.append("this account already has a free repository; the offer is one per account")
    if repos_taken >= FREE_REPOS_TOTAL:
        reasons.append(f"the free tier is closed: all {FREE_REPOS_TOTAL} places are taken")
    return Verdict(not reasons, tuple(reasons))
