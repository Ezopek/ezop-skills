# Review Dimensions

Use this guide to structure reviews and keep findings consistent across dimensions.

## Priority Order

When multiple findings exist, prefer this order:

1. Security vulnerabilities
2. Correctness bugs
3. Breaking changes
4. Missing or misleading tests
5. Performance issues
6. Maintainability concerns
7. Documentation gaps

## Correctness

Review the code for logic errors and behavioral correctness.

What to look for:

- Off-by-one errors in loops and array access
- Wrong boolean conditions or inverted logic
- Missing null/undefined checks where values can be absent
- Incomplete error handling: catch blocks that swallow errors, missing finally blocks
- State mutations that break expected invariants
- Race conditions in async or concurrent code
- Type coercion issues in weakly typed languages

Examples:

- A filter condition uses `>` instead of `>=`, silently dropping boundary values
- An async function does not await a promise, causing silent failures
- A switch statement is missing a default case for an enum that may grow

## Security

Review the code for vulnerabilities and unsafe patterns.

What to look for:

- SQL injection: string concatenation in queries instead of parameterized queries
- XSS: user input rendered without escaping in HTML, JavaScript, or templates
- Command injection: user input passed to shell commands or `exec` calls
- Authentication bypass: missing auth checks on new endpoints or routes
- Authorization gaps: checking auth but not verifying the user has the right role or scope
- Hardcoded secrets: API keys, passwords, tokens in source code
- Insecure defaults: permissive CORS, disabled CSRF protection, overly broad permissions
- Sensitive data exposure: PII, tokens, or passwords in log output
- Missing input validation: accepting unbounded strings, negative numbers, or unexpected types at trust boundaries

Examples:

- A new API endpoint is added without the auth middleware that other endpoints use
- User-provided search input is interpolated directly into a SQL query string
- A debug log statement includes the full request body, which may contain passwords

## Performance

Review the code for efficiency and resource usage.

What to look for:

- N+1 queries: fetching related records inside a loop instead of batching
- Unbounded collections: loading all records into memory without pagination or limits
- Missing indexes on frequently queried columns
- Blocking I/O on hot paths or in event loops
- Memory leaks: event listeners not removed, caches that grow without bounds
- Redundant computation: recalculating values that could be cached or memoized
- Unnecessary network round-trips

Examples:

- A loop fetches user details one at a time for each item in a list instead of batch-loading
- A cache has no TTL or size limit, growing indefinitely in long-running processes
- A synchronous file read blocks the main thread in a request handler

## Testing

Review whether tests adequately cover the changed behavior.

What to look for:

- Changed behavior without corresponding test updates
- Missing tests for error paths and edge cases
- Tests that assert on implementation details rather than behavior
- Flaky test patterns: time-dependent, order-dependent, or network-dependent
- Missing integration tests where unit tests alone are insufficient
- Test descriptions that do not match what the test actually verifies
- Mocks that hide real bugs by stubbing too much

Examples:

- A new validation rule is added but no test covers the rejection case
- An existing test still passes but tests the old behavior, not the new one
- A test mocks the database layer so completely that a broken query would never be caught

## Maintainability

Review the code for long-term readability and health.

What to look for:

- Unclear naming: variables, functions, or classes that do not communicate intent
- High cyclomatic complexity: deeply nested conditionals, long functions
- Tight coupling: one change forces changes in many unrelated files
- Code duplication: similar logic repeated instead of extracted
- Inconsistency with existing codebase patterns
- Magic numbers or strings without explanation
- Dead code left in the diff

Examples:

- A function named `process` that does validation, transformation, and persistence
- Three handlers that share 80% of their logic but each implement it separately
- A new module uses a different error handling pattern than the rest of the codebase

## Breaking Changes

Review the code for backward compatibility issues.

What to look for:

- Removed or renamed API endpoints, fields, or parameters
- Changed response shapes or status codes
- Database migrations that are not backward-compatible with running code
- Configuration keys renamed or removed without migration support
- Changed default values that affect existing deployments
- Removed or changed public function signatures in shared libraries

Examples:

- A REST endpoint changes from returning an array to returning a paginated object
- A database column is renamed without a migration that handles both old and new code
- A shared utility function changes its parameter order

## Documentation

Review whether documentation should move with the code.

What to look for:

- New API endpoints or changed parameters without updated API docs
- New configuration options or environment variables without documentation
- Changed behavior that users, operators, or other developers need to know about
- Inline comments that are now stale after the code change
- README or setup instructions that no longer match reality

Examples:

- A new environment variable is required but not mentioned in the deployment docs
- An API endpoint changes its authentication requirement but the API docs still show the old method
- A setup step was removed from the code but remains in the README
