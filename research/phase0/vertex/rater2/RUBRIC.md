# Rubric — adjudicating AI code-review findings

You are the SECOND independent rater. A first rater has already graded these, and you are not
being shown their verdicts. Do not try to guess them. Grade what is in front of you.

Each finding is a claim produced by an AI reviewer about one function in a real, MERGED pull
request from a well-known open-source Python project. You are given the claim, the two line
numbers it cites, and the code around each of those lines.

## Put every finding in exactly ONE bucket

**CORRECT** — the claim is true of the code shown, AND the cited line_a / line_b actually point
at the code that makes it true, AND it is worth a reviewer's attention.

**WRONG** — the claim is false of the code shown, OR the cited lines do not support the claim.
  - This includes a correct-sounding diagnosis anchored to the wrong lines. The line numbers are
    part of the claim, not decoration: a blank line, a comment, a closing bracket, or an argument
    line one or two below the statement being described is a WRONG anchor.
  - It also includes claims that a test's assertion is incorrect. These pull requests are MERGED,
    so their tests ran and passed. A claim that a passing test's assertion is wrong is false.

**UNFALSIFIABLE** — the claim might be true, but it cannot be decided from the function and the
code shown. It needs the caller, the runtime, or the rest of the repository. Hedged speculation
("may", "likely", "could") about behaviour not visible here belongs in this bucket.

**TRIVIAL** — true, correctly anchored, but not worth a reviewer's comment. Style nits,
restatements of intentional design, duplicates of another finding, or observations with no
consequence.

## Output format — this exactly, one line per finding, nothing else

```
<index> <BUCKET> <one short sentence giving the single fact that decided it>
```

For example:

```
7 WRONG line_a points at a blank line, not the assignment the claim describes
8 CORRECT all([]) is True, so an empty worker list silently reports support
```

Grade every finding you are given. Do not skip any. Do not add commentary before or after the
list.
