# Secure Password Manager

Course project for **ICS0022 Secure Programming** (TalTech).

Author: Sebastian Parra Pinto

A command line application for storing the logins a user has on other websites. The user
protects the vault with a master password, and the whole vault is encrypted before it is
written to disk. The file only contains a salt, a nonce and encrypted data, so a stolen
copy of it does not reveal any passwords.

This is the local counterpart of the web application built for ICS0027. The full design
(architecture, cryptography and threat model) is in [`docs/DESIGN.md`](docs/DESIGN.md).

## Scope

**Features**
- Creating a vault and setting a master password
- Items: create, view, edit and delete saved logins (title, login name, password)
- The whole vault encrypted with AES-256-GCM, using a key derived from the master password
  with Argon2id
- A generator for strong random passwords
- Changing the master password
- Copying a password to the clipboard, which is cleared after a short timeout

**Not included:** sharing, password history, sync between machines, browser integration and
account recovery. A forgotten master password cannot be recovered, because the vault key is
derived from it.

## Planned commands

| Command | Purpose |
|---|---|
| `pwvault init` | Create a vault and set the master password |
| `pwvault add TITLE` | Add an item, asks for the password |
| `pwvault get TITLE` | View one item, with `--clip` or `--show` |
| `pwvault list` | List the item titles, never the passwords |
| `pwvault update TITLE` | Edit an item |
| `pwvault delete TITLE` | Delete an item |
| `pwvault generate` | Make a strong random password, with `--length` |
| `pwvault change-master` | Change the master password |
| `pwvault info` | Vault path, number of items, Argon2 settings |

`--vault PATH` uses a vault file other than `~/.pwvault/vault.pvz`.

Exit codes: `0` success, `1` bad input, `2` wrong master password, `3` vault missing or
modified, `4` no such item.

The master password is never accepted as a command argument or an environment variable,
because anything on the command line is visible in `ps` and is written to the shell
history. It is only ever typed at a prompt with echo turned off.

## Running locally (planned)

The code is added in Checkpoint 2. From then on, the application will be started with these
steps. It will need Python 3.12 or newer, on Linux or macOS.

1. Clone the repository and create a virtual environment: `python -m venv .venv`
2. Activate it: `source .venv/bin/activate`
3. Install the libraries: `pip install -r requirements.txt`
4. Install the application: `pip install -e .`
5. Create a vault: `pwvault init`
6. Run a command, for example `pwvault list`, or `python -m pwvault --help` without
   installing

The vault file and its directory are created with permissions that only allow the owner to
read them, and the application refuses to open a vault whose permissions are wider than
that.

## Status

| Checkpoint | Status |
|---|---|
| 1: Design document and repository with README | Done |
| 2: Key derivation, encryption, storage, and the first commands | Planned |
| 3: Remaining commands, changing the master password, tests | Planned |
