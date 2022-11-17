from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def load_key(path: str) -> RSAPrivateKey:
    with open(path, "rb") as file:
        return load_pem_private_key(file.read(), None)
