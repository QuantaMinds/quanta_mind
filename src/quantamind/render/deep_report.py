"""The reviewer pass, written out with the mechanism behind every discard.

WHAT: `lines(deep)` — what the measurement half did, as text, including the counts it dropped.
WHY:  **PRINTING ONLY `unanchored` REPORTED THREE DIFFERENT FATES AS ONE NUMBER.** A finding the
      oracles refuted and one the model itself withdrew both vanished from the output, and
      "nothing survived the anchor check" was printed over findings that HAD survived it and were
      dropped two stages later. The counts existed on the record and were never shown.

      **AND IT SAYS WHEN THE MODEL WAS NEVER ASKED.** `deep.consulted` is False when the ranked
      files carry no diff, which is an instrument that did not run rather than a review that found
      nothing — rule 3, and the two must not print the same.

      It returns lines rather than printing them so a test can assert on the text.
IMPORTS: types.deep. Leftward.
CONSUMED BY: `serve/deep_review.py`.
"""

from __future__ import annotations

from quantamind.types.deep import Deep

CAVEAT = (
    "read {n} ranked file(s). RAW FINDINGS MEASURE 66.7-82.1% WRONG across four blind rater "
    "pools, at 0.013-0.037 correct per pull request. 'Anchored' means a parser found the quoted "
    "line in the diff. It does NOT mean the claim is true, and nothing here is published to a "
    "pull request."
)


def lines(deep: Deep) -> list[str]:
    """The pass as text. Every discard is named with the mechanism that made it."""
    out = ["[deep] NOT A PRODUCT FEATURE. This is the measurement half, run by hand."]
    if not deep.consulted:
        out.append(
            "[deep] THE MODEL WAS NOT ASKED — the ranked files carry no diff at this commit."
        )
        out.append(
            "[deep] That is an instrument that did not run, NOT a review that found nothing."
        )
        return out
    out.append(f"[deep] {deep.raw} raw finding(s) from the model:")
    out.append(f"[deep]   {len(deep.anchored):>3} anchored and surviving every check")
    out.append(f"[deep]   {deep.unanchored:>3} dropped — the quoted code is not in the diff")
    out.append(f"[deep]   {deep.refuted:>3} dropped — an oracle refuted it or could not settle it")
    out.append(f"[deep]   {deep.withdrawn:>3} withdrawn — the model retracted it, given a fact")
    out.extend(f"  {f.path}:{f.line}  {f.claim}" for f in deep.anchored)
    if not deep.raw:
        out.append("  (the model read the diff and reported nothing — a result, not a failure)")
    elif not deep.anchored:
        out.append("  (the model found things; none of them survived)")
    out.append(f"[deep] {CAVEAT.format(n=len(deep.read))}")
    return out
