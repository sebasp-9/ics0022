"""A second command cannot operate while the first is holding its lock."""
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pwvault import cli, locking, users


class LockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "vault.pvz"
        self.path.parent.chmod(0o700)
        self.password = "Example master password!"
        users.create(self.path, self.password)

    def test_second_command_is_rejected_before_password_prompt(self):
        before = self.path.read_bytes()
        output = io.StringIO()
        with locking.exclusive(self.path), patch("pwvault.cli.password_prompt") as prompt, \
                redirect_stdout(output), redirect_stderr(output):
            self.assertEqual(cli.main(["--vault", str(self.path), "list"]), 1)
            prompt.assert_not_called()
        self.assertIn("Another command", output.getvalue())
        self.assertEqual(self.path.read_bytes(), before)

    def test_exception_releases_lock(self):
        with self.assertRaises(ValueError):
            with locking.exclusive(self.path):
                raise ValueError("simulated command failure")
        with locking.exclusive(self.path):
            pass

    def test_lock_inode_is_reused(self):
        path = self.path.parent / ".pwvault.lock"
        with locking.exclusive(self.path):
            first = path.stat().st_ino
        with locking.exclusive(self.path):
            self.assertEqual(path.stat().st_ino, first)
