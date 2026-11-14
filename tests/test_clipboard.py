"""Clipboard lifecycle checks; the normal suite never touches the real clipboard."""
from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import patch

import pyperclip

from pwvault import clipboard
from pwvault.errors import VaultError

SECRET = "Fictional clipboard secret!"


class ClipboardTests(unittest.TestCase):
    def setUp(self):
        self.value = "previous text"
        self.output = io.StringIO()
        self.enterContext(redirect_stdout(self.output))
        self.copy = self.enterContext(patch("pwvault.clipboard.pyperclip.copy",
                                           side_effect=self.set_clipboard))
        self.paste = self.enterContext(patch("pwvault.clipboard.pyperclip.paste",
                                            side_effect=lambda: self.value))
        self.wait = self.enterContext(patch("pwvault.clipboard.sleep"))

    def set_clipboard(self, value):
        self.value = value

    def test_password_is_available_during_wait_then_cleared_without_printing(self):
        def during_wait(seconds):
            self.assertEqual(seconds, 20)
            self.assertEqual(self.value, SECRET)
        self.wait.side_effect = during_wait
        clipboard.copy_password(SECRET)
        self.assertEqual(self.value, "")
        self.assertNotIn(SECRET, self.output.getvalue())

    def test_newer_clipboard_content_is_preserved(self):
        self.wait.side_effect = lambda seconds: self.set_clipboard("new copied text")
        clipboard.copy_password(SECRET)
        self.assertEqual(self.value, "new copied text")

    def test_ctrl_c_still_clears_the_password(self):
        self.wait.side_effect = KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            clipboard.copy_password(SECRET)
        self.assertEqual(self.value, "")

    def test_unavailable_backend_does_not_leak_details_or_claim_success(self):
        self.copy.side_effect = pyperclip.PyperclipException("private backend path")
        with self.assertRaises(VaultError) as caught:
            clipboard.copy_password(SECRET)
        self.assertNotIn("private", str(caught.exception))
        self.assertEqual(self.output.getvalue(), "")
        self.wait.assert_not_called()

    def test_failed_round_trip_does_not_claim_success_or_erase_other_text(self):
        self.copy.side_effect = lambda value: None
        with self.assertRaises(VaultError):
            clipboard.copy_password(SECRET)
        self.assertEqual(self.value, "previous text")
        self.assertEqual(self.output.getvalue(), "")
        self.wait.assert_not_called()

    def test_clear_failure_is_reported_without_exposing_the_password(self):
        def copy(value):
            if value == "":
                raise pyperclip.PyperclipException("private backend path")
            self.value = value
        self.copy.side_effect = copy
        with self.assertRaises(VaultError) as caught:
            clipboard.copy_password(SECRET)
        self.assertIn("Clear it manually", str(caught.exception))
        self.assertNotIn("private", str(caught.exception))
        self.assertNotIn(SECRET, self.output.getvalue())
