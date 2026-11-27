import base64
import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    salt = os.urandom(16)

    password_hash = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )

    encoded_salt = base64.b64encode(salt).decode('ascii')
    encoded_hash = base64.b64encode(password_hash).decode('ascii')

    return f'scrypt$16384$8$1${encoded_salt}${encoded_hash}'


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt_b64, hash_b64 = stored_hash.split('$')

        if algorithm != 'scrypt':
            return False

        salt = base64.b64decode(salt_b64, validate=True)
        expected_hash = base64.b64decode(hash_b64, validate=True)

        actual_hash = hashlib.scrypt(
            password.encode('utf-8'),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected_hash),
        )

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError):
        return False