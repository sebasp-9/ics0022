"""Audit events contain metadata only; log failures stop commands safely."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pwvault import audit, cli, users

MASTER = "Fictional master password!"
SECRET = "Fictional saved password!"


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.pvz"
        self.path.parent.chmod(0o700)
        users.create(self.path, MASTER)
        self.log_path = self.path.parent / "audit.jsonl"

    def command(self, args, passwords=(), inputs=()):
        output = io.StringIO()
        with patch("pwvault.cli.password_prompt", side_effect=passwords), \
                patch("builtins.input", side_effect=inputs), \
                redirect_stdout(output), redirect_stderr(output):
            code = cli.main(["--vault", str(self.path), *args])
        return code, output.getvalue()

    def events(self):
        return [json.loads(line) for line in self.log_path.read_text().splitlines()]

    def test_success_failure_and_cancellation(self):
        self.assertEqual(self.command(["list"], [MASTER])[0], 0)
        self.assertEqual(self.command(["list"], ["wrong password"])[0], 2)
        self.assertEqual(self.command(["add", "Private title"],
                                     [MASTER, SECRET, SECRET], ["Private login"])[0], 0)
        self.assertEqual(self.command(["delete", "Private title"], [MASTER], ["no"])[0], 0)
        events = self.events()
        self.assertTrue(any(e["event"] == "authentication" and e["outcome"] == "failure"
                            for e in events))
        self.assertEqual(events[-1]["outcome"], "cancelled")
        for event in events:
            self.assertEqual(set(event), {"timestamp", "event", "user", "operation", "source", "outcome"})
            self.assertEqual(event["source"], "local-terminal")
            self.assertIsNotNone(datetime.fromisoformat(event["timestamp"]).tzinfo)
        text = self.log_path.read_text()
        for value in (MASTER, SECRET, "wrong password", "Private title", "Private login", str(self.path)):
            self.assertNotIn(value, text)

    def test_log_failure_before_operation_does_not_prompt_or_change_vault(self):
        before = self.path.read_bytes()
        with patch("pwvault.audit.record", side_effect=OSError("private log path")):
            code, output = self.command(["list"])
        self.assertEqual(code, 3)
        self.assertNotIn("private log path", output)
        self.assertNotIn("Traceback", output)
        self.assertEqual(self.path.read_bytes(), before)

    def test_end_event_failure_returns_error_after_completed_operation(self):
        real_record = audit.record
        def record(fd, operation, outcome, event="command"):
            if event == "command" and outcome == "success":
                raise OSError("private log failure")
            real_record(fd, operation, outcome, event)
        with patch("pwvault.audit.record", side_effect=record):
            code, output = self.command(["add", "Email"], [MASTER, SECRET, SECRET], ["alice"])
        self.assertEqual(code, 3)
        self.assertNotIn("private log failure", output)
        self.assertIn("Email", users.open_vault(self.path, MASTER)[2])
        self.assertEqual(self.events()[0]["outcome"], "attempt")

    def test_untrusted_event_fields_are_rejected(self):
        with audit.open_log(self.path) as descriptor:
            for operation, outcome in (("list\nforged event", "success"), ("list", SECRET)):
                with self.assertRaises(ValueError):
                    audit.record(descriptor, operation, outcome)
        self.assertEqual(self.log_path.read_bytes(), b"")

    def test_log_hardlink_is_rejected(self):
        target = self.path.parent / "other-file"
        target.write_bytes(b"unchanged")
        target.chmod(0o600)
        try:
            os.link(target, self.log_path)
        except (OSError, NotImplementedError):
            self.skipTest("Hardlink creation is unavailable in this environment")
        self.assertEqual(self.command(["list"])[0], 3)
        self.assertEqual(target.read_bytes(), b"unchanged")

    @unittest.skipUnless(os.name == "posix", "Requires POSIX permissions")
    def test_log_permissions_are_private_and_public_log_is_refused(self):
        self.assertEqual(self.command(["list"], [MASTER])[0], 0)
        self.assertEqual(self.log_path.stat().st_mode & 0o777, 0o600)
        self.log_path.chmod(0o644)
        self.assertEqual(self.command(["list"])[0], 3)
