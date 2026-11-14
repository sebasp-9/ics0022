"""Check owned-buffer cleanup, without claiming to erase Python's copies."""
from contextlib import redirect_stdout, redirect_stderr
import io
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pwvault import audit, cli, crypto, memory, users
from pwvault.errors import VaultError

MASTER = "Example master password!"


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "vault.pvz"
        self.path.parent.chmod(0o700)

    def test_wipe_overwrites_alias_without_resizing(self):
        buffer = bytearray(b"fictional secret")
        alias = memoryview(buffer)
        size = len(buffer)
        memory.wipe(buffer)
        self.assertEqual(bytes(alias), b"\x00" * size)
        self.assertEqual(len(buffer), size)
        memory.wipe(bytearray())

    def test_creation_key_is_cleaned_on_success_and_failure(self):
        for failure in (False, True):
            key = bytearray(b"k" * 32)
            with patch("pwvault.users.crypto.derive_key", return_value=key), \
                    patch("pwvault.users.storage.write", side_effect=OSError() if failure else None):
                if failure:
                    with self.assertRaises(OSError):
                        users.create(self.path, MASTER)
                else:
                    users.create(self.path, MASTER)
            self.assertEqual(key, bytearray(32))

    def test_encryption_plaintext_buffer_is_cleaned_even_on_failure(self):
        real_wipe = memory.wipe
        for failure in (False, True):
            buffers = []
            def wipe(buffer):
                buffers.append(buffer)
                real_wipe(buffer)
            with patch("pwvault.crypto.memory.wipe", side_effect=wipe):
                if failure:
                    with patch("pwvault.crypto.AESGCM", side_effect=ValueError()):
                        with self.assertRaises(ValueError):
                            crypto.encrypt(bytearray(b"k" * 32), b"s" * 16, {})
                else:
                    crypto.encrypt(bytearray(b"k" * 32), b"s" * 16, {})
            self.assertTrue(buffers)
            self.assertTrue(all(buffer == bytearray(len(buffer)) for buffer in buffers))

    def test_unlock_failure_cleans_derived_key_and_plaintext(self):
        salt, nonce = b"s" * 16, b"n" * 12
        header = crypto.HEADER.pack(crypto.MAGIC, crypto.VERSION, crypto.MEMORY,
                                   crypto.TIME, crypto.PARALLELISM, salt, nonce)
        for malformed in (False, True):
            key = bytearray(b"k" * 32)
            data = header + AESGCM(key).encrypt(nonce, b"not JSON" if malformed else b"{}", header)
            if not malformed:
                data = data[:-1] + bytes([data[-1] ^ 1])
            with patch("pwvault.crypto.derive_key", return_value=key):
                with self.assertRaises(VaultError):
                    crypto.unlock(data, MASTER)
            self.assertEqual(key, bytearray(32))

    def test_invalid_schema_cleans_key_and_record_references(self):
        key = bytearray(b"k" * 32)
        entry = {"username": "alice"}
        items = {"Email": entry}
        with patch("pwvault.users.storage.read", return_value=b"dummy"), \
                patch("pwvault.users.crypto.unlock", return_value=(key, b"s" * 16, items)):
            with self.assertRaises(VaultError):
                users.open_vault(self.path, MASTER)
        self.assertEqual(key, bytearray(32))
        self.assertEqual(items, {})
        self.assertEqual(entry, {})

    def test_successful_unlock_cleans_serialized_plaintext_but_keeps_live_key(self):
        salt = os.urandom(16)
        key = crypto.derive_key(MASTER, salt)
        encrypted = crypto.encrypt(key, salt, {"Email": {"username": "alice", "password": "dummy"}})
        buffers = []
        real_wipe = memory.wipe
        def wipe(buffer):
            buffers.append(buffer)
            real_wipe(buffer)
        with patch("pwvault.crypto.memory.wipe", side_effect=wipe):
            live_key, _, items = crypto.unlock(encrypted, MASTER)
        self.assertEqual(live_key, key)
        self.assertTrue(buffers)
        self.assertTrue(all(buffer == bytearray(len(buffer)) for buffer in buffers))
        self.assertEqual(items["Email"]["password"], "dummy")
        memory.wipe(key)
        memory.wipe(live_key)
        memory.clear_items(items)

    def test_cli_cleans_on_success_error_and_cancellation(self):
        self.path.write_bytes(b"dummy")
        self.path.chmod(0o600)
        cases = [("list", None, 0), ("get", "missing", 4),
                 ("add", "Email", 1), ("delete", "Email", 0), ("update", "Email", 1)]
        for command, title, expected in cases:
            key = bytearray(b"k" * 32)
            entry = {"username": "alice", "password": "dummy saved secret"}
            items = {"Email": entry}
            args = ["--vault", str(self.path), command] + ([title] if title else [])
            # EOF during update is a cancellation; "no" cancels delete.
            answers = EOFError() if command == "update" else ["no"]
            with self.subTest(command=command), \
                    patch("pwvault.cli.users.open_vault", return_value=(key, b"s" * 16, items)), \
                    patch("pwvault.cli.password_prompt", return_value=MASTER), \
                    patch("builtins.input", side_effect=answers), \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(args), expected)
            self.assertEqual(key, bytearray(32))
            self.assertEqual(items, {})
            self.assertEqual(entry, {})

    def test_authentication_log_failure_after_unlock_still_cleans(self):
        self.path.write_bytes(b"dummy")
        self.path.chmod(0o600)
        key, items = bytearray(b"k" * 32), {}
        real_record = audit.record
        def record(fd, operation, outcome, event="command"):
            if event == "authentication":
                raise OSError("simulated audit failure")
            real_record(fd, operation, outcome, event)
        with patch("pwvault.cli.users.open_vault", return_value=(key, b"s" * 16, items)), \
                patch("pwvault.cli.password_prompt", return_value=MASTER), \
                patch("pwvault.audit.record", side_effect=record), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["--vault", str(self.path), "list"]), 3)
        self.assertEqual(key, bytearray(32))

    @unittest.skipUnless(sys.platform == "linux", "Requires Linux process controls")
    def test_linux_disables_core_dumps_and_process_dumpability(self):
        code = ("from pwvault.memory import harden_process; import ctypes,resource; "
                "harden_process(); "
                "assert resource.getrlimit(resource.RLIMIT_CORE)==(0,0); "
                "assert ctypes.CDLL(None).prctl(3,0,0,0,0)==0")
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_hardening_failure_stops_before_any_command(self):
        with patch("pwvault.cli.memory.harden_process", side_effect=VaultError("internal detail")), \
                patch("pwvault.cli.main") as command, redirect_stderr(io.StringIO()) as output:
            self.assertEqual(cli.entrypoint(), 3)
            command.assert_not_called()
        self.assertNotIn("internal detail", output.getvalue())

    def test_kdf_allocation_failure_is_a_controlled_error(self):
        from argon2.exceptions import HashingError
        for error in (HashingError("internal allocation failure"), MemoryError()):
            with patch("pwvault.crypto.hash_secret_raw", side_effect=error):
                with self.assertRaises(VaultError) as caught:
                    crypto.derive_key(MASTER, b"s" * 16)
            self.assertEqual(caught.exception.code, 3)
            self.assertNotIn("internal", str(caught.exception))
