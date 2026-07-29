# Deep Review Checklist

Use this reference when a review category needs deeper analysis. Not every item applies to every file or language. Pick the relevant items for the code under review.

## Correctness & Logic

- [ ] Boundary conditions: off-by-one in loops, ranges, and index access.
- [ ] Null/None/undefined/nil checks: every dereference or method call on a potentially absent value is guarded.
- [ ] Falsy/truthy pitfalls: `0`, `""`, `[]` treated as falsy where truthy was expected (or vice versa).
- [ ] Integer overflow / truncation: large inputs, division by zero, float-to-int narrowing.
- [ ] Type coercion bugs: implicit conversions, `==` vs `===`, string-number comparisons.
- [ ] Boolean logic: inverted conditions, wrong operator (`&&` vs `||`), De Morgan's law mistakes.
- [ ] Switch/match: missing `default`/`else` branch, fall-through without explicit intent.
- [ ] Concurrency: shared mutable state without synchronization, TOCTOU races, deadlock potential.
- [ ] Error paths: exceptions, error codes, or `Result` types propagated correctly, not silently swallowed.
- [ ] Side effects: function modifies state it should not, or return value depends on hidden state.
- [ ] Async: missing `await`/`async`, unhandled promise rejection, event loop starvation.
- [ ] Time zones: naive datetime vs UTC, DST transitions, timezone conversion errors.
- [ ] Character encoding: UTF-8 vs ASCII assumptions, multi-byte character handling.

## Security

- [ ] SQL injection: dynamic query construction without parameterization.
- [ ] Command injection: `subprocess`, `exec`, `system`, `Runtime.exec` with user input.
- [ ] Path traversal: `../` in file paths, `os.path.join` with untrusted segments.
- [ ] XSS: unescaped user input rendered in HTML, `dangerouslySetInnerHTML`, template injection.
- [ ] SSRF: outbound HTTP requests with user-controlled URLs.
- [ ] Open redirect: redirect target from user input without allowlist.
- [ ] Hardcoded secrets: API keys, passwords, tokens, private keys in source.
- [ ] Insecure deserialization: `pickle`, `yaml.load`, `ObjectInputStream`, `eval` on untrusted data.
- [ ] Authentication: missing auth check, predictable tokens, weak password hashing.
- [ ] Authorization: IDOR, missing ownership check, privilege escalation.
- [ ] Cryptography: weak algorithms (MD5, SHA1 for security), ECB mode, hardcoded IV, short key.
- [ ] Information disclosure: stack traces, internal IPs, version strings in error responses.
- [ ] Dependency security: known vulnerable package versions, pinned to insecure releases.

## Performance

- [ ] Redundant computation: same expensive operation called in a loop.
- [ ] N+1 queries: entity loaded per-iteration instead of batched.
- [ ] Missing indexes: queries filtering/sorting on non-indexed columns.
- [ ] Unbounded growth: collections, caches, or logs that grow without eviction or rotation.
- [ ] Large allocations: loading entire files or result sets into memory.
- [ ] Missing pagination: endpoints returning unbounded lists.
- [ ] Blocking calls: synchronous I/O in async/event-driven code.
- [ ] Redundant serialization: marshal/unmarshal cycles in hot paths.
- [ ] Copy overhead: deep copies where shallow or reference would suffice.
- [ ] String concatenation in loops (O(n²)) where a builder would be O(n).

## API Design & Compatibility

- [ ] Breaking changes: removed public methods, changed signatures, renamed exports.
- [ ] Semver: major version bump for breaking changes, or unflagged breaking change.
- [ ] Return type consistency: same method returns different types in different paths.
- [ ] Parameter ordering: inconsistent with sibling methods or conventions.
- [ ] Error response shape: HTTP endpoints return inconsistent error JSON/status codes.
- [ ] Naming: method/function names that do not match what they do.
- [ ] Documentation: public API without docstrings, JSDoc, or godoc comments.
- [ ] Deprecation: old API removed without a deprecation path or migration guide.
- [ ] Optional vs required: parameters marked optional that should be required, or vice versa.

## Error Handling & Resilience

- [ ] Bare catch: `except Exception` or `catch (e)` that swallows all errors.
- [ ] Missing handling: network call, file I/O, or parse without try/catch or error check.
- [ ] Resource leak: file, socket, connection, or stream opened but not closed on all paths.
- [ ] Missing timeout: HTTP client or DB call without a timeout.
- [ ] No retry: flaky external call without retry or backoff.
- [ ] Silent failure: error logged but execution continues as if nothing happened.
- [ ] Inconsistent error model: mixing exceptions and error codes without a clear boundary.
- [ ] Cleanup ordering: `defer`, `finally`, or cleanup runs in wrong order under error paths.
- [ ] Transaction rollback: partial writes without rollback on failure.

## Test Coverage

- [ ] New logic without tests: changed or added behavior has no test.
- [ ] Tests removed: tests deleted without replacement.
- [ ] Assertion quality: test runs but does not assert the right thing (asserting `!= null` instead of the actual value).
- [ ] Missing edge cases: only happy path tested; no boundary, error, or null input tests.
- [ ] Flaky patterns: `sleep`, wall-clock time, random without seed, external service calls.
- [ ] Test isolation: shared mutable state, test order dependencies.
- [ ] Mock correctness: mocks that do not match the real interface or behavior.
- [ ] Coverage gaps: branches or error paths not exercised.
- [ ] Integration: unit tests pass but no test for the integration point.

## Maintainability & Code Quality

- [ ] Dead code: unreachable branches, unused imports, variables, or private methods.
- [ ] Complexity: function exceeds ~15 branches or nests more than 4 levels.
- [ ] Magic numbers: unexplained literals that should be named constants.
- [ ] Naming: variable, function, or class names that are vague or misleading.
- [ ] Duplication: copy-pasted blocks that should be extracted.
- [ ] Comment quality: stale comments, comments that restate code, or missing comments on non-obvious logic.
- [ ] Function length: function doing too many things, exceeding ~50 lines without clear structure.
- [ ] Coupling: tight coupling between modules that makes change risky.
- [ ] Config hardcoding: environment-specific values (URLs, ports, paths) hardcoded instead of configured.
