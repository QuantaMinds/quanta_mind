"""Where configuration comes from on disk, kept apart from what configuration IS.

WHAT: `DOTENV` is the path, `from_file` parses it. Neither knows what any key means.
WHY:  **SPLIT FROM `types/settings.py` AT THE 200-LINE CAP, AND IT IS A REAL SEAM.** That module
      defines the settings and their defaults; this one answers a different question — reading a
      file off disk and turning lines into a mapping — and it is the half with the security note.

      **THE PATH IS THE REPOSITORY ROOT, NOT THE PACKAGE DIRECTORY.** A `.env` inside
      `src/quantamind/` is package data, and a wheel build can carry package data into a published
      artefact — which would ship a webhook secret and a client secret to anyone who installs it.
      Being gitignored does not help: gitignore governs git, not `build`.
IMPORTS: stdlib pathlib. Nothing from any layer.
CONSUMED BY: `types/settings.py:load`.
"""

from __future__ import annotations

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
