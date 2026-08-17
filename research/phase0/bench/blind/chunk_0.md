# Blind adjudication — do these describe the same issue?

For each item: a GOLDEN comment written by a human reviewer, and the CANDIDATE comments
one automated reviewer produced on that same pull request.

**Question, for each item: does ANY candidate identify the same underlying issue as the
golden comment?** Different wording is fine. Answer `yes` or `no`.

You are not told which reviewer produced which candidates. That is deliberate.

---

## Item 1

**GOLDEN:** In UsernameForm.authenticate(), isConditionalPasskeysEnabled() is called without passing the required UserModel parameter.

**CANDIDATES:**
- isConditionalPasskeysEnabled() is invoked with no arguments, but the only definition in the parent class UsernamePasswordForm has signature isConditionalPasskeysEnabled(UserModel user) - this will fail to compile
- isConditionalPasskeysEnabled(UserModel user) returns false whenever user == null, so fillContextForm is skipped for unauthenticated visits, meaning passkey autocomplete/form will not appear for new logins - breaking initial login passkeys flow
- The challenge() method inverts the original condition - original guard was context.getUser() == null && webauthnAuth != null && webauthnAuth.isPasskeysEnabled(), but new guard isConditionalPasskeysEnabled(context.getUser()) is true only when user != null, so users who submit bad username will see error page without WebAuthn form

## Item 2

**GOLDEN:** The Calendar interface now requires createEvent(event, credentialId), but some implementations (e.g., Lark/Office365) still declare createEvent(event) only—this breaks the interface contract (also applies to other locations in the PR).

**CANDIDATES:**
- In `packages/app-store/googlecalendar/lib/CalendarService.ts`, the logic to find the calendar for `updateEvent` and `deleteEvent` is flawed because it will fail to find the correct calendar if `externalCalendarId` is null or undefined.
- In `packages/app-store/larkcalendar/lib/CalendarService.ts`, the `createEvent` method signature does not match the `Calendar` interface as it is missing the `credentialId` parameter, causing it to always use the first destination calendar which is incorrect for multi-host events.
- In `packages/app-store/office365calendar/lib/CalendarService.ts`, the `createEvent` method signature does not match the `Calendar` interface as it is missing the `credentialId` parameter, causing it to always use the first destination calendar which is incorrect for multi-host events.
- In `packages/lib/CalendarService.ts`, the `createEvent` method in the base class does not match the `Calendar` interface and its logic incorrectly uses only the first destination calendar, which will fail for secondary hosts in a collective event.
- In `packages/core/EventManager.ts`, the check for Google Meet location can cause a runtime error because `mainHostDestinationCalendar` can be `undefined` but its `integration` property is accessed without a null check.
- In `packages/features/bookings/lib/handleNewBooking.ts`, when creating a booking, only the first destination calendar is saved to the database, resulting in data loss for other hosts in a collective event.
- In `packages/core/EventManager.ts`, there is a redundant duplicated condition `if (!calendarReference) if (!calendarReference)` in the `updateOtherCalendarEvents` method.
- In `packages/features/bookings/lib/handleNewBooking.ts`, the `loadUsers` function throws a generic `Error` instead of an `HttpError`, which will result in an unhandled exception and a 500 server error instead of a proper client-facing error message.
- In `packages/core/EventManager.ts`, the fallback logic in `createAllCalendarEvents` can create duplicate calendar events if a user has multiple credentials for the same integration type, as it iterates over all of them.
- In `packages/core/EventManager.ts`, the logic to fallback to Cal Video if Google Meet is selected without a Google Calendar only checks the first destination calendar, which is incorrect for collective events where another host might have a Google Calendar.

## Item 3

**GOLDEN:** postMessage targetOrigin should be the origin (scheme+host+port), not the full referrer URL; using the full URL will cause the message to be dropped and prevent resizing.

**CANDIDATES:**
- In `app/jobs/scheduled/poll_feed.rb`, `open(SiteSetting.feed_polling_url)` is vulnerable to remote command execution because `open-uri`'s `open` method executes shell commands if the argument starts with a pipe character.
- In `app/models/post.rb`, posts with `cook_method` of `raw_html` bypass sanitization, leading to a stored XSS vulnerability if the raw content from an RSS feed contains malicious scripts.
- In `app/assets/javascripts/embed.js`, the origin check for `postMessage` is `discourseUrl.indexOf(e.origin) === -1`, which is insufficient and allows messages from origins that are a prefix of the `discourseUrl`'s origin, creating a security vulnerability.
- In `app/controllers/embed_controller.rb`, `response.headers['X-Frame-Options']` is set to `"ALLOWALL"`, which is not a standard value and effectively disables clickjacking protection for the embedded content.
- In `app/views/layouts/embed.html.erb`, `postMessage` is called with the full `request.referer` URL as the `targetOrigin`, which is invalid and will cause the browser to block the message, breaking the iframe resizing feature.
- In `app/views/embed/loading.html.erb`, the page automatically reloads every 30 seconds, which will cause an endless loop of requests if the background job is slow or fails, potentially leading to a self-inflicted denial of service.
- In `lib/topic_retriever.rb`, `perform_retrieve` calls `Jobs::PollFeed.new.execute({})` to find a single topic, which inefficiently triggers a poll of the entire RSS feed instead of fetching only the required URL.
- In `app/jobs/scheduled/poll_feed.rb`, using `open()` on a URL from site settings without validation allows an administrator to perform Server-Side Request Forgery (SSRF) attacks or read local files using `file://` URIs.
- In `app/models/topic_embed.rb`, `open(url)` is used to fetch remote content, which can lead to a Server-Side Request Forgery (SSRF) vulnerability, as it may allow requests to internal services on the `embeddable_host`.

## Item 4

**GOLDEN:** The PollFeed job calls open(SiteSetting.feed_polling_url) without validating the URL, allowing an attacker who controls the feed_polling_url site setting to make the server fetch arbitrary internal or external URLs.

**CANDIDATES:**
- In `app/jobs/scheduled/poll_feed.rb`, `open(SiteSetting.feed_polling_url)` is vulnerable to remote command execution because `open-uri`'s `open` method executes shell commands if the argument starts with a pipe character.
- In `app/models/post.rb`, posts with `cook_method` of `raw_html` bypass sanitization, leading to a stored XSS vulnerability if the raw content from an RSS feed contains malicious scripts.
- In `app/assets/javascripts/embed.js`, the origin check for `postMessage` is `discourseUrl.indexOf(e.origin) === -1`, which is insufficient and allows messages from origins that are a prefix of the `discourseUrl`'s origin, creating a security vulnerability.
- In `app/controllers/embed_controller.rb`, `response.headers['X-Frame-Options']` is set to `"ALLOWALL"`, which is not a standard value and effectively disables clickjacking protection for the embedded content.
- In `app/views/layouts/embed.html.erb`, `postMessage` is called with the full `request.referer` URL as the `targetOrigin`, which is invalid and will cause the browser to block the message, breaking the iframe resizing feature.
- In `app/views/embed/loading.html.erb`, the page automatically reloads every 30 seconds, which will cause an endless loop of requests if the background job is slow or fails, potentially leading to a self-inflicted denial of service.
- In `lib/topic_retriever.rb`, `perform_retrieve` calls `Jobs::PollFeed.new.execute({})` to find a single topic, which inefficiently triggers a poll of the entire RSS feed instead of fetching only the required URL.
- In `app/jobs/scheduled/poll_feed.rb`, using `open()` on a URL from site settings without validation allows an administrator to perform Server-Side Request Forgery (SSRF) attacks or read local files using `file://` URIs.
- In `app/models/topic_embed.rb`, `open(url)` is used to fetch remote content, which can lead to a Server-Side Request Forgery (SSRF) vulnerability, as it may allow requests to internal services on the `embeddable_host`.

## Item 5

**GOLDEN:** The traceID is no longer logged for plugin requests. During a refactoring, the tracing import and the logic to extract and add traceID from the context to log parameters were removed from the LoggerMiddleware. The newly introduced ContextualLoggerMiddleware does not add this information, resulting in missing traceID in plugin request logs and impacting debugging and request tracing capabilities.

**CANDIDATES:**
- In `pkg/plugins/log/logger.go`, the `FromContext` method on `grafanaInfraLogWrapper` has incorrect fallback logic that discards context information from the `context.Context` argument if the underlying logger is not a `*log.ConcreteLogger`.
- In `pkg/plugins/log/fake.go`, the `TestLogger.FromContext` implementation returns a new empty logger, which violates the `Logger` interface contract stating that the returned logger should contain the context of the original logger.

## Item 6

**GOLDEN:** The translation is in Italian instead of Lithuanian. This should be translated to Lithuanian to match the file's locale (messages_lt.properties).

**CANDIDATES:**
- In `VerifyMessageProperties.java`, the `santizeAnchors` method modifies the string it is iterating over with a `Matcher`, which will cause the matcher to behave unpredictably as its internal state becomes out of sync with the modified string.
- In `VerifyMessageProperties.java`, the `santizeAnchors` method incorrectly assumes that anchor tags will appear in the same order in both the original and translated strings, which will cause it to fail on valid translations that reorder phrases.
- In `js/apps/account-ui/maven-resources/theme/keycloak.v3/account/messages/messages_en.properties` and `js/apps/admin-ui/maven-resources/theme/keycloak.v2/admin/messages/messages_en.properties`, the `error-invalid-multivalued-size` message format was changed to use Java's `MessageFormat` `choice` syntax, which is not compatible with the JavaScript i18n libraries used by these applications and will break pluralization.
- In `themes/src/main/resources-community/theme/base/login/messages/messages_sk.properties`, the `impersonateTitleHtml` key is modified to have an unclosed `<strong>` tag, resulting in malformed HTML.
- In `themes/src/main/resources-community/theme/base/account/messages/messages_lt.properties` and `themes/src/main/resources-community/theme/base/login/messages/messages_lt.properties`, the values for `totpStep1` and `loginTotpStep1` respectively are in Italian, not Lithuanian.

## Item 7

**GOLDEN:** The method name 'santizeAnchors' should be 'sanitizeAnchors' (missing 'i').

**CANDIDATES:**
- StringIndexOutOfBoundsException in diagnostic substring calculation when sanitized shares a common suffix with value that extends past start (start + end >= value.length()), causing value.substring(start, value.length() - end) to throw and crash the Maven goal
- RuntimeException thrown instead of MojoExecutionException on I/O failure in verifySafeHtml, causing confusing stack trace instead of clean error message
- Instance fields POLICY_SOME_HTML, POLICY_NO_HTML, and HTML_TAGS should be static final to avoid allocating new HtmlPolicyBuilder, PolicyFactory, and compiled Pattern for every VerifyMessageProperties instance
- ISO-8859-1 encoding used for potentially UTF-8 properties files when using PropertyResourceBundle(FileInputStream), causing garbled content and potential false positives for non-Latin locales
- Typo in method name: santizeAnchors should be sanitizeAnchors

## Item 8

**GOLDEN:** When length starts at -1 from indefinite-length encoding, the arithmetic 'length = length - bytes.length' will behave unexpectedly, potentially leading to incorrect processing of encoded data.

**CANDIDATES:**
- In ASN1Decoder, readSequence() does not handle indefinite-length encodings, as it will immediately exit the parsing loop and return an empty list if readLength() returns -1.
- In ASN1Decoder, readInteger() will crash with a NegativeArraySizeException if it encounters an indefinite-length encoding because it does not handle the -1 value returned by readLength().
- In AuthzClientCryptoProvider, getBouncyCastleProvider() violates its API contract by returning the default JCA provider instead of a Bouncy Castle provider.
- In AuthzClientCryptoProvider, getKeyStore() uses the default JVM provider search instead of a specific integrated provider, which breaks the CryptoProvider abstraction model and can lead to inconsistent behavior.

## Item 9

**GOLDEN:** The @loaded_locales instance variable in translate_accelerator.rb is lazily initialized and accessed by multiple concurrent threads without synchronization.

**CANDIDATES:**
- In `config/initializers/i18n.rb`, the `FallbackLocaleList#ensure_loaded!` method calls `I18n.ensure_loaded!`, which will raise a `NoMethodError` at runtime because the `ensure_loaded!` method is defined on `I18n.backend`, not the `I18n` module.
- The new `ensure_loaded!` method in `lib/freedom_patches/translate_accelerator.rb` is not thread-safe, as it reads and modifies the shared `@loaded_locales` instance variable without any synchronization, creating a race condition in a multi-threaded environment.

## Item 10

**GOLDEN:** The rendered GrafanaRuleListItem is missing the required key prop for React list items. This can cause rendering issues when the list order changes.

**CANDIDATES:**
- Missing React list key on GrafanaRuleListItem - the key variable is destructured from ruleWithOrigin but never forwarded to GrafanaRuleListItem, unlike sibling branches which supply the key prop, causing incorrect React list reconciliation for streamed/batched results
- Stray literal } in the getGrafanaRuleKey template string (line 209) makes keys slightly malformed
- Delete menu item unavailable in list view despite user having permission - canDelete can be true when only promRule is supplied, but the delete menu item is gated by rulerRule &&, so it will never render for list-view consumers that pass only promRule
- Misleading test descriptions in RuleDetails.test.tsx - descriptions read 'Should not render Edit/Delete button for users with the update/delete permission' which sounds like a permission violation, when the intent is that these buttons have moved to a separate component

## Item 11

**GOLDEN:** Fetching userIdsFromOrg only when teamsFromOrg.length > 0 can exclude org-level members for orgs without child teams; consider deriving from teamIds (which includes orgId) or removing the guard so org-only orgs still include member user bookings.

**CANDIDATES:**
- Non-deterministic ordering in org-scope test: findAllByParentId (teams) and findAllByTeamIds (memberships) are called without orderBy clause, so the order of team IDs and user IDs in the resulting Prisma.Sql object is undefined and may cause flaky test failures
- Behavioral change when team has no members: buildTeamAuthorizationCondition now omits the isTeamBooking = false branch when userIdsFromTeam is empty, which is a silent change from the old implementation that always included both OR arms, and this edge case has no test coverage

## Item 12

**GOLDEN:** logic: macOS-specific sed syntax with empty string after -i flag will fail on Linux systems

**CANDIDATES:**
- The code in `packages/lib/server/repository/user.ts` and `packages/lib/getConnectedDestinationCalendars.ts` attempts to query and use an `updatedAt` field on the `SelectedCalendar` model, but this field does not exist in the database schema and is not being added.
- In `CredentialActionsDropdown.tsx`, confirmation dialogs are closed optimistically on button click, rather than waiting for the asynchronous mutation to complete, which provides misleading feedback to the user if the operation fails.
- In `CalendarService.ts`, `SelectedCalendarRepository.updateManyByCredentialId` is called with an empty data object, which performs no update and has no effect on the database.
- In `CredentialActionsDropdown.tsx`, `Intl.DateTimeFormat` is hardcoded with the "en-US" locale, which will display dates in an American format for all users regardless of their actual locale.
- In `deleteCache.handler.ts`, a generic `Error` is thrown when a credential is not found, which results in a vague 500 Internal Server Error response to the client instead of a more specific TRPC error like `NOT_FOUND`.
- The `test-gcal-webhooks.sh` script uses a `sed -i ''` command syntax that is specific to BSD/macOS and will fail on GNU/Linux systems.

## Item 13

**GOLDEN:** The `refreshOAuthTokens` function is passed `credentialId` instead of `userId`, which breaks the credential sync functionality by causing incorrect user lookups. This issue can lead to failures in syncing user credentials, impacting user experience.

**CANDIDATES:**
- The webhook secret comparison in `app-credential.ts` is not constant-time, which makes it vulnerable to timing attacks.
- In `app-credential.ts`, a call to `JSON.parse` on a decrypted payload is not wrapped in a try-catch block, which will cause an unhandled exception and a server crash if the payload is not valid JSON.
- In `parseRefreshTokenResponse.ts`, if an OAuth provider does not return a new refresh token, the code hardcodes the value to the string "refresh_token", which will cause subsequent token refreshes to fail.
- The `refreshOAuthTokens` function returns a raw `Response` object, but several of its callers (e.g., in Google Calendar, Hubspot, Zoho integrations) expect an object with a `data` property or a specific token structure, which will cause runtime errors.
- In `GoogleCalendarService.ts`, the result of `parseRefreshTokenResponse` is stored directly in the database, but this function returns a `SafeParseReturnType` object (`{ success, data }`) instead of the parsed data itself, leading to incorrect credential data being saved.
- The Salesforce token refresh logic in `SalesforceCalendarService.ts` has been reimplemented without using the new `refreshOAuthTokens` helper, meaning it will not support the external credential sync feature.
- The `refreshToken` callback for the `jsforce` connection in `SalesforceCalendarService.ts` has been removed, breaking the library's ability to automatically refresh expired access tokens during its operation.
- The check for a successful token refresh in `SalesforceCalendarService.ts` uses `response.statusText !== "OK"`, which is unreliable and will fail for any successful HTTP status other than 200.
- In `ZohoBigin/CalendarService.ts`, the `refreshOAuthTokens` function is called with the credential ID instead of the user ID, which will cause the external credential sync to fail for the wrong user.
- The `minimumTokenResponseSchema` in `parseRefreshTokenResponse.ts` uses a generic index signature to find the token expiry time, which is too permissive and could misinterpret other numeric fields in a token response as the expiry.
- The suggested command in `.env.example` for generating `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY` (`openssl rand -base64 24`) produces a 24-byte key, which contradicts the comment stating a 32-byte key is required for AES-256.

## Item 14

**GOLDEN:** get_item_key assumes a numeric key, but the paginator is used with order_by=-datetime in the audit logs endpoint; calling math.floor/ceil on a datetime will raise a TypeError.

**CANDIDATES:**
- get_item_key crashes on datetime values - math.floor() and math.ceil() raise TypeError when passed a datetime object instead of converting to float timestamp first
- Django ORM does not support negative slicing - queryset[negative_int:stop] raises AssertionError, making reverse pagination with negative offset crash
- value_from_cursor returns a raw integer instead of a datetime - causes SQL WHERE datetime comparison to fail with type mismatch
- organization_context.member may be None - causes AttributeError when accessing has_global_access for non-superuser requests where member is unexpectedly None
- Date-range filtering silently removed - statsPeriod, start, and end query parameters were removed without replacement, breaking existing callers that rely on date-scoped audit log queries

## Item 15

**GOLDEN:** The ERB block closes with end if, which is invalid Ruby/ERB and will raise at render; it should just be end to close the if block.

**CANDIDATES:**
- XSS vulnerability: request.referer is interpolated directly into a JavaScript string literal without any escaping, allowing an attacker to craft a Referer header to inject arbitrary JavaScript
- Invalid Ruby syntax: 'end if' is not valid Ruby and will raise a SyntaxError, preventing the template from rendering
- Origin check uses substring matching instead of exact comparison, allowing an attacker whose origin is a prefix of discourseUrl to bypass the guard
- i.content may be nil when RSS/Atom items have no content element, causing NoMethodError when calling .scrub on nil
- Port exclusion in absolutize_urls ignores scheme - an http:// URL on port 443 would have its port silently dropped, producing an incorrect absolute URL

## Item 16

**GOLDEN:** When requests are authenticated with API keys or org auth tokens (which have user_id=None), organization_context.member is None. Line 71 attempts to access organization_context.member.has_global_access without checking if member is None, causing an AttributeError crash when optimized_pagination=true is used, even though the request passed all permission checks with valid org:write scope.

**CANDIDATES:**
- get_item_key crashes on datetime values - math.floor() and math.ceil() raise TypeError when passed a datetime object instead of converting to float timestamp first
- Django ORM does not support negative slicing - queryset[negative_int:stop] raises AssertionError, making reverse pagination with negative offset crash
- value_from_cursor returns a raw integer instead of a datetime - causes SQL WHERE datetime comparison to fail with type mismatch
- organization_context.member may be None - causes AttributeError when accessing has_global_access for non-superuser requests where member is unexpectedly None
- Date-range filtering silently removed - statsPeriod, start, and end query parameters were removed without replacement, breaking existing callers that rely on date-scoped audit log queries

## Item 17

**GOLDEN:** The Salesforce integration checks `response.statusText` instead of `response.ok` when handling OAuth token refresh responses. This can lead to unreliable behavior, as a successful response may not be correctly identified, resulting in the use of stale credentials and potential authentication failures.

**CANDIDATES:**
- The webhook secret comparison in `app-credential.ts` is not constant-time, which makes it vulnerable to timing attacks.
- In `app-credential.ts`, a call to `JSON.parse` on a decrypted payload is not wrapped in a try-catch block, which will cause an unhandled exception and a server crash if the payload is not valid JSON.
- In `parseRefreshTokenResponse.ts`, if an OAuth provider does not return a new refresh token, the code hardcodes the value to the string "refresh_token", which will cause subsequent token refreshes to fail.
- The `refreshOAuthTokens` function returns a raw `Response` object, but several of its callers (e.g., in Google Calendar, Hubspot, Zoho integrations) expect an object with a `data` property or a specific token structure, which will cause runtime errors.
- In `GoogleCalendarService.ts`, the result of `parseRefreshTokenResponse` is stored directly in the database, but this function returns a `SafeParseReturnType` object (`{ success, data }`) instead of the parsed data itself, leading to incorrect credential data being saved.
- The Salesforce token refresh logic in `SalesforceCalendarService.ts` has been reimplemented without using the new `refreshOAuthTokens` helper, meaning it will not support the external credential sync feature.
- The `refreshToken` callback for the `jsforce` connection in `SalesforceCalendarService.ts` has been removed, breaking the library's ability to automatically refresh expired access tokens during its operation.
- The check for a successful token refresh in `SalesforceCalendarService.ts` uses `response.statusText !== "OK"`, which is unreliable and will fail for any successful HTTP status other than 200.
- In `ZohoBigin/CalendarService.ts`, the `refreshOAuthTokens` function is called with the credential ID instead of the user ID, which will cause the external credential sync to fail for the wrong user.
- The `minimumTokenResponseSchema` in `parseRefreshTokenResponse.ts` uses a generic index signature to find the token expiry time, which is too permissive and could misinterpret other numeric fields in a token response as the expiry.
- The suggested command in `.env.example` for generating `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY` (`openssl rand -base64 24`) produces a 24-byte key, which contradicts the comment stating a 32-byte key is required for AES-256.

## Item 18

**GOLDEN:** Using retryCount: reminder.retryCount + 1 reads a possibly stale value and can lose increments under concurrency; consider an atomic increment via Prisma (increment: 1) to avoid race conditions (also applies to the similar update in the catch block).

**CANDIDATES:**
- The `deleteMany` query will delete any type of workflow reminder with a `retryCount` greater than 1, not just SMS reminders, which is likely unintended as this logic is in a file for scheduling SMS reminders.
- The retry count is incremented using a non-atomic read-then-write pattern (`reminder.retryCount + 1`), creating a race condition where concurrent executions can cause failed attempts to be undercounted.
- An error thrown by the database update in the `else` block is caught by the main `catch` block, which incorrectly attempts to increment the retry count a second time for the same failure.
- A database error when updating the retry count inside the main `catch` block is unhandled, which will crash the process and prevent the original scheduling error from being logged.

## Item 19

**GOLDEN:** The exported function TwoFactor handles backup codes and is in BackupCode.tsx. Inconsistent naming.

**CANDIDATES:**
- Case-sensitive backup code comparison will reject valid codes - indexOf lookup is strict string comparison but stored codes are always lowercase hex, so uppercase user input won't match
- Same case-sensitivity bug exists in the disable flow at apps/web/pages/api/auth/two-factor/totp/disable.ts - indexOf comparison without lowercasing user input will block users from disabling 2FA via backup code
- Exported function in BackupCode.tsx is named TwoFactor instead of BackupCode, same name as TOTP component making navigation and stack traces confusing
- resetState doesn't clear backupCodes or backupCodesUrl - if user cancels mid-flow, stale values remain in state and previous object URL isn't revoked

## Item 20

**GOLDEN:** Typo in property name: 'stopNotificiationsText' should be 'stopNotificationsText' (missing 'n' in 'Notifications')

**CANDIDATES:**
- Nil dereference when no TopicUser record exists - TopicUser.find_by returns nil for a user who has never interacted with the topic, and calling tu.notification_level on nil raises NoMethodError, crashing the request with a 500 error
- GET request performs a state-mutating action - Both unsubscribe routes are GET but the controller action immediately writes to the database on every visit, allowing email security scanners and link-prefetching services to silently change notification levels without user intent
- Typo in property name - stopNotificiationsText has an extra 'i' (Notificiations instead of Notifications)
- List-Unsubscribe header omits the new per-topic URL - The header still only advertises user_preferences_url instead of including the new per-topic unsubscribe URL

## Item 21

**GOLDEN:** The DB methods NewInMemoryDB().RunCommands, DB.QueryFramesInto, and DB.TablesList in pkg/expr/sql/db.go return hardcoded 'not implemented' errors after removing the go-duck dependency.

**CANDIDATES:**
- In `pkg/expr/reader.go`, the `enableSqlExpressions` function always returns `false` due to a logic error, which prevents the SQL expression feature from ever being enabled.
- The new SQL database implementation in `pkg/expr/sql/db.go` consists of stub methods that return 'not implemented' errors, breaking the SQL expression functionality that was previously handled by the now-removed `go-duck` dependency.

## Item 22

**GOLDEN:** Hardcoded empty data passed to TableWidgetVisualization causes it to always render an empty table instead of displaying actual results when the feature flag is enabled.

**CANDIDATES:**
- In `src/sentry/integrations/source_code_management/commit_context.py`, the static method `get_merged_pr_single_issue_template` on `PRCommentWorkflow` incorrectly calls `PRCommentWorkflow._truncate_title()`, which does not exist; this method is defined on `CommitContextIntegration` and will cause an `AttributeError` at runtime.
- In `src/sentry/replays/endpoints/project_replay_summarize_breadcrumbs.py`, the `fetch_error_details` function incorrectly uses `zip(error_ids, events.values())` to map error IDs to event data, which is unreliable as the order of `dict.values()` is not guaranteed to correspond to the order of `error_ids`, leading to mismatched data.
- In `static/app/views/dashboards/widgetCard/chart.tsx`, when the `use-table-widget-visualization` feature is enabled, the new `TableWidgetVisualization` component is rendered with static, empty data instead of the actual `tableResults`, which will cause an empty table to be displayed.

## Item 23

**GOLDEN:** The sendAddGuestsEmails function in email-manager.ts passes the full calendarEvent.attendees array when determining which attendees receive AttendeeScheduledEmail vs AttendeeAddGuestsEmail, but checks if newGuests.includes(attendee.email) where newGuests is the input guests array.

**CANDIDATES:**
- In `addGuests.handler.ts`, the authorization check for team members uses `&&` to combine `isTeamAdmin` and `isTeamOwner`, requiring a user to hold both roles to be authorized, which is likely a logic error that should be `||`.
- In `addGuests.handler.ts`, the authorization logic allows any attendee of an event to add more guests, which is an overly permissive security default that could lead to privacy violations or abuse of the booking.
- In `addGuests.handler.ts`, the `sendAddGuestsEmails` function is called with the raw `guests` input array instead of the filtered `uniqueGuests` array, causing existing attendees who are re-added to receive a full new event invitation instead of a simple notification.
- In `addGuests.handler.ts`, if all submitted guests are already attending, the handler throws an error with the message `emails_must_be_unique_valid`, which is misleading for that specific scenario.
- In `addGuests.handler.ts`, the check to see if a guest is already an attendee is subject to a race condition, which can lead to an unhandled database error if two concurrent requests attempt to add the same guest.
- In `addGuests.schema.ts`, the backend Zod schema for `addGuests` does not validate that the incoming `guests` array contains unique emails, which is a validation performed on the frontend. The backend should not trust the client and should perform this validation to prevent unhandled database errors.

## Item 24

**GOLDEN:** With isConditionalPasskeysEnabled(UserModel user) requiring user != null, authenticate(...) will not call webauthnAuth.fillContextForm(context) on the initial login page where context.getUser() is still null, so conditional passkey UI will not be set up for first-time passkey login. Consider whether this should also be enabled when no user has been selected yet so ID-less passkey authentication on the initial login form continues to work.

**CANDIDATES:**
- isConditionalPasskeysEnabled() is invoked with no arguments, but the only definition in the parent class UsernamePasswordForm has signature isConditionalPasskeysEnabled(UserModel user) - this will fail to compile
- isConditionalPasskeysEnabled(UserModel user) returns false whenever user == null, so fillContextForm is skipped for unauthenticated visits, meaning passkey autocomplete/form will not appear for new logins - breaking initial login passkeys flow
- The challenge() method inverts the original condition - original guard was context.getUser() == null && webauthnAuth != null && webauthnAuth.isPasskeysEnabled(), but new guard isConditionalPasskeysEnabled(context.getUser()) is true only when user != null, so users who submit bad username will see error page without WebAuthn form

## Item 25

**GOLDEN:** Docstring says this returns a list of DetectorEvaluationResult, but the method now returns a dict keyed by DetectorGroupKey. Consider updating the docstring to match the new return type.

**CANDIDATES:**
- MetricAlertDetectorHandler subclasses StatefulDetectorHandler but doesn't implement any of the four abstract methods (counter_names, get_dedupe_value, get_group_key_values, build_occurrence_and_event_data), making the class uninstantiable at runtime with TypeError
- TestEvaluateGroupKeyValue.test_dedupe passes wrong group key ('val1') to build_mock_occurrence_and_event, causing fingerprint mismatch with the key ('group_key') passed to evaluate_group_key_value, breaking the assertion
- Stale docstring in detector.py still references 'list' but the method now returns a dict[DetectorGroupKey, DetectorEvaluationResult]

## Item 26

**GOLDEN:** record_for_host compares lower(host) = ? but does not normalize the parameter’s case, so mixed‑case referer hosts may fail to match even though comparison intends to be case‑insensitive.

**CANDIDATES:**
- In `app/assets/javascripts/admin/components/embeddable-host.js.es6`, the `save` action's success callback manually sets the `category` relationship using `Discourse.Category.findById`, which can result in an `undefined` value if the category is not in the client-side cache, leading to an inconsistent UI state.
- In `app/controllers/admin/embeddable_hosts_controller.rb`, the `update` and `destroy` actions will raise a `NoMethodError` and cause a 500 server error if a record with the given `id` is not found, because they do not handle the `nil` case after `where(...).first`.
- In `app/models/embeddable_host.rb`, the `record_for_host` method's database query compares the lowercased host from the database with a potentially mixed-case host from the input URL, which will fail to match records on case-sensitive database collations.
- In `db/migrate/20150818190757_create_embeddable_hosts.rb`, the migration is vulnerable to SQL injection as it directly interpolates host names from a site setting into an SQL `INSERT` query.
- In `db/migrate/20150818190757_create_embeddable_hosts.rb`, the migration will crash with a `NoMethodError` if the `embed_category` site setting is not present, because it unconditionally accesses the first element of the query result.
- The contents of `spec/fabricators/category_fabricator.rb` and the new `spec/fabricators/embeddable_host_fabricator.rb` have been swapped, placing fabricator definitions in the wrong files.

## Item 27

**GOLDEN:** The updateManyByCredentialId call uses an empty data object, which prevents Prisma's @updatedAt decorator from updating the updatedAt timestamp. This results in inaccurate cache status tracking, as the timestamp isn't updated when the cache is refreshed. To fix this, explicitly set the updatedAt field.

**CANDIDATES:**
- The code in `packages/lib/server/repository/user.ts` and `packages/lib/getConnectedDestinationCalendars.ts` attempts to query and use an `updatedAt` field on the `SelectedCalendar` model, but this field does not exist in the database schema and is not being added.
- In `CredentialActionsDropdown.tsx`, confirmation dialogs are closed optimistically on button click, rather than waiting for the asynchronous mutation to complete, which provides misleading feedback to the user if the operation fails.
- In `CalendarService.ts`, `SelectedCalendarRepository.updateManyByCredentialId` is called with an empty data object, which performs no update and has no effect on the database.
- In `CredentialActionsDropdown.tsx`, `Intl.DateTimeFormat` is hardcoded with the "en-US" locale, which will display dates in an American format for all users regardless of their actual locale.
- In `deleteCache.handler.ts`, a generic `Error` is thrown when a credential is not found, which results in a vague 500 Internal Server Error response to the client instead of a more specific TRPC error like `NOT_FOUND`.
- The `test-gcal-webhooks.sh` script uses a `sed -i ''` command syntax that is specific to BSD/macOS and will fail on GNU/Linux systems.

## Item 28

**GOLDEN:** Field HTML_TAGS should be declared as 'private static final' following Java naming conventions for constants

**CANDIDATES:**
- StringIndexOutOfBoundsException in diagnostic substring calculation when sanitized shares a common suffix with value that extends past start (start + end >= value.length()), causing value.substring(start, value.length() - end) to throw and crash the Maven goal
- RuntimeException thrown instead of MojoExecutionException on I/O failure in verifySafeHtml, causing confusing stack trace instead of clean error message
- Instance fields POLICY_SOME_HTML, POLICY_NO_HTML, and HTML_TAGS should be static final to avoid allocating new HtmlPolicyBuilder, PolicyFactory, and compiled Pattern for every VerifyMessageProperties instance
- ISO-8859-1 encoding used for potentially UTF-8 properties files when using PropertyResourceBundle(FileInputStream), causing garbled content and potential false positives for non-Latin locales
- Typo in method name: santizeAnchors should be sanitizeAnchors

## Item 29

**GOLDEN:** Using Python’s built-in hash() to build cache keys is non-deterministic across processes (hash randomization), so keys won’t match across workers and invalidate_upsampling_cache may fail to delete them. Use a deterministic serialization of project_ids for the cache key.

**CANDIDATES:**
- Python's built-in hash() uses a per-process random seed (PYTHONHASHSEED) by default, so the same tuple(sorted(project_ids)) will produce different values across different worker processes, making the shared cache ineffective with constant cache misses
- invalidate_upsampling_cache uses the same non-deterministic hash() bug, meaning cache invalidation from one worker will not clear the key set by another, making invalidation silently a no-op in production
- is_errors_query_for_error_upsampled_projects receives the outer closure dataset variable instead of the scoped_dataset being queried, causing upsampling to be applied to transaction data when it shouldn't be, or skipped for error data when it should apply
- Column alias is hardcoded to 'count' in transform_query_columns_for_error_upsampling, ignoring any existing alias on the column - if caller passes 'count() as errors' the condition fails and upsampling silently does not apply

## Item 30

**GOLDEN:** Backup code validation is case-sensitive due to the use of indexOf(). This causes validation to fail if a user enters uppercase hex characters, as backup codes should be case-insensitive for a better user experience.

**CANDIDATES:**
- Case-sensitive backup code comparison will reject valid codes - indexOf lookup is strict string comparison but stored codes are always lowercase hex, so uppercase user input won't match
- Same case-sensitivity bug exists in the disable flow at apps/web/pages/api/auth/two-factor/totp/disable.ts - indexOf comparison without lowercasing user input will block users from disabling 2FA via backup code
- Exported function in BackupCode.tsx is named TwoFactor instead of BackupCode, same name as TOTP component making navigation and stack traces confusing
- resetState doesn't clear backupCodes or backupCodesUrl - if user cancels mid-flow, stale values remain in state and previous object URL isn't revoked

## Item 31

**GOLDEN:** In ClientPermissionsV2.hasPermission, the method getResourceTypeResource could return null, leading to a NullPointerException in findByResource. Defensive null checks are needed to prevent this issue.

**CANDIDATES:**
- Potential NullPointerException when all-clients resource is missing - getResourceTypeResource can return null and the result is passed directly to findByResource without a null guard
- Dead code: getEvaluationContext is never called - this private method is defined but has no callers within ClientPermissionsV2
- getResourceName doesn't handle the CLIENTS resource type - the method falls through to resource.getDisplayName() which is null for individually-created client resources, producing null/UUID display names

## Item 32

**GOLDEN:** The current origin validation using indexOf is insufficient and can be bypassed. An attacker could use a malicious domain like evil-discourseUrl.com to pass this check.

**CANDIDATES:**
- XSS vulnerability: request.referer is interpolated directly into a JavaScript string literal without any escaping, allowing an attacker to craft a Referer header to inject arbitrary JavaScript
- Invalid Ruby syntax: 'end if' is not valid Ruby and will raise a SyntaxError, preventing the template from rendering
- Origin check uses substring matching instead of exact comparison, allowing an attacker whose origin is a prefix of discourseUrl to bypass the guard
- i.content may be nil when RSS/Atom items have no content element, causing NoMethodError when calling .scrub on nil
- Port exclusion in absolutize_urls ignores scheme - an http:// URL on port 443 would have its port silently dropped, producing an incorrect absolute URL

## Item 33

**GOLDEN:** The Check operation exhibits asymmetric cache trust logic: cached permission grants are trusted and returned immediately, but cached denials from the same permission cache are ignored, leading to a fresh database lookup. This allows stale cached grants to provide access to revoked resources, posing a security risk. 

**CANDIDATES:**
- In the `Check` method, if a user's permissions are found in the cache but do not grant access for the specific resource, the code incorrectly proceeds to query the database instead of returning a denial, which largely defeats the purpose of caching the full permission set.

## Item 34

**GOLDEN:** Starting with an array containing an empty string may cause validation issues. Consider starting with an empty array [] and handling the empty state in the MultiEmail component instead.

**CANDIDATES:**
- AND instead of OR in isTeamAdminOrOwner - isTeamAdmin already returns truthy for both ADMIN and OWNER roles, so the && requires users to satisfy both checks simultaneously, meaning only owners pass while team admins are silently denied access
- Duplicate emails within the input array are not deduplicated - the filter removes guests already in booking.attendees but does not deduplicate within the incoming guests array itself, allowing duplicate Attendee rows to be inserted via createMany
- Empty-string initial state bypasses the early-return guard - multiEmailValue is initialized to [''], so multiEmailValue.length === 0 is never true on first open, causing validation error to show before user types anything
- Error is silently swallowed - the caught err is never logged, making email-delivery failures invisible in production logs
- Schema recreated on every render - ZAddGuestsInputSchema is defined inside the component body, so a new Zod schema object is allocated on every render instead of being at module scope

## Item 35

**GOLDEN:** The cache key construction in `userPermDenialCacheKey` uses simple string concatenation with underscores, which can lead to ambiguous keys and collision risks when any component contains underscores or is empty. This could result in incorrect denial cache hits, affecting user permissions.

**CANDIDATES:**
- Cache key collision with `_` separator: name and parent are concatenated with bare `_` separators, which means `name="dash1_", parent=""` produces the same key as `name="dash1", parent="_"`. Grafana resource UIDs and folder UIDs can contain underscores, so this collision is reachable in practice. A false hit in the denial cache causes a legitimate access check to be immediately denied for up to 30 seconds.
- Metrics double-count cache misses on `!allowed` cache hit: When `getCachedIdentityPermissions` returns a valid entry (`err == nil`) but `checkPermission` returns `!allowed`, the code falls through and still increments `permissionCacheUsage("false", ...)` at line 137. This means a cache hit that resolved to "not found in cached scopes" is reported as a cache miss, inflating the false-miss counter and making it harder to interpret the metric.
- Stale denial cache on permission grant: When a user's permissions are upgraded after a prior denial (e.g., an admin grants access to an existing resource), the `permDenialCache` entry for that `(name, parent)` will continue to block access for up to `shortCacheTTL` (30 s). The DB is never re-queried while the denial entry lives.

## Item 36

**GOLDEN:** Remove unused getEvaluationContext private method in ClientPermissionsV2 - it is defined but never called

**CANDIDATES:**
- Potential NullPointerException when all-clients resource is missing - getResourceTypeResource can return null and the result is passed directly to findByResource without a null guard
- Dead code: getEvaluationContext is never called - this private method is defined but has no callers within ClientPermissionsV2
- getResourceName doesn't handle the CLIENTS resource type - the method falls through to resource.getDisplayName() which is null for individually-created client resources, producing null/UUID display names

## Item 37

**GOLDEN:** Logic error: when externalCalendarId is provided, you're searching for a calendar where externalId === externalCalendarId, but this will always fail since you're looking for a calendar that matches itself. Should likely find by credentialId or use different logic.

**CANDIDATES:**
- In `packages/app-store/googlecalendar/lib/CalendarService.ts`, the logic to find the calendar for `updateEvent` and `deleteEvent` is flawed because it will fail to find the correct calendar if `externalCalendarId` is null or undefined.
- In `packages/app-store/larkcalendar/lib/CalendarService.ts`, the `createEvent` method signature does not match the `Calendar` interface as it is missing the `credentialId` parameter, causing it to always use the first destination calendar which is incorrect for multi-host events.
- In `packages/app-store/office365calendar/lib/CalendarService.ts`, the `createEvent` method signature does not match the `Calendar` interface as it is missing the `credentialId` parameter, causing it to always use the first destination calendar which is incorrect for multi-host events.
- In `packages/lib/CalendarService.ts`, the `createEvent` method in the base class does not match the `Calendar` interface and its logic incorrectly uses only the first destination calendar, which will fail for secondary hosts in a collective event.
- In `packages/core/EventManager.ts`, the check for Google Meet location can cause a runtime error because `mainHostDestinationCalendar` can be `undefined` but its `integration` property is accessed without a null check.
- In `packages/features/bookings/lib/handleNewBooking.ts`, when creating a booking, only the first destination calendar is saved to the database, resulting in data loss for other hosts in a collective event.
- In `packages/core/EventManager.ts`, there is a redundant duplicated condition `if (!calendarReference) if (!calendarReference)` in the `updateOtherCalendarEvents` method.
- In `packages/features/bookings/lib/handleNewBooking.ts`, the `loadUsers` function throws a generic `Error` instead of an `HttpError`, which will result in an unhandled exception and a 500 server error instead of a proper client-facing error message.
- In `packages/core/EventManager.ts`, the fallback logic in `createAllCalendarEvents` can create duplicate calendar events if a user has multiple credentials for the same integration type, as it iterates over all of them.
- In `packages/core/EventManager.ts`, the logic to fallback to Cal Video if Google Meet is selected without a Google Calendar only checks the first destination calendar, which is incorrect for collective events where another host might have a Google Calendar.

## Item 38

**GOLDEN:** Wrong value `6` passed for `group_2` occurrence — the data packet specifies `"group_2": 10`. Should be `10` to accurately reflect the test scenario, which will ensure the test produces the correct occurrence data.

**CANDIDATES:**
- The `MetricAlertDetectorHandler` class inherits from the abstract `StatefulDetectorHandler` but does not implement its abstract methods, which will cause a `TypeError` at runtime.
- In `StatefulDetectorHandler.evaluate_group_key_value`, `PriorityLevel(new_status)` will raise a `ValueError` because it attempts to cast a `DetectorPriorityLevel` enum to a `PriorityLevel` enum, but their underlying integer values are not compatible.
- In `test_state_results_multi_group`, the expected `IssueOccurrence` for `group_2` is built with a hardcoded value of `6`, but the input data packet provides a value of `10`, making the test assertion incorrect.

## Item 39

**GOLDEN:** to_dict() returns a datetime for queued; if this dict is passed in task kwargs (e.g., via apply_async), JSON serialization may fail depending on the serializer, which can cause enqueue errors.

**CANDIDATES:**
- The `AssignmentSource.from_dict` method does not deserialize datetime strings from the `queued` field, causing it to fail when processing data from a Celery task.
- The `sync_status_outbound` method signature incorrectly uses `AssignmentSource` for a parameter that should represent the source of a status change, not an assignment.

## Item 40

**GOLDEN:** The upsampling eligibility check passes the outer dataset instead of the actual dataset used by scoped_dataset. In paths where the query ultimately runs against discover (e.g., dashboard split) while the original dataset is metrics, upsampling may be skipped even when all projects are allowlisted.

**CANDIDATES:**
- Python's built-in hash() uses a per-process random seed (PYTHONHASHSEED) by default, so the same tuple(sorted(project_ids)) will produce different values across different worker processes, making the shared cache ineffective with constant cache misses
- invalidate_upsampling_cache uses the same non-deterministic hash() bug, meaning cache invalidation from one worker will not clear the key set by another, making invalidation silently a no-op in production
- is_errors_query_for_error_upsampled_projects receives the outer closure dataset variable instead of the scoped_dataset being queried, causing upsampling to be applied to transaction data when it shouldn't be, or skipped for error data when it should apply
- Column alias is hardcoded to 'count' in transform_query_columns_for_error_upsampling, ignoring any existing alias on the column - if caller passes 'count() as errors' the condition fails and upsampling silently does not apply
