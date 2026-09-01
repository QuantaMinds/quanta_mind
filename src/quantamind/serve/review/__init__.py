"""The review pipeline: gather the facts, apply the standards, assemble the body, deliver it.

WHAT: `review_delivery.py` orchestrates; `change_facts.py` gathers, `standards_step.py` enforces,
      `deep_review.py` and `pin_review.py` produce findings, `review_body.py` assembles the text.
WHY:  **`serve/` REACHED ITS 15-FILE CAP AND THIS IS THE HONEST SEAM.** The rest of `serve/` is the
      edge — the listener, the webhook, the CLI, health, onboarding — which exists to receive a
      request and hand it here. These six are one pipeline with one entry point, and every one of
      them was added because `deliver()` grew past a cap.
IMPORTS: nothing itself.
CONSUMED BY: `serve/listener.py`, `serve/cli.py`, `serve/webhook_github.py`.
"""
