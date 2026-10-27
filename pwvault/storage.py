"""Read private vault files and save encrypted bytes with atomic replacement."""
import os
from pathlib import Path
import stat
import tempfile

from .crypto import MAX_FILE_SIZE
from .errors import VaultError


def vault_path(value):
    text = str(value)
    if not text or len(text) > 4096 or any(not char.isprintable() for char in text):
        raise VaultError("Enter a valid vault file path.")
    path = Path(text).expanduser().absolute()
    if not path.name:
        raise VaultError("The vault path must name a file.")
    return path


def check_parent(path, create=False):
    parent = path.parent
    if create:
        # Only the default vault directory is automatically created.
        parent.mkdir(mode=0o700, exist_ok=True)
    if parent.is_symlink() or not parent.is_dir():
        raise VaultError("The vault directory must exist and must not be a symbolic link.")
    if os.name == "posix":
        info = parent.stat()
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            raise VaultError("The vault directory must belong to you and not be writable by others.")


def check_file(info):
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise VaultError("The vault must be a regular file, not a link.", 3)
    if os.name == "posix":
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise VaultError("The vault must belong to you with private permissions (chmod 600).", 3)
    elif getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise VaultError("The vault must not be a Windows reparse point.", 3)


def read(path):
    check_parent(path)
    # lstat rejects links before opening; O_NOFOLLOW also closes that race on POSIX.
    check_file(path.lstat())
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as vault:
        check_file(os.fstat(vault.fileno()))
        data = vault.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise VaultError("The vault is too large.", 3)
    return data


def write(path, data, new=False):
    check_parent(path)
    if not new:
        check_file(path.lstat())
    descriptor, temporary = tempfile.mkstemp(prefix=".pwvault-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as vault:
            vault.write(data)
            vault.flush()
            os.fsync(vault.fileno())
        if new:
            # Windows rename refuses an existing target; POSIX link does too.
            if os.name == "nt":
                os.rename(temporary, path)
            else:
                os.link(temporary, path)
        else:
            os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
