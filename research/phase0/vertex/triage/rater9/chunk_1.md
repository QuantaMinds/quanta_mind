# Findings to adjudicate — chunk 1

There are 7 findings below, numbered by their global index. Judge the CLAIM against the function shown.

### FINDING 7
repository: celery/celery   pull request #10420 (MERGED)
file: t/unit/app/test_schedules.py
claim_type: contract_violation
symbols named: crontab.remaining_estimate -> next

CLAIM: The function `crontab.remaining_estimate` returns a timedelta calculated in the schedule's timezone (UTC), but the test adds this delta to `now` which is in a different timezone (Vilnius), resulting in an incorrect `next` datetime that is off by the timezone difference.

THE FUNCTION UNDER REVIEW (test_aware_last_run_at_in_different_timezone, lines 552-569):
   552 |     def test_aware_last_run_at_in_different_timezone(self):
   553 |         # The crontab fields are defined in the schedule's timezone (the app
   554 |         # timezone, UTC here), but an aware last_run_at may arrive in a
   555 |         # different timezone, e.g. from django-celery-beat.  Both datetimes
   556 |         # must be normalized into the schedule's frame before any field
   557 |         # matching (#9715).
   558 |         vilnius = ZoneInfo("Europe/Vilnius")
   559 |         crontab = self.crontab(minute=40, hour=8)
   560 | 
   561 |         # 09:25:08 in Vilnius == 06:25:08 UTC
   562 |         last_run_at = datetime(2025, 5, 20, 9, 25, 8, tzinfo=vilnius)
   563 |         now = datetime(2025, 5, 20, 9, 26, 8, tzinfo=vilnius)
   564 |         crontab.nowfun = lambda: now
   565 | 
   566 |         next = now + crontab.remaining_estimate(last_run_at)
   567 | 
   568 |         # The next run is at 08:40 UTC on the same day, not a day later.
   569 |         assert next == datetime(2025, 5, 20, 8, 40, tzinfo=ZoneInfo("UTC"))

---

### FINDING 8
repository: celery/celery   pull request #10420 (MERGED)
file: celery/schedules.py
claim_type: wrong_order
symbols named: dow_num -> execute_this_date

CLAIM: The day-of-week `dow_num` is calculated from `last_run_at` after it has been converted to `schedule_tz`, which can cause `execute_this_date` to be incorrectly evaluated as `False` if `last_run_at` crosses a day boundary during timezone conversion.

THE FUNCTION UNDER REVIEW (remaining_delta, lines 580-642):
   580 |     def remaining_delta(self, last_run_at: datetime,
   581 |                         tz: str | tzinfo | None = None,
   582 |                         ffwd: type = ffwd) -> tuple[datetime, Any, datetime]:
   583 |         # caching global ffwd
   584 |         schedule_tz: tzinfo = timezone.get_timezone(tz or self.tz)
   585 |         # Normalize both datetimes into the schedule's timezone, so that the
   586 |         # crontab field matching and the next-run arithmetic below operate in
   587 |         # the frame the crontab is defined in. An aware last_run_at may arrive
   588 |         # in a different timezone (e.g. from django-celery-beat).
   589 |         last_run_at = self.maybe_make_aware(last_run_at).astimezone(schedule_tz)
   590 |         now = self.maybe_make_aware(self.now()).astimezone(schedule_tz)
   591 |         dow_num = last_run_at.isoweekday() % 7  # Sunday is day 0, not day 7
   592 | 
   593 |         execute_this_date = (
   594 |             last_run_at.month in self.month_of_year and
   595 |             last_run_at.day in self.day_of_month and
   596 |             dow_num in self.day_of_week
   597 |         )
   598 | 
   599 |         execute_this_hour = (
   600 |             execute_this_date and
   601 |             last_run_at.day == now.day and
   602 |             last_run_at.month == now.month and
   603 |             last_run_at.year == now.year and
   604 |             last_run_at.hour in self.hour and
   605 |             last_run_at.minute < max(self.minute)
   606 |         )
   607 | 
   608 |         if execute_this_hour:
   609 |             next_minute = min(minute for minute in self.minute
   610 |                               if minute > last_run_at.minute)
   611 |             delta = ffwd(minute=next_minute, second=0, microsecond=0)
   612 |         else:
   613 |             next_minute = min(self.minute)
   614 |             execute_today = (execute_this_date and
   615 |                              last_run_at.hour < max(self.hour))
   616 | 
   617 |             if execute_today:
   618 |                 next_hour = min(hour for hour in self.hour
   619 |                                 if hour > last_run_at.hour)
   620 |                 delta = ffwd(hour=next_hour, minute=next_minute,
   621 |                              second=0, microsecond=0)
   622 |             else:
   623 |                 next_hour = min(self.hour)
   624 |                 all_dom_moy = (self._orig_day_of_month == '*' and
   625 |                                self._orig_month_of_year == '*')
   626 |                 if all_dom_moy:
   627 |                     next_day = min([day for day in self.day_of_week
   628 |                                     if day > dow_num] or self.day_of_week)
   629 |                     add_week = next_day == dow_num
   630 | 
   631 |                     delta = ffwd(
   632 |                         weeks=add_week and 1 or 0,
   633 |                         weekday=(next_day - 1) % 7,
   634 |                         hour=next_hour,
   635 |                         minute=next_minute,
   636 |                         second=0,
   637 |                         microsecond=0,
   638 |                     )
   639 |                 else:
   640 |                     delta = self._delta_to_next(last_run_at,
   641 |                                                 next_hour, next_minute)
   642 |         return last_run_at, delta, now

---

### FINDING 9
repository: scikit-learn/scikit-learn   pull request #34741 (MERGED)
file: sklearn/utils/_set_output.py
claim_type: unhandled_case
symbols named: is_supported_container -> is_supported_container

CLAIM: The implementation of `is_supported_container` only checks for the pandas-specific `iloc` attribute, causing it to incorrectly return `False` for other dataframe-like containers that `set_output` is intended to support.

THE FUNCTION UNDER REVIEW (is_supported_container, lines 58-70):
    58 |     def is_supported_container(self, X):
    59 |         """Return True if X is a supported container.
    60 | 
    61 |         Parameters
    62 |         ----------
    63 |         X : container
    64 |             Container to be checked.
    65 | 
    66 |         Returns
    67 |         -------
    68 |         is_supported_container : bool
    69 |             True if X is a supported container.
    70 |         """

---

### FINDING 10
repository: pandas-dev/pandas   pull request #66762 (MERGED)
file: pandas/tests/io/json/test_pandas.py
claim_type: wrong_order
symbols named: df_mixed.index = df_mixed.index.as_unit("ms") -> tm.assert_frame_equal(
            df_mixed,
            df_roundtrip,
            check_index_type=True,
            check_column_type=True,
        )

CLAIM: The modification of `df_mixed` at `symbol_a` occurs after `df_mixed` is used to generate `df_roundtrip` but before the comparison at `symbol_b`, making the test incorrectly pass by altering the expected value to match the actual value.

THE FUNCTION UNDER REVIEW (test_blocks_compat_GH9037, lines 543-640):
   543 |     def test_blocks_compat_GH9037(self, using_infer_string):
   544 |         index = date_range("20000101", periods=10, freq="h", unit="ns")
   545 |         # freq doesn't round-trip
   546 |         index = DatetimeIndex(list(index), freq=None)
   547 | 
   548 |         df_mixed = DataFrame(
   549 |             {
   550 |                 "float_1": [
   551 |                     -0.92077639,
   552 |                     0.77434435,
   553 |                     1.25234727,
   554 |                     0.61485564,
   555 |                     -0.60316077,
   556 |                     0.24653374,
   557 |                     0.28668979,
   558 |                     -2.51969012,
   559 |                     0.95748401,
   560 |                     -1.02970536,
   561 |                 ],
   562 |                 "int_1": [
   563 |                     19680418,
   564 |                     75337055,
   565 |                     99973684,
   566 |                     65103179,
   567 |                     79373900,
   568 |                     40314334,
   569 |                     21290235,
   570 |                     4991321,
   571 |                     41903419,
   572 |                     16008365,
   573 |                 ],
   574 |                 "str_1": [
   575 |                     "78c608f1",
   576 |                     "64a99743",
   577 |                     "13d2ff52",
   578 |                     "ca7f4af2",
   579 |                     "97236474",
   580 |                     "bde7e214",
   581 |                     "1a6bde47",
   582 |                     "b1190be5",
   583 |                     "7a669144",
   584 |                     "8d64d068",
   585 |                 ],
   586 |                 "float_2": [
   587 |                     -0.0428278,
   588 |                     -1.80872357,
   589 |                     3.36042349,
   590 |                     -0.7573685,
   591 |                     -0.48217572,
   592 |                     0.86229683,
   593 |                     1.08935819,
   594 |                     0.93898739,
   595 |                     -0.03030452,
   596 |                     1.43366348,
   597 |                 ],
   598 |                 "str_2": [
   599 |                     "14f04af9",
   600 |                     "d085da90",
   601 |                     "4bcfac83",
   602 |                     "81504caf",
   603 |                     "2ffef4a9",
   604 |                     "08e2f5c4",
   605 |                     "07e1af03",
   606 |                     "addbd4a7",
   607 |                     "1f6a09ba",
   608 |                     "4bfc4d87",
   609 |                 ],
   610 |                 "int_2": [
   611 |                     86967717,
   612 |                     98098830,
   613 |                     51927505,
   614 |                     20372254,
   615 |                     12601730,
   616 |                     20884027,
   617 |                     34193846,
   618 |                     10561746,
   619 |                     24867120,
   620 |                     76131025,
   621 |                 ],
   622 |             },
   623 |             index=index,
   624 |         )
   625 | 
   626 |         # JSON deserialisation always creates unicode strings
   627 |         df_mixed.columns = df_mixed.columns.astype(
   628 |             np.str_ if not using_infer_string else "str"
   629 |         )
   630 |         msg = "The default formatting of datetime/timedelta values will change"
   631 |         with tm.assert_produces_warning(Pandas4Warning, match=msg):
   632 |             data = StringIO(df_mixed.to_json(orient="split"))
   633 |         df_roundtrip = read_json(data, orient="split")
   634 |         df_mixed.index = df_mixed.index.as_unit("ms")
   635 |         tm.assert_frame_equal(
   636 |             df_mixed,
   637 |             df_roundtrip,
   638 |             check_index_type=True,
   639 |             check_column_type=True,
   640 |         )

---

### FINDING 11
repository: ansible/ansible   pull request #87250 (MERGED)
file: lib/ansible/module_utils/_internal/_logging.py
claim_type: wrong_order
symbols named: for arg in log_args: -> journal_args = [("MODULE", module_name)]

CLAIM: The loop processing `log_args` appends to `journal_args` after the `MODULE` field is set from `module_name`, allowing `log_args` to override it when `journal_args` is converted to a dictionary.

THE FUNCTION UNDER REVIEW (log_to_system, lines 28-87):
    28 | def log_to_system(
    29 |     msg: str,
    30 |     *,
    31 |     module_name: str,
    32 |     log_args: dict[str, t.Any] | None = None,
    33 |     syslog_facility: str = "LOG_USER",
    34 |     target_log_info: str | None = None,
    35 | ) -> None:
    36 |     """Log a message to the system logging service (systemd journal or syslog).
    37 | 
    38 |     Dispatches to systemd journal when available, falling back to syslog.
    39 |     The caller is responsible for sanitizing secrets from *msg* before calling.
    40 | 
    41 |     The syslog identifier is built as ``ansible-<module_name>``.
    42 |     When *target_log_info* is provided (typically remote host information), it is prepended to the message.
    43 |     Extra key/value pairs in *log_args* are included as structured journal fields.
    44 |     The *syslog_facility* should be a syslog facility name such as ``LOG_USER``.
    45 | 
    46 |     Raises TypeError or ValueError if the underlying syslog call fails due to invalid input.
    47 |     """
    48 |     if log_args is None:
    49 |         log_args = {}
    50 | 
    51 |     module = "ansible-%s" % module_name
    52 | 
    53 |     if target_log_info:
    54 |         msg = " ".join([target_log_info, msg])
    55 | 
    56 |     if has_journal:
    57 |         journal_args = [("MODULE", module_name)]
    58 |         for arg in log_args:
    59 |             name, value = (arg.upper(), str(log_args[arg]))
    60 |             if name in (
    61 |                 "PRIORITY",
    62 |                 "MESSAGE",
    63 |                 "MESSAGE_ID",
    64 |                 "CODE_FILE",
    65 |                 "CODE_LINE",
    66 |                 "CODE_FUNC",
    67 |                 "SYSLOG_FACILITY",
    68 |                 "SYSLOG_IDENTIFIER",
    69 |                 "SYSLOG_PID",
    70 |             ):
    71 |                 name = "_%s" % name
    72 |             journal_args.append((name, value))
    73 | 
    74 |         try:
    75 |             if HAS_SYSLOG:
    76 |                 facility = getattr(syslog, syslog_facility, syslog.LOG_USER) >> 3
    77 |                 journal.send(
    78 |                     MESSAGE="%s %s" % (module, msg),
    79 |                     SYSLOG_FACILITY=facility,
    80 |                     **dict(journal_args),
    81 |                 )
    82 |             else:
    83 |                 journal.send(MESSAGE="%s %s" % (module, msg), **dict(journal_args))
    84 |         except OSError:
    85 |             _log_to_syslog(msg, module_name, syslog_facility)
    86 |     else:
    87 |         _log_to_syslog(msg, module_name, syslog_facility)

---

### FINDING 12
repository: pandas-dev/pandas   pull request #65195 (MERGED)
file: pandas/core/tools/datetimes.py
claim_type: missing_guard
symbols named: isnan = np.isnan(arr) -> if bad.any():

CLAIM: When `errors` is 'raise', `NaN` values in float columns for year, month, or day are not checked, leading to them being silently coerced to `NaT` instead of raising an exception.

THE FUNCTION UNDER REVIEW (_assemble_from_unit_mappings, lines 1286-1516):
  1286 | def _assemble_from_unit_mappings(
  1287 |     arg, errors: DateTimeErrorChoices, utc: bool
  1288 | ) -> Series:
  1289 |     """
  1290 |     assemble the unit specified fields from the arg (DataFrame)
  1291 |     Return a Series for actual parsing
  1292 | 
  1293 |     Parameters
  1294 |     ----------
  1295 |     arg : DataFrame
  1296 |     errors : {'raise', 'coerce'}, default 'raise'
  1297 | 
  1298 |         - If :const:`'raise'`, then invalid parsing will raise an exception
  1299 |         - If :const:`'coerce'`, then invalid parsing will be set as :const:`NaT`
  1300 |     utc : bool
  1301 |         Whether to convert/localize timestamps to UTC.
  1302 | 
  1303 |     Returns
  1304 |     -------
  1305 |     Series
  1306 |     """
  1307 |     from pandas import (
  1308 |         DataFrame,
  1309 |         Series,
  1310 |         to_numeric,
  1311 |         to_timedelta,
  1312 |     )
  1313 | 
  1314 |     arg = DataFrame(arg)
  1315 |     if not arg.columns.is_unique:
  1316 |         raise ValueError("cannot assemble with duplicate keys")
  1317 | 
  1318 |     # replace passed unit with _unit_map
  1319 |     def f(value):
  1320 |         if value in _unit_map:
  1321 |             return _unit_map[value]
  1322 | 
  1323 |         # m is case significant
  1324 |         if value.lower() in _unit_map:
  1325 |             return _unit_map[value.lower()]
  1326 | 
  1327 |         return value
  1328 | 
  1329 |     unit = {k: f(k) for k in arg.keys()}
  1330 |     unit_rev = {v: k for k, v in unit.items()}
  1331 | 
  1332 |     # we require at least Ymd
  1333 |     required = ["year", "month", "day"]
  1334 |     req = set(required) - set(unit_rev.keys())
  1335 |     if len(req):
  1336 |         _required = ",".join(sorted(req))
  1337 |         raise ValueError(
  1338 |             "to assemble mappings requires at least that "
  1339 |             f"[year, month, day] be specified: [{_required}] is missing"
  1340 |         )
  1341 | 
  1342 |     # keys we don't recognize
  1343 |     excess = set(unit_rev.keys()) - set(_unit_map.values())
  1344 |     if len(excess):
  1345 |         _excess = ",".join(sorted(excess))
  1346 |         raise ValueError(
  1347 |             f"extra keys have been passed to the datetime assemblage: [{_excess}]"
  1348 |         )
  1349 | 
  1350 |     def coerce(values):
  1351 |         # we allow coercion to if errors allows
  1352 |         values = to_numeric(values, errors=errors)
  1353 | 
  1354 |         # prevent precision issues in case of float32 # GH#60506
  1355 |         if is_float_dtype(values.dtype):
  1356 |             values = values.astype("float64")
  1357 | 
  1358 |         # prevent overflow in case of int8 or int16
  1359 |         if is_integer_dtype(values.dtype):
  1360 |             values = values.astype("int64")
  1361 |         return values
  1362 | 
  1363 |     # Convert field values to int64 arrays, tracking rows where a
  1364 |     #  year/month/day column has NaN (e.g. from errors="coerce" parsing)
  1365 |     nan_mask = np.zeros(len(arg), dtype=bool)
  1366 | 
  1367 |     field_spec = [
  1368 |         ("year", 2000),
  1369 |         ("month", 1),
  1370 |         ("day", 1),
  1371 |         ("h", 0),
  1372 |         ("m", 0),
  1373 |         ("s", 0),
  1374 |     ]
  1375 |     i32info = np.iinfo(np.int32)
  1376 |     field_arrs = []
  1377 |     # hour/minute/second columns that cannot go through datetime_from_fields
  1378 |     #  (fractional e.g. hour=1.5, NaN, bool, or out-of-int32 values); added
  1379 |     #  via to_timedelta below, keeping the column-wise semantics of the
  1380 |     #  non-vectorized implementation
  1381 |     td_units: list[tuple[UnitChoices, AnyArrayLike]] = []
  1382 |     for field, default in field_spec:
  1383 |         col_name = unit_rev.get(field)
  1384 |         if col_name is None:
  1385 |             field_arrs.append(np.zeros(len(arg), dtype=np.int64))
  1386 |             continue
  1387 |         vals = coerce(arg[col_name])
  1388 |         arr = np.asarray(vals)
  1389 | 
  1390 |         if field in ("h", "m", "s"):
  1391 |             # the npy_datetimestruct time fields are int32
  1392 |             if is_integer_dtype(arr.dtype):
  1393 |                 fits_struct = len(arr) == 0 or (
  1394 |                     arr.min() >= i32info.min and arr.max() <= i32info.max
  1395 |                 )
  1396 |             elif is_float_dtype(arr.dtype):
  1397 |                 fits_struct = bool(
  1398 |                     (
  1399 |                         (arr == np.floor(arr))
  1400 |                         & (arr >= i32info.min)
  1401 |                         & (arr <= i32info.max)
  1402 |                     ).all()
  1403 |                 )
  1404 |             else:
  1405 |                 fits_struct = False
  1406 |             if fits_struct:
  1407 |                 field_arrs.append(arr.astype(np.int64, copy=False))
  1408 |             else:
  1409 |                 td_units.append((cast("UnitChoices", field), vals))
  1410 |                 field_arrs.append(np.zeros(len(arg), dtype=np.int64))
  1411 |             continue
  1412 | 
  1413 |         # year/month/day
  1414 |         if is_bool_dtype(vals.dtype):
  1415 |             if errors == "raise":
  1416 |                 raise ValueError(
  1417 |                     f"cannot assemble the datetimes: column {col_name!r} has dtype bool"
  1418 |                 )
  1419 |             nan_mask[:] = True
  1420 |             field_arrs.append(np.full(len(arg), default, dtype=np.int64))
  1421 |             continue
  1422 |         if not is_float_dtype(arr.dtype):
  1423 |             field_arrs.append(arr.astype(np.int64, copy=False))
  1424 |             continue
  1425 |         isnan = np.isnan(arr)
  1426 |         fractional = (~isnan) & (arr != np.floor(arr))
  1427 |         if fractional.any() and errors == "raise":
  1428 |             raise ValueError(
  1429 |                 f"cannot assemble the datetimes: column {col_name!r} "
  1430 |                 f"contains fractional values"
  1431 |             )
  1432 |         # +/-inf and values beyond int64 range cannot be cast meaningfully
  1433 |         out_of_range = (arr >= 2**63) | (arr < -(2**63))
  1434 |         if out_of_range.any() and errors == "raise":
  1435 |             raise ValueError(
  1436 |                 f"cannot assemble the datetimes: column {col_name!r} "
  1437 |                 f"contains out-of-bounds values"
  1438 |             )
  1439 |         bad = isnan | fractional | out_of_range
  1440 |         if bad.any():
  1441 |             nan_mask[bad] = True
  1442 |             arr = np.where(bad, default, arr)
  1443 |         field_arrs.append(arr.astype(np.int64))
  1444 | 
  1445 |     # Construct datetime64[us] directly from fields, avoiding the
  1446 |     # object-dtype round-trip through format="%Y%m%d" string parsing.
  1447 |     # Rows with NaN in a year/month/day column get valid placeholders in
  1448 |     # every field and NaT at the end; the Cython function writes iNaT for
  1449 |     # invalid or out-of-bounds dates.
  1450 |     if nan_mask.any():
  1451 |         for idx, (_, default) in enumerate(field_spec):
  1452 |             field_arrs[idx] = np.where(nan_mask, default, field_arrs[idx])
  1453 | 
  1454 |     year_arr, month_arr, day_arr, hour_arr, minute_arr, second_arr = field_arrs
  1455 | 
  1456 |     usecs, first_invalid = datetime_from_fields(
  1457 |         year_arr,
  1458 |         month_arr,
  1459 |         day_arr,
  1460 |         hour_arr,
  1461 |         minute_arr,
  1462 |         second_arr,
  1463 |     )
  1464 |     if first_invalid >= 0 and errors == "raise":
  1465 |         bad_val = (
  1466 |             f"{year_arr[first_invalid]}-{month_arr[first_invalid]:02d}"
  1467 |             f"-{day_arr[first_invalid]:02d}"
  1468 |         )
  1469 |         if (
  1470 |             hour_arr[first_invalid]
  1471 |             or minute_arr[first_invalid]
  1472 |             or second_arr[first_invalid]
  1473 |         ):
  1474 |             bad_val += (
  1475 |                 f" {hour_arr[first_invalid]:02d}:{minute_arr[first_invalid]:02d}"
  1476 |                 f":{second_arr[first_invalid]:02d}"
  1477 |             )
  1478 |         raise ValueError(
  1479 |             f'cannot assemble the datetimes: invalid or out-of-bounds date "{bad_val}"'
  1480 |         )
  1481 |     # errors="coerce": invalid entries already have iNaT from Cython
  1482 |     if nan_mask.any():
  1483 |         usecs[nan_mask] = iNaT
  1484 | 
  1485 |     dt64_values = usecs.view("M8[us]")
  1486 | 
  1487 |     if utc:
  1488 |         dta = DatetimeArray._simple_new(
  1489 |             dt64_values, dtype=DatetimeTZDtype(tz="UTC", unit="us")
  1490 |         )
  1491 |         values = Series(dta, index=arg.index, copy=False)
  1492 |   

---

### FINDING 13
repository: scrapy/scrapy   pull request #7985 (MERGED)
file: tests/utils/bases/download_handlers_http.py
claim_type: missing_guard
symbols named: (settings_dict or {}) -> **(settings_dict or {})

CLAIM: The use of the `or` operator in `symbol_a` to default `settings_dict` to an empty dictionary incorrectly coerces any falsy value (e.g., an empty list `[]`) to `{}`, causing invalid setting types to be silently ignored at `symbol_b` instead of raising a `TypeError`.

THE FUNCTION UNDER REVIEW (get_dh, lines 1542-1554):
  1542 |     @asynccontextmanager
  1543 |     async def get_dh(
  1544 |         self, settings_dict: dict[str, Any] | None = None
  1545 |     ) -> AsyncGenerator[DownloadHandlerProtocol]:
  1546 |         crawler = get_crawler(
  1547 |             DefaultSpider, {**REAL_WEBSITE_SETTINGS, **(settings_dict or {})}
  1548 |         )
  1549 |         crawler.spider = crawler._create_spider()
  1550 |         dh = build_from_crawler(self.download_handler_cls, crawler)
  1551 |         try:
  1552 |             yield dh
  1553 |         finally:
  1554 |             await dh.close()
