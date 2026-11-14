"""Small CLI: passwords are entered without echo and never printed."""
import argparse
import getpass
from pathlib import Path
import sys
import warnings

from . import audit, locking, memory, storage, users
from .errors import VaultError

DEFAULT_VAULT = Path.home() / ".pwvault" / "vault.pvz"


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # Do not echo arbitrary command arguments or terminal control characters.
        self.exit(1, "Invalid command or arguments. Use --help for usage.\n")


def password_prompt(label):
    # Refuse redirected input: passwords must come from a hidden terminal prompt.
    if not sys.stdin.isatty():
        raise VaultError("Use an interactive terminal that supports hidden password input.")
    # getpass may also fail when the terminal cannot turn echo off.
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        try:
            return getpass.getpass(label)
        except getpass.GetPassWarning:
            raise VaultError("Use an interactive terminal that supports hidden password input.") from None


def new_password(label, master=False, optional=False):
    value = password_prompt(label)
    if optional and not value:
        return None
    if master:
        users.master_password(value, new=True)
    else:
        users.text_field(value, "Password")
    if value != password_prompt("Confirm password: "):
        raise VaultError("The passwords do not match.")
    return value


def parser():
    command_line = Parser(description="An encrypted local vault. Passwords are never printed.")
    command_line.add_argument("--vault", default=None, metavar="PATH",
                              help="Vault file path; put this option before the command.")
    commands = command_line.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Create a vault with a master password.")
    commands.add_parser("list", help="List saved login titles.")
    for command, help_text in (
            ("add", "Add a saved login."),
            ("get", "View the title and login name; the password stays hidden."),
            ("update", "Update the login name and/or password."),
            ("delete", "Delete a saved login after confirmation.")):
        subcommand = commands.add_parser(command, help=help_text)
        subcommand.add_argument("title", metavar="TITLE")
    return command_line


def run(args, log=None):
    path = storage.vault_path(args.vault if args.vault is not None else DEFAULT_VAULT)
    if hasattr(args, "title"):
        users.text_field(args.title, "Title", 100)
    if args.command == "init":
        if path.exists() or path.is_symlink():
            raise VaultError("A vault already exists at this path. It was not overwritten.")
        users.create(path, new_password("Choose a master password: ", master=True),
                     create_parent=args.vault is None)
        print("Vault created.")
        return

    # Check the file before prompting, then verify authentication before any output.
    storage.read(path)
    try:
        key, salt, items = users.open_vault(path, password_prompt("Master password: "))
    except VaultError as error:
        if log is not None and error.code == 2:
            audit.record(log, args.command, "failure", event="authentication")
        raise
    try:
        if log is not None:
            audit.record(log, args.command, "success", event="authentication")
        return operate(args, path, key, salt, items)
    finally:
        memory.wipe(key)
        memory.clear_items(items)


def operate(args, path, key, salt, items):
    """Work on an unlocked vault. run() always cleans up when this returns."""
    if args.command == "list":
        for title in sorted(items):
            print(title)
        if not items:
            print("The vault is empty.")
        return
    title = args.title
    if args.command == "add":
        if title in items:
            raise VaultError("An item with that title already exists.")
        username = users.text_field(input("Login name: "), "Login name")
        password = new_password("Password to save: ")
        items[title] = {"username": username, "password": password}
        users.save(path, key, salt, items)
        print("Saved login added.")
        return
    if title not in items:
        raise VaultError("No saved login has that title.", 4)
    if args.command == "get":
        print("Title: " + title)
        print("Login name: " + items[title]["username"])
        print("Password: [hidden]")
    elif args.command == "update":
        username = input("New login name (Enter to keep current): ")
        if username:
            items[title]["username"] = users.text_field(username, "Login name")
        password = new_password("New password (Enter to keep current): ", optional=True)
        if password is not None:
            items[title]["password"] = password
        users.save(path, key, salt, items)
        print("Saved login updated.")
    elif args.command == "delete":
        if input("Delete this saved login? Type yes to confirm: ") != "yes":
            print("Deletion cancelled.")
            return "cancelled"
        del items[title]
        users.save(path, key, salt, items)
        print("Saved login deleted.")


def execute(args, log):
    try:
        outcome = run(args, log) or "success"
        return 0, outcome
    except VaultError as error:
        print("Error: " + str(error), file=sys.stderr)
        return error.code, "failure"
    except FileExistsError:
        print("Error: The vault already exists. Nothing was overwritten.", file=sys.stderr)
        return 1, "failure"
    except FileNotFoundError:
        print("Error: The vault or its parent directory does not exist.", file=sys.stderr)
        return 3, "failure"
    except (PermissionError, OSError, ValueError, RuntimeError):
        # Operating-system errors can contain user-controlled filenames; hide details.
        print("Error: Cannot safely read or save the vault. Check its path and permissions.", file=sys.stderr)
        return 3, "failure"
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 1, "cancelled"


def logged_command(args):
    try:
        path = storage.vault_path(args.vault if args.vault is not None else DEFAULT_VAULT)
        with audit.open_log(path, create_parent=args.command == "init" and args.vault is None) as log:
            # Refuse to run unless the initial event is safely recorded.
            audit.record(log, args.command, "attempt")
            code, outcome = execute(args, log)
            audit.record(log, args.command, outcome)
            return code
    except (VaultError, OSError, ValueError, RuntimeError, KeyError):
        print("Error: Cannot safely write the audit log. Check its directory and permissions.",
              file=sys.stderr)
        return 3


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        path = storage.vault_path(args.vault if args.vault is not None else DEFAULT_VAULT)
        storage.check_parent(path, create=args.command == "init" and args.vault is None)
        with locking.exclusive(path):
            return logged_command(args)
    except VaultError as error:
        print("Error: " + str(error), file=sys.stderr)
        return error.code
    except (OSError, ValueError, RuntimeError):
        print("Error: Cannot safely access the vault directory. Check its path and permissions.",
              file=sys.stderr)
        return 3
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 1


def entrypoint():
    try:
        memory.harden_process()
    except (VaultError, OSError, ValueError):
        print("Error: Cannot enable process memory protections.", file=sys.stderr)
        return 3
    return main()
