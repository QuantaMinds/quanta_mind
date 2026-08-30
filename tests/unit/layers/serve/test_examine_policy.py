"""When the model is consulted, when it is not, and why the two can never look alike.

WHAT: Exercises `serve/deep_review.examine()` — the policy between the allocation and the model.
      Asserts on the `Deep` record it returns, not on whether it raised.
WHY:  **NOT CONSULTED AND FOUND NOTHING ARE THE SAME PICTURE FROM OUTSIDE, AND MUST NOT BE THE
      SAME VALUE.** A delivery where the model was never asked, one where it was unreachable, and
      one where it read the diff and had nothing to say all end with zero findings in the comment.
      This project has shipped that confusion before — a cleanup that claimed a leftover was
      caught later, an oracle that ran on nothing. `None`, `consulted=False` and an empty
      `anchored` with `consulted=True` are three distinguishable answers.

      **AND NOTHING MAY COST MONEY BY DEFAULT.** `Settings()` out of the box must not reach a
      billed endpoint: inference disabled and no project are two separate reasons, and either
      alone is enough to stay silent.

      The outage case drives a real `examine()` over a real `Reading`; only the transport is
      forced to fail, because an outage cannot otherwise be produced on demand. What is asserted
      is the record OUR code builds from it.
IMPORTS: allocate.depth, serve.deep_review, types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quantamind.allocate.depth import Depth, Reading
from quantamind.infer.vertex import Unavailable
from quantamind.serve import deep_review
from quantamind.types.settings import Settings

FUNDED = Reading(Depth.FOCUSED, ("a.py", "b.py"), ("c.py",), "two funded, one named unread")


def _record_calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[object, ...]]:
    """Every call that would have reached a billed endpoint. **ASSERTING `None` IS NOT ENOUGH:**
    a `None` return proves what came back, not that nothing was spent on the way."""
    calls: list[tuple[object, ...]] = []

    def _spy(*args: object, **kwargs: object) -> None:
        calls.append(args)
        raise AssertionError("the model was called when policy said it must not be")

    monkeypatch.setattr(deep_review, "deep", _spy)
    return calls


def test_the_default_configuration_never_reaches_a_billed_endpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _record_calls(monkeypatch)

    out = deep_review.examine(tmp_path, "0" * 40, FUNDED, ["a.py"], Settings())

    assert calls == [], (
        "a stock Settings() reached a billed endpoint. Inference must take two deliberate acts — "
        "enabled AND a project to bill — or a customer's first delivery spends their money"
    )
    assert out is None


@pytest.mark.parametrize(
    ("enabled", "project"),
    [(True, ""), (False, "a-gcp-project")],
)
def test_either_half_of_the_configuration_alone_stays_silent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, enabled: bool, project: str
) -> None:
    """Enabled with nothing to bill, or a project with inference off. Both are
    non-configurations, and neither may spend anything."""
    calls = _record_calls(monkeypatch)
    settings = Settings(inference_enabled=enabled, inference_project=project)

    out = deep_review.examine(tmp_path, "0" * 40, FUNDED, ["a.py"], settings)

    assert calls == [], f"half a configuration ({enabled=}, {project=!r}) still spent money"
    assert out is None


def test_an_allocation_that_funded_nothing_asks_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _record_calls(monkeypatch)
    empty = Reading(Depth.FULL, (), (), "the change touched no file we can read")
    settings = Settings(inference_enabled=True, inference_project="a-gcp-project")

    out = deep_review.examine(tmp_path, "0" * 40, empty, [], settings)

    assert calls == [], "a fully-configured run called the model with nothing allocated to read"
    assert out is None


def test_an_unreachable_model_is_a_typed_record_not_an_exception_and_not_silence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**THE ONE THAT MATTERS.** An outage must not read like a clean review, and must not take
    the ranking down with it — the ranking never needed the model."""

    def _down(*args: object, **kwargs: object) -> None:
        raise Unavailable("vertex returned 503")

    monkeypatch.setattr(deep_review, "deep", _down)
    settings = Settings(inference_enabled=True, inference_project="a-gcp-project")

    out = deep_review.examine(tmp_path, "0" * 40, FUNDED, ["a.py", "b.py", "c.py"], settings)

    assert out is not None, "an outage returned None, which reads as 'never asked'"
    assert out.consulted is False, (
        "an unreachable model produced consulted=True — indistinguishable from a model that read "
        "the diff and approved it, which is exactly the silence this product refuses"
    )
    assert out.anchored == () and out.raw == 0
    assert out.read == FUNDED.paths, "the record must still name what would have been read"
