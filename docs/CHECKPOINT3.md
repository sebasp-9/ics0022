# Checkpoint 3 and final project status

Reviewed 14 November 2026. The implementation, tests, report source and
presentation notes are included in the repository. The Git history records
the separate implementation steps. REVIEW.md distinguishes the student's
reported manual demo from checks run with AI assistance.

| Required item | Status |
|---|---|
| Encrypted credential storage and CRUD | Implemented and tested |
| Master-password access | Salted Argon2id-derived key plus AES-GCM authentication; password not stored |
| Validation | Type/size/text/schema/header/path checks, including negative cases |
| Structured logging and controlled errors | Implemented; no saved fields, keys or passwords passed to the writer |
| Per-user ownership | Linux file policy and two-UID isolation test passed |
| Secure memory handling | Owned buffers overwritten, finally cleanup and Linux dump restrictions; immutable/native copy erasure remains a qualification |
| Tests | All 50 passed as root in disposable Linux containers; 49 passed as the normal user with the root-only case skipped |
| Report | REPORT.md has Introduction, Implementation, Security Analysis and Conclusion; formatted PDF is in the prepared deliverables |

Real Linux terminal tests verify echo is off, CRUD persists across CLI
processes, and Ctrl+C preserves the vault and releases the command.
Separate-container volume persistence also passed. No existing user vault
or Docker volume was used for verification.

See PREPARED_VALIDATION.md, docker-test-results.txt and persistence-results.txt
for evidence. PROGRESS.md and security-test-results.txt describe older work.

## Before handing it in

1. Read the code guide and report so you can explain the design and limits.
2. Review the local commits and push them when ready.
3. Verify the source and report in the submission ZIP match your reviewed code.
4. Submit through Moodle and prepare the on-site demonstration yourself.

The strict immediate-erasure wording is not fully satisfied by Python.
The report documents that limit; it must not be presented as a guarantee.
The source, tests and technical report are otherwise prepared for the stated
prototype scope. Personal review, submission and presentation remain yours.

The supplied brief lists checkpoint 3 as 20 November and final submission
as 4 December 2026. These are the supplied schedule, not a live Moodle check.
