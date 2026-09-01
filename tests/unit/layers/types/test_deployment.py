"""D7f: an air-gapped deployment REFUSES, and refusing is not the same as failing to connect.

WHAT: `types/deployment.py` — the shape, the destinations, and the refusal.
WHY:  **"AN OUTBOUND CALL THAT FAILS QUIETLY IN A BANK IS A FINDING AGAINST US, NOT A BUG."** A
      deployment that merely lacks a route produces timeouts and a late review; the customer finds
      the attempt in their egress log and we never see it. Every test here checks that the refusal
      is OURS, immediate, and names both the shape and the destination.

      **AND THAT THE PERMISSIVE DIRECTION STILL WORKS.** A gate that refuses everything passes any
      test written only about refusals, and would take the product offline in the cloud.
IMPORTS: quantamind.types.deployment.
CONSUMED BY: `just test-unit`.
"""

from __future__ import annotations

import pytest

from quantamind.types.deployment import (
    PERMITTED,
    Destination,
    NetworkRefused,
    NotADeploymentShape,
    Shape,
    current,
    permit,
)


@pytest.mark.parametrize(
    "destination",
    [d for d in Destination if d is not Destination.GIT_REMOTE],
    ids=lambda d: d.value,
)
def test_air_gapped_refuses_every_destination_but_the_clone(destination: Destination) -> None:
    """**PARAMETRISED OVER THE ENUM**, so a destination added later is covered without an edit."""
    with pytest.raises(NetworkRefused) as raised:
        permit(destination, Shape.AIR_GAPPED)
    assert raised.value.destination is destination
    assert raised.value.shape is Shape.AIR_GAPPED


def test_air_gapped_still_permits_the_clone() -> None:
    """**THE CLONE IS THE BOUNDARY, NOT AN EXCEPTION.** With no repository there is nothing to
    review, so refusing it would not be an air gap — it would be an off switch."""
    assert PERMITTED[Shape.AIR_GAPPED] == frozenset({Destination.GIT_REMOTE})
    permit(Destination.GIT_REMOTE, Shape.AIR_GAPPED)


@pytest.mark.parametrize("destination", list(Destination), ids=lambda d: d.value)
def test_cloud_permits_everything(destination: Destination) -> None:
    """The other half: a gate that refused everything would pass every test above."""
    assert destination in PERMITTED[Shape.CLOUD]
    permit(destination, Shape.CLOUD)


def test_on_prem_loses_only_the_metadata_server() -> None:
    """That address exists only inside Google's fabric; asking for it elsewhere hangs to a timeout,
    which is the quiet failure this row removes."""
    assert PERMITTED[Shape.ON_PREM] == frozenset(Destination) - {Destination.GOOGLE_METADATA}
    with pytest.raises(NetworkRefused):
        permit(Destination.GOOGLE_METADATA, Shape.ON_PREM)
    permit(Destination.INFERENCE, Shape.ON_PREM)
    permit(Destination.GITHUB_API, Shape.ON_PREM)


def test_the_refusal_names_the_shape_the_destination_and_what_is_allowed() -> None:
    """**A CUSTOMER READING A STACK TRACE MUST SEE WHY**, not "network error"."""
    with pytest.raises(NetworkRefused) as raised:
        permit(Destination.INFERENCE, Shape.AIR_GAPPED)
    message = str(raised.value)
    assert "air_gapped" in message
    assert "inference" in message
    assert "Nothing was sent" in message
    assert "git_remote" in message, "must say what IS permitted, not only what is not"


def test_every_shape_has_a_permission_set() -> None:
    """**A SHAPE ADDED WITHOUT AN ENTRY WOULD KeyError INSIDE `permit`** — at the call site, in
    production, on the first outbound call rather than at import."""
    assert set(PERMITTED) == set(Shape)


def test_the_shape_is_read_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTAMIND_DEPLOYMENT_SHAPE", "air_gapped")
    assert current() is Shape.AIR_GAPPED
    monkeypatch.delenv("QUANTAMIND_DEPLOYMENT_SHAPE")
    assert current() is Shape.CLOUD, "an unset shape is cloud, which is the documented default"


def test_a_misspelled_shape_refuses_rather_than_defaulting(monkeypatch: pytest.MonkeyPatch) -> None:
    """**THE MOST DANGEROUS DEFAULT IN THE FILE.** Reading a typo as `cloud` would turn a
    misconfigured air-gapped deployment into one that reaches the network."""
    monkeypatch.setenv("QUANTAMIND_DEPLOYMENT_SHAPE", "airgapped")
    with pytest.raises(NotADeploymentShape, match="airgapped"):
        current()


def test_permit_defaults_to_the_configured_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    """Call sites pass one argument; the shape comes from configuration."""
    monkeypatch.setenv("QUANTAMIND_DEPLOYMENT_SHAPE", "air_gapped")
    with pytest.raises(NetworkRefused):
        permit(Destination.GITHUB_API)
