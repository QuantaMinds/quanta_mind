# Findings to adjudicate — chunk 0

There are 6 findings below, numbered by their global index. Judge the CLAIM against the function shown.

### FINDING 0
repository: scrapy/scrapy   pull request #96 (MERGED)
file: scrapy/contrib/downloadermiddleware/cookies.py
claim_type: resource_leak
symbols named: process_request -> CookiesMiddleware.jars

CLAIM: The `process_request` method populates the `self.jars` dictionary using keys from request metadata (`request.meta['cookiejar']`), but because the `spider_closed` cleanup mechanism was removed in the same change, these dictionary entries are never deleted, causing a memory leak.

THE FUNCTION UNDER REVIEW (process_request, lines 20-33):
    20 |     def process_request(self, request, spider):
    21 |         if 'dont_merge_cookies' in request.meta:
    22 |             return
    23 | 
    24 |         cookiejarkey = request.meta.get("cookiejar")
    25 |         jar = self.jars[cookiejarkey]
    26 |         cookies = self._get_request_cookies(jar, request)
    27 |         for cookie in cookies:
    28 |             jar.set_cookie_if_ok(cookie, request)
    29 | 
    30 |         # set Cookie header
    31 |         request.headers.pop('Cookie', None)
    32 |         jar.add_cookie_header(request)
    33 |         self._debug_cookie(request, spider)

---

### FINDING 1
repository: tornadoweb/tornado   pull request #232 (MERGED)
file: tornado/test/testing_test.py
claim_type: missing_guard
symbols named: del os.environ[name] -> set_environ

CLAIM: The `finally` block unconditionally attempts to `del os.environ[name]` if the variable did not exist before the `with` block, but fails with a `KeyError` if the variable was unset within the `with` block itself.

THE FUNCTION UNDER REVIEW (set_environ, lines 18-29):
    18 | @contextlib.contextmanager
    19 | def set_environ(name, value):
    20 |     old_value = os.environ.get(name)
    21 |     os.environ[name] = value
    22 | 
    23 |     try:
    24 |         yield
    25 |     finally:
    26 |         if old_value is None:
    27 |             del os.environ[name]
    28 |         else:
    29 |             os.environ[name] = old_value

---

### FINDING 2
repository: tornadoweb/tornado   pull request #302 (MERGED)
file: tornado/test/twistedreactor_test.py
claim_type: resource_leak
symbols named: _testNoWriter -> ReactorFDTest.tearDown

CLAIM: The function `_testNoWriter` prematurely closes a file object via its inner `stopTest` function, which `ReactorFDTest.tearDown` later attempts to close again, causing a `ValueError` from a double-close operation.

THE FUNCTION UNDER REVIEW (_testNoWriter, lines 234-261):
   234 |     def _testNoWriter(self):
   235 |         """
   236 |         In this test we have no writer. Make sure the reader doesn't
   237 |         read anything.
   238 |         """
   239 |         def checkReadInput(fd):
   240 |             self.fail("Must not be called.")
   241 | 
   242 |         def stopTest():
   243 |             # Close the writer here since the IOLoop doesn't know
   244 |             # about it.
   245 |             self._writer.close()
   246 |             self._reactor.stop()
   247 |         self._reader = Reader(self._p1, checkReadInput)
   248 | 
   249 |         # We create a writer, but it should never be invoked.
   250 |         self._writer = Writer(self._p2, lambda fd: fd.write('x'))
   251 | 
   252 |         # Test that adding and removing the writer leaves us with no writer.
   253 |         self._reactor.addWriter(self._writer)
   254 |         self._reactor.removeWriter(self._writer)
   255 | 
   256 |         # Test that adding and removing the reader doesn't cause
   257 |         # unintended effects.
   258 |         self._reactor.addReader(self._reader)
   259 | 
   260 |         # Wake up after a moment and stop the test
   261 |         self._reactor.callLater(0.001, stopTest)

---

### FINDING 3
repository: celery/celery   pull request #186 (MERGED)
file: celery/schedules.py
claim_type: unhandled_case
symbols named: iso_next_day -> delta

CLAIM: The calculation for `add_week` becomes true when the next scheduled day is the earliest day in the week (e.g., from Friday to Monday), causing `relativedelta` to incorrectly add a week and schedule the task for the wrong day.

THE FUNCTION UNDER REVIEW (__init__, lines 258-266):
   258 |     def __init__(self, max_: int = 60, min_: int = 0):
   259 |         self.max_ = max_
   260 |         self.min_ = min_
   261 |         self.pats: tuple[tuple[re.Pattern, Callable], ...] = (
   262 |             (re.compile(self._range + self._steps), self._range_steps),
   263 |             (re.compile(self._range), self._expand_range),
   264 |             (re.compile(self._star + self._steps), self._star_steps),
   265 |             (re.compile('^' + self._star + '$'), self._expand_star),
   266 |         )

---

### FINDING 4
repository: encode/django-rest-framework   pull request #23 (MERGED)
file: djangorestframework/tests/parsers.py
claim_type: wrong_order
symbols named: setUp -> test_fail

CLAIM: The test `test_fail` relies on a `max_length` validation failure, but the string set up in `setUp` for `field1` also fails `min_length` validation, masking the intended test behavior.

THE FUNCTION UNDER REVIEW (setUp, lines 145-146):
   145 |     def setUp(self):
   146 |         self.string = "field1=abc&field2=defghijk" 

---

### FINDING 5
repository: pallets/flask   pull request #409 (MERGED)
file: flask/templating.py
claim_type: contract_violation
symbols named: def render_template(template_name_or_list, **context): -> render_template(template_name=...)

CLAIM: Renaming the `template_name` parameter to `template_name_or_list` breaks backward compatibility for callers that passed the template name using a keyword argument.

THE FUNCTION UNDER REVIEW (render_template, lines 112-125):
   112 | def render_template(template_name_or_list, **context):
   113 |     """Renders a template from the template folder with the given
   114 |     context.
   115 | 
   116 |     :param template_name_or_list: the name of the template to be
   117 |                                   rendered, or an iterable with template names
   118 |                                   the first one existing will be rendered
   119 |     :param context: the variables that should be available in the
   120 |                     context of the template.
   121 |     """
   122 |     ctx = _request_ctx_stack.top
   123 |     ctx.app.update_template_context(context)
   124 |     return _render(ctx.app.jinja_env.get_or_select_template(template_name_or_list),
   125 |                    context, ctx.app)
