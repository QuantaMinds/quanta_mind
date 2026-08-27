"""The environment a `git` subprocess needs to read a customer's private repository.

WHAT: `environment(token)` returns the environment for a `git clone`/`fetch`/`ls-remote` against
      github.com, authenticated as a GitHub App installation when a token is given. `None` means
      no credential, which is the right answer for a public repository and for the bench.
WHY:  **THE CLONE WAS NEVER AUTHENTICATED, AND NOTHING NOTICED FOR AS LONG AS A DEVELOPER RAN
      IT.** `serve/working_clone.py` cloned `https://github.com/<repo>.git` with no credential at
      all. On a laptop that works and looks like proof: git finds the developer's credential
      helper -- a keychain entry, a `gh` login, a `~/.git-credentials` -- and authenticates as a
      PERSON who happens to have access. In a container there is no helper and no person, so git
      falls through to asking a terminal for a username and exits 128:

          fatal: could not read Username for 'https://github.com': No such device or address

      **THIS FAILED 100% OF REAL DELIVERIES AND 0% OF TESTS.** Customer repositories are private
      -- that is what a code reviewer is for -- so the unauthenticated clone could never fetch
      one. It was found by the first genuine `pull_request` event reaching the running container,
      not by any test, because every test either used a local fixture repository or ran on a
      machine where the developer's own credentials silently answered. It is the same illusion
      the `gh` CLI dependency created and that the `Dockerfile` was written to expose; packaging
      caught that one at build time and this one needed a delivery.

      **THE TOKEN GOES IN A HEADER, NOT IN THE URL.** `https://x-access-token:<token>@github.com/`
      is the common recipe and it is wrong here for two independent reasons. First, `git clone`
      WRITES the URL it was given into `.git/config` as `remote.origin.url`, so the secret is
      persisted to the clone root and stays there; the clone outlives the delivery. Second, an
      installation token expires in an hour while a clone is reused for months -- so the second
      delivery would fetch with a credential that is both stale and on disk. A header supplied
      per-process authenticates this one command and leaves nothing behind.

      **AND IT IS PASSED THROUGH THE ENVIRONMENT, NOT ON THE COMMAND LINE.** `git -c
      http.extraheader=...` puts the credential in `argv`, which is readable by any process on the
      box through `ps`. `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_n`/`GIT_CONFIG_VALUE_n` is the
      documented way to set configuration for one invocation, and an environment is not shared
      with every other process on the machine.

      **THE HEADER IS SCOPED TO github.com ON PURPOSE.** The configuration key carries the URL
      prefix, so a repository with a submodule or a remote pointing somewhere else does not have
      the customer's installation token sent to that host. An unscoped `http.extraheader` sends
      the credential to whatever the repository names, which the repository controls.

      **`GIT_TERMINAL_PROMPT=0` IS NOT DEFENSIVE DECORATION.** Without it, git responds to a
      missing credential by trying to ASK. With no terminal that produced the confusing message
      above; with one -- a developer running the endpoint in a shell -- git BLOCKS on the prompt
      and the delivery never returns, holding the listener thread until the clone timeout. Off, a
      missing or expired token is an immediate non-zero exit that `CloneFailed` can name.
IMPORTS: stdlib only (base64, os). Nothing from the product; the caller supplies the token.
CONSUMED BY: `serve/working_clone.py`.
"""

from __future__ import annotations

import base64
import os

# GitHub's documented username for an installation token used over HTTPS. The password is the
# token; the username is a fixed literal and is not a secret.
APP_USERNAME = "x-access-token"

# Scoped, so the credential reaches github.com and nothing a repository might name instead.
HEADER_KEY = "http.https://github.com/.extraheader"


def environment(token: str | None = None) -> dict[str, str]:
    """The environment for one git subprocess: the caller's, plus a credential if there is one.

    Returns a COMPLETE environment rather than the additions alone, because `subprocess` replaces
    the inherited environment when `env=` is passed -- handing it only these keys would strip
    `PATH`, `HOME` and the proxy settings a customer's network may require, turning an
    authentication fix into "git: command not found".

    `token=None` returns the caller's environment with prompting disabled and no credential. That
    is not a degraded mode: a public repository needs no token, and the research bench reads only
    public repositories. What it must never do is silently fall back to the AMBIENT credentials
    that hid this bug -- and it does not, because nothing here consults a credential helper.
    """
    env = dict(os.environ)
    # Never inherit a caller's prompt setting: the point is that this process must not block.
    env["GIT_TERMINAL_PROMPT"] = "0"
    if token is None:
        return env
    basic = base64.b64encode(f"{APP_USERNAME}:{token}".encode()).decode("ascii")
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = HEADER_KEY
    env["GIT_CONFIG_VALUE_0"] = f"Authorization: Basic {basic}"
    return env
