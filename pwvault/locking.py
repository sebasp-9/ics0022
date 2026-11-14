"""Hold one OS lock while a command reads, prompts and saves."""
from contextlib import contextmanager
import os

from . import storage
from .errors import VaultError


@contextmanager
def exclusive(path):
    # One stable lock file per directory also serializes commands using
    # different vault filenames there. Never unlink an active lock file.
    descriptor = storage.open_audit(path.parent / ".pwvault.lock", read_write=True)
    locked = False
    try:
        try:
            if os.name == "posix":
                import fcntl
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                import msvcrt
                if os.fstat(descriptor).st_size == 0:
                    if os.write(descriptor, b"0") != 1:
                        raise OSError("Cannot initialize lock")
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            locked = True
        except OSError:
            raise VaultError("Another command is using this vault directory. Try again later.") from None
        yield
    finally:
        try:
            if locked:
                if os.name == "posix":
                    import fcntl
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                else:
                    import msvcrt
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        finally:
            os.close(descriptor)
