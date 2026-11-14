# Verification results

Tested with cryptography 50.0.2 and argon2-cffi 25.1.0.

| Environment | Result |
|---|---|
| Docker/Linux, normal user | 49 passed; one root-only test skipped |
| Docker/Linux, root test run | All 50 passed, including two OS-user identities |
| Windows, permissions available | 39 passed; 11 Linux-specific tests skipped |

Exact output is in prepared-test-results.txt and docker-test-results.txt.
Skips are tests that were not run in that environment.

Real Linux pseudo-terminals verify hidden input, CRUD, wrong-password
rejection and Ctrl+C without mocking getpass. Cross-container volume
persistence passed using fictional data (persistence-results.txt).

The five public Python runtime packages have no known advisories reported
by pip-audit 2.10.1 on this check. See DEPENDENCIES.md and dependency-audit.json
for scope. The pip installer and OS packages were not part of that scan.

The manual demo checklist is in REVIEW.md. Older results in
security-test-results.txt and PROGRESS.md describe earlier checkpoints.
