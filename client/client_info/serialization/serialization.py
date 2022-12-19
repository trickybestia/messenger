from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_der_private_key,
    load_der_public_key,
)
from msgpack import packb, unpackb

from client.client_info.private_client_info import PrivateClientInfo
from client.client_info.public_client_info import PublicClientInfo

from .exceptions import DeserializationException


def serialize_public_client_info(info: PublicClientInfo) -> bytes:
    serialized_client_info = {
        "id": info.id,
        "nickname": info.nickname,
        "server_host": info.server_host,
        "server_port": info.server_port,
        "key": info.key.public_bytes(Encoding.DER, PublicFormat.PKCS1),
        "server_key": info.server_key.public_bytes(Encoding.DER, PublicFormat.PKCS1),
    }

    return packb(serialized_client_info)


def deserialize_public_client_info(data: bytes) -> PublicClientInfo:
    try:
        info = unpackb(data)

        key = load_der_public_key(info["key"])
        server_key = load_der_public_key(info["server_key"])

        return PublicClientInfo(
            info["id"],
            key,
            info["nickname"],
            server_key,
            info["server_host"],
            info["server_port"],
        )
    except Exception:
        raise DeserializationException()


def serialize_private_client_info(info: PrivateClientInfo) -> bytes:
    serialized_client_info = {
        "id": info.id,
        "key": info.key.private_bytes(
            Encoding.DER, PrivateFormat.PKCS8, NoEncryption()
        ),
        "server_password": info.server_password,
        "server_key": info.server_key.public_bytes(Encoding.DER, PublicFormat.PKCS1),
        "server_host": info.server_host,
        "server_port": info.server_port,
    }

    return packb(serialized_client_info)


def deserialize_private_client_info(data: bytes) -> PrivateClientInfo:
    try:
        info = unpackb(data)

        key = load_der_private_key(info["key"], None)
        server_key = load_der_public_key(info["server_key"])

        return PrivateClientInfo(
            info["id"],
            key,
            info["server_password"],
            server_key,
            info["server_host"],
            info["server_port"],
        )
    except Exception:
        raise DeserializationException()
