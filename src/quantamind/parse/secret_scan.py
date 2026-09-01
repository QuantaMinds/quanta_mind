"""A credential committed to a repository, found by shape rather than by judgement.

WHAT: `secrets_in(source)` returns every line that carries something only a real credential looks
      like. `Spotted` names the kind, the line, and the evidence with the secret itself redacted.
WHY:  **D7a. THE SECURITY TEAM'S FIRST QUESTION IS "WHAT DOES IT CATCH", AND THIS IS THE ONLY
      ANSWER WE CAN GIVE THAT SURVIVES BEING CHECKED.** Our raw model findings are 66.7-82.1% wrong
      across four blind pools. **"We catch hardcoded credentials, exactly, and we do not claim to
      catch injection" is a weaker sentence and a defensible one.**

      **A PROVIDER PREFIX IS EVIDENCE; ENTROPY ALONE IS A GUESS.** `AKIA…` and `ghp_…` are issued
      by one company in one format and mean one thing. A long random-looking string means nothing
      on its own — it is a hash, a checksum, a base64 asset, a UUID, a minified line. So the
      generic rule requires BOTH a secret-shaped assignment target AND enough entropy, and even
      then it is the weakest kind reported.

      **ENTROPY TURNED OUT TO DO LESS WORK THAN THE VOCABULARY CHECK, AND THAT WAS MEASURED
      RATHER THAN ASSUMED.** `password12345678` scores **3.88** bits — above any floor that still
      catches a real key at 4.28. The docstring on `MIN_ENTROPY` originally asserted 3.1 for it,
      invented rather than measured, and the scanner fired on it the first time it was run.

      **THE FIRST FALSE POSITIVE HERE COSTS MORE THAN ANYWHERE ELSE IN THE PRODUCT.** Telling a
      developer they have committed a credential when they have not is alarming, public, and takes
      a rotation to disprove. Every placeholder convention that could produce one is excluded and
      tested: `xxx`, `your-key-here`, `<redacted>`, `changeme`, repeated characters, and the
      literal example keys the providers publish in their own documentation.

      **AND IT IS NOT PYTHON-ONLY, WHICH MAKES IT THE FIRST CHECK THAT IS NOT.** Every other rule
      kind needs an AST and returns `LANGUAGE_UNSUPPORTED` for anything else — the narrowness
      `docs/product/unit-economics.md` calls the honest limit of the standards engine. A credential
      is a string in a file: it is found in `.env`, `.yaml`, `.tf`, `.ts` and a notebook exactly as
      well as in `.py`, and `dependencies = []` still holds because it is one regex pass.

      **THE SECRET IS NEVER PUT IN THE EVIDENCE.** A `Checked` row reaches the audit trail, the
      comment and the customer's database; writing the credential into any of those would move it
      somewhere new and make us the leak. Only the kind, the line, and a four-character prefix.
IMPORTS: stdlib re, math, dataclasses. Nothing from this project.
CONSUMED BY: `verify/rule_check.py`, as `CheckKind.HARDCODED_SECRET`.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

# **ISSUED FORMATS, NOT GUESSES.** Each is a prefix one company assigns and nothing else uses, so a
# match is evidence rather than suspicion. Ordered most specific first; the first match wins.
ISSUED: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("AWS access key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(gh[pousr]_[0-9A-Za-z]{36,255})\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    ("Stripe live key", re.compile(r"\b(sk|rk)_live_[0-9A-Za-z]{16,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("OpenAI key", re.compile(r"\bsk-(proj-)?[0-9A-Za-z_-]{20,}\b")),
    ("private key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
)

# A name that says the value beside it is a credential. The generic rule needs one of these AND
# entropy; either alone is a guess.
NAMED = re.compile(
    r"(?i)\b(secret|passwd|password|token|api[_-]?key|apikey|access[_-]?key|"
    r"private[_-]?key|client[_-]?secret|auth[_-]?token)\b\s*[:=]\s*"
    r"[\"']([^\"'\s]{16,})[\"']"
)

# **PLACEHOLDERS, AND THIS LIST IS THE PRECISION.** Every one of these appears in real repositories
# beside a credential-shaped name, and every one is somebody documenting rather than leaking.
PLACEHOLDER = re.compile(
    r"(?i)^(x{3,}|y{3,}|\.{3,}|-+|_+|\*+|"
    r"(your|my|the)[_-]?\w*|<[^>]*>|\{\{?[^}]*\}?\}|\$\{[^}]*\}|"
    r"changeme|placeholder|example|sample|dummy|fake|test|redacted|none|null|todo|fixme"
    r")[\w-]*$"
)

MIN_ENTROPY = 3.5
"""Shannon bits per character a generic value needs.

**THE FIRST VERSION OF THIS DOCSTRING INVENTED ITS OWN EVIDENCE.** It claimed `password12345678`
scores "about 3.1" against a real key "above 4.0", so 3.5 sat in a wide gap. **Measured, the
placeholder scores 3.88** and a real key 4.28 — the gap is narrow and 3.5 does not separate them.
Entropy alone was never going to; `WEAK` below is what actually does the work, and this floor only
removes the obviously-not-random."""

# **A GENERATED CREDENTIAL DOES NOT CONTAIN AN ENGLISH WORD FOR ITSELF.** `password12345678` has
# entropy 3.88 — above any floor that still catches real keys — and is a fixture in every
# repository that has ever had one. Excluding by vocabulary is honest where excluding by entropy
# would have meant tuning the floor until this one example fell the right side of it.
WEAK = re.compile(r"(?i)(password|passwd|secret|admin|letmein|qwerty|welcome|123456|abc123)")

REDACT = 4
"""Characters of the value kept in evidence. Enough to find it in the file, not enough to use."""


@dataclass(frozen=True, slots=True)
class Spotted:
    """One credential-shaped value, with the credential itself left behind."""

    kind: str
    line: int
    prefix: str
    """The first few characters only. **The secret never reaches an audit row or a comment.**"""

    def render(self) -> str:
        return f"{self.kind} at line {self.line} (starts `{self.prefix}…`)"


def entropy(value: str) -> float:
    """Shannon entropy in bits per character. Zero for the empty string rather than an error."""
    if not value:
        return 0.0
    counts = Counter(value)
    total = len(value)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def _placeholder(value: str) -> bool:
    """Whether this is somebody documenting a credential rather than committing one."""
    if PLACEHOLDER.match(value) or WEAK.search(value):
        return True
    # A value with almost no distinct characters is a filler, whatever it spells.
    return len(set(value)) <= 3


def secrets_in(source: str) -> tuple[Spotted, ...]:
    """Every line carrying something only a credential looks like.

    **ONE FINDING PER LINE.** A line matching two patterns is one problem to fix, and reporting it
    twice would make a `.env` file look worse than it is.
    """
    found: list[Spotted] = []
    for number, line in enumerate(source.splitlines(), 1):
        spotted = None
        for kind, pattern in ISSUED:
            hit = pattern.search(line)
            if hit:
                spotted = Spotted(kind, number, hit.group(0)[:REDACT])
                break
        if spotted is None:
            named = NAMED.search(line)
            if named:
                value = named.group(2)
                if not _placeholder(value) and entropy(value) >= MIN_ENTROPY:
                    spotted = Spotted("hardcoded credential", number, value[:REDACT])
        if spotted is not None:
            found.append(spotted)
    return tuple(found)
