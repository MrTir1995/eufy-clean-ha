"""Tuya cryptographic utilities for Eufy Clean integration."""

from __future__ import annotations

import math
from hashlib import md5

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Tuya password encryption keys (from Eufy Home Android app)
TUYA_PASSWORD_KEY = bytearray(
    [36, 78, 109, 138, 86, 172, 135, 145, 36, 67, 45, 139, 108, 188, 162, 196]
)
TUYA_PASSWORD_IV = bytearray(
    [119, 36, 86, 242, 167, 102, 76, 243, 57, 44, 53, 151, 233, 62, 87, 71]
)


def unpadded_rsa(key_exponent: int, key_n: int, plaintext: bytes) -> bytes:
    """
    Perform RSA encryption without padding.

    Used for Tuya password encryption.
    Based on: https://github.com/pyca/cryptography/issues/2735#issuecomment-276356841
    """
    keylength = math.ceil(key_n.bit_length() / 8)
    input_nr = int.from_bytes(plaintext, byteorder="big")
    crypted_nr = pow(input_nr, key_exponent, key_n)
    return crypted_nr.to_bytes(keylength, byteorder="big")


def shuffled_md5(value: str) -> str:
    """
    Compute MD5 hash and shuffle the result.

    Tuya uses a specific shuffling pattern for their signatures.
    From: https://github.com/TuyaAPI/cloud/blob/master/index.js#L99
    """
    hash_value = md5(value.encode("utf-8")).hexdigest()
    return hash_value[8:16] + hash_value[0:8] + hash_value[24:32] + hash_value[16:24]


def get_tuya_password_cipher() -> Cipher:
    """Get the Tuya password cipher for AES encryption."""
    return Cipher(
        algorithms.AES(bytes(TUYA_PASSWORD_KEY)),
        modes.CBC(bytes(TUYA_PASSWORD_IV)),
        backend=default_backend(),
    )
