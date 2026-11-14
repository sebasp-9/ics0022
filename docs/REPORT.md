# Secure Password Manager

Sebastian Parra Pinto
ICS0022 Secure Programming
TalTech School of Information Technologies
Lecturer Ali Ghasempour
Tallinn 2026
Course project report

# 1 Introduction

This project implements an offline command-line password manager. Its purpose is to store login names and passwords securely, require a master password before access, and prevent unsafe input or file access. It applies the course topics of cryptography, validation, file handling, access control, memory handling and secure errors. The required report structure and project scope come from the supplied project instructions [1].

The application supports creating a vault and adding, listing, viewing, updating and deleting saved logins. Password input is hidden. The view command prints the title and login name but never the saved password. Optional get --copy retrieves a password through the local desktop clipboard. There is no cleartext-display command, network service, browser interface, synchronization or account recovery.

Docker/Linux is the storage and ownership test environment. Clipboard retrieval runs on a local desktop and was checked on Windows. One OS user owns the vault and its records. Threats include a stolen or modified vault, malformed input, another OS user, path redirection and interrupted operations. Root, a compromised OS, keyloggers and malicious owner processes remain outside the protection model.

The Checkpoint 3 prototype includes encrypted record operations, clipboard retrieval, validation, structured logging, ownership checks and a passing test suite. Python cannot guarantee immediate erasure of every secret copy. This memory-handling limitation is documented explicitly rather than claimed as solved.

# 2 Implementation

The application uses Python 3.12 with pinned argon2-cffi, cryptography and pyperclip dependencies. Each command authenticates, performs one operation and exits. The modules keep the security boundaries small enough to review.

## 2.1 Program flow

The installed entry point first enables Linux process protections. It then parses the command, checks the vault directory and holds an OS file lock. The lock prevents a second cooperating command from reading an old vault and overwriting newer changes. It covers input prompts as well as saving and is released on normal exit, exceptions and process termination.

The CLI delegates validation and vault operations to users.py. The crypto.py module derives keys and authenticates encrypted data. The storage.py module handles ownership, permissions, file reads and replacement. The audit.py module records fixed event metadata. The memory.py module cleans owned buffers and enables process protections. The locking.py module serializes commands using a stable private lock file.

clipboard.py implements optional retrieval through pyperclip [6]. After authentication, get --copy copies the password without printing it, waits 20 seconds and clears matching clipboard text. Ctrl+C also runs cleanup; newer copied text is preserved. Missing backends and cleanup failures produce controlled errors. Docker has no desktop clipboard; this feature runs locally.

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

The Docker image built successfully. The suite ran 59 tests as the normal non-root user: 58 passed and the root-only ownership case was skipped. Running as root passed all 59, including child processes with UIDs 10001 and 10002. Windows passed 48 and skipped 11 platform-specific cases. Exact output is in docs/test-results/.

| Area | Verified behavior |
|---|---|
| Encryption | Round trip, no literal saved secret in ciphertext, fresh nonces, rejection of modified header, ciphertext and tag |
| Authentication | Wrong passwords rejected on every existing-vault command without changing the vault |
| Validation | Length boundaries, Unicode, wrong types, control characters, invalid schemas and duplicate JSON names |
| File policy | Private permissions, link rejection, unsafe ancestors, directory replacement and refusal of another OS user's access |
| Failure paths | Failed save preserves the vault; temporary files removed; log/KDF errors produce controlled messages |
| Memory and locking | Owned-buffer cleanup on success/failure/cancellation; Linux process controls; a second command cannot enter while locked |
| Actual terminal | Password echo disabled; full CRUD flow across CLI processes; Ctrl+C preserves the vault and releases the command |
| Clipboard | Authentication required; no secret output/logging; timeout and cancellation cleanup; newer contents preserved; controlled backend failures |

Linux pseudo-terminal tests run the actual CLI without mocking getpass. A separate disposable Docker volume verified cross-container persistence, encrypted contents and mode 0600. Existing user data was not used.

A temporary-vault check used the real Windows clipboard and full 20-second wait. Timeout and Ctrl+C cleared the password; vault bytes were unchanged and output/logs contained no secrets. Master-password input was fictional; Linux terminal tests cover hidden prompts.

## 3.2 Findings and corrections

Tests found unsuitable master-password values, duplicate JSON names and a Linux temporary-file cleanup error after rename. These were corrected and the Linux suites rerun.

An additional dependency scan reported three unique advisories for cryptography 48.0.1, affecting certificate and PKCS7 features unused by this app. The pin was updated to 50.0.2. The six checked public runtime packages, including pyperclip, then had no reported known vulnerabilities. TESTS.md records the scope and results.

## 3.3 Residual risks and requirement coverage

Encrypted storage, authentication, validation, hidden output, events and OS-user ownership are tested. Owned buffers are wiped, but Python/native copies may remain; immediate erasure is not guaranteed.

Clipboard retrieval never prints passwords. History/sync and other apps may retain them; forced termination can prevent cleanup. Section 2.2 explains Argon2id/AES-GCM authentication without a separate hash verifier.

Older valid vaults can be restored undetected. Deletion does not erase backups or old disk blocks. There is no forgotten-password recovery, automatic log rotation or sharing. Keep protected backups.

One Docker UID is one identity. Tests use local Linux filesystems; network filesystems may differ.

# 4 Conclusion

The project provides a working encrypted CLI with tested authentication, validation, file ownership, structured logging and controlled failure paths. It can be built from the supplied source using Docker. The final verification includes real hidden prompts, interruption handling, cross-process use, persistence across containers and two OS-user identities.

The main technical lesson is that each boundary needs its own control and evidence. Encryption authenticates vault bytes, permissions restrict local users, directory handles bind operations to opened objects, and cleanup must run on failure as well as success. Platform-specific tests found an issue that the original Windows suite could not expose.

The most important design challenge is the tension between simple Python code and strict secret-memory erasure. The current project implements practical cleanup and process protections while documenting the remaining limit. It is suitable for demonstrating and explaining the tested prototype controls; the literal immediate-wiping claim requires further native-memory work or explicit acceptance of the managed-language limitation.

## 4.1 AI tools

AI tools were used for requirements review, code, automated tests and documentation. I ran the manual demo and checked the password-manager flow. TESTS.md contains the checks and remaining work.

# References

[1] Ali Ghasempour. ICS0022 Secure Programming Project Instructions, autumn 2026/2027. Supplied course PDF, sections 1.3, 4.2 and 4.4.3. Supplemented by the supplied Checkpoint 3 checklist and ICS0022 lecture collection: S02, S03, S04, S07, S08 and S09. Source-local lecture IDs refer to the supplied course master PDF.

[2] argon2-cffi. API Reference, version 25.1.0. https://argon2-cffi.readthedocs.io/en/stable/api.html.

[3] Python Cryptographic Authority. Authenticated encryption documentation. https://cryptography.io/en/stable/hazmat/primitives/aead/.

[4] Linux man-pages. PR_SET_DUMPABLE. https://man7.org/linux/man-pages/man2/PR_SET_DUMPABLE.2const.html.

[5] TalTech School of Information Technologies. Guidelines for writing and formatting a thesis, 2025 edition. Formatting principles adapted for this course report; thesis-only declarations and publication licences are not asserted. https://haldus.taltech.ee/sites/default/files/2025-08/School%20of%20IT_Guidelines%20for%20writing%20and%20formatting%20a%20thesis.pdf.

[6] Al Sweigart. Pyperclip 1.11.0, desktop clipboard copy and paste library. https://pypi.org/project/pyperclip/.
