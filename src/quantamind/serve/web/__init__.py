"""The human-facing surface: sign-in now, the dashboard later.

WHAT: A sub-package for routes a PERSON reaches with a browser, as distinct from `serve/`'s
      webhook, which only GitHub ever calls.
WHY:  **TWO SURFACES WITH DIFFERENT THREAT MODELS AND DIFFERENT CALLERS.** The webhook
      authenticates an HMAC over raw bytes and answers a machine; this answers a human holding a
      cookie, and the failure modes are CSRF and session theft rather than a forged signature.
      Keeping them apart is also what makes `serve/` fit its file cap without trimming the
      comments that explain the webhook.
CONSUMED BY: `serve/listener.py`.
"""
