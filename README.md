# Secure Password Manager

Course project for **ICS0022 Secure Programming** (TalTech).
Author: Sebastian Parra Pinto.

A terminal application that stores login names and passwords in one encrypted
vault. Each command requires the master password. Passwords are never printed.

## Run with Docker

Install and start **Docker Desktop** (Windows/macOS), or **Docker Engine with
Compose** (Linux). Use Linux containers. No Python installation is needed.

Download and build the project:

```sh
git clone https://github.com/sebasp-9/ics0022.git
cd ics0022
docker compose build
```

If you already have the project, open a terminal in its folder and run only
the build command.

Create a vault once:

```sh
docker compose run --rm vault init
```

Choose a master password of 12–128 characters and confirm it. Password prompts
stay blank while you type. A forgotten master password cannot be recovered.

## Commands

| Command | Purpose |
|---|---|
| `docker compose run --rm vault add "Email"` | Save a login name and password |
| `docker compose run --rm vault list` | List saved titles |
| `docker compose run --rm vault get "Email"` | Show the login name; password stays hidden |
| `docker compose run --rm vault update "Email"` | Change the login name or password |
| `docker compose run --rm vault delete "Email"` | Delete after typing `yes` to confirm |
| `docker compose run --rm vault --help` | Show help |

For updates, press Enter to keep a field unchanged. There is no `--show` option
or clipboard retrieval in checkpoint 2.

Docker removes each container after the command, but keeps the encrypted vault
in the `vault-data` volume. Keep the same project folder name to reuse it.
Deleting that volume deletes the vault. Run one command at a time.

## Checkpoint 2

- **Storage and encryption:** the whole vault uses AES-256-GCM, with an
  Argon2id key derived from the master password and a fresh nonce per save.
- **Authentication:** wrong passwords or modified ciphertext fail verification
  before any saved items are used.
- **Interface:** passwords use hidden prompts and never appear in output.
- **Submission:** include the source, Dockerfile, Compose file and
  [progress note](docs/PROGRESS.md).

The Docker image built successfully, and all 31 CLI checks passed inside the
Linux container, including encryption, authentication and file permissions.

Password generation, clipboard support and master-password changes remain
planned for checkpoint 3. Further details are in [the design](docs/DESIGN.md).
