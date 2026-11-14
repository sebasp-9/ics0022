# Tests and checks

## Run the suite

From the project folder with Docker running:

```sh
docker compose build
docker compose run --rm --entrypoint python vault -m unittest discover -s tests -v
docker compose run --rm --user 0 --entrypoint python vault -m unittest discover -s tests -v
```

The second run includes the two-OS-user ownership test. Root is only used
for this test; normal commands run as the non-root app user. Tests use
temporary vaults and fictional credentials.

| Environment | Saved result |
|---|---|
| Linux, normal user | 58 passed, one root-only test skipped |
| Linux, root test run | All 59 passed |
| Windows | 48 passed, 11 platform-specific tests skipped |

## Coverage

| Test file | Main checks |
|---|---|
| test_security.py | Encryption, tampering, authentication, input boundaries and CRUD |
| test_audit.py | Private event logs, no saved secrets, and logging failures |
| test_storage.py | Ownership, permissions, links and directory replacement |
| test_locking.py | Concurrent command rejection and lock release |
| test_memory.py | Owned-buffer cleanup, failure paths and Linux dump restrictions |
| test_terminal.py | Actual hidden input, CRUD, persistence and Ctrl+C in a Linux terminal |
| test_clipboard.py | Timeout/Ctrl+C cleanup, newer content, unavailable backend and clear failures |

Raw results are in [test-results/](test-results/): linux.txt, windows.txt,
terminal.txt, persistence.txt, clipboard.txt and dependencies.json.

A separate Windows check used the actual clipboard and a temporary encrypted
vault. It verified retrieval, the full 20-second timeout, Ctrl+C, unchanged
vault bytes and no secrets in output/logs. The master-password prompt used
fictional test input. Hidden prompts are covered by the Linux PTY tests.

## Manual demo

I ran the terminal demo with fictional credentials: create, add, list, get,
update and delete. I checked that typing passwords stayed invisible, get
displayed [hidden], a wrong master password was rejected, entries survived
between commands, and Ctrl+C left the vault usable.

## Dependencies

cryptography was updated from 48.0.1 to 50.0.2 after three unique advisories
were reported: PYSEC-2026-3552, PYSEC-2026-3553 and PYSEC-2026-3554. The affected
certificate/PKCS7 features are unused by this vault. The follow-up pip-audit
scan found no known advisories in the six checked runtime packages, including
the pinned pyperclip 1.11.0 clipboard dependency.
The pip installer and OS packages were outside that scan.

## Requirement review

Passing the suite verifies the checks it contains, not every requirement.

| Checkpoint 3 criterion | Review result |
|---|---|
| Secure memory handling | Owned buffers wiped and failure paths tested; Python/native-copy limits explicitly documented |
| Full field validation | Implemented and tested |
| Structured logging and secure errors | Implemented and tested; logs exclude saved fields and secrets |
| Per-user record access | Tested for separate Linux OS users; one shared Docker UID is one identity |
| Passing tests including validation and memory checks | Verified: 58 normal Linux passes, all 59 as root; 48 Windows passes |
| Report with all four required sections | Present in Markdown and the generated PDF |

Password retrieval is implemented with get --copy on a local desktop.
Passwords are never printed. Matching clipboard text is cleared after
20 seconds or Ctrl+C; newer content is preserved. Docker has no desktop
clipboard and returns a controlled error for this optional flag.

Authentication works through salted Argon2id key derivation and AES-GCM tag
verification. No separate password hash is stored. This differs from the
brief's wording about a stored password hash: the salted KDF derives the
key, and authenticated decryption verifies it. The report explains this
offline-vault design and the use of OS users for record ownership.

## Limits and remaining work

Python cannot guarantee erasure of every secret copy. Memory tests check
owned buffers and cleanup paths, not physical RAM/swap forensics. Network
filesystems, every possible race and a compromised OS are outside these checks.
Clipboard history/sync, other apps and forced process termination can retain
copies beyond the timer. Real clipboard integration was checked on Windows.

The Checkpoint 3 implementation, test evidence and draft report are prepared
with these stated limitations. Lecturer assessment remains separate.

## Completed preparation

- [x] Code review: authentication, encryption, field validation, file access, logging and cleanup paths.
- [x] Scripted terminal demonstration: hidden input, CRUD, persistence, wrong-password rejection and Ctrl+C.
- [x] Real Windows clipboard check: retrieval, full timeout, cancellation and no secrets in output/logs.
- [x] Speaking notes, code map and likely questions prepared in the local walkthrough.

## Before presenting or submitting

- [x] Review the code and report.
- [ ] Rehearse the live demonstration.
- [ ] Explain the documented memory limits, authentication and OS-user ownership during review.
- [ ] Try get --copy locally using fictional data before demonstrating it.
- [ ] Check Moodle access and submission requirements.
- [ ] Submit the final ZIP and complete the live presentation and questions.
