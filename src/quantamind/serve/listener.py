"""The socket. Authenticate, claim the delivery, acknowledge inside ten seconds, then work.

WHAT: the request handler. It owns `POST /webhook` — verify, claim, answer, then work — and hands
      every other path to `serve/web/{get_reply,post_routes}.py`, which build replies as values.
WHY:  **STDLIB, AND THE DEPENDENCY COUNT STAYS AT ZERO.** The plan calls this "a separate decision
      about whether to take a framework or use stdlib", and it is the first runtime dependency this
      project would ever take. What this endpoint needs is one POST route, an HMAC compare and a
      status code — no routing table, no serialisation layer, no ORM. A framework would be paid for
      on every install to save perhaps forty lines.

      **`http.server` IS NOT A HARDENED PRODUCTION SERVER, AND ITS OWN DOCUMENTATION SAYS SO.** No
      rate limiting, no TLS, no slow-loris defence. **Run it behind a reverse proxy that terminates
      TLS** and treat this process as an application rather than an edge. That is a deployment
      requirement, written here because a reader who mistakes this for a web server will not find
      the warning anywhere else.

      **VERIFY BEFORE PARSE, ALWAYS.** The body is read by `Content-Length` and handed to
      `verify()` as raw bytes before anything treats it as JSON. Parsing first would run an
      untrusted document through a parser for anyone who can reach the port — and the HMAC covers
      the exact bytes, so re-serialising to check a signature is how an authentic delivery starts
      failing.

      **ACKNOWLEDGE, THEN WORK, WHICH IS WHAT `begin()`/`complete()` EXIST FOR.** GitHub requires a
      2XX within ten seconds; a real run clones and indexes a repository and will not finish in
      ten. So the handler claims the delivery, answers **202**, and processes afterwards. If the
      process dies mid-work the row has no `completed_at`, and GitHub's redelivery — which reuses
      the GUID — is a legitimate retry rather than a replay.
IMPORTS: serve.{webhook_github,web.*}, store.{deliveries,schema,tenancy}. Rightmost layer.
CONSUMED BY: `serve/cli.py`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

from quantamind.serve.installation.installation_event import settle
from quantamind.serve.web import get_reply, post_routes
from quantamind.serve.web.http_io import read_body
from quantamind.serve.webhook_github import (
    DELIVERY_HEADER,
    EVENT_HEADER,
    SIGNATURE_HEADER,
    interpret,
    verify,
)
from quantamind.store import deliveries, schema, tenancy
from quantamind.types.forge.delivery import Ignore, Installed, Review, Withdrawn

# GitHub's documented maximum payload is 25 MB. A read with no ceiling is memory exhaustion handed
# to anyone who can reach the port, and Content-Length is attacker-controlled.
MAX_BODY_BYTES = 25 * 1024 * 1024
WEBHOOK_PATH = "/webhook"

Work = Callable[[Review], None]


class _Handler(BaseHTTPRequestHandler):
    server_version = "quantamind"
    sys_version = ""  # do not advertise the Python version

    settings: Any
    secret: str
    provision_secret: str = ""
    work: Work

    def _say(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        """One line per request, on stdout, without the client address the stdlib would print."""
        print(f"[listener] {fmt % args}", flush=True)

    def do_GET(self) -> None:
        # **THE GUARD do_POST HAS, WRITTEN FOR THE WEBHOOK AND NEVER APPLIED HERE.** A browser at
        # `/` before any account store existed got a dropped connection and no status: the stdlib
        # handler closes the socket on an unhandled exception, which nobody can see or report.
        try:
            self._get()
        except Exception as exc:
            print(
                f"[listener] unhandled fault on GET {self.path}: {type(exc).__name__}: {exc}",
                flush=True,
            )
            self._say(500, {"error": f"{type(exc).__name__}: {exc}"})

    def _get(self) -> None:
        # Every GET, health included, comes back as a `Reply` that was built without a socket --
        # so a forged callback is testable as a value. Unknown paths 404 there, not here.
        reply = get_reply.reply_for(self.path, self.headers.get("Cookie", ""), self.settings)
        body = reply.body.encode()
        self.send_response(reply.status)
        for name, value in reply.headers:
            self.send_header(name, value)
        self.send_header("Content-Type", reply.kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        # As above, and GitHub records a dropped POST as a failed delivery with no status -- the
        # least diagnosable outcome. Answered 500 so a redelivery retries something we can see.
        try:
            self._post()
        except Exception as exc:
            print(f"[listener] unhandled fault: {type(exc).__name__}: {exc}", flush=True)
            self._say(500, {"error": f"{type(exc).__name__}: {exc}"})

    def _post(self) -> None:
        # Provisioning, checkout and the Stripe webhook. `None` means this is not one of them --
        # `/webhook` below is still the listener's, because it alone is answered before it is
        # worked. -> `serve/web/post_routes.py`.
        posted = post_routes.route(self)
        if posted is not None:
            self._say(*posted)
            return
        if self.path != WEBHOOK_PATH:
            self._say(404, {"error": "no such path"})
            return
        body, why = read_body(self)
        if body is None:
            self._say(411, {"error": why})
            return

        # AUTHENTICATE FIRST. Nothing below reads the body as a document until this has passed.
        #
        # `verify()` raises `MisconfiguredSecret` on an empty secret, and this deliberately does NOT
        # catch it. `build()` refuses to bind on `not secret.strip()`, which is strictly stronger,
        # so the branch would be UNREACHABLE -- the exact defect rule 14 names: a check that runs
        # only where the thing it checks cannot happen is indistinguishable from a real negative.
        # The pair is held together by a test instead, not by a handler nothing can enter.
        rejected = verify(self.secret, body, self.headers.get(SIGNATURE_HEADER))
        if rejected is not None:
            self._say(401, {"error": rejected.value})
            return

        delivery_id = self.headers.get(DELIVERY_HEADER, "")
        event = self.headers.get(EVENT_HEADER, "")
        decision = interpret(event, body)
        if isinstance(decision, Ignore):
            # **THE REASON IS PRINTED, NOT ONLY RETURNED.** It went into the HTTP body, which
            # GitHub reads and discards, so an operator watching the log saw `200` and could not
            # tell an ignored ping from a completed review. `Ignore` has carried a reason all
            # along; nothing was showing it to the person who needed it.
            print(f"[serve] ignored {event!r}: {decision.reason}", flush=True)
            self._say(200, {"ignored": decision.reason})
            return

        if isinstance(decision, Installed | Withdrawn):
            # Answers in the middle: provisioning is fast, warming a repository is not.
            settle(decision, self.settings, self._say)
            return

        # **THE DELIVERY LEDGER IS ITS OWN STORE, BESIDE THE TENANTS AND NOT INSIDE ONE.**
        # Delivery ids are global -- the same id must not be processed twice for ANY tenant -- so
        # the ledger cannot live in a tenant's file. `tenancy.tenants()` globs `<root>/<owner>/*.db`
        # and so does not mistake this for a customer. This line once opened `database_path` as a
        # database after it became a ROOT; the same defect outlived it in `run_dashboard`, and
        # `docs/engineering/CODEBASE.md` records both under the compliance section.
        conn = schema.open_store(
            tenancy.shared(Path(self.settings.database_path), tenancy.DELIVERIES)
        )
        try:
            try:
                fresh = deliveries.begin(conn, delivery_id, event)
            except ValueError as exc:
                self._say(400, {"error": str(exc)})
                return
            if not fresh:
                self._say(200, {"replay": delivery_id, "note": "already completed, not repeated"})
                return

            # ANSWERED BEFORE THE WORK RUNS. See the module docstring.
            self._say(202, {"accepted": delivery_id, "repo": decision.repo, "pr": decision.number})
            try:
                self.work(decision)
            except Exception as exc:
                print(f"[listener] {delivery_id} FAILED, left retryable: {exc}", flush=True)
                return
            deliveries.complete(conn, delivery_id)
        finally:
            conn.close()
