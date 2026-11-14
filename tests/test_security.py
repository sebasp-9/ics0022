"""Security regression tests using fictional secrets and disposable vaults."""
from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pwvault import cli, crypto, storage, users
from pwvault.errors import VaultError


MASTER = "Example master password!"
SECRET = "Fictional saved secret!"
ITEMS = {"Email": {"username": "alice@example.test", "password": SECRET}}


class ValidationTests(unittest.TestCase):
    def test_text_boundaries_and_unicode(self):
        for maximum in (100, 200):
            for text in ("x", "x" * maximum, "Caf\u00e9 \U0001f512"):
                self.assertEqual(users.text_field(text, "Field", maximum), text)
            for text in ("", "x" * (maximum + 1), None, 1, [], "line\nbreak",
                         "tab\there", "\x00", "\x1b[31m", "\ud800", "\u202e"):
                with self.subTest(maximum=maximum, text=repr(text)):
                    with self.assertRaises(VaultError):
                        users.text_field(text, "Field", maximum)

    def test_master_password_boundaries(self):
        for new, minimum in ((True, 12), (False, 1)):
            for length in (minimum, 128):
                self.assertEqual(users.master_password("x" * length, new), "x" * length)
            invalid = ["x" * (minimum - 1), "x" * 129, None, 1, "a" * 12 + "\ud800"]
            if new:
                invalid.extend(("a" * 12 + "\n", "a" * 12 + "\x00"))
            for value in invalid:
                with self.subTest(new=new, value=repr(value)):
                    with self.assertRaises(VaultError):
                        users.master_password(value, new)

    def test_legacy_control_character_passwords_remain_usable_for_unlock(self):
        value = "Old password\twith tab"
        self.assertEqual(users.master_password(value), value)
        with self.assertRaises(VaultError):
            users.master_password(value, new=True)

    def test_schema_rejects_invalid_records(self):
        invalid = [[], None, {"": ITEMS["Email"]}, {"Email": []},
                   {"Email": {"username": "alice"}},
                   {"Email": {**ITEMS["Email"], "extra": "field"}},
                   {"Email": {"username": 1, "password": SECRET}},
                   {"Email": {"username": "alice", "password": "\x1b"}}]
        for items in invalid:
            with self.subTest(items=items):
                with self.assertRaises(VaultError):
                    users.validate_items(items)

    def test_shell_and_format_syntax_remain_literal_data(self):
        for text in ("%s%n", "{x.__class__}", "$(whoami); rm -rf dummy", "' OR 1=1 --"):
            self.assertEqual(users.text_field(text, "Field"), text)

    def test_invalid_paths(self):
        for path in ("", "x" * 4097, "line\nbreak", "\x00", "\x1b[31m"):
            with self.subTest(path=repr(path)):
                with self.assertRaises(VaultError):
                    storage.vault_path(path)


class CryptoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.salt = os.urandom(16)
        cls.key = crypto.derive_key(MASTER, cls.salt)

    def test_encryption_round_trip_and_no_plaintext(self):
        encrypted = crypto.encrypt(self.key, self.salt, ITEMS)
        key, salt, items = crypto.unlock(encrypted, MASTER)
        self.assertEqual((key, salt, items), (self.key, self.salt, ITEMS))
        for value in (MASTER, "Email", "alice@example.test", SECRET):
            self.assertNotIn(value.encode(), encrypted)

    def test_each_save_uses_fresh_nonce(self):
        first = crypto.encrypt(self.key, self.salt, ITEMS)
        second = crypto.encrypt(self.key, self.salt, ITEMS)
        self.assertNotEqual(crypto.HEADER.unpack(first[:crypto.HEADER.size])[-1],
                            crypto.HEADER.unpack(second[:crypto.HEADER.size])[-1])
        self.assertEqual(crypto.unlock(second, MASTER)[2], ITEMS)

    def test_wrong_password_and_tampering_fail_authentication(self):
        data = crypto.encrypt(self.key, self.salt, ITEMS)
        with self.assertRaises(VaultError) as wrong:
            crypto.unlock(data, "Wrong master password!")
        self.assertEqual(wrong.exception.code, 2)
        # Salt, nonce, ciphertext and authentication tag are all protected.
        for offset in (13, 29, crypto.HEADER.size, len(data) - 1):
            changed = bytearray(data)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(VaultError) as tampered:
                crypto.unlock(bytes(changed), MASTER)
            self.assertEqual(str(tampered.exception), str(wrong.exception))
            self.assertEqual(tampered.exception.code, 2)

    def test_invalid_header_and_size_rejected_before_kdf(self):
        header = crypto.HEADER.pack(crypto.MAGIC, crypto.VERSION, 2**32 - 1,
                                   crypto.TIME, crypto.PARALLELISM, self.salt, b"n" * 12)
        for data in (b"", b"x" * (crypto.HEADER.size + 15), header + b"t" * 16,
                     b"x" * (crypto.MAX_FILE_SIZE + 1)):
            with patch("pwvault.crypto.derive_key") as derive:
                with self.assertRaises(VaultError):
                    crypto.unlock(data, MASTER)
                derive.assert_not_called()

    def encrypted_json(self, plaintext):
        nonce = os.urandom(12)
        header = crypto.HEADER.pack(crypto.MAGIC, crypto.VERSION, crypto.MEMORY,
                                   crypto.TIME, crypto.PARALLELISM, self.salt, nonce)
        return header + AESGCM(self.key).encrypt(nonce, plaintext, header)

    def test_malformed_authenticated_json_is_rejected(self):
        for plaintext in (b"not JSON", b"\xff", b"[" * 1100):
            with self.subTest(plaintext=plaintext[:20]), self.assertRaises(VaultError):
                crypto.unlock(self.encrypted_json(plaintext), MASTER)

    def test_duplicate_json_names_are_rejected(self):
        for plaintext in (b'{"Email":{},"Email":{}}',
                          b'{"Email":{"username":"a","username":"b","password":"c"}}'):
            with self.subTest(plaintext=plaintext), self.assertRaises(VaultError):
                crypto.unlock(self.encrypted_json(plaintext), MASTER)


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.directory.chmod(0o700)
        self.path = self.directory / "test.pvz"
        users.create(self.path, MASTER)

    def command(self, *args, passwords=(), inputs=()):
        output, errors = io.StringIO(), io.StringIO()
        with patch("pwvault.cli.password_prompt", side_effect=passwords), \
                patch("builtins.input", side_effect=inputs), \
                redirect_stdout(output), redirect_stderr(errors):
            code = cli.main(["--vault", str(self.path), *args])
        for secret in (MASTER, SECRET):
            self.assertNotIn(secret, output.getvalue() + errors.getvalue())
        return code, output.getvalue(), errors.getvalue()

    def test_cli_add_list_get_update_delete(self):
        title = "%s {literal} $(echo dummy)"
        self.assertEqual(self.command("add", title, passwords=(MASTER, SECRET, SECRET),
                                      inputs=("alice",))[0], 0)
        self.assertIn(title, self.command("list", passwords=(MASTER,))[1])
        before = self.path.read_bytes()
        code, output, _ = self.command("get", title, passwords=(MASTER,))
        self.assertEqual(code, 0)
        self.assertIn("Login name: alice", output)
        self.assertIn("Password: [hidden]", output)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.command("update", title, passwords=(MASTER, ""), inputs=("bob",))[0], 0)
        self.assertEqual(users.open_vault(self.path, MASTER)[2][title],
                         {"username": "bob", "password": SECRET})
        before = self.path.read_bytes()
        self.assertIn("cancelled", self.command("delete", title, passwords=(MASTER,), inputs=("no",))[1])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.command("delete", title, passwords=(MASTER,), inputs=("yes",))[0], 0)
        self.assertEqual(users.open_vault(self.path, MASTER)[2], {})

    def test_every_existing_vault_command_requires_authentication(self):
        before = self.path.read_bytes()
        for args in (("list",), ("get", "Email"), ("add", "Email"),
                     ("update", "Email"), ("delete", "Email")):
            with self.subTest(command=args):
                code, output, errors = self.command(*args, passwords=("Wrong password!",))
                self.assertEqual(code, 2)
                self.assertEqual(output, "")
                self.assertNotIn("Traceback", errors)
                self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_title_rejected_without_prompt_or_write(self):
        before = self.path.read_bytes()
        for title in ("", "x" * 101, "\x1b[31m", "line\nbreak"):
            with self.subTest(title=repr(title)):
                self.assertEqual(self.command("add", title)[0], 1)
                self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_save_preserves_vault(self):
        key, salt, _ = users.open_vault(self.path, MASTER)
        before = self.path.read_bytes()
        with self.assertRaises(VaultError):
            users.save(self.path, key, salt, {"Email": {"password": SECRET}})
        self.assertEqual(self.path.read_bytes(), before)

    def test_failed_replace_preserves_vault_and_removes_tempfile(self):
        before = self.path.read_bytes()
        with patch("pwvault.storage.os.replace", side_effect=OSError("private internal path")):
            with self.assertRaises(OSError):
                storage.write(self.path, b"replacement encrypted bytes")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.directory.glob(".pwvault-*")), [])

    def test_initialization_never_overwrites_existing_vault(self):
        before = self.path.read_bytes()
        with self.assertRaises(FileExistsError):
            users.create(self.path, MASTER)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.directory.glob(".pwvault-*")), [])

    def test_os_errors_hide_internal_details(self):
        with patch("pwvault.cli.storage.read", side_effect=OSError("private internal path")):
            code, output, errors = self.command("list")
        self.assertEqual(code, 3)
        self.assertEqual(output, "")
        self.assertNotIn("private internal path", errors)
        self.assertNotIn("Traceback", errors)

    def test_redirected_password_input_is_refused(self):
        with patch("pwvault.cli.sys.stdin.isatty", return_value=False), \
                patch("pwvault.cli.getpass.getpass") as prompt:
            with self.assertRaises(VaultError):
                cli.password_prompt("Master password: ")
            prompt.assert_not_called()

    @unittest.skipUnless(os.name == "posix", "Requires POSIX owner and mode semantics")
    def test_posix_private_permissions_on_read_and_save(self):
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.path.chmod(0o644)
        for operation in (lambda: storage.read(self.path),
                          lambda: storage.write(self.path, b"replacement")):
            with self.assertRaises(VaultError):
                operation()
        self.path.chmod(0o600)
        self.directory.chmod(0o777)
        try:
            with self.assertRaises(VaultError):
                storage.read(self.path)
        finally:
            self.directory.chmod(0o700)


if __name__ == "__main__":
    unittest.main()
