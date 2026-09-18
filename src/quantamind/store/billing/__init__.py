"""Who is paying, and what that entitles — kept apart from what a repository told us.

WHAT: `subscriptions.py` writes one row per subscription from an authenticated Stripe delivery;
      `entitlement.py` stores and reads the coverage the billing service pushes.
WHY:  **`store/` IS AT THE FIFTEEN-FILE CAP, SO THIS IS A PACKAGE RATHER THAN MORE FILES.** The
      cap asked the question and the answer it produced is right anyway: every row in here arrives
      from a payment processor or from the service in front of one, never from a repository — a
      different source, a different trust argument, and a different thing to check when it is
      wrong.

      **THE TWO ARRIVE BY DIFFERENT ROUTES AND THAT IS THE POINT OF KEEPING BOTH VISIBLE.**
      `subscriptions.py` is written by a Stripe webhook this service receives directly.
      `entitlement.py` is written by `POST /entitlement` from the billing service, which owns the
      Stripe relationship. They are not two spellings of one thing, and which of them is the
      authority is a decision recorded in `docs/engineering/STRIPE.md`, not here.
IMPORTS: stdlib only. The store layer.
CONSUMED BY: `serve/review/`, `serve/web/entitlement_route.py`, `verify/paid_access.py`.
"""
