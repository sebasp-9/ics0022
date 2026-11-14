# Course references

The project follows the password-manager option in Projects.pdf, chapter 4.
Section 1.3 defines the report structure. Checkpoint 3.md contains the
checkpoint checklist. The course materials are stored in the parent folder.

## Source map

| Stable source | Original material | Pages | Connection to this project |
|---|---|---:|---|
| S01 | Introduction to Secure Programming | 24 | Scope, input boundaries, security requirements and lifecycle |
| S02 | Key Concepts in Secure Programming | 43 | Threat model, fail-safe defaults, complete mediation, least privilege |
| S03 | Week 3 - Secure file_io | 64 | Ownership, permissions, links, atomic creation and TOCTOU |
| S04 | Week 4 - Strings and Input validation | 41 | Length boundaries, encodings, validation and safe text handling |
| S05 | Integer Security | 51 | Bounds before allocation or conversion; bounded file/KDF parsing |
| S06 | Week 6 - In-Depth Study of Buffer Overflows and Their Mitigation | 42 | Object lifetimes and bounds; runtime protections do not repair unsafe code |
| S07 | Week 7 - Formated_output_new | 48 | Keep user text as data rather than a format or interpreter input |
| S08 | Week 9 - Error Handling | 52 | Controlled failures, cleanup and generic output |
| S09 | W11-ICS0022-Secure Coding in Multi-User Systems - Protecting Secret Information | 138 | AEAD, password KDFs, identity, access checks and secret lifecycle |
| S10 | Secure Coding in Multi-User Systems - Protecting Secret Information | 125 | Overlapping companion; not an additional independent policy source |
| R01 | Week 4 - Rehim, Python Penetration Testing Cookbook excerpt | 16 | Historical format-string lab; not production implementation guidance |
| R02 | Week 5 - Multiple RTOS (Update E), CISA | 17 | Allocator integer failures and their consequences |
| R03 | Week 6 - gdb-tutorial-handout | 21 | Debugging hypotheses, state inspection and reproducibility |

## Main references

- S02: fail-safe defaults, least privilege and complete mediation.
- S03: file ownership, permissions, links and filesystem races.
- S04: validation, length boundaries and character encoding.
- S07: keep untrusted text separate from formatting instructions.
- S08: controlled exceptions, resource cleanup and generic errors.
- S09: password derivation, authenticated encryption and access checks.

The master PDF preserves the original slides. Source-local references such
as S03:054 identify original pages. The companion text includes corrections
to some examples; image-based code should be checked against the original.
The two secrets decks overlap, and later course weeks were not yet supplied.

## Relation to the web project

Both projects store saved credentials. The web application has server
accounts, sessions and row ownership. This CLI authenticates an encrypted
vault and uses local OS-user permissions. Browser-specific controls such
as CSRF protection do not apply to the offline CLI.
