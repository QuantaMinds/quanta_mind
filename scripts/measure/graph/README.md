# Graph-derived measurements

**Everything here asks the same question about a different signal: does something the import graph
can see separate an outcome anybody cares about?**

Split out of `scripts/measure/` when it hit its fifteen-file cap, and split on this line because
the answers belong together. Two of the three are already decided:

| script | signal | verdict |
|---|---|---|
| `run_six.py` | blast radius — in-degree as a ranking | **INCONCLUSIVE**, 10 discordant pairs against a floor of 20, and prior-fix history beat it 65-13 where they disagreed. D2d and D2b dropped 2026-08-31 |
| `drift_separates.py` | architectural drift — import shifts per commit | this one |

**The category's pitch names both as "deep context".** A consensus is not a measurement, and this
directory is where that gets tested rather than repeated.
