# Verification results

Rechecked 14 November 2026, with cryptography 50.0.2 and argon2-cffi 25.1.0.

| Environment | Result |
|---|---|
| Docker/Linux, normal user | 49 passed; one root-only test skipped |
| Docker/Linux, root test run | All 50 passed, including two OS-user identities |
| Windows, permissions available | 39 passed; 11 Linux-specific tests skipped |

The restricted Windows sandbox previously skipped one additional hardlink
test. Exact current output is in prepared-test-results.txt and
docker-test-results.txt. Skips are not passing tests.

Real Linux pseudo-terminals verify hidden input, CRUD, wrong-password
rejection and Ctrl+C without mocking getpass. Cross-container volume
persistence passed using fictional data (persistence-results.txt).

The five public Python runtime packages have no known advisories reported
by pip-audit 2.10.1 on this check. See DEPENDENCIES.md and dependency-audit.json
for scope. The pip installer and OS packages were not part of that scan.

All checks above were run with AI assistance. Personal checks are recorded
separately in REVIEW.md. Older security-test-results.txt/PROGRESS.md entries
remain historical evidence, not the latest result.
