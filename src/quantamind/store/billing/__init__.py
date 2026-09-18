"""What Stripe has told us about who is paying, kept apart from what GitHub has told us.

`subscriptions.py` writes one row per subscription from an authenticated delivery and reads back
the current one. Split out when `store/` reached its fifteen-file cap, and grouped rather than
scattered because every row in here arrives from a payment processor rather than from a repository
— a different source, a different trust argument, and a different thing to check when it is wrong.
"""
