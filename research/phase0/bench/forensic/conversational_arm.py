"""Does making the reviewer ASK, instead of assert, convert confabulation into truth or silence?

WHAT: Replays design thirteen's 86 real adjudicated findings. For each, the model is shown the same
      claim and asked whether it rests on an external fact and, if so, what question would settle
      it. The oracle answers from GitHub or PyPI. Counts ASKED, SETTLED, and -- the number that
      decides the arm -- how many of the 7 CORRECT findings stop publishing.
WHY:  **THE MODEL ASSERTS FACTS IT CANNOT CHECK, AND MEASURED LIVE ITS DISCRIMINATION ON THE
      LARGEST SUCH CLASS IS -8.3%.** The architecture under test makes it a questioner instead. Two
      rules: it may not answer its own question, and the oracle never judges.

      **THE HARD STOP IS THE POINT OF THE EXPERIMENT.** Design 8's quote requirement was satisfied
      by ABSTAINING rather than by better anchoring -- the model complied by saying less -- and a
      model asked to seek permission has exactly that escape. So losing 2 of the 7 correct findings
      ends this as a FAIL whatever the wrong-rate does. Seven is the entire correct yield of this
      pool of 86; two is 29% of it.

      **AND RANDOM SUPPRESSION IS THE NULL.** An arm that drops findings blindly loses the same
      share of correct ones as wrong ones, so a drop in the wrong-rate means nothing reported
      alone. Both are printed together.
      -> `docs/plans/preregistrations/reviewer/conversational-oracle-preregistration.md`
IMPORTS: stdlib; the product's `verify` oracles; the Vertex `client`.
CONSUMED BY: read by a human; writes `results/conversational_arm.json`.
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "vertex"))
sys.path.insert(0, str(HERE.parents[3] / "src"))

from client import Client  # noqa: E402
from conversing import NAMES_SHA, answer, redecide, settle  # noqa: E402

OUT = HERE.parent / "results" / "conversational_arm.json"
ADJ = HERE.parents[1] / "quote" / "adj13"
RUN = HERE.parents[1] / "quote" / "results" / "quote13_run.json"

# **The model is asked what would settle its claim -- never whether the claim is true.** Asking it
# to self-assess is the lever measured five times at 8.5-16.8% retained discrimination.
ASK = """You wrote this code-review finding:

{claim}

Does this finding depend on a fact that is NOT in the diff -- something about a repository's tags,
a package index, or today's date?

Answer with ONLY a JSON object:
{{"external": true or false, "question": "the single factual question that would settle it, or ''"}}

If the finding rests only on the code shown, answer false. Do not judge whether the finding is
correct."""

VERDICTS = ("CORRECT", "WRONG", "TRIVIAL", "UNFALSIFIABLE")


def pool() -> list[dict[str, object]]:
    """The 86 real items, each with its claim text and its adjudicated verdict."""
    key = json.loads((ADJ / "KEY_DO_NOT_OPEN.json").read_text())
    said = json.loads((ADJ / "verdicts.json").read_text())
    published = [
        f
        for r in json.loads(RUN.read_text())["results"]
        for arm in r.get("published", {}).values()
        for f in arm
    ]
    by_site = {(f["repo"], f["pr"], f["path"], f["line"]): f for f in published}

    out = []
    for entry in key:
        if entry["kind"] != "real":
            continue
        raw = said.get(str(entry["item"]), "")
        verdict = next((v for v in VERDICTS if raw.startswith(v)), "?")
        found = by_site.get((entry["repo"], entry["pr"], entry["path"], entry["line"]))
        if found is None:
            continue
        out.append(
            {
                "item": entry["item"],
                "verdict": verdict,
                "repo": entry["repo"],
                "claim": str(found["claim"]),
                "quote": str(found.get("quote", "")),
            }
        )
    return out


def ask(client: Client, claim: str) -> dict[str, object]:
    """What the model says would settle its own claim. Never whether it is right."""
    reply = client.generate(
        {
            "contents": [{"role": "user", "parts": [{"text": ASK.format(claim=claim)}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048},
        }
    )
    text = str(reply.get("text") or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        return {"external": None, "question": "", "raw": text[:200]}
    try:
        got = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {"external": None, "question": "", "raw": text[:200]}
    return {"external": bool(got.get("external")), "question": str(got.get("question", ""))}


def main() -> int:
    client = Client("gemini-2.5-pro")
    items = pool()
    print(f"  {len(items)} real items recovered from the blind key\n", flush=True)

    rows: list[dict[str, object]] = []
    for i, it in enumerate(items, 1):
        asked = ask(client, str(it["claim"]))
        verdict, detail, stands = "NOT_ASKED", "", None
        if asked["external"]:
            # The finding's own text carries the SHA its question refers to as "the given
            # commit hash" -- the same shape that took `pin_mismatch` from 4 refutations to 7.
            in_claim = NAMES_SHA.findall(str(it["claim"]) + " " + str(it["quote"]))
            fact, got = answer(
                str(asked["question"]), str(it["repo"]), in_claim[0] if in_claim else ""
            )
            if got and fact:
                verdict, detail = "ANSWERED", fact
                stands = redecide(client, str(it["claim"]), str(asked["question"]), fact)
            else:
                verdict, detail = settle(str(asked["question"]), str(it["claim"]), str(it["repo"]))
        rows.append({**it, **asked, "oracle": verdict, "detail": detail, "stands": stands})
        if i % 10 == 0:
            print(f"    {i}/{len(items)}", flush=True)

    OUT.write_text(json.dumps(rows, indent=1))

    def share(sub: list[dict[str, object]], pred: object) -> str:
        n = sum(1 for r in sub if pred(r))  # type: ignore[operator]
        return f"{n}/{len(sub)}" + (f" = {n / len(sub):.0%}" if sub else "")

    wrong = [r for r in rows if r["verdict"] == "WRONG"]
    right = [r for r in rows if r["verdict"] == "CORRECT"]

    def dropped(r: dict[str, object]) -> bool:
        """A finding stops publishing when the oracle refuted it, could not settle it, or the
        model withdrew it once given the fact."""
        return r["oracle"] in ("REFUTED", "UNRESOLVABLE") or r["stands"] is False

    print(f"\n  WRONG findings   (n={len(wrong)})")
    print(f"    asked rather than asserted : {share(wrong, lambda r: r['external'])}")
    decided = ("REFUTED", "CONFIRMED")
    print(f"    settled by an oracle       : {share(wrong, lambda r: r['oracle'] in decided)}")
    print(f"    would no longer publish    : {share(wrong, dropped)}")
    print(f"\n  CORRECT findings (n={len(right)})   <- THE HARD STOP")
    print(f"    asked rather than asserted : {share(right, lambda r: r['external'])}")
    print(f"    would no longer publish    : {share(right, dropped)}")
    lost = sum(1 for r in right if dropped(r))
    print(f"\n  LOST: {lost} of {len(right)} correct findings")
    print("  BAR: 2 or more is a FAIL, whatever the wrong-rate did.")
    d = sum(1 for r in wrong if dropped(r)) / max(1, len(wrong))
    print(f"\n  chance null: random suppression would lose {d:.0%} of the correct findings")
    print(f"  ({d * len(right):.1f} of {len(right)}); observed {lost}.")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
