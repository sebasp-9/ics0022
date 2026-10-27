# Checkpoint 2 progress

| Requirement | Implementation |
|---|---|
| Basic vault storage | One encrypted file; init/add/list/get/update/delete commands |
| Credentials encrypted at rest | Whole-vault AES-256-GCM, Argon2id key derivation, fresh nonce per save |
| Master-password authentication | Vault data is used only after successful authentication-tag verification |
| Interface never prints passwords | Hidden password prompts; get displays only title and login name |
| Clean-machine instructions | Dockerfile, Compose file and Docker-only README |

**Validation:** the Docker image built successfully, command help ran inside the
container, and all 31 CLI checks passed inside the Linux container. Checks
covered encryption, incorrect passwords, tampering, fresh nonces, failed saves,
hidden password output and private file/directory permissions. Password input
was simulated in the automated checks. Installation/package build and Docker
configuration checks also passed.

**Scope:** password generation, clipboard retrieval and master-password changes
remain for checkpoint 3. Use one vault command at a time.

**History:** checkpoint 1 is preserved, with checkpoint 2 recorded as a separate
implementation commit.
