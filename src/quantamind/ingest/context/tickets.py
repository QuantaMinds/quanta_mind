"""The ticket behind a change, read for the human and never for a model.

WHAT: `behind(repo, number)` returns a `Context`: the author's stated goal, one `Ticket` per
      same-repository issue their text names, and one `Skipped` for every reference not read.
WHY:  **THIS IS THE HALF OF THE GOLDEN QUESTION THAT DEPENDED ON A MODEL.** *Did this pull request
      achieve the goal it set out to achieve* has no first half without the goal, and until now
      the goal appeared in a comment only when `infer/` produced a summary -- the path measured at
      **25.0% correct**. `ingest/diff.stated_goal` was fetched on every delivery and handed
      straight to a prompt. What is read here is read for the reader, and a deterministic block
      built from it is worth the same whatever the model does or does not manage.

      **EVERY REFERENCE NOT READ BECOMES A `Skipped` ROW.** Non-negotiable 3: "no ticket here" and
      "we failed to read the ticket" must never be the same value on the wire. Three reasons, and
      a reader can tell them apart on the page.

      **A CROSS-REPOSITORY REFERENCE IS REFUSED, NOT ATTEMPTED.** `issue_refs.Ref.foreign` decides
      it from the text alone, so no request is made at all. Quoting `otherorg/private#5`'s title
      into this repository's pull request moves their data across a boundary nobody opted into,
      and we may hold no token for it either -- the second reason would produce a 404 that looks
      like a deleted issue. `product-build.md` "D6c Sources, cheapest first" states the rule for
      Jira and Slack; it binds here first, where honouring it costs nothing.

      **A LOCAL REASON ENUM, NOT A NEW MEMBER OF `types/verdict.Reason`.** That enum resolves CODE
      CONSTRUCTS -- a call site, an import, an attribute -- and `Unresolved` pairs it with a
      `Construct`. A 404 from the issues API is neither. Widening it so a ticket could ride in it
      would make `Unresolved` mean two things, and the coverage line that consumes it would start
      reporting retrieval failures as unparsed code.

      **THE CAP IS NAMED AND ITS REMAINDER IS COUNTED.** One reference is one API call, and a body
      listing thirty issues would spend thirty on a block nobody reads to the bottom. The ones past
      the cap are `Skipped`, so the block says how many it did not fetch rather than ending early.
IMPORTS: stdlib json; `ingest.github_api` and `ingest.diff` (same layer, public surface only),
      `ingest.context.issue_refs`.
CONSUMED BY: `render/context/goal_block.py` via `serve/review_delivery.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from quantamind.ingest import github_api
from quantamind.ingest.context.issue_refs import Ref, references
from quantamind.ingest.diff import DiffReadFailed, Stated, stated_goal

FETCH_CAP = 5
"""References fetched at most. Chosen as a COST bound, not a display one — the remainder is
counted and printed, so raising it changes what we spend and not what the reader is told."""


class Declined(Enum):
    """Why a reference the author made was not read. Closed, and each renders differently."""

    ANOTHER_REPOSITORY = "it names another repository, and we do not quote across one"
    NOT_READABLE = "GitHub would not return it"
    OVER_THE_CAP = "more references than we fetch"


@dataclass(frozen=True, slots=True)
class Ticket:
    """One issue the author named, as GitHub answered it."""

    ref: Ref
    title: str
    state: str
    """`open` or `closed`, in GitHub's own words. Never normalised into a boolean."""

    is_pull: bool
    """GitHub numbers issues and pull requests in one sequence, so `#412` is often a pull
    request. Reported as what it is rather than asserted to be an issue."""

    def render(self) -> str:
        kind = "pull request" if self.is_pull else "issue"
        return f"{self.ref.render()} — {self.title} ({kind}, {self.state})"


@dataclass(frozen=True, slots=True)
class Skipped:
    """One reference we did not read, and why. Never dropped."""

    ref: Ref
    why: Declined

    def render(self) -> str:
        return f"{self.ref.render()} — {self.why.value}"


@dataclass(frozen=True, slots=True)
class Context:
    """What the author said this change is for, and what stood behind it."""

    stated: Stated
    tickets: tuple[Ticket, ...] = ()
    skipped: tuple[Skipped, ...] = ()
    unreadable: str = ""
    """Why the pull request's own text could not be read, empty when it was.

    **AN AUTHOR WHO WROTE NOTHING AND A READ THAT FAILED ARE DIFFERENT ANSWERS.** Both leave
    `stated` empty, and collapsing them would print "the author stated no goal" about a pull
    request whose description we never saw — an assertion about somebody's work, made out of our
    own outage. This is the field that keeps them apart on the page.
    """

    def empty(self) -> bool:
        """True when the author stated no goal, named no ticket, and the read SUCCEEDED.

        **A REAL RESULT, NOT AN ERROR.** An author who wrote nothing stated no goal, and the block
        says so; a caller that treated this as "nothing to render" would print the same page as
        one where retrieval failed.
        """
        return not (self.stated.text() or self.tickets or self.skipped or self.unreadable)


def _issue(repo: str, ref: Ref) -> Ticket | Skipped:
    """One issue, or a typed refusal.

    **NEVER RAISES: A MISSING TICKET MUST NOT COST THE REVIEW.** The comment is worth posting
    whether or not the issues API answered, and an exception here would trade the whole review
    for one line of context — the same trade `store/rule_checks.persist` refuses.
    """
    try:
        raw = github_api.call(repo, f"repos/{repo}/issues/{ref.number}")
    except github_api.ApiFailed:
        # The reason is not carried into the page. A 404 here means "deleted, or never existed,
        # or not visible to this installation" and printing GitHub's words would invite a reader
        # to distinguish three cases the status code does not distinguish.
        return Skipped(ref, Declined.NOT_READABLE)
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        return Skipped(ref, Declined.NOT_READABLE)
    return Ticket(
        ref=ref,
        title=str(payload.get("title") or "").strip(),
        state=str(payload.get("state") or "unknown"),
        is_pull="pull_request" in payload,
    )


def behind(repo: str, number: int) -> Context:
    """The author's goal and the tickets their text names, for THIS repository only.

    **THE STATED GOAL IS TAKEN VERBATIM AND NOT SUMMARISED.** It is the claim the review is
    measured against, so paraphrasing it would move the target. `render/context/goal_block.py`
    decides how much of it fits on a page; nothing here shortens it.

    **NEVER RAISES, AND THE FAILURE IS A VALUE RATHER THAN AN EMPTY CONTEXT.** A delivery must not
    be lost because the pull request endpoint was unavailable, and returning a bare empty `Context`
    would make an outage read as an author who wrote no description.
    """
    try:
        stated = stated_goal(repo, number)
    except DiffReadFailed as exc:
        return Context(stated=Stated("", ""), unreadable=str(exc))
    found = references(stated.title, stated.body, repo)

    tickets: list[Ticket] = []
    skipped: list[Skipped] = []
    budget = FETCH_CAP
    for ref in found:
        if ref.foreign:
            skipped.append(Skipped(ref, Declined.ANOTHER_REPOSITORY))
            continue
        if budget == 0:
            skipped.append(Skipped(ref, Declined.OVER_THE_CAP))
            continue
        budget -= 1
        outcome = _issue(repo, ref)
        if isinstance(outcome, Ticket):
            tickets.append(outcome)
        else:
            skipped.append(outcome)
    return Context(stated=stated, tickets=tuple(tickets), skipped=tuple(skipped))
