# Checkpoint 3 progress

My project is an offline password manager. The implementation, tests,
report and presentation notes are included in the repository.

| Required item | Status |
|---|---|
| Encrypted credential storage and CRUD | Implemented and tested |
| Master-password access | Salted Argon2id-derived key plus AES-GCM authentication; password not stored |
| Validation | Type/size/text/schema/header/path checks, including negative cases |
| Structured logging and controlled errors | Implemented; no saved fields, keys or passwords passed to the writer |
| Per-user ownership | Linux file policy and two-UID isolation test passed |
| Secure memory handling | Owned buffers overwritten, finally cleanup and Linux dump restrictions; immutable/native copy erasure remains a qualification |
| Tests | All 50 passed as root in disposable Linux containers; 49 passed as the normal user with the root-only case skipped |
| Report | REPORT.md has Introduction, Implementation, Security Analysis and Conclusion; PDF supplied with the submission |

Real Linux terminal tests verify echo is off, CRUD persists across CLI
processes, and Ctrl+C preserves the vault and releases the command.
Separate-container volume persistence also passed. No existing user vault
or Docker volume was used for verification.

See PREPARED_VALIDATION.md, docker-test-results.txt and persistence-results.txt
for evidence. PROGRESS.md and security-test-results.txt describe older work.

## Before submission

- [ ] Review the code and report.
- [ ] Check that the submission ZIP contains the current source and report.
- [ ] Rehearse the live demonstration with fictional data.
- [ ] Confirm the documented Python memory limitation with the lecturer.

Owned buffers are wiped, but Python cannot guarantee immediate erasure of
every immutable or native copy. This limitation is explained in the report.
The submission and presentation schedule is given in the course brief.
