from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

DEFAULT_DEVELOPMENT_IMAGE_KEY = "griLWrQWk4knSGGNhmlmvt9EDT-Vh7pv_7hdsRvQY-M="


class ImageCryptoError(Exception):
    pass


def _get_fernet() -> Fernet:
    settings = get_settings()
    key = settings.product_image_encryption_key
    if (
        settings.app_env not in {"development", "test", "testing"}
        and key == DEFAULT_DEVELOPMENT_IMAGE_KEY
    ):
        raise ImageCryptoError("product_image_encryption_key_required")

    try:
        return Fernet(key.encode())
    except Exception as exc:
        raise ImageCryptoError("invalid_product_image_encryption_key") from exc


def encrypt_image(plaintext: bytes) -> bytes:
    return _get_fernet().encrypt(plaintext)


def decrypt_image(ciphertext: bytes) -> bytes:
    try:
        return _get_fernet().decrypt(ciphertext)
    except InvalidToken as exc:
        raise ImageCryptoError("invalid_product_image_ciphertext") from exc
