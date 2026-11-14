# Dependency review

Checked with pip-audit 2.10.1 against the public Python
runtime package versions collected from the built application image.

The original cryptography 48.0.1 pin had three unique reported advisories:
PYSEC-2026-3552, PYSEC-2026-3553 and PYSEC-2026-3554. The scanner returned
duplicate entries for those IDs. The affected features concern certificate
verification and PKCS7 processing, which this offline AES-GCM vault does not
use. The library was still updated to cryptography 50.0.2 before committing.

The final scan found **no known vulnerabilities in the five checked packages**:
argon2-cffi, argon2-cffi-bindings, cffi, cryptography and pycparser.
Exact versions/results are in dependency-audit.json. The application suites
were rerun after the upgrade; the encrypted vault format is unchanged.

The scan used an isolated disposable container. It did not alter the app
image or install audit tools into the project virtual environment.
It excludes the local project, pip installer and operating-system packages.
A clean advisory scan is not proof that no vulnerabilities exist.

Upstream release notes: https://cryptography.io/en/latest/changelog/
Scanner documentation: https://github.com/pypa/pip-audit
