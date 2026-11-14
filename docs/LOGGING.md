# Safe event logging

Each command appends JSON lines to `audit.jsonl` beside the vault. For the
default Docker vault this is `/home/app/.pwvault/audit.jsonl`, kept in the
same volume. The log is not encrypted: it contains metadata only.

Fields: UTC timestamp, event, OS user, operation, source (`local-terminal`)
and outcome. It records command attempts/results and authentication results.
Delete cancellation is recorded as `cancelled`, not a successful deletion.
Titles, saved login names, passwords, keys, vault paths and exception text
are never passed to the log writer. Only known event names are accepted.

The log must be a private, singly linked regular file. On POSIX it must
belong to the current user and have no group/other permissions. The parent
directory is checked too. Windows uses inherited directory ACLs; Docker/Linux
is the intended environment for OS-user isolation.

If the attempt cannot be written and flushed, the command stops before
asking for the password or changing the vault. If logging fails after a
save, the command reports an error but the save may already be complete.
Check the vault before retrying. An `attempt` without a final result is an
incomplete audit record; it does not mean the operation failed.

The log is not tamper-proof against its owner or root. It grows until its
owner archives it; log rotation is not implemented. Invalid command syntax
is rejected before choosing a vault/log location. Failures that prevent
opening any trusted log are reported generically, not written elsewhere.
