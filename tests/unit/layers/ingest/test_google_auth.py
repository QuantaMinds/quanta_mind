"""A token, from wherever we are running — and a failure that says where we are not.

WHAT: Exercises `ingest/google_auth.token()` for real: the fallback to `gcloud`, the refusal when
      no source answers, and the bound on the metadata probe.
WHY:  **THE METADATA PROBE MUST NOT HANG, AND THAT IS CORRECTNESS RATHER THAN TUNING.**
      `metadata.google.internal` does not resolve off GCP. Without a bound, every review on a
      laptop would stall on DNS before falling back, and a product that takes ten seconds to
      decide it is not on GCP looks broken rather than unconfigured. The timing assertion here is
      the only thing that would catch that bound being removed.

      **AND A REFUSAL MUST NAME EVERY SOURCE IT TRIED.** "No access token" tells an operator
      nothing. This is not a style preference: the CLI's own `gcloud` path was broken while the
      webhook's worked, and the only reason it was found was that the message named which source
      had been asked and with what path.
IMPORTS: ingest.google_auth, types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import socket
import threading
import time

import pytest

from quantamind.ingest import google_auth
from quantamind.types.settings import load

NO_SUCH_GCLOUD = "/nonexistent/path/to/gcloud"


def test_no_source_at_all_refuses_and_names_both() -> None:
    """Off GCP with no usable gcloud, the failure has to say which two things were tried."""
    with pytest.raises(google_auth.Unavailable) as caught:
        google_auth.token(NO_SUCH_GCLOUD)

    message = str(caught.value)
    assert "metadata" in message, f"the refusal does not mention the metadata server: {message!r}"
    assert NO_SUCH_GCLOUD in message, (
        f"the refusal does not name the gcloud path it tried: {message!r}. That path being wrong "
        "is exactly the failure this message exists to make findable"
    )


def test_the_metadata_probe_is_bounded_against_a_host_that_never_answers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**THE ONE THAT MATTERS OFF GCP**, and the first version of it was vacuous.

    Timing `token()` on this machine proves nothing: `metadata.google.internal` fails DNS
    instantly, so the timeout never engages and widening it to 15s still passed in 0.10s. Verified
    by sabotage, which is the only reason it was caught.

    So this points the probe at a real socket that ACCEPTS and never replies — the shape a
    metadata server takes when a network blackholes it. Without a read timeout this blocks
    forever, which is why the call runs on a bounded thread rather than inline: an unbounded probe
    must fail the test rather than hang the suite, the same reasoning as the serve-banner test.
    """
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    monkeypatch.setattr(
        google_auth, "METADATA_URL", f"http://127.0.0.1:{listener.getsockname()[1]}/t"
    )

    answered: list[str | None] = []
    prober = threading.Thread(
        target=lambda: answered.append(google_auth._from_metadata()), daemon=True
    )
    started = time.monotonic()
    prober.start()
    prober.join(timeout=10.0)
    elapsed = time.monotonic() - started
    still_running = prober.is_alive()
    listener.close()

    assert not still_running, (
        f"the probe was still blocked after {elapsed:.1f}s against a host that accepts and never "
        f"replies. The bound is {google_auth.METADATA_TIMEOUT_S}s and it is what stops every "
        "review on a laptop stalling before it falls through to gcloud"
    )
    assert answered == [None], f"a silent host produced {answered!r} rather than 'not on GCP'"


def test_a_token_carries_the_source_that_produced_it() -> None:
    """Which identity answered is what an operator needs when a permission error appears."""
    path = load().gcloud_path
    try:
        got = google_auth.token(path)
    except google_auth.Unavailable:
        pytest.skip(f"no Google credentials available here (gcloud_path={path!r})")

    assert got.source in {"metadata", "gcloud"}, f"unnamed source: {got.source!r}"
    assert got.value and got.value != got.source, "the token must be the token, not its label"


def test_an_empty_gcloud_path_setting_falls_back_rather_than_being_used() -> None:
    """**FOUND BY THIS PRODUCT'S OWN DEEP REVIEW**, on the commit that added the setting.

    `QUANTAMIND_GCLOUD_PATH=` — set but empty, which is what commenting a line out in a `.env`
    produces — returned `""` from a `get` default, and `subprocess.run([""])` then fails with
    something that names no cause.
    """
    assert load({"QUANTAMIND_GCLOUD_PATH": ""}).gcloud_path == "gcloud"
    assert load({}).gcloud_path == "gcloud"
    assert load({"QUANTAMIND_GCLOUD_PATH": "/opt/x/gcloud"}).gcloud_path == "/opt/x/gcloud"
