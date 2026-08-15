# Findings to adjudicate — chunk 1

There are 6 findings below, numbered by their global index. Judge the CLAIM against the function shown.

### FINDING 6
repository: encode/django-rest-framework   pull request #18 (MERGED)
file: djangorestframework/resources.py
claim_type: unhandled_case
symbols named: fname, fields = fname -> _model_to_dict

CLAIM: The tuple unpacking `fname, fields = fname` assumes that if `fname` is a tuple or list it will have exactly two elements, causing a `ValueError` that crashes the `_model_to_dict` function if the tuple/list has a different number of elements.

THE FUNCTION UNDER REVIEW (_model_to_dict, lines 22-98):
    22 | def _model_to_dict(instance, resource=None):
    23 |     """
    24 |     Given a model instance, return a ``dict`` representing the model.
    25 |     
    26 |     The implementation is similar to Django's ``django.forms.model_to_dict``, except:
    27 | 
    28 |     * It doesn't coerce related objects into primary keys.
    29 |     * It doesn't drop ``editable=False`` fields.
    30 |     * It also supports attribute or method fields on the instance or resource.
    31 |     """
    32 |     opts = instance._meta
    33 |     data = {}
    34 | 
    35 |     #print [rel.name for rel in opts.get_all_related_objects()]
    36 |     #related = [rel.get_accessor_name() for rel in opts.get_all_related_objects()]
    37 |     #print [getattr(instance, rel) for rel in related]
    38 |     #if resource.fields:
    39 |     #    fields = resource.fields
    40 |     #else:
    41 |     #    fields = set(opts.fields + opts.many_to_many)
    42 |     
    43 |     fields = resource and resource.fields or ()
    44 |     include = resource and resource.include or ()
    45 |     exclude = resource and resource.exclude or ()
    46 | 
    47 |     extra_fields = fields and list(fields) or list(include)
    48 | 
    49 |     # Model fields
    50 |     for f in opts.fields + opts.many_to_many:
    51 |         if fields and not f.name in fields:
    52 |             continue
    53 |         if exclude and f.name in exclude:
    54 |             continue
    55 |         if isinstance(f, models.ForeignKey):
    56 |             data[f.name] = getattr(instance, f.name)
    57 |         else:
    58 |             data[f.name] = f.value_from_object(instance)
    59 |         
    60 |         if extra_fields and f.name in extra_fields:
    61 |             extra_fields.remove(f.name)
    62 |     
    63 |     # Method fields
    64 |     for fname in extra_fields:
    65 |         
    66 |         if isinstance(fname, (tuple, list)):
    67 |             fname, fields = fname
    68 |         else:
    69 |             fname, fields = fname, False
    70 | 
    71 |         try:
    72 |             if hasattr(resource, fname):
    73 |                 # check the resource first, to allow it to override fields
    74 |                 obj = getattr(resource, fname)
    75 |                 # if it's a method like foo(self, instance), then call it 
    76 |                 if inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) == 2:
    77 |                     obj = obj(instance)
    78 |             elif hasattr(instance, fname):
    79 |                 # now check the object instance
    80 |                 obj = getattr(instance, fname)
    81 |             else:
    82 |                 continue
    83 |     
    84 |             # TODO: It would be nicer if this didn't recurse here.
    85 |             # Let's keep _model_to_dict flat, and _object_to_data recursive.
    86 |             if fields:
    87 |                 Resource = type('Resource', (object,), {'fields': fields,
    88 |                                                         'include': (),
    89 |                                                         'exclude': ()})
    90 |                 data[fname] = _object_to_data(obj, Resource())
    91 |             else:
    92 |                 data[fname] = _object_to_data(obj)
    93 | 
    94 |         except NoReverseMatch:
    95 |             # Ug, bit of a hack for now
    96 |             pass
    97 |    
    98 |     return data

---

### FINDING 7
repository: pallets/flask   pull request #307 (MERGED)
file: flask/blueprints.py
claim_type: unhandled_case
symbols named: route -> add_url_rule

CLAIM: The `route` decorator calls `add_url_rule` with a positional argument for `endpoint` (`f.__name__`) and also forwards `**options` which may contain a keyword argument `endpoint`, causing a `TypeError` for receiving the same argument twice.

THE FUNCTION UNDER REVIEW (route, lines 155-163):
   155 |     def route(self, rule, **options):
   156 |         """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
   157 |         :func:`url_for` function is prefixed with the name of the blueprint.
   158 |         """
   159 |         def decorator(f):
   160 |             endpoint = options.pop("endpoint", f.__name__)
   161 |             self.add_url_rule(rule, endpoint, f, **options)
   162 |             return f
   163 |         return decorator

---

### FINDING 8
repository: tornadoweb/tornado   pull request #232 (MERGED)
file: tornado/test/testing_test.py
claim_type: resource_leak
symbols named: test_wait_timeout -> AsyncTestCase.tearDown

CLAIM: In test_wait_timeout, add_timeout schedules a callback, but when wait() times out, this callback is never cancelled, leaving it pending when tearDown is executed, which can cause spurious failures or warnings.

THE FUNCTION UNDER REVIEW (test_wait_timeout, lines 33-49):
    33 |     def test_wait_timeout(self):
    34 |         time = self.io_loop.time
    35 | 
    36 |         # Accept default 5-second timeout, no error
    37 |         self.io_loop.add_timeout(time() + 0.01, self.stop)
    38 |         self.wait()
    39 | 
    40 |         # Timeout passed to wait()
    41 |         self.io_loop.add_timeout(time() + 1, self.stop)
    42 |         with self.assertRaises(self.failureException):
    43 |             self.wait(timeout=0.01)
    44 | 
    45 |         # Timeout set with environment variable
    46 |         self.io_loop.add_timeout(time() + 1, self.stop)
    47 |         with set_environ("ASYNC_TEST_TIMEOUT", "0.01"):
    48 |             with self.assertRaises(self.failureException):
    49 |                 self.wait()

---

### FINDING 9
repository: encode/django-rest-framework   pull request #18 (MERGED)
file: djangorestframework/tests/resources.py
claim_type: wrong_order
symbols named: _object_to_data -> _object_to_data

CLAIM: The implementation of `_object_to_data` processes nested fields but incorrectly uses a `filter` object, which is an iterator, leading to only the first nested field being processed in a recursive call if multiple are specified.

THE FUNCTION UNDER REVIEW (test_tuples, lines 35-59):
    35 |     def test_tuples(self):
    36 |         """ Test tuple serialisation """
    37 |         class M1(models.Model):
    38 |             field1 = models.CharField()
    39 |             field2 = models.CharField()
    40 |         
    41 |         class M2(models.Model):
    42 |             field = models.OneToOneField(M1)
    43 |         
    44 |         class M3(models.Model):
    45 |             field = models.ForeignKey(M1)
    46 |         
    47 |         m1 = M1(field1='foo', field2='bar')
    48 |         m2 = M2(field=m1)
    49 |         m3 = M3(field=m1)
    50 |         
    51 |         Resource = type('Resource', (object,), {'fields':(), 'include':(), 'exclude':()})
    52 |         
    53 |         r = Resource()
    54 |         r.fields = (('field', ('field1')),)
    55 | 
    56 |         self.assertEqual(_object_to_data(m2, r), dict(field=dict(field1=u'foo')))
    57 |         
    58 |         r.fields = (('field', ('field2')),)
    59 |         self.assertEqual(_object_to_data(m3, r), dict(field=dict(field2=u'bar')))

---

### FINDING 10
repository: scrapy/scrapy   pull request #97 (MERGED)
file: scrapy/http/response/text.py
claim_type: wrong_order
symbols named: _body_inferred_encoding -> body_as_unicode

CLAIM: Calling `_body_inferred_encoding` unconditionally sets `_cached_ubody`, which can overwrite a value previously set by `body_as_unicode` using a user-specified encoding.

THE FUNCTION UNDER REVIEW (_body_inferred_encoding, lines 67-75):
    67 |     def _body_inferred_encoding(self):
    68 |         if self._cached_benc is None:
    69 |             content_type = self.headers.get('Content-Type')
    70 |             benc, ubody = html_to_unicode(content_type, self.body, \
    71 |                     auto_detect_fun=self._auto_detect_fun, \
    72 |                     default_encoding=self._DEFAULT_ENCODING)
    73 |             self._cached_benc = benc
    74 |             self._cached_ubody = ubody
    75 |         return self._cached_benc

---

### FINDING 11
repository: pallets/flask   pull request #413 (MERGED)
file: examples/blueprintexample/simple_page/simple_page.py
claim_type: unhandled_case
symbols named: page -> render_template

CLAIM: User-controlled input `page` is formatted into a template path without sanitization, allowing path traversal characters like `..` to make `render_template` access files outside the intended `pages/` sub-directory.

THE FUNCTION UNDER REVIEW (show, lines 7-13):
     7 | @simple_page.route('/', defaults={'page': 'index'})
     8 | @simple_page.route('/<page>')
     9 | def show(page):
    10 |     try:
    11 |         return render_template('pages/%s.html' % page)
    12 |     except TemplateNotFound:
    13 |         abort(404)
