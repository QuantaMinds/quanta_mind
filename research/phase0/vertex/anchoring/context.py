"""Build the structured context a reviewer would actually have at review time.

WHAT: For one changed function, extracts from its file the things the first run's failures needed
      and did not get -- the enclosing class's attributes and method signatures, the signatures of
      other functions in the file, the imports, and the call sites of this function within the
      file.
WHY:  The first run gave the model one function and one diff, about 1,674 tokens. Its
      UNFALSIFIABLE findings asked questions this context answers: "can `self.model_executor` be
      None" is decided by `__init__`; "is this passed None by its only caller" is decided by the
      call sites. That was 7.6% of findings outright, plus an unknown share of the semantic
      errors.

      EVERYTHING HERE IS AVAILABLE AT REVIEW TIME. Deliberately excluded: whether the pull
      request merged and whether CI passed. Several first-run findings would be killed by knowing
      a test passed -- and a real reviewer does not know that yet, so using it would measure a
      reviewer that cannot exist.
IMPORTS: stdlib only (ast).
CONSUMED BY: `enriched.py` in this package.
"""

from __future__ import annotations

import ast

MAX_SIGS, MAX_CALLERS = 40, 6


def _sig(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = [a.arg for a in node.args.args]
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    ret = ""
    if node.returns is not None:
        try:
            ret = " -> " + ast.unparse(node.returns)
        except (AttributeError, ValueError):
            ret = ""
    kind = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    return f"{kind} {node.name}({', '.join(args)}){ret}"


def _class_of(tree: ast.Module, target: str) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(
            isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)) and c.name == target
            for c in node.body
        ):
            return node
    return None


def _self_attributes(cls: ast.ClassDef) -> list[str]:
    """`self.x = ...` assignments, which is what answers 'can this attribute be None'."""
    out: list[str] = []
    for node in ast.walk(cls):
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if (
                isinstance(t, ast.Attribute)
                and isinstance(t.value, ast.Name)
                and t.value.id == "self"
            ):
                try:
                    out.append(f"self.{t.attr} = {ast.unparse(node.value)[:90]}")
                except (AttributeError, ValueError):
                    out.append(f"self.{t.attr} = ...")
    return out


def _callers(tree: ast.Module, target: str, lines: list[str]) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if name != target:
            continue
        ln = getattr(node, "lineno", 0)
        if 1 <= ln <= len(lines):
            out.append(f"line {ln}: {lines[ln - 1].strip()[:110]}")
    return out


def build(source: str, target: str) -> str:
    """The structured block for `target`, or '' when the file does not parse."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return ""
    lines = source.split("\n")
    parts: list[str] = []

    imports = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if imports:
        parts.append("IMPORTS IN THIS FILE:\n" + "\n".join(f"  {i}" for i in imports[:MAX_SIGS]))

    cls = _class_of(tree, target)
    if cls is not None:
        attrs = _self_attributes(cls)
        methods = [
            _sig(c) for c in cls.body if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        block = [f"ENCLOSING CLASS: class {cls.name}"]
        if attrs:
            block.append(
                "  attributes assigned anywhere in the class "
                "(this decides whether an attribute can be absent or None):"
            )
            block += [f"    {a}" for a in dict.fromkeys(attrs)][:MAX_SIGS]
        if methods:
            block.append("  methods:")
            block += [f"    {m}" for m in methods[:MAX_SIGS]]
        parts.append("\n".join(block))

    others = [
        _sig(n)
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name != target
    ]
    if others:
        parts.append(
            "OTHER FUNCTIONS DEFINED IN THIS FILE (signatures only):\n"
            + "\n".join(f"  {x}" for x in list(dict.fromkeys(others))[:MAX_SIGS])
        )

    calls = _callers(tree, target, lines)
    parts.append(
        f"CALL SITES OF `{target}` WITHIN THIS FILE ({len(calls)} found):\n"
        + (
            "\n".join(f"  {c}" for c in calls[:MAX_CALLERS])
            if calls
            else "  none in this file. Do NOT assert what callers pass -- you cannot see them."
        )
    )
    return "\n\n".join(parts)
