from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from model import Id


@dataclass(frozen=True)
class PublicClientInfo:
    id: Id
    key: RSAPublicKey
    nickname: str
    server_key: RSAPublicKey
    server_host: str
    server_port: int
