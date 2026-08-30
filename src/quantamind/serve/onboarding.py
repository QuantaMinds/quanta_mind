"""What happens to a repository when it is installed: decide whether we serve it, then warm it.

WHAT: `admit(repos, settings)` is the entry point — it qualifies each repository for the free
      tier and warms the ones that pass. `warm(repo, settings)` clones and builds the touch index,
      returning the rows it then holds; `warm_all` does that for several and names both outcomes.
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
IMPORTS: serve.{run_review,working_clone}, ingest.github_api, parse.suite_reach, store.tenancy,
      types.settings, verify.qualification.
CONSUMED BY: `serve/listener.py`, on an installation event.
"""

from __future__ import annotations

import time
from pathlib import Path

from quantamind.ingest.github_api import token_for
from quantamind.parse.suite_reach import NoSource, reach
from quantamind.serve.run_review import index_repository
from quantamind.serve.working_clone import ensure
from quantamind.store import installations, tenancy
from quantamind.store.schema import open_store
from quantamind.types.settings import Settings
from quantamind.verify.qualification import Verdict, facts_for, qualifies


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
    # **WHAT ITS OWN SUITE REACHES, SAID ONCE, WHERE A CLONE ALREADY EXISTS.** `product-build.md`
    # B8 asks for eligibility to be "a measured answer about their repository instead of a sales
    # rule"; a repository whose tests import little of its own source is one where a review has
    # less to stand on. Reported, never enforced — it is information for a human, not a gate.
    try:
        print(f"[serve] {repo}: {reach(clone).sentence()}", flush=True)
    except NoSource as empty:
        print(f"[serve] {repo}: suite reach unreadable — {empty}", flush=True)

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


def _record(settings: Settings, account: str, repo: str, verdict: Verdict | None) -> None:
    """Write the installation row beside the tenant's own data. Flattened here because
    `store/` sits left of `verify/` and cannot import a `Verdict`."""
    owner, _, name = repo.partition("/")
    store = tenancy.store_for(Path(settings.database_path), owner, name)
    conn = open_store(store)
    try:
        installations.record(
            conn,
            account,
            repo,
            at=int(time.time()),
            eligible=None if verdict is None else verdict.eligible,
            reasons=() if verdict is None else verdict.reasons,
        )
    finally:
        conn.close()


def admit(repos: list[str], settings: Settings, account: str = "") -> dict[str, Verdict]:
    """Qualify each repository, warm the ones that pass, and return every verdict.

    **THE VERDICT IS RECORDED AND REPORTED; IT DOES NOT REFUSE THE INSTALLATION.** Enforcement
    belongs at delivery, which is B5 in `docs/plans/product/product-build.md` — "today any
    installation is reviewed, paid or not". Refusing to provision here, with no entitlement
    system to say "but this one is a customer", would turn every non-qualifying install into a
    dead end with no override.

    **AN UNQUALIFIED REPOSITORY IS NOT WARMED**, which is the part that costs money. A clone and a
    ~31s index build spent on a repository we have decided not to serve is the free tier paying
    for itself twice.

    **A QUALIFICATION THAT COULD NOT BE READ IS NOT A REFUSAL.** `facts_for` raises rather than
    defaulting, and a repository whose facts are unreadable is warmed anyway: an outage at GitHub
    must not quietly downgrade somebody's installation.
    """
    verdicts: dict[str, Verdict] = {}
    warm_these: list[str] = []
    # Listed ONCE. This read the directory again per repository, so a hundred-repository
    # installation globbed the store root a hundred and one times for an answer that cannot
    # change mid-loop: nothing here provisions a tenant.
    already = tenancy.tenants(Path(settings.database_path))
    taken = len(already)
    owners = {owner for owner, _ in already}
    for repo in repos:
        owner = repo.partition("/")[0]
        try:
            facts = facts_for(repo)
        except Exception as exc:  # an unreadable repository is served, not refused
            print(f"[serve] {repo}: eligibility unreadable ({exc}); warming anyway", flush=True)
            warm_these.append(repo)
            _record(settings, account or owner, repo, None)
            continue
        verdict = qualifies(facts, owner_already_free=owner in owners, repos_taken=taken)
        verdicts[repo] = verdict
        _record(settings, account or owner, repo, verdict)
        if verdict.eligible:
            warm_these.append(repo)
        else:
            for reason in verdict.reasons:
                print(f"[serve] {repo}: not free-tier eligible — {reason}", flush=True)
    warm_all(warm_these, settings)
    return verdicts
