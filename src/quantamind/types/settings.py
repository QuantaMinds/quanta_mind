"""One frozen settings object, read from the environment once and validated on the spot.

WHAT: `Settings`, and `load()` which builds it from a mapping (the environment by default).
WHY:  No module reads the environment directly. A service that picks up configuration in
      scattered places acquires undocumented configuration -- nobody can say what it is
      running on, and a wrong value shows up as behaviour rather than as an error. Reading
      it in one place and validating at construction turns a misconfiguration into a
      startup failure with a name in it.
IMPORTS: stdlib only (dataclasses, os). No project imports -- this must load before anything.
CONSUMED BY: serve constructs it at startup and hands it down; nothing else reads os.environ.
      `SettingsError` is re-exported from `types/env_values.py` so its callers are unchanged.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from quantamind.types.env_values import (
    PREFIX,
    SettingsError,
    read_bool,
    read_float,
    read_int,
)

# **RE-EXPORTED, NOT RELOCATED-AND-FORGOTTEN.** `SettingsError` moved to `types/env_values.py` when
# this file hit the 200-line cap. Six modules import it from here, and the failure they catch has
# not changed, so the name stays reachable where it has always been rather than editing every
# `except` clause in the tree to chase a refactor.
__all__ = ["DOTENV", "PREFIX", "Settings", "SettingsError", "from_file", "load"]

# Three requests: a deep read of rank 1 at one pass, and one shallow read each for ranks 2
# and 3. One pass at rank 1 is a decision, not a default -- at two passes allocation costs
# more than reading the whole diff, which inverts the argument for having an allocator.
DEFAULT_MAX_REQUESTS = 3

# A top-decile rule fires on 10-12% of pull requests across an eighty-fold range of
# repository velocity, where "twelve prior touches" fired on 11% of one and 53% of another.
DEFAULT_THRESHOLD_PERCENTILE = 0.9


@dataclass(frozen=True, slots=True)
class Settings:
    """Everything the process needs to know, fixed at startup.

    `inference_enabled` defaults to False on purpose. The deterministic path is the whole
    free tier, it needs no key, and a process that starts calling a model because a default
    said so is the expensive kind of surprise.
    """

    database_path: str = "quantamind.db"
    max_requests: int = DEFAULT_MAX_REQUESTS
    threshold_percentile: float = DEFAULT_THRESHOLD_PERCENTILE
    inference_enabled: bool = False
    model: str = "claude-opus-5"
    subprocess_timeout_seconds: int = 30
    clone_root: str = ".quantamind-clones"
    app_id: str = ""
    """The GitHub App's numeric id. Public: it identifies the App, it authorises nothing."""

    public_read_token: str = ""
    """Used ONLY where we are NOT installed, never a customer -- see `ingest/github_api`.

    Unauthenticated is 60/hour and one live run exhausts it. The installation token is tried
    FIRST, so this cannot reach a repository the App is installed on.
    """

    gcloud_path: str = "gcloud"
    """How to invoke gcloud. **A HOMEBREW PATH WAS COMPILED INTO THE PRODUCT.**

    `infer/gemini.py` defaulted to `/opt/homebrew/share/google-cloud-sdk/bin/gcloud` — correct on
    one laptop and absent in the container, where Half B would have failed the way the clone did.
    The default is now the bare name, resolved from PATH like any other tool.
    """

    inference_project: str = ""
    """The GCP project the model is billed to. Empty means the webhook runs NO inference.

    The CLI takes it as `--deep <project>`; a webhook has no argv. Two deliberate acts before a
    delivery costs anybody money, rather than one forgotten default.
    """

    app_key_path: str = ""
    """Where the App's private key lives. **THE PATH IS CONFIGURATION; THE KEY IS NOT.** The key is
    read from disk at the moment it signs and never held here, for the same reason the webhook
    secret is read in `serve/run_endpoint.py` rather than stored: a credential in a settings object
    reaches a log or a config dump the first time anybody prints one."""

    posting_enabled: bool = False
    """**False on purpose, and it is the one default that writes to somebody else's project.**
    With it off the endpoint runs the whole pipeline and prints the comment it would have posted,
    which is a complete rehearsal of a delivery and touches nothing. A process that starts
    commenting on a customer's pull requests because a default said so is not recoverable by
    changing the default back -- the comments are already there."""

    def __post_init__(self) -> None:
        if self.max_requests < 0:
            raise SettingsError("MAX_REQUESTS", f"cannot be negative, got {self.max_requests}")
        if not 0.0 < self.threshold_percentile < 1.0:
            raise SettingsError(
                "THRESHOLD_PERCENTILE",
                f"must be strictly between 0 and 1, got {self.threshold_percentile}",
            )
        if self.subprocess_timeout_seconds <= 0:
            raise SettingsError(
                "SUBPROCESS_TIMEOUT_SECONDS",
                f"must be positive, got {self.subprocess_timeout_seconds}",
            )
        if not self.database_path:
            raise SettingsError("DATABASE_PATH", "is empty")
        # **POSTING WITHOUT AN APP IS NOT A DEGRADED MODE, IT IS A MISCONFIGURATION.** Without an
        # App the only way to comment is as whoever authenticated the `gh` CLI, which is the
        # developer-tool behaviour this replaced. Refusing at construction beats discovering it on
        # the first delivery a customer sees.
        if self.posting_enabled and not (self.app_id and self.app_key_path):
            raise SettingsError(
                "APP_ID",
                "posting is enabled but no GitHub App is configured; set QUANTAMIND_APP_ID and "
                "QUANTAMIND_APP_KEY_PATH, or leave QUANTAMIND_POSTING_ENABLED off",
            )

    @property
    def runs_model(self) -> bool:
        """**AND THE PROJECT:** `quantamind config` prints this, and a banner here already
        announced behaviour it did not have. Without a project the webhook cannot call a model."""
        return self.inference_enabled and self.max_requests > 0 and bool(self.inference_project)


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


def load(env: Mapping[str, str] | None = None) -> Settings:
    """Build settings from a mapping, defaulting to the process environment.

    Takes the mapping as an argument so tests configure it by passing a dict rather than by
    mutating global state -- a test that sets os.environ leaks into whatever runs next.
    """
    source: Mapping[str, str] = {**from_file(DOTENV), **os.environ} if env is None else env
    return Settings(
        database_path=source.get(PREFIX + "DATABASE_PATH", "quantamind.db"),
        max_requests=read_int(source, "MAX_REQUESTS", DEFAULT_MAX_REQUESTS),
        threshold_percentile=read_float(
            source, "THRESHOLD_PERCENTILE", DEFAULT_THRESHOLD_PERCENTILE
        ),
        inference_enabled=read_bool(source, "INFERENCE_ENABLED", False),
        model=source.get(PREFIX + "MODEL", "claude-opus-5"),
        subprocess_timeout_seconds=read_int(source, "SUBPROCESS_TIMEOUT_SECONDS", 30),
        clone_root=source.get(PREFIX + "CLONE_ROOT", ".quantamind-clones"),
        posting_enabled=read_bool(source, "POSTING_ENABLED", False),
        app_id=source.get(PREFIX + "APP_ID", ""),
        app_key_path=source.get(PREFIX + "APP_KEY_PATH", ""),
        public_read_token=source.get(PREFIX + "PUBLIC_READ_TOKEN", ""),
        inference_project=source.get(PREFIX + "INFERENCE_PROJECT", ""),
        gcloud_path=source.get(PREFIX + "GCLOUD_PATH", "gcloud"),
    )
