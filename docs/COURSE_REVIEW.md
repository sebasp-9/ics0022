# Course materials and implementation context

Reviewed 14 November 2026 against repository baseline `dad3ae4`.
Local course files are outside this Git repository, in its parent folder.
The authoritative assignment is `../Projects.pdf`, with the extracted
checklist in `../Checkpoint 3.md`. This project is the password-manager
option (chapter 4); the file-manager requirements in chapter 3 are a
different option.

## Available materials

Inventoried both course-material folders and extracted text from all 13
original slide/reading PDFs. The originals contain 682 pages in total.
The master PDF contains 711 pages including its editorial guide. Read the
AI context's guide and correction register, checked relevant original
source pages and visually checked the checkpoint checklist and master
string-validation guide. This was not a visual audit of every original
diagram or a verification of every external link or historical claim.
Image-based code should be checked against its original before reuse.

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

`../united_slides/ICS0022_AI_Context_v1.0.md` contains the editorial guide
and 557 source-page records, excluding the overlapping S10 transcript.
`../united_slides/ICS0022_Secure_Programming_Master_v1.0.pdf` preserves all
682 original pages. The guide mentions an archive and per-source transcripts
that are not present in this workspace. Later teaching weeks have not yet
been supplied; the reference itself marks the course as in progress.

## References used for this increment

- **S01:017; S04:026-028,037-041:** validate type, size and text at the
  boundary; test the largest accepted and first rejected values. Python
  character counts and encoded byte counts are different. Printable Unicode
  is accepted; no stripping or silent password normalization is performed.
- **S07:045-048:** shell syntax and format placeholders are safe only while
  treated as data. Tests preserve them literally; no shell/eval/format
  interpreter was added.
- **S08:016-021,031-034,047:** controlled exceptions, cleanup and generic
  user errors. Tests check failed replacement cleanup and output redaction.
- **S09:055-063:** salt/KDF/password principles. Existing Argon2id settings
  are retained; untrusted file-supplied costs are rejected before work starts.
- **S03:053-059,063; S09:096,104:** ownership and complete mediation remain
  a separate access-control audit, rather than being declared complete by
  authentication tests. The guide's C12-C15 corrections explain why path
  normalization or shortening a race window is insufficient.

The course's C/C++ examples do not imply that Python provides guaranteed
secret erasure. The project's immutable strings, JSON and crypto-library
copies need explicit treatment in the remaining memory-handling work.

## Comparison with Web Application Security

Read the sibling ICS0027 checkout's README, progress/checkpoint notes and
security tests through `764f562`. Both projects store saved credentials,
but their trust boundaries differ. ICS0027 authenticates application users
and checks row ownership on a server. ICS0022 authenticates a whole vault
and currently relies on local OS-user file permissions plus the master key.
The portable lesson is a repeatable negative test suite and honest evidence,
not copying web-only defenses or claiming Docker UID isolation per person.
