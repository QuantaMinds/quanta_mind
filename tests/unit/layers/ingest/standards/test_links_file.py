"""The links a business declares, and the four answers that must not collapse into each other.

WHAT: Drives `ingest.standards.links_file.read()` over declaration files this test writes into a
      real git repository, and reads them back at a commit.
WHY:  **NO FILE, AN EMPTY FILE, A MALFORMED FILE AND AN UNREADABLE ONE ARE FOUR ANSWERS.** Three of
      them leave `links` empty, and only one of them means *this business declared no links*. The
      other two mean *we could not tell* — and printing the first for either of those is a claim
      about somebody's architecture made out of our own failed read. That is `AGENTS.md`
      non-negotiable 3, applied to a repository boundary.

      **DECLARED BEATS DISCOVERED, WHICH IS WHY THE PARSER IS STRICT.** A link the customer wrote
      is provenance an auditor can be shown; one we inferred is our guess. So `owner/name` or
      nothing — guessing the owner from the repository under review would invent a link nobody
      declared, and a bare name is not something a reader can go and open.

      **A DUPLICATE IS A TYPO, NOT A CONTRADICTION.** Refusing the whole file over one would cost
      the customer every other link they declared, which is a bigger loss than the typo.
IMPORTS: quantamind.ingest.standards.links_file.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from quantamind.ingest.standards.links_file import LINKS_PATH, read

GIT_ENV = {
    "PATH": "/usr/bin:/bin:/usr/local/bin",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def _committed(root: Path, body: str | None) -> str:
    """A repository holding `body` at `.quantamind/links.toml`, or holding no such file."""
    env = {**GIT_ENV, "HOME": str(root)}
    run = lambda *a: subprocess.run(  # noqa: E731
        ["git", "-C", str(root), *a], capture_output=True, text=True, timeout=30, env=env
    )
    run("init", "-q", "-b", "main")
    (root / "seed.txt").write_text("seed\n", encoding="utf-8")
    if body is not None:
        (root / LINKS_PATH).parent.mkdir(parents=True, exist_ok=True)
        (root / LINKS_PATH).write_text(body, encoding="utf-8")
    run("add", "-A")
    run("commit", "-qm", "x")
    return run("rev-parse", "HEAD").stdout.strip()


def test_a_declared_link_carries_the_repository_and_the_reason(tmp_path: Path) -> None:
    """Both are the customer's own words, printed verbatim. Nothing here is inferred."""
    sha = _committed(tmp_path, '[[link]]\nrepo = "acme/billing"\nwhy = "consumes our schema"\n')

    links, refused = read(tmp_path, sha)

    assert refused == ()
    assert (links[0].repo, links[0].why) == ("acme/billing", "consumes our schema")
    assert links[0].render() == "`acme/billing` — consumes our schema"


def test_a_link_with_no_reason_is_still_a_link(tmp_path: Path) -> None:
    """The reason is what the customer chose to say. Requiring it would refuse a true declaration
    for being terse."""
    sha = _committed(tmp_path, '[[link]]\nrepo = "acme/mobile"\n')

    links, _ = read(tmp_path, sha)

    assert links[0].render() == "`acme/mobile`"


def test_no_declaration_is_no_links_and_no_refusal(tmp_path: Path) -> None:
    """**THE ONLY ONE OF THE FOUR THAT MEANS "THIS BUSINESS DECLARED NONE".** It is also the common
    case, so it must be cheap and silent."""
    sha = _committed(tmp_path, None)

    assert read(tmp_path, sha) == ((), ())


def test_a_file_that_is_not_toml_is_refused_and_not_read_as_empty(tmp_path: Path) -> None:
    """ "They declared no links" and "we could not read what they declared" must not be one value:
    the first narrows their cross-repository surface to nothing on the day their file breaks."""
    sha = _committed(tmp_path, "this is not toml [[[\n")

    links, refused = read(tmp_path, sha)

    assert links == ()
    assert len(refused) == 1
    assert LINKS_PATH.as_posix() in refused[0].render()


def test_a_name_that_is_not_owner_slash_repo_is_refused(tmp_path: Path) -> None:
    """A bare name is not something a reader can open, and guessing the owner from the repository
    under review would invent a link the customer did not declare."""
    sha = _committed(tmp_path, '[[link]]\nrepo = "billing"\n')

    links, refused = read(tmp_path, sha)

    assert links == ()
    assert len(refused) == 1


def test_one_bad_declaration_does_not_cost_the_good_ones(tmp_path: Path) -> None:
    """A file is a list of independent statements. Refusing all of them over one malformed entry
    would lose the customer every link they got right."""
    sha = _committed(tmp_path, '[[link]]\nrepo = "acme/billing"\n\n[[link]]\nrepo = "nope"\n')

    links, refused = read(tmp_path, sha)

    assert [link.repo for link in links] == ["acme/billing"]
    assert len(refused) == 1


def test_the_same_repository_twice_is_one_link(tmp_path: Path) -> None:
    """A typo, not a contradiction. Printing it twice puts our defect in their comment."""
    sha = _committed(
        tmp_path, '[[link]]\nrepo = "acme/billing"\n\n[[link]]\nrepo = "Acme/Billing"\n'
    )

    links, refused = read(tmp_path, sha)

    assert [link.repo for link in links] == ["acme/billing"]
    assert refused == ()
