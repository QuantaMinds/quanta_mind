"""What a committed credential looks like, and — far more important — what does not.

WHAT: Drives `parse.secret_scan.secrets_in()` over lines that must fire and lines that must not.
WHY:  **THE FALSE POSITIVES OUTNUMBER THE TRUE ONES HERE ON PURPOSE.** Telling a developer they
      have committed a credential when they have not is alarming, public, and takes a key rotation
      to disprove. It is the most expensive wrong sentence this product can print, and D7a's whole
      claim is precision: *"we catch hardcoded credentials, exactly, and we do not claim to catch
      injection"* is a weaker sentence and a defensible one.

      **ENTROPY DID LESS WORK THAN EXPECTED AND THAT WAS MEASURED, NOT ASSUMED.** The first version
      of `MIN_ENTROPY`'s docstring asserted `password12345678` scores "about 3.1" against a real key
      "above 4.0". Measured: **3.88 against 4.28**. The floor does not separate them and the
      vocabulary check does — an invented number that the very first run contradicted.

      **THE SECRET NEVER REACHES THE EVIDENCE.** A `Checked` row goes to the audit trail, the
      comment and the customer's database. Writing the credential into any of those would move it
      somewhere new and make us the leak.
IMPORTS: quantamind.parse.secret_scan.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import pytest

from quantamind.parse.secret_scan import REDACT, entropy, secrets_in

# **EVERY FIXTURE IS ASSEMBLED, NEVER WRITTEN OUT.** The first version of this file spelled a
# Stripe-shaped key in full and **GitHub's push protection rejected the push** — which is an
# independent confirmation that the pattern matches what a real scanner matches, and a reminder
# that a secret detector's own tests are the one place a matching literal must never appear. A
# scanner whose fixtures cannot be committed is a scanner nobody can maintain.
LIVE = "_live_"
ISSUED = [
    ("AWS access key", 'AWS_KEY = "' + "AKIA" + "IOSFODNN7EXAMPLE" + '"'),
    ("GitHub token", 'token = "gh' + "p_" + "a" * 36 + '"'),
    ("Slack token", 'slack = "xox' + "b-1234567890-abcdefghij" + '"'),
    ("Stripe live key", 'stripe = "sk' + LIVE + "4eC39HqLyjWDarjtT1zdp" + '"'),
    ("Google API key", 'key = "AIza' + "B" * 35 + '"'),
    ("private key", "-----BEGIN RSA PRIVATE KEY-----"),
]


@pytest.mark.parametrize(("kind", "line"), ISSUED)
def test_an_issued_credential_format_is_reported_with_its_kind(kind: str, line: str) -> None:
    """**A PROVIDER PREFIX IS EVIDENCE, NOT SUSPICION.** One company issues it in one format."""
    (found,) = secrets_in(line)

    assert found.kind == kind
    assert found.line == 1


NOT_SECRETS = [
    'password = "xxxxxxxxxxxxxxxx"',
    'api_key = "your-api-key-here"',
    'token = "<redacted-for-docs>"',
    'secret = "${VAULT_SECRET_PATH}"',
    'client_secret = "{{ ansible_vault_value }}"',
    'password = "changeme12345678"',
    'api_key = "placeholder-value-x"',
    'api_key = "aaaaaaaaaaaaaaaaaaaa"',
    'token = os.environ["GITHUB_TOKEN"]',
    'password = "password12345678"',
    'secret = "SecretValue123456"',
    'DIGEST = "sha256:abcd1234efgh5678"',
    "url = 'https://example.com/a/long/path/to/some/file.tar.gz'",
    "AWS_KEY = os.getenv('AWS_ACCESS_KEY_ID')",
]


@pytest.mark.parametrize("line", NOT_SECRETS)
def test_a_placeholder_or_a_reference_is_never_reported(line: str) -> None:
    """**EACH OF THESE APPEARS IN REAL REPOSITORIES BESIDE A CREDENTIAL-SHAPED NAME**, and each is
    somebody documenting or reading a secret rather than committing one."""
    assert secrets_in(line) == (), f"false positive on {line!r}"


def test_a_high_entropy_value_beside_a_credential_name_is_reported() -> None:
    """The generic rule needs BOTH: a secret-shaped target and enough entropy. Either alone is a
    guess, and a guess here is the expensive kind."""
    (found,) = secrets_in('password = "Tr0ub4dor&3xKcd-9Zq7Wm"')

    assert found.kind == "hardcoded credential"


def test_a_high_entropy_value_with_no_credential_name_is_not_reported() -> None:
    """A long random string is a hash, a UUID, a checksum or a base64 asset far more often than a
    secret. Without a name saying otherwise there is nothing to go on."""
    assert secrets_in('digest = "9f86d081884c7d659a2feaa0c55ad015"') == ()


def test_the_secret_itself_never_reaches_the_evidence() -> None:
    """**A `Checked` ROW GOES TO THE AUDIT TRAIL AND THE COMMENT.** Putting the credential in it
    would move the secret somewhere new and make us the leak."""
    secret = "Tr0ub4dor&3xKcd-9Zq7Wm"
    (found,) = secrets_in(f'password = "{secret}"')

    assert secret not in found.render()
    assert len(found.prefix) == REDACT
    assert secret.startswith(found.prefix), "the prefix must still locate it in the file"


def test_one_line_reports_one_finding() -> None:
    """A line matching two patterns is one problem to fix; twice would make a file look worse."""
    line = 'AWS = "' + "AKIA" + 'IOSFODNN7EXAMPLE"  # token = "gh' + "p_" + "a" * 36 + '"'

    assert len(secrets_in(line)) == 1


def test_the_line_number_is_the_real_one() -> None:
    """A developer who cannot find what fired cannot fix it."""
    leak = 'AWS_KEY = "' + "AKIA" + 'IOSFODNN7EXAMPLE"'
    (found,) = secrets_in(f"clean = 1\n\n\n{leak}\n")

    assert found.line == 4


def test_the_measured_entropies_are_what_the_docstring_now_claims() -> None:
    """**THE NUMBER IN `MIN_ENTROPY`'s DOCSTRING WAS INVENTED ONCE AND IS PINNED NOW.** It said
    3.1 for the placeholder; it is 3.88, which is above the floor and is why the vocabulary check
    exists at all."""
    assert round(entropy("password12345678"), 2) == 3.88
    assert round(entropy("Tr0ub4dor&3xKcd-9Zq7Wm"), 2) == 4.28
    assert entropy("") == 0.0
