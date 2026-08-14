"""One frozen settings object, read from the environment once and validated on the spot.

WHAT: `Settings`, and `load()` which builds it from a mapping (the environment by default).
WHY:  No module reads the environment directly. A service that picks up configuration in
      scattered places acquires undocumented configuration -- nobody can say what it is
      running on, and a wrong value shows up as behaviour rather than as an error. Reading
      it in one place and validating at construction turns a misconfiguration into a
      startup failure with a name in it.
IMPORTS: stdlib only (dataclasses, os). No project imports -- this must load before anything.
CONSUMED BY: serve constructs it at startup and hands it down; nothing else reads os.environ.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

PREFIX = "QUANTAMIND_"

# Three requests: a deep read of rank 1 at one pass, and one shallow read each for ranks 2
# and 3. One pass at rank 1 is a decision, not a default -- at two passes allocation costs
# more than reading the whole diff, which inverts the argument for having an allocator.
DEFAULT_MAX_REQUESTS = 3

# A top-decile rule fires on 10-12% of pull requests across an eighty-fold range of
# repository velocity, where "twelve prior touches" fired on 11% of one and 53% of another.
DEFAULT_THRESHOLD_PERCENTILE = 0.9


class SettingsError(Exception):
    """Raised when configuration is missing or unusable. Carries the variable name."""

    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"{PREFIX}{name}: {reason}")
        self.name = name
        self.reason = reason


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

    @property
    def runs_model(self) -> bool:
        return self.inference_enabled and self.max_requests > 0


def _read_int(env: Mapping[str, str], name: str, fallback: int) -> int:
    raw = env.get(PREFIX + name)
    if raw is None:
        return fallback
    try:
        return int(raw)
    except ValueError as exc:
        raise SettingsError(name, f"expected an integer, got {raw!r}") from exc


def _read_float(env: Mapping[str, str], name: str, fallback: float) -> float:
    raw = env.get(PREFIX + name)
    if raw is None:
        return fallback
    try:
        return float(raw)
    except ValueError as exc:
        raise SettingsError(name, f"expected a number, got {raw!r}") from exc


def _read_bool(env: Mapping[str, str], name: str, fallback: bool) -> bool:
    raw = env.get(PREFIX + name)
    if raw is None:
        return fallback
    lowered = raw.strip().lower()
    if lowered in ("1", "true", "yes", "on"):
        return True
    if lowered in ("0", "false", "no", "off"):
        return False
    raise SettingsError(name, f"expected a boolean, got {raw!r}")


def load(env: Mapping[str, str] | None = None) -> Settings:
    """Build settings from a mapping, defaulting to the process environment.

    Takes the mapping as an argument so tests configure it by passing a dict rather than by
    mutating global state -- a test that sets os.environ leaks into whatever runs next.
    """
    source: Mapping[str, str] = os.environ if env is None else env
    return Settings(
        database_path=source.get(PREFIX + "DATABASE_PATH", "quantamind.db"),
        max_requests=_read_int(source, "MAX_REQUESTS", DEFAULT_MAX_REQUESTS),
        threshold_percentile=_read_float(
            source, "THRESHOLD_PERCENTILE", DEFAULT_THRESHOLD_PERCENTILE
        ),
        inference_enabled=_read_bool(source, "INFERENCE_ENABLED", False),
        model=source.get(PREFIX + "MODEL", "claude-opus-5"),
        subprocess_timeout_seconds=_read_int(source, "SUBPROCESS_TIMEOUT_SECONDS", 30),
    )
