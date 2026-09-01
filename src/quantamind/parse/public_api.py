"""What a module offers to anything outside it, and what a change took away.

WHAT: `surface(source)` returns the public names a module defines, each with its call signature.
      `broke(before, after)` returns the ones a change removed, renamed, or made stricter.
WHY:  **D3b's CLAIM IS "A CHANGED EXPORTED SYMBOL AGAINST THE REPOSITORIES THAT IMPORT IT", AND
      THE FIRST HALF OF THAT IS ENTIRELY LOCAL.** Deciding that `Invoice.total` disappeared needs
      the diff's two sides and nothing else — no clone of anybody else's repository, no token, no
      permission. Building that half first means the expensive half can arrive later without the
      cheap half waiting for it.

      **IT IS A PARSER'S ANSWER, WHICH IS WHY IT MAY BE ASSERTED.** "This function no longer takes
      `timeout`" is re-runnable on the same commit by anyone. Qodo advertises exactly this —
      *function signature violations, broken API contracts and schema drift* — and theirs is a
      model's reading. → `docs/product/comment-golden-rules.md`

      **A LEADING UNDERSCORE IS THE ONLY PRIVACY PYTHON HAS, AND `__all__` OVERRIDES IT.** A module
      that declares `__all__` has said what it offers; anything else is a convention we are reading
      rather than a rule the author wrote. When `__all__` is present it wins outright, including
      when it exports an underscored name on purpose.

      **A NEW ARGUMENT IS ONLY BREAKING WHEN IT IS REQUIRED.** Adding `timeout: int = 30` breaks
      nobody; adding `timeout: int` breaks every caller. Reporting both would make the section
      fire on ordinary additive work, which is the first false positive that stops it being read.

      **AND A REORDER IS BREAKING EVEN WHEN THE NAMES ARE UNCHANGED**, because positional callers
      exist and are invisible from here. Same reasoning as `AGENTS.md` rule 3: we cannot see the
      call sites, so we report the change and let the reader judge.
IMPORTS: stdlib ast, dataclasses. `parse.python_names.UnparseableSource` for the one failure.
CONSUMED BY: `serve/change_facts.py`, and D3b's consumer check when it lands.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from quantamind.parse.python_names import UnparseableSource

Definition = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


@dataclass(frozen=True, slots=True)
class Export:
    """One public name, and enough of its shape to tell a compatible change from a breaking one."""

    name: str
    kind: str
    """`function`, `async function` or `class`. A name that changes kind broke."""

    positional: tuple[str, ...] = ()
    """Parameters a caller may pass by position, in order. Order is part of the contract."""

    required: frozenset[str] = frozenset()
    """Parameters with no default. Adding one of these breaks every existing caller."""


@dataclass(frozen=True, slots=True)
class Break:
    """One way a change stopped honouring what the module used to offer."""

    name: str
    why: str

    def render(self) -> str:
        return f"`{self.name}` — {self.why}"


def _signature(node: Definition) -> tuple[tuple[str, ...], frozenset[str]]:
    """Positional parameter names in order, and the subset with no default."""
    if isinstance(node, ast.ClassDef):
        return (), frozenset()
    spec = node.args
    positional = [*spec.posonlyargs, *spec.args]
    # `self` is not part of the contract a caller sees; a method that loses it is a different
    # defect and one this module deliberately does not try to name.
    names = tuple(arg.arg for arg in positional if arg.arg not in ("self", "cls"))
    filled = len(spec.defaults)
    without = names[: len(names) - filled] if filled else names
    keyword_required = {
        arg.arg
        for arg, default in zip(spec.kwonlyargs, spec.kw_defaults, strict=True)
        if default is None
    }
    return names, frozenset({*without, *keyword_required})


def surface(source: str) -> dict[str, Export]:
    """The public names this module defines, by name.

    **TOP LEVEL ONLY.** A class's methods are reached through the class, so a change inside one is
    a change to the class — reporting both would name the same break twice and bury the useful line.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError) as exc:
        raise UnparseableSource(str(exc)) from None

    declared: set[str] | None = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            continue
        if isinstance(node.value, ast.List | ast.Tuple):
            declared = {
                element.value
                for element in node.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            }

    out: dict[str, Export] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        public = node.name in declared if declared is not None else not node.name.startswith("_")
        if not public:
            continue
        kind = "class" if isinstance(node, ast.ClassDef) else "function"
        if isinstance(node, ast.AsyncFunctionDef):
            kind = "async function"
        positional, required = _signature(node)
        out[node.name] = Export(node.name, kind, positional, required)
    return out


def broke(before: dict[str, Export], after: dict[str, Export]) -> tuple[Break, ...]:
    """Every way `after` stopped honouring what `before` offered. Empty when nothing did.

    **ADDITIONS ARE NEVER BREAKS.** A new export, a new optional argument and a new module all
    leave every existing caller working, and a section that fired on them would fire on most
    pull requests.
    """
    found: list[Break] = []
    for name, was in sorted(before.items()):
        now = after.get(name)
        if now is None:
            found.append(Break(name, "removed or renamed"))
            continue
        if now.kind != was.kind:
            found.append(Break(name, f"was a {was.kind}, is now a {now.kind}"))
            continue
        gone = [p for p in was.positional if p not in now.positional]
        if gone:
            found.append(Break(name, f"no longer takes {', '.join(f'`{p}`' for p in gone)}"))
            continue
        kept = [p for p in now.positional if p in was.positional]
        if kept != [p for p in was.positional if p in now.positional]:
            found.append(
                Break(name, "its parameters were reordered, which breaks positional calls")
            )
            continue
        added = sorted(now.required - was.required - set(was.positional))
        if added:
            found.append(
                Break(
                    name, f"now requires {', '.join(f'`{p}`' for p in added)}, which had no default"
                )
            )
    return tuple(found)
