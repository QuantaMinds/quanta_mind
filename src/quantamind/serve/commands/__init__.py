"""One module per command the CLI exposes, in one place instead of scattered through `serve/`.

`cli.py` dispatches to exactly these: `run_review` ranks a pull request, `run_commit` ranks a local
commit, `run_endpoint` binds the webhook, `run_report` prints a repository's board or compliance
table, and `run_migrate` brings a store up to this build's schema. They share a shape -- parse what
the operator asked for, call one pipeline, print or post the result -- and nothing else.

They were grouped when `serve/` reached its fifteen-file cap and the blocking status check needed
somewhere to live. **The cap is a prompt to split by concern, not a number to raise**, and "these
five are the command line" is the concern that was already there and unnamed.
"""
