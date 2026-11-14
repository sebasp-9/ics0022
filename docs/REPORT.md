# Secure Password Manager

Sebastian Parra Pinto
ICS0022 Secure Programming
TalTech School of Information Technologies
Lecturer Ali Ghasempour
Tallinn 2026
Technical report prepared 14 November 2026

# 1 Introduction

This project implements an offline command-line password manager. Its purpose is to store login names and passwords securely, require a master password before access, and prevent unsafe input or file access. It applies the course topics of cryptography, validation, file handling, access control, memory handling and secure errors. The required report structure and project scope come from the supplied project instructions [1].

The application supports creating a vault and adding, listing, viewing, updating and deleting saved logins. Password input is hidden. The view command prints the title and login name but never the saved password. There is no password-reveal command, network service, browser interface, synchronization or account recovery.

The intended environment is Docker with Linux containers. One OS user owns the vault and all its records. The threat model includes a stolen or modified vault file, malformed input, another OS user, path redirection and interrupted operations. Root, a compromised operating system, keyloggers and malicious processes already running as the vault owner remain outside the protection model.

The implementation and test evidence are complete for the stated prototype scope. A literal guarantee that every secret copy is immediately erased is not achieved by the current Python design. This limitation is analyzed explicitly rather than described as a completed requirement.

# 2 Implementation

The application uses Python 3.12 with pinned argon2-cffi and cryptography dependencies. Commands are short-lived: each command authenticates, performs one operation and exits. The modules keep the security boundaries small enough to review.

## 2.1 Program flow

The installed entry point first enables Linux process protections. It then parses the command, checks the vault directory and holds an OS file lock. The lock prevents a second cooperating command from reading an old vault and overwriting newer changes. It covers input prompts as well as saving and is released on normal exit, exceptions and process termination.

The CLI delegates validation and vault operations to users.py. The crypto.py module derives keys and authenticates encrypted data. The storage.py module handles ownership, permissions, file reads and replacement. The audit.py module records fixed event metadata. The memory.py module cleans owned buffers and enables process protections. The locking.py module serializes commands using a stable private lock file.

## 2.2 Authentication and encrypted storage

Argon2id derives a 256-bit key from the master password and a random 16-byte salt. Its parameters are 64 MiB memory, three iterations and parallelism four. The implementation retains the established library and project parameters [2]. A stolen vault still allows offline guessing, so the master password must be strong.

AES-256-GCM encrypts the complete JSON vault, including titles, login names and passwords. Every save uses a fresh random 12-byte nonce. The header is supplied as authenticated associated data. Decryption verifies the authentication tag before the program parses or displays records [3].

The master password is not stored. AES-GCM tag verification authenticates the derived key and vault. Wrong passwords and changed ciphertext share one error. Unlike a server, this offline vault has no separate password verifier; the report records this choice against the brief's hashing requirement.

The file starts with a 41-byte header containing magic bytes, a format version, KDF parameters, salt and nonce. Encrypted JSON and a 16-byte tag follow. Unsupported parameters are rejected before key derivation, and vault files are limited to 2 MiB. The format remains compatible with the checkpoint 2 implementation.

## 2.3 Validation and file access

Titles allow 1-100 printable Python characters. Saved login names and passwords allow 1-200. New master passwords allow 12-128 printable characters. Inputs are checked for type, length and text validity. Existing supported master passwords remain usable for unlocking. Passwords are not stripped, truncated or normalized silently.

Decrypted records must have the expected structure. Duplicate JSON names are rejected instead of silently keeping the last value. Shell text and formatting placeholders remain ordinary data: the program does not execute user text. Titles are dictionary keys and never become filenames. Vault paths reject control characters and parent traversal components.

On Linux, the program walks directories without following symbolic links and retains the opened parent directory handle. Reads and writes use that handle, so replacing an ancestor pathname cannot redirect the operation. The vault must be a singly linked regular file belonging to the current OS user, with no group or other permissions. The immediate directory must belong to that user and not be writable by others. Unsafe ancestors are refused; root-owned sticky temporary directories are allowed.

Updates write encrypted bytes to a private temporary file, flush and synchronize it, then replace the vault. Initialization publishes a new file without replacing an existing target. Failed replacement preserves the old vault and removes the temporary file. Windows detects links and reparse points but relies on inherited ACLs and has weaker race guarantees; Linux is the intended ownership demonstration environment.

## 2.4 Events and errors

The private audit.jsonl file records a UTC timestamp, event, OS user, operation, local source and outcome. Command attempts, results, authentication failures and cancellations are recorded. The log writer accepts a fixed set of operations and outcomes. Saved fields, passwords, keys, vault paths and raw exception text are not passed to it.

The first event must be written and synchronized before the operation begins. If a final log write fails after a save, the save may already be complete. The application reports an error, and the unmatched attempt must be checked before retrying. Expected storage, authentication and key-derivation failures use controlled messages rather than tracebacks. The owner can alter the log; it is not a tamper-proof audit service.

## 2.5 Memory handling

Derived keys and serialized plaintext are held in owned bytearray buffers and overwritten in place when finished. Cleanup runs on authentication failure, invalid data, normal completion, cancellation and later logging failures. Record dictionaries are cleared, and master-password references are released as soon as practical. Tests retain aliases to check that owned buffers contain zeros after cleanup.

On Linux, the real entry points also disable core dumps and mark the process non-dumpable before reading secrets. Linux uses that setting to restrict core dumping and ordinary process attachment [4]. Failure to enable the required protections stops the command before password input.

Python input, JSON encoding and cryptographic bindings can create immutable strings, bytes or native copies that the application cannot reliably overwrite. Clearing a dictionary releases references rather than erasing its former strings. The process protections reduce exposure but do not guarantee erasure of those copies or protect against privileged memory acquisition. This is the remaining qualification against the brief's strict immediate-wiping requirement.

# 3 Security analysis

The security review combines positive functional checks with negative cases and injected failures. The standard-library test suite uses fictional credentials and temporary vaults. It exercises the real Argon2id and AES-GCM implementations. Tests that require root run only in disposable Linux containers.

## 3.1 Test results

On 14 November 2026, the final Docker image built successfully. The final suite ran 50 tests as the normal non-root user: 49 passed and the root-only ownership case was skipped. Running the suite as root passed all 50 tests, including child processes with UIDs 10001 and 10002. Windows passed 39 tests and skipped 11 environment-specific cases. Exact output is saved with the source.

| Area | Verified behavior |
|---|---|
| Encryption | Round trip, no literal saved secret in ciphertext, fresh nonces, rejection of modified header, ciphertext and tag |
| Authentication | Wrong passwords rejected on every existing-vault command without changing the vault |
| Validation | Length boundaries, Unicode, wrong types, control characters, invalid schemas and duplicate JSON names |
| File policy | Private permissions, link rejection, unsafe ancestors, directory replacement and refusal of another OS user's access |
| Failure paths | Failed save preserves the vault; temporary files removed; log/KDF errors produce controlled messages |
| Memory and locking | Owned-buffer cleanup on success/failure/cancellation; Linux process controls; a second command cannot enter while locked |
| Actual terminal | Password echo disabled; full CRUD flow across CLI processes; Ctrl+C preserves the vault and releases the command |

The terminal tests use real Linux pseudo-terminals and the actual CLI without mocking getpass. A separate Docker check wrote a fictional entry in a fresh volume and reopened it in a second container. It verified persistence, encrypted contents and mode 0600. Only that newly created verification volume was removed afterward; existing user data was not used.

## 3.2 Findings and corrections

Validation tests found unsuitable master-password values and duplicate JSON names. Both were fixed. Linux testing found a temporary-file cleanup error after rename; it was corrected and the Linux suites were rerun.

The command lock prevents accidental concurrent updates. File ownership is checked at storage access, and encryption authentication happens before record use. Two-UID testing verifies that another OS user cannot read or replace the owner's test vault.

An additional dependency scan reported three unique advisories for cryptography 48.0.1, affecting certificate and PKCS7 features unused by this app. The pin was updated to 50.0.2. The five checked public runtime packages then had no reported known vulnerabilities. DEPENDENCIES.md records the scope and results.

## 3.3 Residual risks and requirement coverage

Encrypted storage, master-password access, validation, hidden output, structured events, ownership checks and the required report sections are implemented and tested. Memory handling includes owned-buffer wiping and Linux process hardening, but complete erasure of immutable or native copies remains unproven. This report does not claim full satisfaction of that literal requirement.

The program does not detect rollback to an older valid vault. Deleting a record removes it from the current encrypted payload; it does not erase backups or guarantee deletion from old filesystem blocks. There is no recovery for a forgotten master password, automatic log rotation or secure sharing. The owner should keep protected backups and archive the metadata log when needed.

A shared Docker volume under one UID represents one OS identity. It must not be presented as a separate vault account for every person using the computer. Filesystem guarantees can also differ on network filesystems; the tested environment is the local Linux filesystem provided by Docker Desktop.

# 4 Conclusion

The project provides a working encrypted CLI with tested authentication, validation, file ownership, structured logging and controlled failure paths. It can be built from the supplied source using Docker. The final verification includes real hidden prompts, interruption handling, cross-process use, persistence across containers and two OS-user identities.

The main technical lesson is that each boundary needs its own control and evidence. Encryption authenticates vault bytes, permissions restrict local users, directory handles bind operations to opened objects, and cleanup must run on failure as well as success. Platform-specific tests found an issue that the original Windows suite could not expose.

The most important design challenge is the tension between simple Python code and strict secret-memory erasure. The current project implements practical cleanup and process protections while documenting the remaining limit. It is suitable for demonstrating and explaining the tested prototype controls; the literal immediate-wiping claim requires further native-memory work or explicit acceptance of the managed-language limitation.

## 4.1 AI tools

AI tools were used for requirements review, code, automated tests and documentation. I ran the terminal demo myself, checking hidden input, saved-login operations, wrong-password rejection, persistence and Ctrl+C. Additional automated and terminal checks were run with AI assistance. REVIEW.md records the checks and remaining limits.

# References

[1] Ali Ghasempour. ICS0022 Secure Programming Project Instructions, autumn 2026/2027. Supplied course PDF, sections 1.3, 4.2 and 4.4.3. Supplemented by the supplied Checkpoint 3 checklist and ICS0022 lecture collection: S02, S03, S04, S07, S08 and S09. The local source map is recorded in COURSE_REVIEW.md.

[2] argon2-cffi. API Reference, version 25.1.0. https://argon2-cffi.readthedocs.io/en/stable/api.html. Accessed 14 November 2026.

[3] Python Cryptographic Authority. Authenticated encryption documentation. https://cryptography.io/en/stable/hazmat/primitives/aead/. Accessed 14 November 2026.

[4] Linux man-pages. PR_SET_DUMPABLE. https://man7.org/linux/man-pages/man2/PR_SET_DUMPABLE.2const.html. Accessed 14 November 2026.

[5] TalTech School of Information Technologies. Guidelines for writing and formatting a thesis, approved 11 August 2025. Formatting principles adapted for this course report; thesis-only declarations and publication licences are not asserted. https://haldus.taltech.ee/sites/default/files/2025-08/School%20of%20IT_Guidelines%20for%20writing%20and%20formatting%20a%20thesis.pdf. Accessed 14 November 2026.
