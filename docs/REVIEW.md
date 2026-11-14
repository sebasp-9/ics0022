# Review and checks

14 November 2026. AI tools assisted with requirements review, code, automated
tests and documentation. The checks below were run with AI assistance.
They are not presented as tests personally performed by the student.

## Technical checks

- Docker build and full suite as the normal Linux user and as root.
- Hidden input, CRUD, wrong-password rejection and Ctrl+C in actual Linux
  pseudo-terminals, using the CLI rather than mocked password input.
- Saved data reopened in a separate container using a fresh test volume.
- Ciphertext/permissions, private logs and two-OS-user ownership checks.
- Windows tests, dependency consistency and Git whitespace checks.
- Known-advisory scan of five Python runtime packages after updating
  cryptography to 50.0.2; no known vulnerabilities reported (DEPENDENCIES.md).
- Scan of project text for em dashes and en dashes; plain hyphens used.

Exact results are in PREPARED_VALIDATION.md, docker-test-results.txt,
prepared-test-results.txt and persistence-results.txt. Tests use fictional
credentials. They do not open the owner's existing vault.

## Personal checks

The student reported on 14 November 2026 that the complete manual demo
worked. These boxes record that report; personal code/report review is not
claimed. The assistant also ran a separate interactive demo; its evidence
is in interactive-review-results.txt.

- [ ] Read the changes and explain the main functions in your own words.
- [x] Type the Docker demo commands yourself in your own terminal.
- [x] Check that your terminal hides passwords and that get keeps them hidden.
- [x] Add, update and delete a fictional entry; try one wrong master password.
- [x] Close a command and reopen the same demo vault to check persistence.
- [x] Ctrl+C left the demo vault usable, as reported by the student.
- [ ] Read the report and confirm that it matches your understanding.
- [ ] Rehearse the presentation and discuss the Python memory limit with the lecturer.

No pull request was created for these changes. Personal code/report review
and presentation preparation remain unchecked above.

## Limits of this verification

No claim is made for erasure of every Python/native secret copy, physical
memory/swap forensics, every possible filesystem race or a compromised OS.
The OS packages and pip installer were not covered by the Python dependency
scan. Windows has weaker filesystem guarantees than the intended Docker/Linux
environment. A student demonstration and lecturer acceptance of the memory
qualification remain separate from automated test results.
