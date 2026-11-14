"""One JSON event per line. Only fixed event fields reach this log."""
from contextlib import contextmanager
from datetime import datetime, timezone
import getpass
import json
import os

from . import storage

OPERATIONS = {"init", "list", "get", "add", "update", "delete"}
OUTCOMES = {"attempt", "success", "failure", "cancelled"}


@contextmanager
def open_log(vault_path, create_parent=False):
    storage.check_parent(vault_path, create=create_parent)
    path = vault_path.parent / "audit.jsonl"
    descriptor = storage.open_audit(path)
    try:
        storage.check_file(os.fstat(descriptor))
        yield descriptor
    finally:
        os.close(descriptor)


def record(descriptor, operation, outcome, event="command"):
    if operation not in OPERATIONS or outcome not in OUTCOMES:
        raise ValueError("Unsupported audit event")
    if event not in {"command", "authentication"}:
        raise ValueError("Unsupported audit event")
    # The OS identity identifies the local user, never a saved login name.
    identity = str(os.getuid()) if os.name == "posix" else getpass.getuser()
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
             "event": event, "user": identity, "operation": operation,
             "source": "local-terminal", "outcome": outcome}
    data = (json.dumps(entry, ensure_ascii=True) + "\n").encode("utf-8")
    if os.write(descriptor, data) != len(data):
        raise OSError("Incomplete audit write")
    os.fsync(descriptor)
