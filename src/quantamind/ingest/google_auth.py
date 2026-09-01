"""An access token for Google APIs, from the metadata server or from `gcloud`, never from a key.

WHAT: `token(gcloud_path)` returns a bearer token and the name of the source that produced it.
      `Unavailable` when neither source answers, naming both attempts.
WHY:  **THERE IS NO SERVICE-ACCOUNT KEY, AND THAT IS DELIBERATE.** The plan was a key file
      mirroring `app.pem`; the project's org policy refuses to issue one
      (`constraints/iam.disableServiceAccountKeyCreation`). It could be disabled — the account
      has owner — and is not, because a long-lived downloadable credential is worse than the
      inconvenience it removes. A container on GCP reads a token from the metadata server, which
      means **no credential on disk at all**, and that is a stronger answer to "what do you do
      with our code?" than any key-handling policy.

      **`gcloud` WAS COMPILED INTO THE PRODUCT AS A HOMEBREW PATH.** `/opt/homebrew/share/...`
      was correct on one laptop and absent in the container, so Half B would have failed there
      exactly as the unauthenticated clone did. It survives only as the DEVELOPMENT source.

      **THE METADATA PROBE MUST BE FAST, AND THAT IS CORRECTNESS RATHER THAN TUNING.**
      `metadata.google.internal` does not resolve off GCP. Without a short timeout every review on
      a laptop would stall on DNS before falling back, and a product that takes ten seconds to
      decide it is not on GCP looks broken rather than unconfigured.

      **A FAILURE NAMES EVERY SOURCE IT TRIED.** "No access token" tells an operator nothing.
      "not on GCP (no metadata server), and gcloud is not installed" tells them which of the two
      deployments they are in and what to do about it.
IMPORTS: stdlib only (subprocess, urllib). No `google-auth`, which would be this product's first
      runtime dependency.
CONSUMED BY: `infer/gemini.py`.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from typing import NamedTuple

from quantamind.types.deployment import Destination, permit

METADATA_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
)
# **ONE SECOND, BECAUSE OFF GCP THIS HOST DOES NOT RESOLVE.** Long enough for a real metadata
# server, which answers from the local hypervisor in single-digit milliseconds; short enough that
# a laptop falls through to `gcloud` before anybody notices.
METADATA_TIMEOUT_S = 1.0
GCLOUD_TIMEOUT_S = 30


class Unavailable(RuntimeError):
    """No source produced a token. Carries what was tried, so the reader knows where they are."""


class Token(NamedTuple):
    """The token and the source that produced it. **The source is carried so it can be logged**
    without logging the token: "metadata" and "gcloud" are different deployments, and an operator
    debugging a permission error needs to know which identity was used."""

    value: str
    source: str


def _from_metadata() -> str | None:
    """A token from the GCP metadata server, or `None` when we are not on GCP."""
    request = urllib.request.Request(METADATA_URL, headers={"Metadata-Flavor": "Google"})
    try:
        # **ASK BEFORE THE SOCKET OPENS.** D7f: an air-gapped deployment REFUSES
        # this, rather than attempting it and failing somewhere the customer sees
        # in their egress log and we do not.
        permit(Destination.GOOGLE_METADATA)
        with urllib.request.urlopen(request, timeout=METADATA_TIMEOUT_S) as reply:
            body = json.loads(reply.read())
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        # Not on GCP, or the metadata server refused. Both mean "ask the next source", and
        # neither is an error worth raising while another source may still answer.
        return None
    value = body.get("access_token")
    return str(value) if value else None


def _from_gcloud(gcloud_path: str) -> str | None:
    """A token from a developer's own `gcloud` login, or `None` when it is absent or logged out."""
    try:
        done = subprocess.run(
            [gcloud_path, "auth", "print-access-token"],
            capture_output=True,
            text=True,
            timeout=GCLOUD_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    printed = done.stdout.strip()
    return printed if done.returncode == 0 and printed else None


def token(gcloud_path: str = "gcloud") -> Token:
    """A bearer token, and which source produced it. Raises naming both when neither does."""
    from_metadata = _from_metadata()
    if from_metadata:
        return Token(from_metadata, "metadata")
    from_gcloud = _from_gcloud(gcloud_path)
    if from_gcloud:
        return Token(from_gcloud, "gcloud")
    raise Unavailable(
        f"no access token: not on GCP (no metadata server answered in {METADATA_TIMEOUT_S}s), "
        f"and {gcloud_path!r} produced none. On GCP this needs a service account attached to the "
        f"instance; on a laptop, `gcloud auth login`."
    )
