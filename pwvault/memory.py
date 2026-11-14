"""Best-effort cleanup of buffers we own, not a guarantee for Python copies."""
import sys

from .errors import VaultError


def wipe(buffer):
    """Overwrite a mutable byte buffer in place; aliases see the zeros too."""
    buffer[:] = b"\x00" * len(buffer)


def clear_items(items):
    """Release record references. Immutable strings themselves are not erased."""
    for entry in items.values():
        if isinstance(entry, dict):
            entry.clear()
    items.clear()


def harden_process():
    """Block core dumps and ordinary same-user process inspection on Linux."""
    if sys.platform != "linux":
        return
    import ctypes
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                           ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    if libc.prctl(4, 0, 0, 0, 0) != 0:  # Linux PR_SET_DUMPABLE = 4.
        raise VaultError("Cannot enable process memory protections.", 3)
