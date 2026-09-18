"""The entitlement push reaches its handler through the dispatcher, not only in a unit test.

WHAT: `serve/web/post_routes.route` for `/entitlement`, driven through the same adapter a socket
      would use — `Content-Length`, an `rfile`, a bearer header.
WHY:  **EVERY OTHER TEST HERE CALLS `answer` DIRECTLY, SO NONE OF THEM CAN SEE THE ROUTE.** The
      registration in `post_routes` was DELETED and all 1267 unit tests stayed green: the handler
      was perfect and unreachable, which from the billing service's side is a 404 and an
      entitlement that never lands. AGENTS.md rule 14 — the suite's output was the same whether
      the route was wired or not.

      **IT ASSERTS `route()` DID NOT RETURN None, NOT THAT THE PUSH SUCCEEDED.** None is
      `post_routes`' word for "not my path", which is exactly what an unregistered route returns.
      Whether the push is then accepted or refused is the other tests' job; this one only proves
      the door exists.
IMPORTS: quantamind.serve.web.post_routes, quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from quantamind.serve.web import post_routes
from quantamind.types.settings import Settings


class _Handler:
    """The smallest thing `read_body` and `for_request` will accept."""

    def __init__(self, path: str, body: bytes, root: Path, secret: str = "s3cret") -> None:
        self.path = path
        self.rfile = io.BytesIO(body)
        self.headers: dict[str, str] = {
            "Content-Length": str(len(body)),
            "Authorization": f"Bearer {secret}",
        }
        self.provision_secret = secret
        self.settings = Settings(database_path=str(root))


def _body() -> bytes:
    return json.dumps(
        {
            "forge": "github",
            "account": "acme",
            "tier": "team",
            "state": "active",
            "seats_included": 5,
            "as_of": 1_700_000_000,
        }
    ).encode()


def test_the_dispatcher_routes_entitlement_to_its_handler(tmp_path: Path) -> None:
    got = post_routes.route(_Handler("/entitlement", _body(), tmp_path))

    assert got is not None, (
        "POST /entitlement was not routed. `post_routes.route` returned None, which means the "
        "reviewer answers 404 to every entitlement push the billing service sends."
    )
    status, _ = got
    assert status == 200, f"the route is registered but refused a well-formed push: {got}"


def test_a_query_string_does_not_lose_the_route(tmp_path: Path) -> None:
    # A proxy in front of the reviewer may append one. Matching the raw path would turn a correct
    # push into "no such route", which reads as a missing deployment rather than a rewritten URL.
    got = post_routes.route(_Handler("/entitlement?trace=abc", _body(), tmp_path))

    assert got is not None, "a query string made the entitlement route unreachable"
    assert got[0] == 200


def test_exactly_one_path_is_claimed_and_it_is_the_right_one(tmp_path: Path) -> None:
    """The whole matching decision as one value, so both ways of getting it wrong are visible.

    Asserting only that `/entitlement` routes would pass for a `route()` that claims EVERYTHING —
    including `/webhook`, which `serve/listener.py` owns and whose loss would take the GitHub path
    down with it. Asserting only that neighbours are refused would pass for a route that was never
    registered. The map is both at once.
    """
    paths = [
        "/entitlement",
        "/entitlement?trace=abc",
        "/entitlements",
        "/entitlement/extra",
        "/ENTITLEMENT",
        "/webhook",
        "/",
    ]
    claimed = {
        path: post_routes.route(_Handler(path, _body(), tmp_path)) is not None for path in paths
    }

    assert claimed == {
        "/entitlement": True,
        "/entitlement?trace=abc": True,
        "/entitlements": False,
        "/entitlement/extra": False,
        "/ENTITLEMENT": False,
        "/webhook": False,
        "/": False,
    }
