"""File-policy checks; Linux-only cases are explicitly skipped elsewhere."""
from contextlib import redirect_stdout, redirect_stderr
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pwvault import storage
from pwvault.errors import VaultError


class PathTests(unittest.TestCase):
    def test_parent_traversal_is_rejected(self):
        for path in ("../vault.pvz", "private/../vault.pvz"):
            with self.subTest(path=path), self.assertRaises(VaultError):
                storage.vault_path(path)


@unittest.skipUnless(os.name == "posix", "Requires Linux/POSIX file operations")
class PosixStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.directory = self.root / "private"
        self.directory.mkdir(mode=0o700)
        self.path = self.directory / "vault.pvz"
        storage.write(self.path, b"original", new=True)

    def test_file_and_ancestor_links_are_rejected(self):
        link = self.root / "alias"
        link.symlink_to(self.directory, target_is_directory=True)
        file_link = self.directory / "alias.pvz"
        file_link.symlink_to(self.path)
        for path in (link / "vault.pvz", file_link):
            with self.subTest(path=path):
                for operation in (lambda: storage.read(path), lambda: storage.write(path, b"changed")):
                    with self.assertRaises((VaultError, OSError)):
                        operation()
        self.assertEqual(self.path.read_bytes(), b"original")

    def test_hardlinked_vault_is_rejected(self):
        os.link(self.path, self.directory / "alias.pvz")
        with self.assertRaises(VaultError):
            storage.read(self.path)
        with self.assertRaises(VaultError):
            storage.write(self.path, b"changed")
        self.assertEqual(self.path.read_bytes(), b"original")

    def test_opened_directory_survives_ancestor_replacement(self):
        # Simulate a path rename after a trusted directory handle is opened.
        moved = self.root / "moved"
        with storage.parent_descriptor(self.path) as descriptor:
            self.directory.rename(moved)
            self.directory.mkdir(mode=0o700)
            replacement = self.directory / "vault.pvz"
            replacement.write_bytes(b"unrelated")
            replacement.chmod(0o600)
            with patch("pwvault.storage.parent_descriptor") as parent:
                parent.return_value.__enter__.return_value = descriptor
                storage.write(self.path, b"updated")
        self.assertEqual((moved / "vault.pvz").read_bytes(), b"updated")
        self.assertEqual(replacement.read_bytes(), b"unrelated")

    def test_unsafe_ancestor_is_rejected(self):
        self.root.chmod(0o777)
        try:
            with self.assertRaises(VaultError):
                storage.read(self.path)
        finally:
            self.root.chmod(0o700)

    def test_fifo_is_rejected_without_opening_or_blocking(self):
        fifo = self.directory / "pipe"
        os.mkfifo(fifo, 0o600)
        with patch("pwvault.storage.os.open", wraps=os.open) as opened:
            with self.assertRaises(VaultError):
                storage.read(fifo)
        self.assertFalse(any(call.args[0] == fifo.name for call in opened.call_args_list))


@unittest.skipUnless(os.name == "posix" and getattr(os, "geteuid", lambda: -1)() == 0,
                     "Run as root in a disposable Linux test container for two-UID checks")
class TwoUserTests(unittest.TestCase):
    def test_other_os_user_cannot_read_or_replace_vault(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            root.chmod(0o755)
            directory = root / "alice"
            directory.mkdir(mode=0o700)
            path = directory / "vault.pvz"
            path.write_bytes(b"original")
            path.chmod(0o600)
            os.chown(path, 10001, 10001)
            os.chown(directory, 10001, 10001)

            def run_as(uid, action):
                # POSIX subprocess user/group parameters drop privileges in
                # the child. No real user accounts or vaults are modified.
                code = ("from pathlib import Path; from pwvault import storage; import sys; "
                        "p=Path(sys.argv[1]); " + action)
                return subprocess.run([sys.executable, "-c", code, str(path)],
                                      user=uid, group=uid, extra_groups=[],
                                      capture_output=True, timeout=10)

            self.assertEqual(run_as(10001, "storage.read(p)").returncode, 0)
            self.assertNotEqual(run_as(10002, "storage.read(p)").returncode, 0)
            self.assertNotEqual(run_as(10002, "storage.write(p,b'changed')").returncode, 0)
            self.assertEqual(path.read_bytes(), b"original")
            self.assertEqual(run_as(10001, "storage.write(p,b'owner update')").returncode, 0)
            self.assertEqual(path.read_bytes(), b"owner update")
