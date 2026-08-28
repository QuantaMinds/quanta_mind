"""The join: a verified delivery becomes a clone, a ranking, and a comment on the pull request.

WHAT: `deliver(review, settings)` clones or fetches the repository, asks GitHub what the pull
      request changed and what it was opened against, runs the ranking, and posts the comment --
      or, with posting off, prints exactly what it would have posted. Returns a `Delivered` naming
      which of six outcomes occurred.
WHY:  **THE ENDPOINT AUTHENTICATED DELIVERIES AND REVIEWED NOTHING.** `run_endpoint.work()` logged
      "NOT REVIEWED: no pipeline is attached to this callback" and returned. Every piece existed --
      `review()` ranks and renders, `changed_files()` and `base_commit()` read the pull request,
      `github_comments.post()` writes idempotently keyed on the head SHA -- and nothing joined
      them. This is that join, and it is the gap between a command-line tool and a product a
      customer can install.

      **POSTING IS OFF UNLESS TURNED ON, AND THE DRY RUN IS A COMPLETE REHEARSAL.** With
      `posting_enabled` false everything runs -- clone, fetch, API reads, ranking, rendering -- and
      the comment is printed instead of sent. So the thing being rehearsed is the delivery rather
      than a description of it, and the only step not exercised is the one that writes to someone
      else's project.

      **EVERY OUTCOME IS NAMED, INCLUDING THE QUIET ONES.** "Nothing worth saying", "every changed
      file is in a language we do not read", and "already commented on this commit" are three
      different results and a caller must be able to tell them apart. Collapsing them into a
      silent return is the defect this product exists to refuse -- `Outcome` is an enum for that
      reason, and mypy's exhaustiveness check is what keeps a seventh case from being forgotten.

      **THE BASE COMMIT'S TIMESTAMP BOUNDS THE HISTORY, AND IT IS NOT `now`.** A ranking that reads
      commits made after the pull request opened is scoring the change against its own future.
IMPORTS: ingest.{diff,github_api,github_comments}, serve.{run_review,working_clone},
      types.settings.
      Rightmost layer.
CONSUMED BY: `serve/run_endpoint.py`.
"""

from __future__ import annotations

from pathlib import Path

from quantamind.allocate.depth import plan as allocate
from quantamind.infer.change_review import explain
from quantamind.ingest.diff import base_commit, changed_files
from quantamind.ingest.github_api import token_for
from quantamind.ingest.github_reviews import publish
from quantamind.render.comment import comment as rendered
from quantamind.render.pin_block import block
from quantamind.serve import pin_check
from quantamind.serve.deep_review import examine
from quantamind.serve.run_review import review as run_ranking
from quantamind.serve.working_clone import ensure, sweep
from quantamind.store import tenancy
from quantamind.store.reviews import bank
from quantamind.types.review import Delivered, Outcome
from quantamind.types.settings import Settings
from quantamind.types.spend import Spend
from quantamind.verify.rule_check import enforce


def deliver(delivery_repo: str, number: int, head_sha: str, settings: Settings) -> Delivered:
    """Run the pipeline for one pull request and post, or rehearse posting.

    Takes the three fields rather than the `Review` record so this never imports the webhook
    parser: the join has no business knowing what shape GitHub's payload arrives in.
    """
    # **THE CLONE MUST AUTHENTICATE, BECAUSE EVERY CUSTOMER REPOSITORY IS PRIVATE.** That is
    # what a code reviewer is for. Without a credential git asks a terminal for a username and
    # exits 128, which is exactly what the first genuine `pull_request` delivery did -- after
    # every test passed, because a developer's machine has a credential helper and a container
    # does not. The token is minted only when an App is configured: an endpoint without one can
    # still read public repositories, and `token_for` would refuse rather than return nothing.
    app = bool(settings.app_id and settings.app_key_path)
    clone = ensure(
        delivery_repo,
        Path(settings.clone_root),
        token=token_for(delivery_repo) if app else None,
    )
    # **BOUND THE ROOT ON EVERY DELIVERY, AND PRINT THE COUNT RATHER THAN ASSUME IT.** `sweep()`
    # was written with a docstring explaining why it returns a number instead of claiming a
    # cleanup happened -- and was then never called from anywhere, for the whole of its existence.
    # Eleven gigabytes of clones accumulated in a single working session and filled the disk.
    #
    # It runs AFTER `ensure()` deliberately: `sweep` keeps the most recently modified clones and
    # the one just fetched is the newest, so this delivery's own clone cannot be what it deletes.
    swept = sweep(Path(settings.clone_root))
    if swept:
        print(f"[deliver] removed {swept} stale clone(s)", flush=True)

    store = tenancy.store_for(Path(settings.database_path), *delivery_repo.split("/", 1))
    changed = changed_files(delivery_repo, number)
    if not changed:
        return Delivered(Outcome.NO_FILES, (), (), None)

    # **The base commit, not the head and not the clock.** See the module docstring.
    base = base_commit(delivery_repo, number, clone)
    reviewed = run_ranking(
        clone,
        delivery_repo,
        changed,
        # **ONE STORE PER REPOSITORY, NOT ONE FOR EVERYBODY.** `database_path` is now the root
        # under which each tenant gets its own file: the schema already separated them logically,
        # but a shared file means a shared blast radius and a shared SQLite writer lock, and
        # offboarding a customer means hand-written cascades across five tables instead of `rm`.
        store,
        as_of=base.committed_at,
        # **Passed so the review is RECORDED.** Without these the ranking runs and leaves no row,
        # which is how `review` and `ranked_unit` sat in the schema with zero writers.
        pr_number=number,
        head_sha=head_sha,
    )

    # **THE ALLOCATION DECIDES WHERE INFERENCE GOES.** The measured claim -- top three by fix
    # history misses 1.21% against alphabetical's 3.12% -- is about which files to read FIRST,
    # and a budget is the only consumer that claim ever fitted.
    reading = allocate(reviewed.ranking, list(changed))
    examined = examine(clone, head_sha, reading, list(changed), settings)
    # **RE-RENDERED HERE WITH WHAT ONLY THIS LAYER HAS.** `run_review` renders a ranking-only
    # body for the CLI, which has no pull request to read a goal from. A delivery does.
    # The ranking already carries each file's prior-fix count, so the summary reads the same
    # numbers rather than querying the store twice and risking two answers.
    past = {u.unit.site.path: int(u.score.value) for u in reviewed.ranking.units}
    told, unreadable = explain(
        clone, head_sha, delivery_repo, number, reading.paths, settings, history=past
    )
    if examined is not None:
        print(f"[deliver] {reading.depth.value}: {reading.why}", flush=True)
        print(
            f"[deliver] model: {len(examined.anchored)} finding(s) kept of {examined.raw} raw "
            f"({examined.unanchored} unanchored, {examined.refuted} refuted, "
            f"{examined.withdrawn} withdrawn), consulted={examined.consulted}",
            flush=True,
        )

    # **THE PIN CHECK RUNS ON THE RAW CHANGED LIST, NOT THE RANKED ONE.** Workflows are not a
    # reviewable suffix, so they never appear in `reviewed.considered` — which is exactly why the
    # detector sat unreachable behind the reviewer until now. It needs no model and no ranking.
    # **THE DECLARED STANDARDS, CHECKED DETERMINISTICALLY.** These verdicts are reproducible on
    # the same commit by anyone, which is why they may be asserted where a model finding may not.
    checks = enforce(clone, head_sha, list(changed), store, delivery_repo, number)

    # **WHAT THIS REVIEW COST, ON THE RECORD.** The columns have existed since the schema was
    # written and nothing ever wrote them, so every pricing question so far has been arithmetic
    # over a number nobody measured. A spend that is only a floor is refused rather than rounded.
    spent = Spend()
    for part in (told, examined):
        if part is not None:
            spent = spent.plus(part.spend)
    if bank(store, delivery_repo, number, head_sha, spent):
        print(
            f"[deliver] cost: {spent.requests} call(s), {spent.tokens_out} tokens out", flush=True
        )

    mismatched, _unresolved = pin_check.check(clone, head_sha, changed)
    pins = block(mismatched)

    if reviewed.body is None and not pins:
        quiet = Outcome.NO_READABLE_FILES if not reviewed.considered else Outcome.NOTHING_TO_SAY
        return Delivered(quiet, reviewed.considered, reviewed.skipped, None)

    kept = examined.anchored if examined is not None else ()
    fuller = rendered(
        reviewed.ranking, summary=told, findings=kept, checks=checks, blind=unreadable
    )
    body = (fuller if told is not None or kept or checks else (reviewed.body or "")) + pins

    if not settings.posting_enabled:
        return Delivered(Outcome.REHEARSED, reviewed.considered, reviewed.skipped, body)

    wrote = publish(delivery_repo, number, head_sha, body, kept)
    return Delivered(
        Outcome.POSTED if wrote else Outcome.DUPLICATE,
        reviewed.considered,
        reviewed.skipped,
        reviewed.body,
    )
