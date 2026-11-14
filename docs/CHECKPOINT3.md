# Checkpoint 3 progress

14 November 2026. **Started, not complete.** The supplied ICS0022 project
brief lists checkpoint 3 as 20 November 2026 (section 1.1). Requirements are
in sections 4.2 and 4.4.3; the report structure is in section 1.3.

## First increment: validation and repeatable tests

- Added a standard-library `unittest` suite using temporary vaults and
  fictional credentials. It runs the real Argon2id and AES-GCM code.
- Master-password validation now handles wrong types and invalid Unicode
  with a controlled error. New passwords must be printable. Unlocking still
  accepts control characters allowed by checkpoint 2, so existing vaults do
  not become inaccessible because of the new creation policy.
- Decrypted JSON now rejects duplicate object names at every nesting level.
  Previously Python silently kept the last duplicate title or record field.
  This is a format/data-integrity check after authentication, not a way for
  someone without the key to bypass AES-GCM.
- Included tests in the Docker image and documented both Docker and local
  Python test commands in the README.

The regression tests first reproduced the password and duplicate-name gaps
against checkpoint 2 before the fixes were applied. The vault format and
cryptographic parameters have not changed.

## Validation results

Python 3.12.14 on Windows, using a fresh project virtual environment with
the pinned dependencies: **21 tests run, 20 passed, 1 skipped**.
The skipped case requires POSIX file ownership and permissions.
`pip check`, the installed `pwvault --help` command and `git diff --check`
also passed. Full output is in [security-test-results.txt](security-test-results.txt).

| Area | Evidence in the suite |
|---|---|
| Encryption | Round trip; no literal credential text in ciphertext; fresh nonce on save |
| Integrity/authentication | Wrong password; modified salt, nonce, ciphertext and tag all rejected |
| File parser | Invalid size or KDF costs rejected before derivation; malformed JSON and duplicate names rejected |
| Field validation | Exact length boundaries; wrong types; Unicode; NUL, escape and control characters; invalid record schemas |
| CLI | Add/list/get/update/delete; password stays hidden; literal shell/format syntax remains data |
| Failure paths | Every existing-vault command rejects wrong passwords without changing the file; invalid saves and failed replacement preserve the vault |
| Storage | Existing files cannot be overwritten by init; temporary files removed after failure |
| Error output | Simulated OS error does not expose its message/path or a traceback |
| Password prompt | Redirected input refused before calling getpass |

These tests do not prove secure memory erasure, per-user isolation or freedom
from filesystem races. They simulate password input, rather than testing an
actual terminal. Deleting an entry removes it from the current encrypted
payload; it is not a promise to erase backups, old filesystem blocks or RAM.

Docker was unavailable during initial Windows validation. On 14 November
2026 the prepared image built and Linux tests passed. Current evidence is
in [PREPARED_VALIDATION.md](PREPARED_VALIDATION.md) and docker-test-results.txt;
the checkpoint 2 results in PROGRESS.md remain historical evidence.

## Remaining meaningful increments

Update: structured logging is implemented, with authentication and command
events, private log files and failure-path tests. See [LOGGING.md](LOGGING.md).
The list below records the original plan; memory/access work and the report
are still pending. The results above describe the original 21-test suite;
run the full suite for current results.

1. **Structured logging and failure handling.** Add an event schema with
   timestamp, OS user identity, operation and outcome. This offline CLI has
   no network source address; record that explicitly where needed. Keep
   titles, usernames, paths, passwords, keys and vault contents out of logs.
   Protect the log file and test log injection, secret absence and failures
   during logging, authentication and storage.
2. **Memory lifecycle and access control.** Reduce plaintext/key lifetimes
   and release resources on success, failure and cancellation. Do not claim
   `del` or overwriting one buffer erases immutable Python/library copies.
   Decide how to meet the brief's wiping requirement and document residual
   risk. Audit every operation against OS-user ownership, ancestor directory
   links/reparse points and check/use races; test as two Linux users. Shared
   Docker volumes run under the same UID and are not separate user accounts.
3. **Report and final verification.** Write Introduction, Implementation,
   Security Analysis and Conclusion, referencing actual controls and test
   evidence. Rebuild Docker, run the POSIX suite, test a real hidden terminal
   prompt and persistence, then record results. Add permission/link/race and
   memory-handling regression cases alongside the relevant changes.

The design also planned password generation, clipboard support and changing
the master password. These are extra planned features, not explicit
checkpoint 3 deliverables in the supplied brief. Review their value after
the required controls; the interface must continue to avoid printing secrets.

Each increment above is substantive future work suitable for its own commit.
This note is a progress record, not the report draft or a claim that checkpoint
3 is ready for submission.

## Course context

See [course review](COURSE_REVIEW.md) for the supplied materials, review scope
and relevant stable slide references. ICS0027's automated tests inspired the
repeatable test approach; its Flask sessions, CSRF and SQL controls do not
apply directly to this offline encrypted-file CLI.
