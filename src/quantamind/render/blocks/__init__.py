"""The pieces a pull-request comment is assembled from — one module per block.

`render/` stood at its fifteen-file cap for three consecutive changes, and `check_structure.py`
says to introduce a sub-package rather than raise it. This is that package: everything here
renders ONE section and knows nothing about the others, which is what lets `comment.py` decide
the order in one place. `context/` (D6) and the report renderers stay outside it — they are
whole documents, not sections of one.
"""
