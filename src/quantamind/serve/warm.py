"""Clone and index a repository before its first review, so nobody waits for the cold start.

WHAT: `warm(repo, settings)` clones the repository and builds its touch index now, returning the
      rows the index holds afterwards. `warm_all(repos, settings)` does that for each and returns
      what succeeded and what did not, both named.
WHY:  **THE COLD START IS A FULL CLONE PLUS A ~31s INDEX BUILD ON A 115,776-COMMIT REPOSITORY**,
      and Cloud Run's ephemeral disk means every new instance pays it again. Paid on the first
      pull request, that is a customer watching a review take half a minute longer than it ever
      needs to again.

      **AND `listener.py` ALREADY CLAIMED THIS WAS HANDLED.** The line beside the installation
      branch read "Provisioned here so a first review pays no cold index", but
      `tenancy.provision` creates the store FILE and nothing else — no clone, no touches, no
      watermark. The claim was true of nothing until this module existed. `AGENTS.md` rule 14: a
      comment may explain why, never assert whether.

      **IT CANNOT RUN INLINE.** GitHub requires a 2XX within ten seconds and a clone will not
      finish in ten, so the handler answers first and warms afterwards — the same
      acknowledge-then-work shape `listener.py` documents for deliveries.

      **A FAILED WARM-UP IS NOT A FAILED INSTALLATION.** The repository is installed either way
      and the first review will simply pay the cost it would have paid anyway, so `warm_all`
      returns the failures instead of raising: an install that 500s because a clone was slow is a
      worse outcome than a slow first review. Each outcome is PRINTED as it happens as well as
      returned — an operator watching the log is the only person who can see a warm-up that has
      been failing quietly for a week.
IMPORTS: serve.{run_review,working_clone}, ingest.github_api, store.tenancy, types.settings.
CONSUMED BY: `serve/listener.py`, on an installation event.
"""

from __future__ import annotations

from pathlib import Path

from quantamind.ingest.github_api import token_for
from quantamind.serve.run_review import index_repository
from quantamind.serve.working_clone import ensure
from quantamind.store import tenancy
from quantamind.types.settings import Settings


def warm(repo: str, settings: Settings) -> int:
    """Clone `repo`, build its touch index, and return the rows the index then holds.

    **THE COUNT IS RETURNED RATHER THAN A BOOLEAN**, because a warm-up that indexed nothing and
    one that never ran must not report the same thing. A repository with no history in any
    language we read is a real answer and comes back as a count, not as a failure.

    **IT DOES EXACTLY WHAT A REVIEW WOULD DO, WHICH IS WHY REPEATING IT IS CHEAP.**
    `index_repository` reads the watermark and appends only `<watermark>..HEAD`, so a review that
    arrives mid-warm, or a redelivered installation event, costs the remaining range and not the
    world.
    """
    app = bool(settings.app_id and settings.app_key_path)
    clone = ensure(repo, Path(settings.clone_root), token=token_for(repo) if app else None)
    owner, _, name = repo.partition("/")
    store = tenancy.store_for(Path(settings.database_path), owner, name)
    conn, _ = index_repository(clone, repo, store)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM touch").fetchone()[0])
    finally:
        conn.close()


def warm_all(repos: list[str], settings: Settings) -> tuple[dict[str, int], dict[str, str]]:
    """Warm each repository. Returns `(indexed, failed)` — rows per repo, and why each failed.

    **FAILURES ARE COLLECTED, NEVER RAISED PAST THE CALLER.** This runs after the endpoint has
    already answered 200; an exception here would kill a worker thread for something that costs
    nothing worse than a slow first review.
    """
    indexed: dict[str, int] = {}
    failed: dict[str, str] = {}
    for repo in repos:
        try:
            indexed[repo] = warm(repo, settings)
            print(f"[serve] warmed {repo}: {indexed[repo]} touch row(s) indexed", flush=True)
        except Exception as exc:
            failed[repo] = f"{type(exc).__name__}: {exc}"
            print(
                f"[serve] warm-up FAILED for {repo}; the first review pays it: {failed[repo]}",
                flush=True,
            )
    return indexed, failed
