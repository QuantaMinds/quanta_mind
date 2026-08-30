"""What one review cost, in the units a bill is written in.

WHAT: `Spend(requests, tokens_in, tokens_out, ms)` and `plus()` to add two together.
      **THIS ABSORBED `RequestLedger`, WHICH MEANT THE SAME THING.** That type carried requests,
      tokens in and tokens out and was read only by the budget gate; this one was written without
      noticing it. Two types for one idea is how two numbers come to disagree about one review, so
      there is now one — with `within()` moved across, and `ms` and `complete` added.

WHY:  **THE COLUMNS FOR THIS HAVE EXISTED SINCE THE SCHEMA WAS WRITTEN AND NOTHING EVER WROTE
      THEM.** `review.request_count`, `tokens_in`, `tokens_out` and `latency_ms` have sat at their
      defaults through every delivery — the same "tables with zero writers" defect this codebase
      already found once, in `review` and `ranked_unit`.

      **UNTIL THIS EXISTS, EVERY PRICING DECISION IS A GUESS.** BYOK, the free-tier cap, whether
      the model half earns its cost — all of them are arithmetic over a number nobody has measured.
      That is why recording comes before reading it: the answer decides what is worth building.

      **`tokens_out` INCLUDES THE MODEL'S OWN REASONING.** Vertex reports `thoughtsTokenCount`
      separately from the answer, and both are billed. A count of only the visible reply would
      understate a review's cost by most of it — the failure that produced `MAX_TOKENS` on a real
      delivery was a thinking budget nobody was measuring.

      **ADDITION IS EXPLICIT, BECAUSE A REVIEW MAKES SEVERAL CALLS.** The summary and the deep pass
      are separate requests, and a total that silently kept only the last would report a fraction
      of what was spent.
IMPORTS: stdlib only.
CONSUMED BY: `infer/`, and `store/reviews.py`, which writes it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantamind.types.ranking import Budget


@dataclass(frozen=True, slots=True)
class Spend:
    """One review's cost. Zero means "no model was asked", never "we did not measure"."""

    requests: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    ms: int = 0
    cache_read_tokens: int = 0
    """Tokens served from cache. Cheaper, still real, and counted apart so they can be seen."""

    complete: bool = True
    """False when some call in this review was not metered, making the total a FLOOR.

    **A COST THAT MIGHT BE AN UNDERCOUNT MUST SAY SO ON THE VALUE.** `serve/settle.py` asks the
    model once or twice per surviving finding through `infer/prompt_once`, which does not report
    usage yet. Recording the rest as though it were the whole would put a number on a dashboard
    that is quietly low, and pricing decided from it would be wrong in the expensive direction.
    A floor a reader can see beats a total a reader cannot check.
    """

    def __post_init__(self) -> None:
        for name in ("requests", "tokens_in", "tokens_out", "ms", "cache_read_tokens"):
            if getattr(self, name) < 0:
                raise ValueError(f"Spend.{name} is negative: a cost cannot be refunded here")
        if self.requests == 0 and (self.tokens_in or self.tokens_out):
            raise ValueError(
                "tokens were spent with no request recorded; the count that reaches a bill and "
                "the count that reaches a dashboard would then disagree"
            )

    def within(self, budget: Budget) -> bool:
        """Whether this review stayed inside its request ceiling."""
        return self.requests <= budget.max_requests

    @property
    def used_cache(self) -> bool:
        """False after a multi-request review means the prompt prefix is not caching.

        A persistent zero here with more than one request is the signature of an invalidator in
        the cached prefix -- a clock, a request id -- which produces no error and simply costs full
        price on every call. **It came across with `RequestLedger` and was nearly lost in the
        merge; a test caught it**, which is the only reason this paragraph still exists.
        """
        return self.cache_read_tokens > 0

    @staticmethod
    def total(*parts: Spend) -> Spend:
        """Every part of one review, added. `total()` with nothing is a measured zero, not a gap.

        **THE FOLD LIVES ON THE TYPE SO EVERY CALLER GETS THE SAME ONE.** Written out at a call
        site it is four lines that must remember `complete` is contagious; forgetting that turns a
        floor into a total silently, which is the exact failure `complete` exists to prevent.
        """
        running = Spend()
        for part in parts:
            running = running.plus(part)
        return running

    def plus(self, other: Spend) -> Spend:
        """Two calls, added. A review makes several and pays for all of them."""
        return Spend(
            self.requests + other.requests,
            self.tokens_in + other.tokens_in,
            self.tokens_out + other.tokens_out,
            self.ms + other.ms,
            self.cache_read_tokens + other.cache_read_tokens,
            # Incomplete is contagious: a total containing one unmetered call is itself a floor.
            self.complete and other.complete,
        )


def measured(reply: dict[str, Any], ms: int) -> Spend:
    """One Vertex reply's usage. **Absent usage is zero requests, not zero cost pretending to be
    a measurement** — a reply without `usageMetadata` was still paid for, so it records the call
    and leaves the tokens at zero rather than inventing them."""
    usage = reply.get("usageMetadata")
    if not isinstance(usage, dict):
        return Spend(requests=1, ms=ms)
    prompt = int(usage.get("promptTokenCount", 0) or 0)
    total = int(usage.get("totalTokenCount", 0) or 0)
    # total - prompt covers the answer AND `thoughtsTokenCount`, both of which are billed.
    return Spend(requests=1, tokens_in=prompt, tokens_out=max(0, total - prompt), ms=ms)
