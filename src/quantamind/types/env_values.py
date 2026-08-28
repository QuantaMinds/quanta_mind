"""Reading one configuration value out of an environment mapping, and the error when it is junk.

WHAT: `PREFIX`, `SettingsError`, and the three typed readers `read_int`, `read_float`, `read_bool`.
      Each returns the fallback when a name is absent and RAISES when it is present and unusable.
WHY:  **SPLIT OUT OF `settings.py` AT THE 200-LINE CAP, AND IT IS a REAL SEAM.** `settings.py` owns
      what the product is configured to do; this owns turning a string into a value, which is a
      different job with a different failure mode.

      **AN UNPARSEABLE VALUE RAISES RATHER THAN FALLING BACK.** `QUANTAMIND_MAX_REQUESTS=three` is
      somebody trying to set a budget, and silently using the default would run a review at a limit
      they did not choose and never told them. Absent means "not configured"; present-and-wrong
      means "configured, badly", and the two must not produce the same value.
IMPORTS: stdlib only (collections.abc). Nothing from the product -- this loads before everything.
CONSUMED BY: `types/settings.py`, and `SettingsError` is re-exported there for its callers.
"""

from __future__ import annotations

from collections.abc import Mapping

PREFIX = "QUANTAMIND_"


class SettingsError(Exception):
    """Raised when configuration is missing or unusable. Carries the variable name."""

    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"{PREFIX}{name}: {reason}")
        self.name = name
        self.reason = reason


def read_int(env: Mapping[str, str], name: str, fallback: int) -> int:
    raw = env.get(PREFIX + name)
    if raw is None:
        return fallback
    try:
        return int(raw)
    except ValueError as exc:
        raise SettingsError(name, f"expected an integer, got {raw!r}") from exc


def read_float(env: Mapping[str, str], name: str, fallback: float) -> float:
    raw = env.get(PREFIX + name)
    if raw is None:
        return fallback
    try:
        return float(raw)
    except ValueError as exc:
        raise SettingsError(name, f"expected a number, got {raw!r}") from exc


def read_bool(env: Mapping[str, str], name: str, fallback: bool) -> bool:
    raw = env.get(PREFIX + name)
    if raw is None:
        return fallback
    lowered = raw.strip().lower()
    if lowered in ("1", "true", "yes", "on"):
        return True
    if lowered in ("0", "false", "no", "off"):
        return False
    raise SettingsError(name, f"expected a boolean, got {raw!r}")
