"""The credential must actually reach git, and must never reach the disk.

WHAT: Runs REAL `git` against the environment `ingest/git_credentials.environment()` builds, and a
      REAL `git clone` to prove the token is not written into the clone's config.
WHY:  **THE BUG THESE COVER SHIPPED BECAUSE EVERY TEST RAN WHERE A CREDENTIAL HELPER EXISTED.**
      The clone was unauthenticated and worked on a developer's machine, where git quietly
      authenticated as a person. So asserting "environment() returns a dict with these keys" would
      repeat the original mistake in a smaller form: it checks what we intended, not what git
      does. `git config --get` here is git PARSING our environment -- a wrong `GIT_CONFIG_COUNT`,
      a mistyped key, or a value git rejects fails these, and a dict-shape assertion would not.
IMPORTS: ingest.git_credentials. stdlib base64, os, subprocess, tempfile.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import base64
import os
import subprocess
import tempfile
from pathlib import Path

from quantamind.ingest.git_credentials import APP_USERNAME, HEADER_KEY, environment

GIT_TIMEOUT_S = 30
TOKEN = "ghs_ThisIsNotARealTokenItIsATestFixture"


def _git(
    args: list[str], env: dict[str, str], cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run git with ONLY the environment under test contributing configuration.

    **THIS USED TO INHERIT WHATEVER CONFIG THE WORKING DIRECTORY HAD, AND CI CAUGHT IT.**
    `git config --get` reads system, global and repository config as well as the environment.
    Under pytest the working directory is this repository, and on a GitHub Actions runner
    `actions/checkout` writes `http.https://github.com/.extraheader` into its `.git/config` —
    so `test_no_token_means_no_credential_and_still_no_prompt` found a credential it had not
    been given and failed, correctly, about the wrong subject.

    **IT IS THE SAME SHAPE AS THE BUG THIS FILE EXISTS FOR.** The module docstring says these
    tests were written because "every test ran where a credential helper existed"; the tests
    then ran where a credential CONFIG existed. A developer with a global `http.extraheader`
    would have seen the same failure locally and had no idea why.

    `/dev/null` for both config files and a directory outside any repository leaves exactly one
    source of truth: the dict `environment()` returned.
    """
    isolated = {**env, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_S,
        env=isolated,
        cwd=cwd or tempfile.gettempdir(),
    )


def test_git_reads_the_credential_out_of_the_environment_we_build() -> None:
    """git resolves our env into the exact Basic header GitHub expects. A real parse, not a dict."""
    done = _git(["config", "--get", HEADER_KEY], environment(TOKEN))

    assert done.returncode == 0, (
        f"git did not resolve {HEADER_KEY} from the environment: {done.stderr.strip()!r}. "
        f"GIT_CONFIG_COUNT/KEY_0/VALUE_0 is how the credential reaches a clone; if git will not "
        f"parse it, every private repository fails with 'could not read Username'."
    )
    scheme, _, encoded = done.stdout.strip().partition(" Basic ")
    assert scheme == "Authorization:", f"the header is malformed: {done.stdout.strip()!r}"
    assert base64.b64decode(encoded).decode() == f"{APP_USERNAME}:{TOKEN}", (
        "the decoded credential is not 'x-access-token:<token>'. GitHub rejects any other "
        "username for an installation token, and the failure looks like a bad token."
    )


def test_the_credential_is_scoped_to_github_and_not_sent_to_any_host() -> None:
    """An unscoped extraheader would send a customer's token wherever their repository points."""
    done = _git(["config", "--get", "http.extraheader"], environment(TOKEN))

    assert done.returncode != 0 and not done.stdout.strip(), (
        f"an UNSCOPED http.extraheader is set: {done.stdout.strip()!r}. git would then attach the "
        f"installation token to every http remote the repository names -- a submodule host, a "
        f"mirror -- and the repository, not us, chooses those."
    )


def test_no_token_means_no_credential_and_still_no_prompt() -> None:
    """A public repository needs no token. What it must never do is fall back to asking, or to
    whatever ambient credential happens to be on the machine."""
    env = environment(None)

    assert env["GIT_TERMINAL_PROMPT"] == "0", (
        "prompting is enabled. With a terminal, git BLOCKS on the username prompt and the "
        "delivery never returns; the listener thread is held until the clone timeout."
    )
    assert "GIT_CONFIG_KEY_0" not in env, "a credential was built for a caller that gave no token"
    assert _git(["config", "--get", HEADER_KEY], env).returncode != 0, (
        "git resolved a credential header with no token supplied"
    )


def test_a_real_clone_leaves_no_token_on_disk(tmp_path: Path) -> None:
    """**THE REASON THE TOKEN IS NOT IN THE URL.** `git clone` writes the URL it was given into
    `.git/config` as `remote.origin.url`. A token there outlives the delivery by months and is
    dead within the hour, so the next fetch authenticates with an expired secret read off disk.
    """
    origin, clone = tmp_path / "origin", tmp_path / "clone"
    origin.mkdir()
    assert _git(["init", "--quiet", "--bare", str(origin)], environment(None)).returncode == 0

    done = _git(["clone", "--no-checkout", f"file://{origin}", str(clone)], environment(TOKEN))
    assert done.returncode == 0, f"the fixture clone failed: {done.stderr.strip()!r}"

    config = (clone / ".git" / "config").read_text()
    assert TOKEN not in config, (
        f"the token was persisted into {clone / '.git' / 'config'}. It is supplied per-process "
        f"precisely so it cannot be, and a clone root full of live credentials is the failure "
        f"mode a URL-embedded token produces. Read: {config!r}"
    )
