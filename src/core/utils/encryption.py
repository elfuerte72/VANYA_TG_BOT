"""
Utilities for encrypting and decrypting data.
"""
import base64
import os
from typing import Any, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from sqlalchemy import String, TypeDecorator

from src.config.settings import DATABASE_SECRET_KEY


class EncryptedData:
    """
    Helper class for encrypting and decrypting data with AES.
    """

    @staticmethod
    def _get_key_from_password(password: str) -> bytes:
        """
        Derive a 32-byte key from a password string.
        Simple but not as secure as proper key derivation function.
        """
        # Ensure the key is 32 bytes (256 bits) for AES-256
        raw_key = password.encode("utf-8")
        # Pad or truncate to 32 bytes
        return raw_key.ljust(32, b"\0")[:32]

    @staticmethod
    def encrypt(data: str, password: Optional[str] = None) -> str:
        """
        Encrypt data using AES encryption.

        Args:
            data: String data to encrypt
            password: Password for encryption. If None, use DATABASE_SECRET_KEY

        Returns:
            Base64-encoded encrypted data
        """
        if not data:
            return ""

        if password is None:
            password = DATABASE_SECRET_KEY

        # Generate a random 16-byte IV
        iv = os.urandom(16)

        # Get the encryption key from the password
        key = EncryptedData._get_key_from_password(password)

        # Create AES cipher with CBC mode
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad the data to match AES block size
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data.encode("utf-8")) + padder.finalize()

        # Encrypt the data
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # Combine IV and encrypted data and encode to base64
        result = base64.b64encode(iv + encrypted_data).decode("utf-8")

        return result

    @staticmethod
    def decrypt(encrypted_data: str, password: Optional[str] = None) -> str:
        """
        Decrypt data using AES encryption.

        Args:
            encrypted_data: Base64-encoded encrypted data
            password: Password for decryption. If None, use DATABASE_SECRET_KEY

        Returns:
            Decrypted string
        """
        if not encrypted_data:
            return ""

        if password is None:
            password = DATABASE_SECRET_KEY

        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_data)

        # Extract IV (first 16 bytes)
        iv = encrypted_bytes[:16]
        encrypted_data_bytes = encrypted_bytes[16:]

        # Get the decryption key from the password
        key = EncryptedData._get_key_from_password(password)

        # Create AES cipher with CBC mode
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the data
        padded_data = decryptor.update(encrypted_data_bytes) + decryptor.finalize()

        # Unpad the decrypted data
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data.decode("utf-8")


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type decorator that transparently encrypts/decrypts
    string data in the database.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        """Encrypt the string before storing in the database."""
        if value is None:
            return None
        return EncryptedData.encrypt(str(value))

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Decrypt the string when retrieving from the database."""
        if value is None:
            return None
        return EncryptedData.decrypt(value)
