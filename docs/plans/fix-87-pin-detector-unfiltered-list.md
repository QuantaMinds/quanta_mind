# Make the oracles reachable — the four fixes from the investigation

**Branch** `fix/87-pin-detector-unfiltered-list`, issue #87. Diagnosis:
`docs/findings/oracles/WHY_THE_ORACLES_NEVER_FIRE_2026-08.md`. This touches `verify/`, so the plan is
written first as the working rules require.

## 1. Give the pin detector the list it was designed for

`serve/review_delivery.py:87` calls `changed_files()` with the default
`suffixes=REVIEWABLE_SUFFIXES`, and line 150 hands that filtered list to `pin_check.check()`, so
`workflows(changed)` is always `[]`.

**`changed_files` gains `suffixes: tuple[str, ...] | None`, where `None` means no filter.** Not an
empty tuple: `"a.py".endswith(())` is `False`, so `()` would filter everything out and read as
working. The delivery path fetches once with `None` and filters locally for ranking, so this
costs no extra API calls and the ranker's input is unchanged.

**The ranking filter is correct and stays.** Only the detector, which needs no model and reads
only `.github/workflows/`, sees the unfiltered list.

## 2. A wiring test, not another unit test

Every existing oracle test calls `detect()` with a synthetic diff string, so all of them pass with
the wiring broken. The new test starts from an **unfiltered changed-file list** containing a
workflow and asserts a mismatch survives to what the caller receives. It must fail if the filtered
list is passed again.

## 3. Stop the hex-token false drop

`external_facts.adjudicate` extracts any 7–40 char hex token; with no `owner/repo` it returns
`UNRESOLVABLE`, and `gate()` drops the finding. A cache key or a colour constant is enough, so the
gate's only live behaviour is discarding findings that mention hex.

**The fix distinguishes "not an external claim" from "an external claim we could not settle".** A
hex token alone is not a claim about a commit; a hex token **plus** `DENIES_EXISTENCE` or
`ASSERTS_TAG` is. So:

- hex, no repo, no denial/tag assertion → **`NO_CLAIM`** (publishes; nothing was checked and
  nothing is pretended)
- hex, denial or tag assertion, no repo → **`UNRESOLVABLE`** (drops, unchanged)

**The safety policy is preserved deliberately.** `docs/CORRECTIONS.md` entry 8 records a verifier
that defaulted to confirming and validated every false claim it existed to refute. A real external
claim we cannot settle still drops.

## 4. Count refuted and unresolvable apart

`serve/deep_review.py` increments one `refuted` counter for both. "An authority contradicted this"
and "we could not check this" are different events and one of them is a false drop. `Deep` gains
`unresolvable`; `raw = kept + unanchored + refuted + unresolvable + withdrawn` must still hold.

## What could still silently fail

- **The detector fires on a repository with no pins and we read that as it working.** Its base
  rate is 0.24%, so silence is the expected outcome; the test asserts on a *known* mismatch.
- **`suffixes=None` reaching the ranker** would widen what the model reads and break the cost
  argument. Only `pin_check` receives the unfiltered list, and a test pins that.
- **Making `NO_CLAIM` too broad** would let a real SHA claim publish unchecked. The trigger is
  narrowed by requiring denial-or-tag phrasing, not by removing the check.

## Done when

`just verify` green; the wiring test fails when handed the filtered list; the hex fix is proven by
a claim that used to drop and now publishes, and by a real SHA claim that still drops;
`CODEBASE.md` updated; a re-measured run reports the two counts apart.
