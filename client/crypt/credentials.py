from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.hashes import SHA256, Hash
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from .csprng import create_random_function
from .rsa import generate_key


@dataclass(frozen=True)
class Credentials:
    key: RSAPrivateKey
    server_password_salt: bytes

    def get_server_password(self, server_key: RSAPublicKey) -> bytes:
        kdf = PBKDF2HMAC(SHA256(), 32, self.server_password_salt, 500_000)

        return kdf.derive(server_key.public_bytes(Encoding.DER, PublicFormat.PKCS1))

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
