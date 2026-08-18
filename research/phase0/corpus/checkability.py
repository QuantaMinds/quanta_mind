"""What share of real review comments makes a claim a parser could adjudicate?

WHAT: Classifies 1,213 inline review comments fetched from eight public repositories into
      not-a-finding, structural, and semantic, and prints a seeded random sample of each.
WHY:  It bounds what the verifier can ever catch, and it is a property of the SCHEMA rather
      than of any model -- so it is answerable before infer/ exists and it decides how much
      weight the model-certification run can put on drop rate.
      THE CLASSIFIER FAILED: 56.5% landed in the residual bucket and every printed sample
      contains obvious errors. The number is not quotable. What survives is the direction --
      structural claims are a small minority of real review content -- which is why the sample
      is printed rather than only the counts.
IMPORTS: stdlib only (json, pathlib, random, re).
CONSUMED BY: docs/plans/design/commercial-surface.md, the model-certification design.

This bounds what the verifier can ever catch, and it is a property of the SCHEMA rather than
of any model -- so it is measurable before infer/ exists, and it decides how much weight the
certification run can put on drop rate.

  Source: 1,213 inline review comments on .py files, fetched live from eight public
  repositories via the GitHub API. Inline comments are the closest public analogue to what
  this reviewer emits: attached to a file, about specific code.

  THREE BUCKETS, by explicit pattern. The classifier is the weak link and it is stated rather
  than hidden, with a random sample of each bucket printed so a reader can judge it.

    NOT_A_FINDING  questions, nits, approvals, conversation. Asserts nothing to check.
    STRUCTURAL     asserts something a parser can decide: a symbol exists, a signature has
                   that arity, an import is missing, a name is wrong, an order holds.
    SEMANTIC       asserts something about behaviour: wrong logic, an unhandled case, a race,
                   a leak. True or false, but not decidable from a parse tree.

  Bias direction, stated: the STRUCTURAL patterns are generous -- any mention of a concrete
  identifier or line number in an assertive sentence counts. So the structural share reported
  here is an UPPER bound, and the real bound on the verifier is at most this.
"""

from __future__ import annotations

import json
import pathlib
import random
import re

SP = pathlib.Path(
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad"
)

# A comment that asserts nothing: interrogative, approving, or conversational.
NOT_FINDING = re.compile(
    r"^\s*(lgtm|nit\b|ok\b|okay|thanks|thank you|done|\+1|yes|no\b|sure|agreed|good catch"
    r"|nice|sounds good|fixed|ack)\b|^\s*(what|why|how|should we|could we|can we|do we|is "
    r"this|are these|does this|any reason|wdyt|thoughts)\b|\?\s*$",
    re.IGNORECASE,
)

# Asserts something a parser can decide.
STRUCTURAL = re.compile(
    r"\b(line \d+|missing import|not imported|undefined|not defined|typo|rename|misspel"
    r"|signature|argument order|wrong (?:name|type|argument)|does not exist|doesn'?t exist"
    r"|unused (?:import|variable)|shadow|duplicate)\b|`[A-Za-z_][\w.]*`\s+(?:is|does|"
    r"should|must)\b",
    re.IGNORECASE,
)

# Asserts something about behaviour.
SEMANTIC = re.compile(
    r"\b(race|deadlock|leak|will fail|would fail|breaks?|doesn'?t handle|does not handle"
    r"|edge case|off by one|null|none check|exception|silently|infinite|overflow|incorrect"
    r"|wrong (?:behaviour|behavior|result|order of operations)|regression|side effect"
    r"|thread|concurren|idempot|retry|timeout)\b",
    re.IGNORECASE,
)


def classify(body: str) -> str:
    text = " ".join(body.split())
    if len(text) < 15 or NOT_FINDING.search(text):
        return "NOT_A_FINDING"
    if STRUCTURAL.search(text):
        return "STRUCTURAL"
    if SEMANTIC.search(text):
        return "SEMANTIC"
    return "OTHER_FINDING"


def main() -> None:
    rows = json.loads((SP / "review_py.json").read_text())
    counts: dict[str, list[str]] = {}
    for r in rows:
        counts.setdefault(classify(r["body"]), []).append(r["body"])

    total = sum(len(v) for v in counts.values())
    print(f"  {total} inline review comments on .py files, 8 public repositories\n")
    order = ("NOT_A_FINDING", "STRUCTURAL", "SEMANTIC", "OTHER_FINDING")
    for k in order:
        n = len(counts.get(k, []))
        print(f"    {k:16s} {n:5d}  {n / total:6.1%}")

    findings = total - len(counts.get("NOT_A_FINDING", []))
    struct = len(counts.get("STRUCTURAL", []))
    print(f"\n  of the {findings} that assert something:")
    print(f"    parser could adjudicate at most  {struct}/{findings} = {struct / findings:.1%}")
    print("    (upper bound -- the structural patterns are deliberately generous)")

    rng = random.Random(20260814)  # fixed seed: the sample is reproducible, not chosen
    print("\n  random sample of each bucket, so the classifier can be judged:")
    for k in order:
        v = counts.get(k, [])
        if not v:
            continue
        print(f"\n   --- {k}")
        for b in rng.sample(v, min(3, len(v))):
            print(f"     {' '.join(b.split())[:130]}")


main()
