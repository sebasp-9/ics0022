"""Create/unlock the vault and validate its saved logins."""
import os

from . import crypto, storage
from .errors import VaultError


def text_field(value, label, maximum=200):
    if not isinstance(value, str) or not 1 <= len(value) <= maximum or not value.isprintable():
        raise VaultError(label + " must contain 1–" + str(maximum) + " printable characters.")
    return value


def master_password(value, new=False):
    minimum = 12 if new else 1
    if not minimum <= len(value) <= 128:
        raise VaultError("The master password must contain " + str(minimum) + "–128 characters.")
    return value


def validate_items(items):
    if not isinstance(items, dict):
        raise VaultError("The vault contents are invalid.", 3)
    try:
        for title, entry in items.items():
            text_field(title, "Title", 100)
            if not isinstance(entry, dict) or set(entry) != {"username", "password"}:
                raise VaultError("Invalid saved login.")
            text_field(entry["username"], "Login name")
            text_field(entry["password"], "Password")
    except VaultError:
        raise VaultError("The vault contains invalid fields.", 3) from None


def create(path, password, create_parent=False):
    master_password(password, new=True)
    storage.check_parent(path, create=create_parent)
    salt = os.urandom(16)
    key = crypto.derive_key(password, salt)
    storage.write(path, crypto.encrypt(key, salt, {}), new=True)


def open_vault(path, password):
    master_password(password)
    key, salt, items = crypto.unlock(storage.read(path), password)
    validate_items(items)
    return key, salt, items


def save(path, key, salt, items):
    validate_items(items)
    storage.write(path, crypto.encrypt(key, salt, items))
