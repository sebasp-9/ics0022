# Explain the project

## The 30 second explanation

This is an offline password manager. A master password derives a key that
opens one encrypted vault. Every command authenticates again. The program
checks input, file ownership and permissions, then performs one action.
Passwords never appear in output. Events are logged without their contents.

## Read the code in this order

1. **cli.py:** commands, hidden prompts, success/error output. Start at
   `main`, then `logged_command`, `run` and `operate`.
2. **users.py:** allowed field values and the create/open/save operations.
3. **crypto.py:** Argon2id derives the key; AES-GCM encrypts and detects changes.
4. **storage.py:** private files, safe directory handles and temporary saves.
5. **audit.py:** fixed log fields. No saved entry data is accepted by the writer.
6. **locking.py:** lets only one command at a time use a vault directory.
7. **memory.py:** overwrites owned buffers and restricts Linux memory dumps.

Read one function, then find its test. You do not need to memorize the code.

## Words to know

- **Salt:** public random data that makes each vault's key derivation different.
- **Argon2id:** deliberately expensive password-to-key calculation.
- **Nonce:** random encryption input; each save needs a fresh value.
- **Authentication tag:** detects an incorrect key or changed encrypted data.
- **File descriptor:** an OS handle to an opened object, rather than its name.
- **Finally:** cleanup that runs when a Python block finishes or raises an error.
- **OS user:** the local identity owning the vault. This is not a web account.

## A ten minute presentation

1. **One minute:** explain the goal and what is out of scope.
2. **Three minutes:** run init/add/list/get/update/delete with fictional data.
   Show that typing a password stays blank and get keeps it hidden.
3. **Two minutes:** show a wrong-password rejection, the test results and
   an audit event. Use a fresh demo vault, not your personal vault.
4. **Two minutes:** explain the module flow, encryption and safe saving.
5. **Two minutes:** explain ownership, cleanup, limits and the test-discovered
   Linux cleanup bug that was fixed. Leave time for questions.

Docker command prefix: `docker compose run --rm vault`.
For a separate demo vault, append `--vault /home/app/.pwvault/demo.pvz`
before the command, for example:

```sh
docker compose run --rm vault --vault /home/app/.pwvault/demo.pvz init
docker compose run --rm vault --vault /home/app/.pwvault/demo.pvz add "Email"
docker compose run --rm vault --vault /home/app/.pwvault/demo.pvz get "Email"
```

## Likely questions

**Why does a wrong password fail?** It derives the wrong key, so the AES-GCM
authentication tag cannot be verified.

**Why not just hash saved passwords?** You must be able to retrieve saved
credentials internally. Encryption supports that. The master password is
instead used in a slow salted key derivation and is not stored.

**Does AES alone solve access control?** No. The file policy also checks the
OS user and permissions, and every command authenticates before record use.

**Why use an opened directory?** A pathname can change. A handle keeps the
operation attached to the directory that was actually opened.

**Are all secrets wiped from RAM?** No. Owned buffers are overwritten and
Linux dumps are restricted. Python and native libraries can retain copies
that this application cannot reliably overwrite. Say that clearly.

**Can a forgotten password be recovered?** No. There is no recovery key.

**Does delete erase backups?** No. It removes the current record, not old copies.

**Can two people share a Docker volume as separate users?** No. One container
UID is one identity. The isolation test uses two actual OS-user identities.
