# File access in plain language

One OS user owns one vault. Every CLI read or change unlocks that whole
vault first. There are no separately shared records or application accounts.
Linux file permissions and the master password protect all records together.

On Linux, file operations now open the directory and keep its handle.
Reads, temporary-file creation and replacement use that same handle. If a
directory's old path is moved or replaced, the operation stays attached to
the opened directory. Ancestor components are opened without following links.

The immediate directory must belong to this user and not be writable by
others. Ancestors must belong to root or this user and not be group/other
writable, except root-owned sticky temporary directories such as `/tmp`.
The vault must be a singly linked regular file, owned by this user, with no
group/other permissions. Reads check the opened file too. Relative `..`
components, symlinked ancestors and Windows reparse points are rejected.
Titles are dictionary keys, never file paths or shell commands.

This deliberately refuses some shared, symlinked or mounted directory layouts.
Use the default private Docker directory, or another real private directory.
A private stable .pwvault.lock file now serializes CLI commands, including
prompts. A second command is refused; locks are released after errors or
process exit. Do not manually remove the lock file while a command runs. Processes already running as the same OS user,
and root, remain trusted. These checks do not defend against a compromised OS.

Windows rejects detected links/reparse points but uses inherited ACLs and
does not have the Linux directory-handle implementation. Use Docker/Linux
for the intended multi-user file-policy demonstration. A shared Docker volume
under one container UID is one identity, not a separate account per person.

## Check on Linux/Docker

Run the normal suite after rebuilding. Then run this extra test in the
container as root; it creates only temporary test files and uses two child
process UIDs, not real accounts:

```sh
docker compose run --rm --user 0 --entrypoint python vault -m unittest discover -s tests -p test_storage.py -v
```

These Linux checks passed on 14 November 2026 in Docker. The full suite
also passed as root, including the two-UID test. Exact commands and output
are saved in docker-test-results.txt. Containers used only temporary files;
no real saved-vault volume was mounted.
