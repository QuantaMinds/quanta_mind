# D6a — the ticket behind the change, shown to the reader

**Branch** `feat/d6a-the-goal-behind-the-change`. Build order item 12, the lowest number in
`docs/plans/roadmap/product-build.md` that is neither ticked nor parked. Rows 12–30 were
re-verified against the code first and none of the unticked ones turned out to be built.

## What is missing, precisely

`ingest/diff.py:158` already fetches the pull request's title and body as `Stated`, and
**`infer/change_review.py:69` is its only consumer**. So the author's stated goal is retrieved on
every delivery, handed to a model, and never shown to the human — while `render/comment.py` prints
a goal line only when the model produced a summary, which is exactly the path measured at 25.0%
correct.

D6a is the row that says this must not depend on the model: *"Retrieval for the READER. The ticket
and discussion behind the files being changed, shown in the comment. **Deterministic, and worth
something whatever the model does.**"* And the golden rule the whole product is judged against —
*did this pull request achieve the goal it set out to achieve, without disturbing anything else* —
has no first half without it.

**What is genuinely absent is the ticket.** Nothing anywhere parses `Closes #412` out of a pull
request body, and nothing reads the issue it names.

## What gets built

| where | what |
|---|---|
| `ingest/context/issue_refs.py` | `references(text)` — the issue references in a title and body, with the closing keyword when there is one. Pure, no I/O |
| `ingest/context/tickets.py` | `behind(repo, number)` — the stated goal plus each same-repository ticket, and a typed record for every reference not read |
| `render/context/goal_block.py` | the block, rendered from that and nothing else |

`render/` is at its fifteen-file cap, so the block goes in a sub-package — which is what
`check_structure.py` tells you to do, and what `ingest/publish/` and `serve/commands/` already are.

## Three decisions that are not obvious

**A cross-repository reference is DECLINED, named, and never fetched.** `otherorg/private#5` in a
body is a reference we may have no installation token for, and quoting its title into this
repository's comment would move somebody's data across a boundary nobody opted into. D6c states the
rule for Jira and Slack — *"egress is a decision, not a detail"* — and it binds here first, where
it is cheapest to honour. The reference is printed as declined so the reader knows the context
exists and where it is.

**A reference we could not read gets a record with a reason, never silence.** Non-negotiable 3:
"no ticket here" and "we failed to read the ticket" must never be the same value on the wire. The
reason enum is local to `ingest/context/` rather than a new member of `types/verdict.Reason`, which
is about resolving *code constructs* — a 404 from the issues API is not a call site, and widening
that enum to hold retrieval failures would make `Unresolved` mean two things.

**An empty body is a RESULT.** `stated_goal` already says so; the block prints "the author stated
no goal" rather than omitting the section, because a missing section reads as a section that had
nothing to report.

## What could still silently fail

- ~~**A reference in a code fence or a quoted log line is still a reference to this parser.** The
  cost is a spurious ticket in the block, not a wrong verdict.~~ **REPRICED BY THE LIVE RUN AND
  FIXED.** The first real pull request — `QuantaMinds/quanta_mind#91` — carried the sentence
  *"`Closes #412` has never been parsed anywhere"* in its own description, and the posted comment
  said issue 412 could not be read. Estimating this as rare was wrong for a repository whose pull
  requests discuss issue numbers. `issue_refs._prose` blanks fenced blocks and code spans now.
  Indented code blocks and reference-style links are still unhandled, and would be next.
- **`#123` is a pull request as often as an issue on a busy repository**, because GitHub numbers
  them in one sequence. The API answers both from `repos/{repo}/issues/{n}`, and the block prints
  whichever GitHub says it is rather than asserting "issue".
- **The block reports what the author WROTE, not what is true.** A stale `Closes #12` is repeated
  faithfully. That is the point — it is the claim the change is measured against — but nothing here
  checks the ticket is still open or still describes this work.
