"""Tests for Fitbit token encryption utilities."""
import pytest
from app.core.encryption import encrypt_token, decrypt_token


def test_encrypt_decrypt_token():
    """Test that tokens can be encrypted and decrypted."""
    original = "my_secret_access_token_12345"

    encrypted = encrypt_token(original)
    decrypted = decrypt_token(encrypted)

    assert decrypted == original
    assert encrypted != original  # Should be encrypted


def test_encrypt_produces_different_output():
    """Test that encrypting the same token twice produces different ciphertext."""
    token = "test_token"

    encrypted1 = encrypt_token(token)
    encrypted2 = encrypt_token(token)

    # Fernet includes random IV, so outputs differ
    assert encrypted1 != encrypted2

    # But both decrypt to the same value
    assert decrypt_token(encrypted1) == token
    assert decrypt_token(encrypted2) == token


def test_decrypt_invalid_token_raises_error():
    """Test that decrypting invalid data raises an error."""
    with pytest.raises(Exception):
        decrypt_token("invalid_encrypted_data")


def test_encrypt_empty_string():
    """Test encrypting and decrypting empty string."""
    original = ""
    encrypted = encrypt_token(original)
    decrypted = decrypt_token(encrypted)

    assert decrypted == original


def test_encrypt_unicode_token():
    """Test encrypting tokens with unicode characters."""
    original = "token_with_unicode_🔐_chars"
    encrypted = encrypt_token(original)
    decrypted = decrypt_token(encrypted)

    assert decrypted == original
