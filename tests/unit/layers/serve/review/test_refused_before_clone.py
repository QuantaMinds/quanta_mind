"""A repository we refuse is never cloned. Ordering, asserted rather than assumed.

WHAT: `deliver()` against a store whose installation row is ineligible, with `ensure` instrumented
      to record whether it was called at all.
WHY:  **THE CHECK USED TO RUN AFTER THE CLONE.** A refused repository was cloned first — a full
      copy of somebody's private source pulled onto our disk and kept, for a review we then
      declined to do. `docs/product/pricing.md` promises "one working copy of your repository, on
      our servers, used for reviewing and nothing else"; holding a clone of a repository we refused
      makes that sentence false, and it is the kind of false that becomes a contract problem rather
      than a credibility one.

      **ORDERING IS INVISIBLE TO EVERY OTHER TEST.** Both orders produce the same `NOT_ENTITLED`
      outcome and the same comment. The only observable difference is whether the network was
      touched, so that is what this asserts.

      Sabotage: move the seat block back below `ensure()` and this fails.
IMPORTS: quantamind.serve.review.review_delivery, quantamind.store.{installations,schema,tenancy},
      quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantamind.serve.review import review_delivery
from quantamind.store import installations, schema, tenancy
from quantamind.types.settings import Settings


def test_a_refused_repository_is_never_cloned(tmp_path: Path, monkeypatch: Any) -> None:
    root = tmp_path / "stores"
    root.mkdir()
    conn = schema.open_store(tenancy.shared(root, tenancy.ACCOUNTS))
    try:
        installations.record(
            conn,
            "acme",
            "acme/secret",
            at=1_700_000_000,
            eligible=False,
            reasons=("the repository is private; the free tier is public repositories only",),
        )
    finally:
        conn.close()

    cloned: list[str] = []

    def _never(repo: str, *args: Any, **kwargs: Any) -> Path:
        cloned.append(repo)
        raise AssertionError(f"cloned {repo} before checking whether we would review it")

    monkeypatch.setattr(review_delivery, "ensure", _never)

    done = review_delivery.deliver(
        "acme/secret",
        7,
        "deadbeef",
        Settings(database_path=str(root), clone_root=str(tmp_path / "clones")),
    )

    assert cloned == [], "a repository we refused was cloned anyway"
    assert done.outcome is review_delivery.Outcome.NOT_ENTITLED
    assert "private" in (done.body or ""), "the refusal did not say why"
