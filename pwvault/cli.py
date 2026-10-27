"""Small CLI: passwords are entered without echo and never printed."""
import argparse
import getpass
from pathlib import Path
import sys
import warnings

from . import storage, users
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


def run(args):
    path = storage.vault_path(args.vault if args.vault is not None else DEFAULT_VAULT)
    if hasattr(args, "title"):
        users.text_field(args.title, "Title", 100)
    if args.command == "init":
        if path.exists() or path.is_symlink():
            raise VaultError("A vault already exists at this path. It was not overwritten.")
        password = new_password("Choose a master password: ", master=True)
        users.create(path, password, create_parent=args.vault is None)
        print("Vault created.")
        return

    # Check the file before prompting, then verify authentication before any output.
    storage.read(path)
    key, salt, items = users.open_vault(path, password_prompt("Master password: "))
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
            return
        del items[title]
        users.save(path, key, salt, items)
        print("Saved login deleted.")


def main(argv=None):
    try:
        run(parser().parse_args(argv))
        return 0
    except VaultError as error:
        print("Error: " + str(error), file=sys.stderr)
        return error.code
    except FileExistsError:
        print("Error: The vault already exists. Nothing was overwritten.", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("Error: The vault or its parent directory does not exist.", file=sys.stderr)
        return 3
    except (PermissionError, OSError, ValueError, RuntimeError):
        # Operating-system errors can contain user-controlled filenames; hide details.
        print("Error: Cannot safely read or save the vault. Check its path and permissions.", file=sys.stderr)
        return 3
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 1
