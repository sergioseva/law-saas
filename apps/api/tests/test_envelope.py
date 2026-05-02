"""Encryption envelope round-trip tests — no DB needed."""
from encryption.envelope import (
    decrypt_payload,
    decrypt_text,
    encrypt_payload,
    encrypt_text,
    generate_dek,
    unwrap_dek,
    wrap_dek,
)


def test_wrap_unwrap_dek_roundtrip() -> None:
    dek = generate_dek()
    wrapped = wrap_dek(dek)
    assert isinstance(wrapped, str)
    assert wrapped != dek.decode("ascii")  # actually encrypted
    assert unwrap_dek(wrapped) == dek


def test_payload_roundtrip() -> None:
    dek = generate_dek()
    payload = {"full_name": "María José", "dni": "30123456", "nested": {"x": 1}}
    token = encrypt_payload(dek, payload)
    assert isinstance(token, str)
    assert "María" not in token  # plaintext should not leak
    assert decrypt_payload(dek, token) == payload


def test_text_roundtrip_and_none() -> None:
    dek = generate_dek()
    assert encrypt_text(dek, None) is None
    assert encrypt_text(dek, "") is None
    token = encrypt_text(dek, "secret-note")
    assert decrypt_text(dek, token) == "secret-note"
    assert decrypt_text(dek, None) is None


def test_different_deks_dont_decrypt() -> None:
    a, b = generate_dek(), generate_dek()
    token = encrypt_payload(a, {"x": 1})
    import pytest
    from cryptography.fernet import InvalidToken

    with pytest.raises(InvalidToken):
        decrypt_payload(b, token)
