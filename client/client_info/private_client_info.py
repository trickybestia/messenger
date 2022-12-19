from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from model import Id

from .public_client_info import PublicClientInfo


@dataclass(frozen=True)
class PrivateClientInfo:
    id: Id
    key: RSAPrivateKey
    server_password: bytes
    server_key: RSAPublicKey
    server_host: str
    server_port: int

    def public_info(self, nickname: str) -> PublicClientInfo:
        return PublicClientInfo(
            self.id,
            self.key.public_key(),
            nickname,
            self.server_key,
            self.server_host,
            self.server_port,
        )
