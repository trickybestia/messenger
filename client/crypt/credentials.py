from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.hashes import SHA256, Hash
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .csprng import create_random_function
from .rsa import generate_key


@dataclass(frozen=True)
class Credentials:
    key: RSAPrivateKey
    server_password: bytes

    @classmethod
    def from_master_password(cls, password: str) -> "Credentials":
        password_bytes = password.encode("utf-8")
        hash = Hash(SHA256())

        hash.update(password_bytes)

        password_hash = hash.finalize()

        kdf = PBKDF2HMAC(SHA256(), 64, password_hash, 500_000)

        kdf_result = kdf.derive(password_bytes)
        server_password = kdf_result[:32]
        random_seed = kdf_result[32:]
        random_function = create_random_function(random_seed)
        key = generate_key(random_function)

        return Credentials(key, server_password)
