import secrets
import string


def crypto_random_string(length: int) -> str:
    """Generate a semi crypto random string of a given length."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length)).lower()
