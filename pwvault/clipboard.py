"""Optional desktop clipboard retrieval; never print the copied password."""
from time import sleep

import pyperclip

from .errors import VaultError

SECONDS = 20


def copy_password(password):
    copied = False
    try:
        pyperclip.copy(password)
        copied = True
        if pyperclip.paste() != password:
            raise VaultError("The clipboard did not accept the password.", 3)
        print("Password copied for 20 seconds. Paste it into a password field.")
        print("Keep this command open. Ctrl+C clears it sooner.")
        sleep(SECONDS)
    except (pyperclip.PyperclipException, OSError, ValueError):
        raise VaultError("Cannot use the clipboard. Run --copy on a local desktop, outside Docker.",
                         3) from None
    finally:
        if copied:
            try:
                # Preserve anything the user copied after this password.
                if pyperclip.paste() == password:
                    pyperclip.copy("")
            except (pyperclip.PyperclipException, OSError, ValueError):
                raise VaultError("Cannot clear the clipboard. Clear it manually.", 3) from None
