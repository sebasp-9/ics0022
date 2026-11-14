"""Run the actual CLI in a Linux terminal, without mocking password input."""
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest

if os.name == "posix":
    import pty
    import select
    import termios


@unittest.skipUnless(os.name == "posix", "Requires a Linux/POSIX pseudo-terminal")
class TerminalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "vault.pvz"
        self.path.parent.chmod(0o700)
        self.master = b"Terminal master password!"
        self.secret = b"Terminal saved secret!"

    def command(self, args, answers):
        child, terminal = pty.fork()
        if child == 0:
            os.execv(sys.executable, [sys.executable, "-m", "pwvault", "--vault", str(self.path), *args])
        transcript = bytearray()
        cursor = 0
        pending = list(answers)
        finished = False
        deadline = time.monotonic() + 20
        try:
            while time.monotonic() < deadline:
                ready, _, _ = select.select([terminal], [], [], 0.1)
                if not ready:
                    continue
                try:
                    chunk = os.read(terminal, 4096)
                except OSError as error:
                    if error.errno != 5:  # Linux PTY reports EIO after child exit.
                        raise
                    break
                if not chunk:
                    break
                transcript.extend(chunk)
                while pending:
                    prompt, answer, hidden = pending[0]
                    position = transcript.find(prompt, cursor)
                    if position < 0:
                        break
                    cursor = position + len(prompt)
                    if hidden:
                        self.assertFalse(termios.tcgetattr(terminal)[3] & termios.ECHO,
                                         "Password prompt left terminal echo enabled")
                    os.write(terminal, answer if answer == b"\x03" else answer + b"\n")
                    pending.pop(0)
            else:
                self.fail("CLI terminal interaction timed out")
            _, status = os.waitpid(child, 0)
            finished = True
            self.assertEqual(pending, [], "A required prompt was not reached")
            output = bytes(transcript)
            for secret in (self.master, self.secret, b"New terminal secret!"):
                self.assertNotIn(secret, output)
            self.assertNotIn(b"Traceback", output)
            return os.waitstatus_to_exitcode(status), output
        finally:
            os.close(terminal)
            if not finished:
                try:
                    os.kill(child, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                os.waitpid(child, 0)

    def initialize(self):
        self.assertEqual(self.command(["init"], [
            (b"Choose a master password: ", self.master, True),
            (b"Confirm password: ", self.master, True)])[0], 0)

    def test_real_prompts_and_persistence_between_cli_processes(self):
        self.initialize()
        self.assertEqual(self.command(["add", "Email"], [
            (b"Master password: ", self.master, True),
            (b"Login name: ", b"alice@example.test", False),
            (b"Password to save: ", self.secret, True),
            (b"Confirm password: ", self.secret, True)])[0], 0)
        self.assertIn(b"Email", self.command(["list"], [(b"Master password: ", self.master, True)])[1])
        code, output = self.command(["get", "Email"], [(b"Master password: ", self.master, True)])
        self.assertEqual(code, 0)
        self.assertIn(b"alice@example.test", output)
        self.assertIn(b"Password: [hidden]", output)
        before = self.path.read_bytes()
        self.assertEqual(self.command(["list"], [(b"Master password: ", b"wrong password", True)])[0], 2)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.command(["update", "Email"], [
            (b"Master password: ", self.master, True),
            (b"New login name (Enter to keep current): ", b"bob@example.test", False),
            (b"New password (Enter to keep current): ", b"New terminal secret!", True),
            (b"Confirm password: ", b"New terminal secret!", True)])[0], 0)
        self.assertIn(b"bob@example.test", self.command(["get", "Email"], [
            (b"Master password: ", self.master, True)])[1])
        self.assertEqual(self.command(["delete", "Email"], [
            (b"Master password: ", self.master, True),
            (b"Delete this saved login? Type yes to confirm: ", b"yes", False)])[0], 0)
        self.assertIn(b"empty", self.command(["list"], [(b"Master password: ", self.master, True)])[1])

    def test_ctrl_c_restores_prompt_and_preserves_vault(self):
        self.initialize()
        before = self.path.read_bytes()
        code, output = self.command(["list"], [(b"Master password: ", b"\x03", True)])
        self.assertEqual(code, 1)
        self.assertIn(b"Cancelled", output)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.command(["list"], [(b"Master password: ", self.master, True)])[0], 0)
