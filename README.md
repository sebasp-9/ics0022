# Secure Password Manager

ICS0022 Secure Programming, TalTech. Sebastian Parra Pinto.

A terminal app that stores login names and passwords in one encrypted vault.
Each command asks for the master password. Saved passwords are never printed.

## Start with Docker

Install/start Docker Desktop with Linux containers, or Docker Engine with
Compose on Linux. No separate Python installation is needed.

```sh
git clone https://github.com/sebasp-9/ics0022.git
cd ics0022
docker compose build
docker compose run --rm vault init
```

If the project is already downloaded, open its folder and start at build.
Run init once; it refuses to overwrite an existing vault. Choose and confirm
a master password of 12-128 printable characters. Typing stays invisible.
A forgotten master password cannot be recovered.

## Commands

| Command | Purpose |
|---|---|
| `docker compose run --rm vault add "Email"` | Save a login name and password |
| `docker compose run --rm vault list` | List saved titles |
| `docker compose run --rm vault get "Email"` | Show the login name; password stays hidden |
| `docker compose run --rm vault update "Email"` | Change the login name or password; Enter keeps a field |
| `docker compose run --rm vault delete "Email"` | Delete after typing yes |
| `docker compose run --rm vault --help` | Show options, including another vault path |

## Retrieve a password

On a local desktop, get --copy copies the password without printing it.
It waits 20 seconds, then clears the clipboard if it still contains that
password. Ctrl+C clears it sooner; newer copied text is left alone.

For Windows, follow [Python development](#python-development), then use a
separate local vault:

```powershell
.\.venv\Scripts\python.exe -m pwvault init
.\.venv\Scripts\python.exe -m pwvault add "Email"
.\.venv\Scripts\python.exe -m pwvault get "Email" --copy
```

Paste only into a password field. Clipboard history, cloud sync and other
apps can retain copies, so turn history/sync off for real credentials.
Clearing is best effort if the process is killed or the clipboard fails.
Docker has no desktop clipboard; --copy reports a controlled error there.
The local vault and Docker's vault are separate.

## Vault data

The encrypted vault stays in Docker's vault-data volume between commands.
Keep the same project folder name to reuse it. Deleting the volume deletes
the vault. A second concurrent command is refused.

## How it works

Argon2id derives a key from the master password and random salt. AES-256-GCM
encrypts the entire vault and detects changes. Updates use a private
temporary file before replacing the vault. Linux file checks enforce OS-user
ownership and private permissions. Logs record operations, not saved fields.

The main flow is cli.py -> users.py -> crypto.py/storage.py. Details are in
[the design](docs/DESIGN.md) and [the report](docs/REPORT.md).

## Tests and requirements

```sh
docker compose run --rm --entrypoint python vault -m unittest discover -s tests -v
docker compose run --rm --user 0 --entrypoint python vault -m unittest discover -s tests -v
```

Linux results: 58 passed with one root-only skip; all 59 passed as root.
Root is only for the ownership test, not normal vault commands. Tests use
fictional data. See [tests, results and remaining work](docs/TESTS.md).

Python cannot guarantee erasure of every secret copy. Owned buffers are
wiped, but immutable/native copies remain a documented memory-handling limit.

## Python development

With Python 3.12 or newer, run from the project folder on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pwvault --help
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On Linux/macOS, use python3 to create the environment and .venv/bin/python
afterward. Native Python uses the home .pwvault directory, separate from
Docker's volume. Windows skips Linux-specific tests.

## AI tools

AI tools were used for requirements review, code, automated tests and
documentation. I ran the manual demo and checked the password-manager flow.
