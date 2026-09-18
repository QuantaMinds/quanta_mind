"""What a subscription IS, kept as its own package so the money types are one thing to read.

`subscription.py` holds `Standing`, `Subscription` and the refusal for a status this build does not
know. Split into a package when `types/` reached its fifteen-file cap — and the split is by concern
rather than by alphabet: everything here is about whether an account is paying, which is the one
question in the type layer that has an answer outside this codebase.

The names are re-exported so callers import `quantamind.types.billing` exactly as before. **A
re-export is not a second definition** — `AGENTS.md` rule 13 is about two FILES claiming one name,
and there is one file here.
"""

from quantamind.types.billing.subscription import (
    NotAStanding,
    Standing,
    Subscription,
    standing,
)

__all__ = ["NotAStanding", "Standing", "Subscription", "standing"]
