"""Hand-counted fixture for the census gate — RUNBOOK section 1.1.

WHAT: A realistic Python module whose non-builtin call sites have been counted by
      hand, used as ground truth for census.count_call_sites.
WHY:  RUNBOOK section 1.1 gates the denominator on an *exact* match against an
      independently counted file. Ground truth produced by the tool under test
      would prove nothing, so the count here comes from markers placed by reading.
IMPORTS: functools, so the fixture contains a realistic decorator call. Nothing
      from phase0 — a fixture that imported the harness could not be ground truth
      for it.
CONSUMED BY: tests/test_census.py::test_hand_counted_fixture_matches_exactly.

Every NON-BUILTIN call site is marked with a trailing `# SITE` comment; a line
with two sites is marked `# SITE x2`. The expected total is the sum of those
markers, established by reading this file rather than by running the census over
it, which is what makes it an independent ground truth.

Recount: `grep -o "# SITE\\( x2\\)\\?" hand_counted.py | sort | uniq -c`

Builtin calls are deliberately present and deliberately unmarked — `len`, `print`,
`isinstance`, `super`, `sorted`, `.append`, `.get`, `.strip`, `KeyError`. They must
NOT reach the denominator: DyPyBench found they are ~59% of the apparent
static-vs-dynamic gap, and counting them makes coverage meaningless.

The constructs mirror what the study cares about: super() chains, computed getattr
dispatch, registering decorators, and string-keyed lookup.
"""

from __future__ import annotations

import functools

REGISTRY: dict[str, object] = {}


def register(name):
    """A registering decorator — the edge no static analyser follows."""

    def wrap(fn):
        REGISTRY[name] = fn
        return fn

    return wrap


def audit(fn):
    @functools.wraps(fn)  # SITE
    def inner(*args, **kwargs):
        return fn(*args, **kwargs)  # SITE

    return inner


class Validator:
    def __init__(self, rules):
        self.rules = rules
        self.errors = []

    def validate(self, payload):
        for rule in self.rules:
            outcome = rule(payload)  # SITE
            if not outcome:
                self.errors.append(rule)
        return len(self.errors) == 0

    def describe(self):
        return f"validator with {len(self.rules)} rules"

    def reset(self):
        self.errors.clear()
        return self


class StrictValidator(Validator):
    """The switchboard: PyCG emits no edge for the super() call below."""

    def validate(self, payload):
        base = super().validate(payload)  # SITE
        return base and self.check_strict(payload)  # SITE

    def check_strict(self, payload):
        return isinstance(payload, dict)


class LoggingValidator(Validator):
    def validate(self, payload):
        self.before()  # SITE
        result = super().validate(payload)  # SITE
        self.after(result)  # SITE
        return result

    def before(self):
        print("starting")

    def after(self, result):
        print("finished", result)


@register("strict")  # SITE
def build_strict(rules):
    return StrictValidator(rules)  # SITE


@register("logging")  # SITE
def build_logging(rules):
    return LoggingValidator(rules)  # SITE


@audit  # SITE
def dispatch(kind, payload):
    """String-keyed dispatch — the registry lookup is invisible statically."""
    factory = REGISTRY.get(kind)
    if factory is None:
        raise KeyError(kind)
    validator = factory([])  # SITE
    return validator.validate(payload)  # SITE


def dynamic_call(module, config):
    """Computed getattr — undecidable, and the reason this study exists."""
    handler = getattr(module, config["handler"])
    return handler(config)  # SITE


def chained_helpers(source):
    return normalise(trim(source))  # SITE x2


def trim(value):
    return value.strip()


def normalise(value):
    return value.lower()


def comprehension_caller(values):
    return [transform(v) for v in values]  # SITE


def transform(value):
    return value * 2


def nested_comprehension(rows):
    return [[transform(cell) for cell in row] for row in rows]  # SITE


def conditional_dispatch(flag, payload):
    if flag:
        return build_strict([]).validate(payload)  # SITE x2
    return build_logging([]).validate(payload)  # SITE x2


def with_defaults(payload, factory=None):
    chosen = factory or build_strict
    return chosen([])  # SITE


def loop_caller(items):
    total = 0
    for item in items:
        total += score(item)  # SITE
    return total


def score(item):
    return len(str(item))


def try_caller(payload):
    try:
        return dispatch("strict", payload)  # SITE
    except KeyError:
        return fallback(payload)  # SITE


def fallback(payload):
    return sorted(payload.keys())


def lambda_caller(values):
    def apply_all(fn, xs):
        return [fn(x) for x in xs]  # SITE

    return apply_all(transform, values)  # SITE


def method_on_result(payload):
    return build_strict([]).describe()  # SITE x2


def module_level_entry():
    validator = build_strict([])  # SITE
    validator.reset()  # SITE
    return validator


RESULT = module_level_entry()  # SITE
