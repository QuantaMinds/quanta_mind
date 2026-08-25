"""The oracle experiments: what the model asserts about facts it cannot check, and how often.

Four measurements that share one question — does the reviewer know the difference between a fact it
can reach and one it cannot. `confabulation` says no at -8.3% discrimination; `pin_prevalence` and
`registry_prevalence` size the defects those false claims are about, at 0.24% and 0.00%; and
`date_grounding` found the class did not reproduce live at all.
"""
