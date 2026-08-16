# Findings to adjudicate — chunk 1

There are 9 findings below, numbered by their global index. Judge the CLAIM against the function shown.

### FINDING 9
repository: scrapy/scrapy   pull request #97 (MERGED)
file: scrapy/tests/test_http_response.py
claim_type: contract_violation
symbols named: self.assertEqual(r3._declared_encoding(), "cp1252") -> self._assert_response_values(r3, 'iso-8859-1', u"\xa3")

CLAIM: The change to a new encoding utility causes 'iso-8859-1' to be resolved to 'cp1252', as checked at symbol_a, which makes the response's final encoding 'cp1252', contradicting the outdated check at symbol_b which still expects 'iso-8859-1'.

THE FUNCTION UNDER REVIEW (test_encoding, lines 161-187):
   161 |     def test_encoding(self):
   162 |         r1 = self.response_class("http://www.example.com", headers={"Content-type": ["text/html; charset=utf-8"]}, body="\xc2\xa3")
   163 |         r2 = self.response_class("http://www.example.com", encoding='utf-8', body=u"\xa3")
   164 |         r3 = self.response_class("http://www.example.com", headers={"Content-type": ["text/html; charset=iso-8859-1"]}, body="\xa3")
   165 |         r4 = self.response_class("http://www.example.com", body="\xa2\xa3")
   166 |         r5 = self.response_class("http://www.example.com", headers={"Content-type": ["text/html; charset=None"]}, body="\xc2\xa3")
   167 |         r6 = self.response_class("http://www.example.com", headers={"Content-type": ["text/html; charset=gb2312"]}, body="\xa8D")
   168 |         r7 = self.response_class("http://www.example.com", headers={"Content-type": ["text/html; charset=gbk"]}, body="\xa8D")
   169 | 
   170 |         self.assertEqual(r1._headers_encoding(), "utf-8")
   171 |         self.assertEqual(r2._headers_encoding(), None)
   172 |         self.assertEqual(r2._declared_encoding(), 'utf-8')
   173 |         self._assert_response_encoding(r2, 'utf-8')
   174 |         self.assertEqual(r3._headers_encoding(), "cp1252")
   175 |         self.assertEqual(r3._declared_encoding(), "cp1252")
   176 |         self.assertEqual(r4._headers_encoding(), None)
   177 |         self.assertEqual(r5._headers_encoding(), None)
   178 |         self._assert_response_encoding(r5, "utf-8")
   179 |         assert r4._body_inferred_encoding() is not None and r4._body_inferred_encoding() != 'ascii'
   180 |         self._assert_response_values(r1, 'utf-8', u"\xa3")
   181 |         self._assert_response_values(r2, 'utf-8', u"\xa3")
   182 |         self._assert_response_values(r3, 'iso-8859-1', u"\xa3")
   183 |         self._assert_response_values(r6, 'gb18030', u"\u2015")
   184 |         self._assert_response_values(r7, 'gb18030', u"\u2015")
   185 | 
   186 |         # TextResponse (and subclasses) must be passed a encoding when instantiating with unicode bodies
   187 |         self.assertRaises(TypeError, self.response_class, "http://www.example.com", body=u"\xa3")

---

### FINDING 10
repository: psf/requests   pull request #26 (MERGED)
file: requests/__init__.py
claim_type: contract_violation
symbols named: settings.__init__ -> settings.__exit__

CLAIM: The `settings.__init__` method stores the original module state in a class-level dictionary `cache`, which is shared by all instances, causing nested `settings` contexts to overwrite this cache and leading `settings.__exit__` to restore an incorrect state.

THE FUNCTION UNDER REVIEW (__exit__, lines 28-31):
    28 |     def __exit__(self, type, value, traceback):
    29 |         # Restore settings 
    30 |         for key in self.cache:
    31 |             setattr(self.module, key, self.cache[key])

---

### FINDING 11
repository: scrapy/scrapy   pull request #97 (MERGED)
file: scrapy/http/response/text.py
claim_type: wrong_order
symbols named: _auto_detect_fun -> _auto_detect_fun

CLAIM: When the default encoding is a permissive single-byte encoding like 'latin1' or 'cp1252', the loop in `_auto_detect_fun` successfully decodes any byte sequence with it, causing it to incorrectly return the default encoding even if the text is actually UTF-8.

THE FUNCTION UNDER REVIEW (_auto_detect_fun, lines 77-83):
    77 |     def _auto_detect_fun(self, text):
    78 |         for enc in (self._DEFAULT_ENCODING, 'utf-8', 'cp1252'):
    79 |             try:
    80 |                 text.decode(enc)
    81 |             except UnicodeError:
    82 |                 continue
    83 |             return resolve_encoding(enc)

---

### FINDING 12
repository: pallets/flask   pull request #309 (MERGED)
file: flask/testing.py
claim_type: wrong_order
symbols named: kwargs.pop('environ_overrides', {}) -> app.test_request_context(*args, **kwargs)

CLAIM: The call to `kwargs.pop()` removes the `environ_overrides` key from `kwargs`, so when `app.test_request_context` is called with `**kwargs`, any environment overrides provided by the user are lost.

THE FUNCTION UNDER REVIEW (session_transaction, lines 42-88):
    42 |     @contextmanager
    43 |     def session_transaction(self, *args, **kwargs):
    44 |         """When used in combination with a with statement this opens a
    45 |         session transaction.  This can be used to modify the session that
    46 |         the test client uses.  Once the with block is left the session is
    47 |         stored back.
    48 | 
    49 |             with client.session_transaction() as session:
    50 |                 session['value'] = 42
    51 | 
    52 |         Internally this is implemented by going through a temporary test
    53 |         request context and since session handling could depend on
    54 |         request variables this function accepts the same arguments as
    55 |         :meth:`~flask.Flask.test_request_context` which are directly
    56 |         passed through.
    57 |         """
    58 |         if self.cookie_jar is None:
    59 |             raise RuntimeError('Session transactions only make sense '
    60 |                                'with cookies enabled.')
    61 |         app = self.application
    62 |         environ_overrides = kwargs.setdefault('environ_overrides', {})
    63 |         self.cookie_jar.inject_wsgi(environ_overrides)
    64 |         outer_reqctx = _request_ctx_stack.top
    65 |         with app.test_request_context(*args, **kwargs) as c:
    66 |             sess = app.open_session(c.request)
    67 |             if sess is None:
    68 |                 raise RuntimeError('Session backend did not open a session. '
    69 |                                    'Check the configuration')
    70 | 
    71 |             # Since we have to open a new request context for the session
    72 |             # handling we want to make sure that we hide out own context
    73 |             # from the caller.  By pushing the original request context
    74 |             # (or None) on top of this and popping it we get exactly that
    75 |             # behavior.  It's important to not use the push and pop
    76 |             # methods of the actual request context object since that would
    77 |             # mean that cleanup handlers are called
    78 |             _request_ctx_stack.push(outer_reqctx)
    79 |             try:
    80 |                 yield sess
    81 |             finally:
    82 |                 _request_ctx_stack.pop()
    83 | 
    84 |             resp = app.response_class()
    85 |             if not app.session_interface.is_null_session(sess):
    86 |                 app.save_session(sess, resp)
    87 |             headers = resp.get_wsgi_headers(c.request.environ)
    88 |             self.cookie_jar.extract_wsgi(c.request.environ, headers)

---

### FINDING 13
repository: scrapy/scrapy   pull request #96 (MERGED)
file: scrapy/tests/test_downloadermiddleware_cookies.py
claim_type: resource_leak
symbols named: tearDown -> test_cookiejar_key

CLAIM: The test `tearDown` method no longer calls `spider_closed`, causing `test_cookiejar_key` to leak `CookieJar` objects that are not cleaned up from the middleware's internal `jars` dictionary.

THE FUNCTION UNDER REVIEW (test_cookiejar_key, lines 67-91):
    67 |     def test_cookiejar_key(self):
    68 |         req = Request('http://scrapytest.org/', cookies={'galleta': 'salada'}, meta={'cookiejar': "store1"})
    69 |         assert self.mw.process_request(req, self.spider) is None
    70 |         self.assertEquals(req.headers.get('Cookie'), 'galleta=salada')
    71 | 
    72 |         headers = {'Set-Cookie': 'C1=value1; path=/'}
    73 |         res = Response('http://scrapytest.org/', headers=headers, request=req)
    74 |         assert self.mw.process_response(req, res, self.spider) is res
    75 | 
    76 |         req2 = Request('http://scrapytest.org/', meta=res.meta)
    77 |         assert self.mw.process_request(req2, self.spider) is None
    78 |         self.assertEquals(req2.headers.get('Cookie'), 'C1=value1; galleta=salada')
    79 | 
    80 | 
    81 |         req3 = Request('http://scrapytest.org/', cookies={'galleta': 'dulce'}, meta={'cookiejar': "store2"})
    82 |         assert self.mw.process_request(req3, self.spider) is None
    83 |         self.assertEquals(req3.headers.get('Cookie'), 'galleta=dulce')
    84 | 
    85 |         headers = {'Set-Cookie': 'C2=value2; path=/'}
    86 |         res2 = Response('http://scrapytest.org/', headers=headers, request=req3)
    87 |         assert self.mw.process_response(req3, res2, self.spider) is res2
    88 | 
    89 |         req4 = Request('http://scrapytest.org/', meta=res2.meta)
    90 |         assert self.mw.process_request(req4, self.spider) is None
    91 |         self.assertEquals(req4.headers.get('Cookie'), 'C2=value2; galleta=dulce')

---

### FINDING 14
repository: tornadoweb/tornado   pull request #273 (MERGED)
file: tornado/test/httpserver_test.py
claim_type: missing_guard
symbols named: prepare -> self.request.cookies.keys()[0]

CLAIM: The function accesses the first element of `self.request.cookies` without checking if it is empty, causing an `IndexError` if a request is made without any cookies.

THE FUNCTION UNDER REVIEW (prepare, lines 148-171):
   148 |     def prepare(self):
   149 |         self.errors = {}
   150 |         fields = [
   151 |             ('method', str),
   152 |             ('uri', str),
   153 |             ('version', str),
   154 |             ('remote_ip', str),
   155 |             ('protocol', str),
   156 |             ('host', str),
   157 |             ('path', str),
   158 |             ('query', str),
   159 |             ]
   160 |         for field, expected_type in fields:
   161 |             self.check_type(field, getattr(self.request, field), expected_type)
   162 | 
   163 |         self.check_type('header_key', self.request.headers.keys()[0], str)
   164 |         self.check_type('header_value', self.request.headers.values()[0], str)
   165 | 
   166 |         self.check_type('cookie_key', self.request.cookies.keys()[0], str)
   167 |         self.check_type('cookie_value', self.request.cookies.values()[0].value, str)
   168 |         # secure cookies
   169 | 
   170 |         self.check_type('arg_key', self.request.arguments.keys()[0], str)
   171 |         self.check_type('arg_value', self.request.arguments.values()[0][0], bytes_type)

---

### FINDING 15
repository: encode/django-rest-framework   pull request #23 (MERGED)
file: djangorestframework/tests/parsers.py
claim_type: resource_leak
symbols named: StringIO(self.string) -> test_parse

CLAIM: The function creates a `StringIO` stream object that is passed to a parser but is never explicitly closed before the function returns.

THE FUNCTION UNDER REVIEW (test_parse, lines 153-160):
   153 |     def test_parse(self):
   154 |         """ Make sure the `QueryDict` works OK """
   155 |         parser = FormParser(None)
   156 |         
   157 |         stream = StringIO(self.string)
   158 |         (data, files) = parser.parse(stream)
   159 | 
   160 |         self.assertEqual(Form(data).is_valid(), True)

---

### FINDING 16
repository: pallets/flask   pull request #413 (MERGED)
file: examples/blueprintexample/blueprintexample_test.py
claim_type: contract_violation
symbols named: blueprintexample.app -> setUp

CLAIM: The setUp method creates a test client from a global, module-level app object, so state modifications made in one test will leak into subsequent tests, violating test isolation.

THE FUNCTION UNDER REVIEW (setUp, lines 14-15):
    14 |     def setUp(self):
    15 |         self.app = blueprintexample.app.test_client()

---

### FINDING 17
repository: scrapy/scrapy   pull request #96 (MERGED)
file: scrapy/contrib/downloadermiddleware/cookies.py
claim_type: resource_leak
symbols named: jar = self.jars[cookiejarkey] -> self.jars

CLAIM: The removal of the `spider_closed` signal handler, which previously cleared cookie jars after a spider finished, means that jars created for `cookiejar` keys in `request.meta` are now stored indefinitely in `self.jars`, causing a memory leak over multiple spider runs within the same process.

THE FUNCTION UNDER REVIEW (process_response, lines 35-45):
    35 |     def process_response(self, request, response, spider):
    36 |         if 'dont_merge_cookies' in request.meta:
    37 |             return response
    38 | 
    39 |         # extract cookies from Set-Cookie and drop invalid/expired cookies
    40 |         cookiejarkey = request.meta.get("cookiejar")
    41 |         jar = self.jars[cookiejarkey]
    42 |         jar.extract_cookies(response, request)
    43 |         self._debug_set_cookie(response, spider)
    44 | 
    45 |         return response
