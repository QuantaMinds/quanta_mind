"""Grade design fourteen's chunks with a model that is shown the rubric and nothing else.

WHAT: Sends `adj14/chunk_*.md` with `vertex/rater2/RUBRIC.md` to a judge model, parses one verdict
      line per item, and writes `adj14/verdicts.json`. Unparseable lines are reported, never
      dropped.
WHY:  **THE JUDGE IS SHOWN THE RUBRIC AND THE FINDINGS. IT IS NOT SHOWN THE DESIGN, THE
      HYPOTHESIS, THE BARS, OR THE EXPECTED RESULT.** The pre-registration records a prior --
      W/n near 42%, C/n far below the floor -- and a judge that knew it would be grading toward it.
      Nothing in this file's prompt names design fourteen.

      **THIS CANNOT BE THE INDEPENDENT CLEARANCE, AND SAYING SO IS THE POINT.** The reserve
      conditions require G2 to hold twice with at least one rater who did not design the
      experiment. The subject model here is `gemini-2.5-pro` and this judge is the same family, so
      it is grading work from its own family -- the limitation the adjudication pre-registration
      already flagged when rater 2 shared rater 1's family. It is run this way for COMPARABILITY
      with design thirteen, whose numbers were produced the same way, and it yields at most rater 1.
      A second, genuinely independent grade is a separate exercise and is not this file.

      **THE SABOTAGE ITEMS ARE THE CHECK ON THIS JUDGE.** `score14.py` prints their catch-rate
      before any result and refuses to report anything if the pool rubber-stamped them.
IMPORTS: stdlib only (json, pathlib, re, sys). Local: the Vertex `client`.
CONSUMED BY: a human, before `score14.py`.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / "vertex"))

from client import Client  # noqa: E402

ADJ = HERE / "adj14"
RUBRIC = HERE.parent / "vertex" / "rater2" / "RUBRIC.md"
MODEL = "gemini-2.5-pro"
BUCKETS = ("CORRECT", "WRONG", "UNFALSIFIABLE", "TRIVIAL")
BATCH = 12
LINE = re.compile(r"^\s*(\d+)\s+(" + "|".join(BUCKETS) + r")\b\s*(.*)$")


def grade(client: Client, rubric: str, chunk: str) -> dict[str, str]:
    """One chunk. Returns {index: 'BUCKET sentence CAUSE'} for every line that parsed."""
    body = {
        "contents": [{"role": "user", "parts": [{"text": rubric + "\n\n---\n\n" + chunk}]}],
        # 32768 to match `reviewer.py`. The first attempt used 8192 and finished MAX_TOKENS on the
        # first chunk: Gemini's thinking tokens are billed against this ceiling, and 45 graded items
        # behind several thousand thinking tokens does not fit. It RAISED rather than returning a
        # short pool, which is the whole reason `finish` is checked -- a truncated grading reads as
        # a judge that graded fewer items.
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 32768},
    }
    answer = client.generate(body)
    if answer["finish"] != "STOP":
        # A truncated grading reads as "the judge graded fewer items", which is the exact shape
        # this project keeps mistaking for a result. Raised, never trimmed and continued past.
        raise RuntimeError(f"judge finished {answer['finish']!r}, not STOP — grading is incomplete")
    out: dict[str, str] = {}
    unparsed: list[str] = []
    for line in str(answer["text"]).splitlines():
        if not line.strip() or line.strip().startswith("```"):
            continue
        m = LINE.match(line)
        if m:
            out[m.group(1)] = f"{m.group(2)} {m.group(3)}".strip()
        else:
            unparsed.append(line.strip()[:80])
    if unparsed:
        print(f"    {len(unparsed)} line(s) did not parse: {unparsed[:3]}")
    return out


def items_of(chunk: str) -> tuple[str, list[tuple[str, str]]]:
    """(header, [(index, item markdown)]). Split on the `## <n>` headings the pool writes."""
    parts = re.split(r"^## (\d+)\s*$", chunk, flags=re.M)
    head = parts[0]
    return head, [(parts[i], f"## {parts[i]}\n{parts[i + 1]}") for i in range(1, len(parts), 2)]


def grade_all(
    client: Client, rubric: str, head: str, items: list[tuple[str, str]]
) -> dict[str, str]:
    """Grade in batches and RETRY whatever a batch left out, rather than trusting it covered them.

    **A batch that returns STOP having graded 30 of its 45 items is the failure this exists for.**
    The first attempt sent 45 at a time; the model finished cleanly and silently skipped 26 of 114.
    Nothing about that answer looks wrong -- it is well-formed, correctly formatted, and short.
    Coverage is therefore checked against the indices that went in, and the remainder is re-sent.
    """
    out: dict[str, str] = {}
    todo = list(items)
    for attempt, size in enumerate((BATCH, BATCH // 3, 1), 1):
        if not todo:
            break
        print(f"    pass {attempt}: {len(todo)} item(s) in batches of {size}", flush=True)
        for start in range(0, len(todo), size):
            batch = todo[start : start + size]
            body = head + "\n" + "\n".join(md for _, md in batch)
            out |= grade(client, rubric, body)
        todo = [(i, md) for i, md in todo if i not in out]
    if todo:
        print(f"    {len(todo)} item(s) ungraded after three passes: {[i for i, _ in todo][:8]}")
    return out


def main() -> int:
    chunks = sorted(ADJ.glob("chunk_*.md"))
    if not chunks:
        print(f"  no chunks in {ADJ}; run adjudicate14.py first")
        return 1
    key = json.loads((ADJ / "KEY_DO_NOT_OPEN.json").read_text())
    rubric = RUBRIC.read_text()
    client = Client(MODEL)

    verdicts: dict[str, str] = {}
    for path in chunks:
        print(f"  grading {path.name} ...", flush=True)
        head, items = items_of(path.read_text())
        verdicts |= grade_all(client, rubric, head, items)

    expected = {str(e["item"]) for e in key}
    missing = sorted(expected - set(verdicts), key=int)
    extra = sorted(set(verdicts) - expected, key=int)
    if extra:
        print(f"  {len(extra)} verdict(s) for items that do not exist: {extra[:8]}")
        for i in extra:
            verdicts.pop(i)
    print(f"\n  {len(verdicts)}/{len(expected)} items graded")
    if missing:
        # NOT filled in with a default. An ungraded item and an item graded CORRECT must never be
        # the same value on the wire; score14.py refuses to score an incomplete pool.
        print(f"  {len(missing)} UNGRADED: {missing[:12]}")
        print("  score14.py will refuse this pool until every item has a verdict.")

    (ADJ / "verdicts.json").write_text(json.dumps(verdicts, indent=1))
    print(f"  -> {ADJ / 'verdicts.json'}")
    print("\n  This is rater 1 and the same family as the subject. It is NOT the independent")
    print("  clearance the reserve conditions require. See this file's docstring.")
    return 0


# Guarded, because `judge_compare.py` imports `grade_all` and `items_of` from this module to hold
# the judge fixed while varying the design. Unguarded, that import RE-RAN the whole design-14
# grading and overwrote its verdicts -- an import with a side effect that costs money and data.
if __name__ == "__main__":
    raise SystemExit(main())
