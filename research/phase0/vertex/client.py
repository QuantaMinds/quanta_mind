"""Authenticated Vertex calls that survive a token expiry and never lose a completed request.

WHAT: Wraps `generateContent` with a token that is re-minted from `gcloud` on a 401, and returns
      the billed token counts together with the finish reason.
WHY:  Two defects in the first C3 run, both of which would have produced a wrong number rather
      than an error. The access token expires after about an hour and the run took fifty
      minutes, so it died at request 66 of 72 and wrote nothing -- correct refusal, total loss.
      And 11 of its 39 recorded answers were ONE token long behind six to thirteen thousand
      thinking tokens, which is what a MAX_TOKENS truncation looks like; reported without the
      finish reason it would have read as "the model found nothing", which is the exact shape of
      failure this project keeps hitting. The finish reason is now returned, never inferred.
IMPORTS: stdlib only (json, subprocess, urllib).
CONSUMED BY: `cost.py` in this package.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request

GCLOUD = "/opt/homebrew/share/google-cloud-sdk/bin/gcloud"
PROJECT, LOCATION = "quantamind-oss", "us-central1"


class VertexError(RuntimeError):
    """A call that failed for a reason other than an expired token."""


def mint() -> str:
    p = subprocess.run(
        [GCLOUD, "auth", "print-access-token"], capture_output=True, text=True, timeout=60
    )
    if p.returncode != 0:
        raise VertexError(f"gcloud could not mint a token: {p.stderr.strip()[:150]}")
    return p.stdout.strip()


class Client:
    """Holds one token and replaces it when Vertex says it is no longer valid."""

    def __init__(self, model: str) -> None:
        self.model = model
        self._token = mint()

    def _post(self, body: dict[str, object]) -> tuple[int, object]:
        url = (
            f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT}"
            f"/locations/{LOCATION}/publishers/google/models/{self.model}:generateContent"
        )
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, e.read()[:300].decode("utf-8", "replace")

    def generate(self, body: dict[str, object]) -> dict[str, object]:
        """One request. Re-mints once on 401; any other non-200 is raised, never swallowed."""
        status, resp = self._post(body)
        if status == 401:
            self._token = mint()
            status, resp = self._post(body)
        if status != 200 or not isinstance(resp, dict):
            raise VertexError(f"HTTP {status}: {str(resp)[:200]}")

        cand = (resp.get("candidates") or [{}])[0]
        text = "".join(
            part.get("text", "") for part in ((cand.get("content") or {}).get("parts") or [])
        )
        um = resp.get("usageMetadata") or {}
        return {
            "prompt": int(um.get("promptTokenCount", 0)),
            "out": int(um.get("candidatesTokenCount", 0)),
            "thoughts": int(um.get("thoughtsTokenCount", 0)),
            "cached": int(um.get("cachedContentTokenCount", 0)),
            "total": int(um.get("totalTokenCount", 0)),
            # never inferred: an empty answer and a truncated answer must not look the same
            "finish": str(cand.get("finishReason", "")),
            "text": text[:4000],
        }
