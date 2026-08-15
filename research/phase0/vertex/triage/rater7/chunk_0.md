# Findings to adjudicate — chunk 0

There are 9 findings below, numbered by their global index. Judge the CLAIM against the function shown.

### FINDING 0
repository: pallets/flask   pull request #307 (MERGED)
file: flask/blueprints.py
claim_type: unhandled_case
symbols named: decorator -> add_url_rule

CLAIM: The function `decorator` extracts `endpoint` from `options` and passes it to `add_url_rule`, but `add_url_rule` does not validate that `endpoint` is a string before performing a substring check, causing a `TypeError` if a non-iterable value like an integer is passed.

THE FUNCTION UNDER REVIEW (decorator, lines 159-162):
   159 |         def decorator(f):
   160 |             endpoint = options.pop("endpoint", f.__name__)
   161 |             self.add_url_rule(rule, endpoint, f, **options)
   162 |             return f

---

### FINDING 1
repository: psf/requests   pull request #26 (MERGED)
file: requests/__init__.py
claim_type: contract_violation
symbols named: settings.cache -> timeout

CLAIM: Because `settings.cache` is a class attribute shared across all instances, a nested `settings` context manager overwrites the value cached by the outer context, preventing the outer context from correctly restoring the original module-level `timeout` upon exit.

THE FUNCTION UNDER REVIEW (__enter__, lines 25-26):
    25 |     def __enter__(self):
    26 |         pass

---

### FINDING 2
repository: celery/celery   pull request #186 (MERGED)
file: celery/schedules.py
claim_type: contract_violation
symbols named: _expand_range -> _expand_range

CLAIM: The range expansion logic for wrap-around cron fields incorrectly calculates the upper bound of the first part of the range as `self.min_ + self.max_`, which fails to include the maximum value when `self.min_` is 0.

THE FUNCTION UNDER REVIEW (_expand_range, lines 283-291):
   283 |     def _expand_range(self, toks: Sequence[str]) -> list[int]:
   284 |         fr = self._expand_number(toks[0])
   285 |         if len(toks) > 1:
   286 |             to = self._expand_number(toks[1])
   287 |             if to < fr:  # Wrap around max_ if necessary
   288 |                 return (list(range(fr, self.min_ + self.max_)) +
   289 |                         list(range(self.min_, to + 1)))
   290 |             return list(range(fr, to + 1))
   291 |         return [fr]

---

### FINDING 3
repository: pallets/flask   pull request #413 (MERGED)
file: examples/blueprintexample/blueprintexample_test.py
claim_type: contract_violation
symbols named: unittest.TestCase -> self.assertEquals

CLAIM: The method `assertEquals` was removed from `unittest.TestCase` in Python 3.2, so calling it violates the class's modern API contract and will raise an `AttributeError`.

THE FUNCTION UNDER REVIEW (test_urls, lines 17-32):
    17 |     def test_urls(self):
    18 |         r = self.app.get('/')
    19 |         self.assertEquals(r.status_code, 200)
    20 |         
    21 |         r = self.app.get('/hello')
    22 |         self.assertEquals(r.status_code, 200)
    23 |         
    24 |         r = self.app.get('/world')
    25 |         self.assertEquals(r.status_code, 200)
    26 |         
    27 |         #second blueprint instance
    28 |         r = self.app.get('/pages/hello')
    29 |         self.assertEquals(r.status_code, 200)
    30 |         
    31 |         r = self.app.get('/pages/world')
    32 |         self.assertEquals(r.status_code, 200)

---

### FINDING 4
repository: celery/celery   pull request #215 (MERGED)
file: celery/apps/beat.py
claim_type: contract_violation
symbols named: start_scheduler -> logging.Handler

CLAIM: The call to `logger.critical` in `start_scheduler` manually formats the exception traceback into the message string instead of using the `exc_info` argument, preventing log handlers from accessing structured exception information for custom processing.

THE FUNCTION UNDER REVIEW (setup_logging, lines 86-91):
    86 |     def setup_logging(self, colorize: bool | None = None) -> None:
    87 |         if colorize is None and self.no_color is not None:
    88 |             colorize = not self.no_color
    89 |         self.app.log.setup(self.loglevel, self.logfile,
    90 |                            self.redirect_stdouts, self.redirect_stdouts_level,
    91 |                            colorize=colorize)

---

### FINDING 5
repository: tornadoweb/tornado   pull request #273 (MERGED)
file: tornado/database.py
claim_type: contract_violation
symbols named: _execute -> execute_rowcount

CLAIM: The helper function _execute, upon a database disconnect, attempts to reconnect and retry the query using a cursor that belongs to the old, now-closed connection, which is invalid and violates the DB-API contract.

THE FUNCTION UNDER REVIEW (execute_rowcount, lines 141-148):
   141 |     def execute_rowcount(self, query, *parameters):
   142 |         """Executes the given query, returning the rowcount from the query."""
   143 |         cursor = self._cursor()
   144 |         try:
   145 |             self._execute(cursor, query, parameters)
   146 |             return cursor.rowcount
   147 |         finally:
   148 |             cursor.close()

---

### FINDING 6
repository: pallets/flask   pull request #307 (MERGED)
file: flask/blueprints.py
claim_type: unhandled_case
symbols named: add_url_rule -> url_for

CLAIM: By not validating that an endpoint name contains a dot, `add_url_rule` allows registering a view that later causes infinite recursion in `url_for` during URL resolution.

THE FUNCTION UNDER REVIEW (add_url_rule, lines 165-172):
   165 |     def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
   166 |         """Like :meth:`Flask.add_url_rule` but for a blueprint.  The endpoint for
   167 |         the :func:`url_for` function is prefixed with the name of the blueprint.
   168 |         """
   169 |         if endpoint:
   170 |             assert '.' not in endpoint, "Blueprint endpoint's should not contain dot's"
   171 |         self.record(lambda s:
   172 |             s.add_url_rule(rule, endpoint, view_func, **options))

---

### FINDING 7
repository: tornadoweb/tornado   pull request #273 (MERGED)
file: tornado/database.py
claim_type: missing_guard
symbols named: executemany_rowcount -> executemany_rowcount

CLAIM: When `cursor.executemany` raises an `OperationalError` indicating a lost connection, `executemany_rowcount` fails to call `self.close()` to mark the connection as closed, which prevents future automatic reconnection.

THE FUNCTION UNDER REVIEW (executemany_rowcount, lines 169-179):
   169 |     def executemany_rowcount(self, query, parameters):
   170 |         """Executes the given query against all the given param sequences.
   171 | 
   172 |         We return the rowcount from the query.
   173 |         """
   174 |         cursor = self._cursor()
   175 |         try:
   176 |             cursor.executemany(query, parameters)
   177 |             return cursor.rowcount
   178 |         finally:
   179 |             cursor.close()

---

### FINDING 8
repository: psf/requests   pull request #26 (MERGED)
file: requests/__init__.py
claim_type: contract_violation
symbols named: self.cache['timeout'] = self.module.timeout -> setattr(self.module, key, self.cache[key])

CLAIM: The assignment to the shared class attribute `self.cache` in `__init__` overwrites the cached value, causing `__exit__` to restore an incorrect value when `settings` context managers are nested.

THE FUNCTION UNDER REVIEW (__init__, lines 17-23):
    17 |     def __init__(self, timeout):
    18 |         self.module = inspect.getmodule(self)
    19 |         
    20 |         # Cache settings
    21 |         self.cache['timeout'] = self.module.timeout
    22 |         
    23 |         self.module.timeout = timeout
