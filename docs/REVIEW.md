# Checks and remaining work

## Manual demo

I ran the password manager in my terminal with fictional credentials. I
checked the full flow and confirmed that saved passwords stayed hidden.

- [x] Create a vault and confirm the master password.
- [x] Add a saved login, list it and view its login name.
- [x] Keep password input invisible and display saved passwords as [hidden].
- [x] Reject a wrong master password, then reopen with the correct one.
- [x] Update an entry and check the changed login name.
- [x] Reopen the vault between commands and keep the saved entry.
- [x] Cancel with Ctrl+C, then reopen the vault successfully.
- [x] Delete the entry and confirm that the vault is empty.

## Automated checks

The Linux suite passed all 50 tests as root. The normal-user run passed 49
tests and skipped the root-only ownership test. Windows passed 39 tests
and skipped 11 Linux-specific cases.

The checks cover encryption, authentication, input boundaries, ownership,
links, failed saves, private logging, locking and buffer cleanup. The
dependency scan found no known advisories in the five checked runtime
packages after the cryptography update.

Results: PREPARED_VALIDATION.md, docker-test-results.txt,
prepared-test-results.txt, interactive-review-results.txt and
persistence-results.txt. Dependency scope is recorded in DEPENDENCIES.md.

## Before submission

- [ ] Review the code and explain the main functions in my own words.
- [ ] Read the report and check that it matches my understanding.
- [ ] Rehearse the presentation and discuss the Python memory limit.

Python cannot guarantee erasure of every immutable or native secret copy.
Physical RAM/swap forensics, exhaustive race analysis, OS-package scanning
and the pip installer are outside these checks. Windows has weaker
filesystem guarantees than the intended Docker/Linux environment.
