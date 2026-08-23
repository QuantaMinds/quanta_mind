"""Run the webhook endpoint until it is interrupted, and say plainly what it does not do.

WHAT: `run(port)` reads the secret from the environment, binds the listener, prints the startup
      banner and serves until Ctrl-C. Returns the process exit code.
WHY:  **Split out of `cli.py` at the 200-line cap, and it is the right seam.** `cli.py` parses
      arguments and dispatches; this owns one command, including the one decision in it that is not
      mechanical -- what the banner is allowed to claim.

      **THE WORK CALLBACK IS DELIBERATELY NOT WIRED TO A PIPELINE.** Everything from a delivery to a
      posted comment exists as decisions, but nothing yet clones a repository on receipt, because
      `review` is not built. So the banner says the endpoint authenticates and acknowledges and does
      not review. An endpoint that quietly accepted the work and dropped it would be
      indistinguishable, from the outside, from one that was doing its job.

      **The secret is read here, from the environment, and is deliberately absent from `Settings`**
      -- so it cannot reach `quantamind config` and be printed into a terminal scrollback or a CI
      log. There is no default: `build()` refuses to bind without one.
IMPORTS: types.settings, and serve.{listener,webhook_github} inside the function so `--version` and
      `config` do not pay for the socket layer.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

import os

from quantamind.types.settings import load

# The webhook secret is read from the environment at serve time and never from `Settings`, so it
# cannot reach `quantamind config` and be printed into a terminal scrollback or a CI log.
SECRET_VARIABLE = "QUANTAMIND_WEBHOOK_SECRET"


def run(port: int) -> int:
    """Bind, and say plainly what this endpoint does and does not do.

    The work callback is deliberately not wired to a pipeline. Everything from a delivery to a
    posted comment exists as decisions, but nothing yet clones a repository on receipt -- so the
    honest startup banner says the endpoint authenticates and acknowledges, and does not review.
    An endpoint that quietly accepted and dropped the work would be indistinguishable from one
    that was doing something.
    """
    from quantamind.ingest.diff import DiffReadFailed
    from quantamind.ingest.github_comments import CommentFailed
    from quantamind.serve.listener import build
    from quantamind.serve.review_delivery import deliver
    from quantamind.serve.webhook_github import MisconfiguredSecret, Review
    from quantamind.serve.working_clone import CloneFailed

    secret = os.environ.get(SECRET_VARIABLE, "")
    accepted: list[Review] = []

    settings = load()

    def work(review: Review) -> None:
        accepted.append(review)
        print(
            f"[serve] accepted {review.repo}#{review.number} at {review.head_sha[:12]}", flush=True
        )
        # **A FAILURE HERE MUST NOT BE SWALLOWED AND MUST NOT KILL THE THREAD SILENTLY.** The
        # listener leaves the delivery without a `completed_at` when this raises, which makes
        # GitHub's redelivery a legitimate retry -- so the exception is allowed to propagate after
        # it has been named. What is NOT allowed is a bare except that turns a broken pipeline into
        # a quiet 202, which is indistinguishable from a working one.
        try:
            done = deliver(review.repo, review.number, review.head_sha, settings)
        except (CloneFailed, CommentFailed, DiffReadFailed) as exc:
            print(f"[serve] {review.repo}#{review.number} FAILED: {exc}", flush=True)
            raise
        if done.body is not None and not settings.posting_enabled:
            print(f"[serve] --- comment it would have posted ---\n{done.body}", flush=True)
        print(f"[serve] {review.repo}#{review.number}: {done.sentence()}", flush=True)

    try:
        server = build(settings, secret, work, port=port)
    except MisconfiguredSecret as exc:
        print(f"configuration error: {exc}\n\nSet {SECRET_VARIABLE} and try again.")
        return 1
    except OSError as exc:
        print(f"could not bind port {port}: {exc}")
        return 1

    # **`flush=True`, AND IT IS NOT DECORATION.** Python block-buffers stdout when it is a pipe
    # rather than a terminal, which is every real deployment -- systemd, Docker, CI, a log file.
    # `serve_forever()` then never returns, the 4 KB buffer never fills, and SIGTERM kills the
    # process without flushing: the banner is not merely late, it is LOST. Found by running the
    # command under a pipe, having passed every test that captured it in-process. The line this
    # cost is the one that matters most -- "IT DOES NOT REVIEW", invisible to exactly the operator
    # who needed it. `tests/unit/layers/serve/test_serve_banner.py` reads it through a real pipe.
    #
    # `server_address[0]` is bytes on some address families; `build()` binds loopback, so the
    # host is stated rather than formatted out of the tuple.
    print(f"[serve] listening on 127.0.0.1:{server.server_address[1]}", flush=True)
    print(
        "[serve] POST /webhook  — verifies the signature, refuses a replay, answers 202", flush=True
    )
    print(
        "[serve] GET  /health   — opens the store and reports what is wrong, never raises",
        flush=True,
    )
    print(
        "[serve] IT DOES NOT REVIEW. The work callback logs and returns; see run_endpoint.py.",
        flush=True,
    )
    print(
        "[serve] http.server is not a hardened edge — run it behind a TLS-terminating proxy.",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[serve] stopping", flush=True)
    finally:
        server.shutdown()
        server.server_close()
    return 0
