"""Argon2id key derivation and authenticated encryption of the whole vault."""
import json
import os
import struct

from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .errors import VaultError

MAGIC = b"PVLT01"
VERSION = 1
MEMORY = 65536  # KiB: 64 MiB
TIME = 3
PARALLELISM = 4
# Magic, version, memory, time, parallelism, salt and nonce (41 bytes).
HEADER = struct.Struct(">6sBIBB16s12s")
MAX_FILE_SIZE = 2 * 1024 * 1024


def derive_key(password, salt):
    return hash_secret_raw(
        password.encode("utf-8"), salt, time_cost=TIME, memory_cost=MEMORY,
        parallelism=PARALLELISM, hash_len=32, type=Type.ID,
    )


def encrypt(key, salt, items):
    nonce = os.urandom(12)
    header = HEADER.pack(MAGIC, VERSION, MEMORY, TIME, PARALLELISM, salt, nonce)
    plaintext = json.dumps(items, ensure_ascii=False).encode("utf-8")
    encrypted = header + AESGCM(key).encrypt(nonce, plaintext, header)
    if len(encrypted) > MAX_FILE_SIZE:
        raise VaultError("The vault is full (maximum file size: 2 MiB).")
    return encrypted


def unlock(data, password):
    if not HEADER.size + 16 <= len(data) <= MAX_FILE_SIZE:
        raise VaultError("The vault is incomplete or too large.", 3)
    header = data[:HEADER.size]
    magic, version, memory, time_cost, parallelism, salt, nonce = HEADER.unpack(header)
    # Never trust file-supplied cost values: reject unsupported values before KDF.
    if (magic, version, memory, time_cost, parallelism) != (
            MAGIC, VERSION, MEMORY, TIME, PARALLELISM):
        raise VaultError("The vault header is damaged or unsupported.", 3)
    key = derive_key(password, salt)
    try:
        plaintext = AESGCM(key).decrypt(nonce, data[HEADER.size:], header)
    except InvalidTag:
        # Authentication cannot distinguish a wrong password from changed data.
        raise VaultError("Wrong master password or modified vault. Nothing was changed.", 2) from None
    try:
        items = json.loads(plaintext)
    except (ValueError, UnicodeError, RecursionError):
        raise VaultError("The decrypted vault format is invalid.", 3) from None
    return key, salt, items
