"""Where configuration comes from on disk, kept apart from what configuration IS.

WHAT: `DOTENV` is the path, `from_file` parses it, `credential` reads ONE named secret from the
      same two sources `types/settings.load()` uses. None of them knows what any key means.
WHY:  **SPLIT FROM `types/settings.py` AT THE 200-LINE CAP, AND IT IS A REAL SEAM.** That module
      defines the settings and their defaults; this one answers a different question — reading a
      file off disk and turning lines into a mapping — and it is the half with the security note.

      **THE PATH IS THE REPOSITORY ROOT, NOT THE PACKAGE DIRECTORY.** A `.env` inside
      `src/quantamind/` is package data, and a wheel build can carry package data into a published
      artefact — which would ship a webhook secret and a client secret to anyone who installs it.
      Being gitignored does not help: gitignore governs git, not `build`.
      **`credential` EXISTS BECAUSE THREE SECRETS IN `.env` WERE READ BY NOTHING.**
      `serve/commands/run_endpoint.py` read `QUANTAMIND_WEBHOOK_SECRET`,
      `QUANTAMIND_PROVISION_SECRET` and the two Stripe values straight from `os.environ`, and
      `from_file` deliberately does not touch `os.environ` — so a `.env` holding the webhook secret
      produced *"no webhook secret: refusing to bind"*. **The file looked configured and was not**,
      which is the failure mode this project names repeatedly: a variable nothing reads is worse
      than an absent one. Verified by running the command, not by reading it.

      **IT IS A FUNCTION HERE AND NOT A FIELD ON `Settings`, AND THAT DISTINCTION IS THE WHOLE
      POINT.** `types/settings.py` refuses to hold credentials because `quantamind config` prints
      that object into a scrollback. This gives the same two sources with the same precedence
      without putting the value anywhere that gets printed.
IMPORTS: stdlib os and pathlib. Nothing from any layer.
CONSUMED BY: `types/settings.py:load`, and `serve/commands/run_endpoint.py` for credentials.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


def from_file(path: Path) -> dict[str, str]:
    """`KEY=VALUE` lines from a file, as a mapping. Missing file is an empty mapping, not an error.

    **IT DOES NOT TOUCH `os.environ`.** A loader that mutates the process environment makes every
    later reader depend on import order, and the effect outlives the test that caused it. This
    returns a value and `load()` decides what to do with it.

    **THE REAL ENVIRONMENT WINS.** A file checked into a working tree must never override what an
    operator exported for this process.
    """
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        out[key.strip()] = value.strip().strip("'\"")
    return out


DOTENV = Path(__file__).resolve().parents[3] / ".env"
"""The repository root, NOT the package directory.

**A `.env` INSIDE `src/quantamind/` IS PACKAGE DATA.** It was there, and a wheel build can carry
package data into a published artefact -- which would ship a webhook secret and a client secret to
anyone who installs it. Being gitignored does not help: gitignore governs git, not `build`. The
root is both the convention and outside the package."""


def credential(name: str, env: Mapping[str, str] | None = None) -> str:
    """One named secret, from the real environment first and the repository `.env` second.

    **THE REAL ENVIRONMENT WINS**, exactly as it does in `types/settings.load()`. A file in a
    working tree must never override what an operator exported for this process, and a container
    that has no `.env` at all must behave the same way it always has.

    **EMPTY WHEN ABSENT, NEVER A DEFAULT.** Every caller treats empty as a refusal — the endpoint
    will not bind without a webhook secret, and the billing routes answer 503 naming the variable
    rather than opening. Returning a placeholder here would defeat all of it at once.

    `env` is injectable so a test configures it by passing a dict rather than mutating global
    state; a test that sets `os.environ` leaks into whatever runs next.
    """
    if env is not None:
        return env.get(name, "")
    return os.environ.get(name) or from_file(DOTENV).get(name, "")
