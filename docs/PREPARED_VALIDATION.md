# Prepared validation

Prepared and tested on 14 November 2026 using Python 3.12.14 on Windows,
with the existing pinned dependencies. All changes were prepared on this
date; later commits do not represent later test runs.

```text
Ran 37 tests in 2.010s

OK (skipped=9)
```

Full output: [prepared-test-results.txt](prepared-test-results.txt).

Skipped cases require Linux/POSIX, root in a disposable Linux container,
or hardlink creation blocked by this sandbox. Skips are not passes.
Docker/Linux was also verified on 14 November 2026. See
[docker-test-results.txt](docker-test-results.txt) for exact commands and results.
36 tests passed as non-root; the root-only case was skipped.
All 37 passed as root, including the two-UID check.
Password input was simulated in this increment; actual terminal
verification is included in the third increment.
The saved original security-test-results.txt remains historical evidence
for the first 21 tests, not the expanded suite.
