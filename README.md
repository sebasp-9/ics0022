# Secure Password Manager

ICS0022 Secure Programming, TalTech. Sebastian Parra Pinto.

A terminal app that stores login names and passwords in one encrypted file
(the vault). Each command asks for the master password. Passwords are never printed.

## Run with Docker

Install and start **Docker Desktop** (Windows/macOS), or **Docker Engine with
Compose** (Linux). Use Linux containers. No Python installation is needed.

Download, build and create your vault:

```sh
git clone https://github.com/sebasp-9/ics0022.git
cd ics0022
docker compose build
docker compose run --rm vault init
```

If you already have the project, open its folder and run the build command.
Run `init` only to create a new vault; it refuses to overwrite an existing one.

Choose and confirm a master password of 12–128 printable characters.
Password prompts stay blank while you type. A forgotten master password cannot
be recovered.

## Commands

| Command | Purpose |
|---|---|
| `docker compose run --rm vault add "Email"` | Save a login name and password |
| `docker compose run --rm vault list` | List saved titles |
| `docker compose run --rm vault get "Email"` | Show the login name; password stays hidden |
| `docker compose run --rm vault update "Email"` | Change the login name or password |
| `docker compose run --rm vault delete "Email"` | Delete after typing `yes` to confirm |
| `docker compose run --rm vault --help` | Show help |

For updates, press Enter to keep a field unchanged. There is no password reveal
option or clipboard retrieval.

Docker removes each container after the command, but keeps the encrypted vault
in the `vault-data` volume. Keep the same project folder name to reuse it.
Deleting that volume deletes the vault. Run one command at a time.

## How it works

1. You enter the master password through a hidden terminal prompt.
2. Argon2id derives an encryption key from that password and a random salt.
   The master password is not stored.
3. AES-256-GCM decrypts the vault and checks its integrity. A wrong password
   or changed encrypted data stops the command before any entries are used.
4. Changes are encrypted with a fresh nonce (an encryption input), written to
   a temporary file, then replace the old vault.

Titles, login names and passwords are all encrypted. On Linux, the app also
checks file ownership and private permissions. Python cannot guarantee erasure
of passwords or keys from memory; memory handling still needs work.

The code follows the same flow: `cli.py` handles commands and prompts,
`users.py` validates fields and coordinates operations, `crypto.py` handles
encryption, and `storage.py` reads and writes the file. These are in `pwvault/`.

## Progress

Checkpoint 2 added the basic commands and encrypted storage. Its Docker build
and 31 CLI checks passed; see the [checkpoint 2 note](docs/PROGRESS.md).

Checkpoint 3 is **in progress**: validation fixes and automated tests are in
place, with 20 tests passed and one POSIX test skipped on Windows. The updated
Docker image still needs verification because the engine was unavailable.
Logging, memory handling, access-control hardening and the report remain.
Password generation, clipboard support and master-password changes are also
planned, but are not explicit checkpoint 3 requirements.

See [checkpoint 3 results and next steps](docs/CHECKPOINT3.md) and
[the design and threat model](docs/DESIGN.md). For submission, include the source,
Dockerfile, Compose file and documentation.

## Run the tests

Run the tests after rebuilding the Docker image:

```sh
docker compose build
docker compose run --rm --entrypoint python vault -m unittest discover -s tests -v
```

Tests use disposable vaults and fictional passwords. They do not open your
normal vault. Password prompts are simulated; real terminal behavior still
needs a manual check. The POSIX permissions test runs on Linux and is skipped
on Windows.

For development without Docker, install Python 3.12 or newer, then run from
the project directory on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On Linux/macOS, use `python3` for the first command and `.venv/bin/python`
for the last two commands.
