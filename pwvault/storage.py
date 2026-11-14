"""Read private vault files and save encrypted bytes with atomic replacement."""
import os
from contextlib import contextmanager
from pathlib import Path
import secrets
import stat
import tempfile

from .crypto import MAX_FILE_SIZE
from .errors import VaultError


def vault_path(value):
    text = str(value)
    if not text or len(text) > 4096 or any(not char.isprintable() for char in text):
        raise VaultError("Enter a valid vault file path.")
    path = Path(text).expanduser().absolute()
    if not path.name or ".." in path.parts:
        raise VaultError("The vault path must name a file.")
    return path


def check_parent(path, create=False):
    parent = path.parent
    if create:
        # Only the default vault directory is automatically created.
        parent.mkdir(mode=0o700, exist_ok=True)
    if parent.is_symlink() or not parent.is_dir():
        raise VaultError("The vault directory must exist and must not be a symbolic link.")
    # Check every component, including junctions/reparse points on Windows.
    for component in (parent, *parent.parents):
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or (
                getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
            raise VaultError("The vault directory path must not contain links.", 3)
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
    if os.name == "posix":
        return read_posix(path)
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
    if os.name == "posix":
        return write_posix(path, data, new)
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


@contextmanager
def parent_descriptor(path):
    """Walk from root without following links; keep the opened directory."""
    path = vault_path(path)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(path.anchor, flags)
    try:
        # Ancestors may belong to root or this user. Root-owned sticky /tmp
        # is allowed; other shared writable ancestors are refused.
        for name in path.parent.parts[1:]:
            current = os.fstat(descriptor)
            check_ancestor(current)
            next_descriptor = os.open(name, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        info = os.fstat(descriptor)
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            raise VaultError("The vault directory must belong to you and not be writable by others.", 3)
        yield descriptor
    finally:
        os.close(descriptor)


def check_ancestor(info):
    if info.st_uid not in (0, os.getuid()):
        raise VaultError("The vault directory has an untrusted ancestor.", 3)
    shared = info.st_mode & 0o022
    trusted_temporary = info.st_uid == 0 and info.st_mode & stat.S_ISVTX
    if shared and not trusted_temporary:
        raise VaultError("The vault directory has an unsafe writable ancestor.", 3)


def read_posix(path):
    path = vault_path(path)
    with parent_descriptor(path) as parent:
        check_file(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(descriptor, "rb") as vault:
            check_file(os.fstat(vault.fileno()))
            data = vault.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise VaultError("The vault is too large.", 3)
    return data


def write_posix(path, data, new=False):
    path = vault_path(path)
    with parent_descriptor(path) as parent:
        if not new:
            check_file(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
        temporary = ".pwvault-" + secrets.token_hex(16)
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=parent)
        try:
            with os.fdopen(descriptor, "wb") as vault:
                vault.write(data)
                vault.flush()
                os.fsync(vault.fileno())
            if new:
                os.link(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent,
                        follow_symlinks=False)
                os.unlink(temporary, dir_fd=parent)
            else:
                # Recheck immediately before publishing. All name operations
                # use the same directory descriptor, even if ancestors move.
                check_file(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
                os.replace(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass


def open_audit(path, read_write=False):
    """Return a checked append-only descriptor; caller closes it."""
    flags = (os.O_RDWR if read_write else os.O_WRONLY) | os.O_APPEND | os.O_CREAT
    flags |= getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    if os.name == "posix":
        with parent_descriptor(path) as parent:
            # O_NONBLOCK avoids hanging if a file is replaced by a FIFO.
            descriptor = os.open(path.name, flags | os.O_NONBLOCK, 0o600, dir_fd=parent)
    else:
        check_parent(path)
        if path.exists() or path.is_symlink():
            check_file(path.lstat())
        descriptor = os.open(path, flags, 0o600)
    try:
        check_file(os.fstat(descriptor))
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor
