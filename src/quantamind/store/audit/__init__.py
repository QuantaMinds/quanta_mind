"""The audit trail as something a compliance team can be handed, not only queried.

Split out when `store/` reached its fifteen-file cap. `store/rule_checks.py` writes the rows and
`store/compliance.py` summarises them; this reads them out whole.
"""
