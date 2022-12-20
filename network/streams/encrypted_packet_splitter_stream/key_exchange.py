from dataclasses import dataclass
from os import urandom

from cryptography.hazmat.primitives.asymmetric.padding import MGF1, OAEP
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.hashes import SHA256

from ..packet_splitter_stream import PacketSplitterStream


@dataclass(frozen=True)
class KeyExcangeResult:
    key: bytes
    our_nonce: int
    peer_nonce: int


async def exchange_key(
    stream: PacketSplitterStream[bytes], server_key: RSAPublicKey
) -> KeyExcangeResult:
    """
    Метод, вызываемый клиентом при подключении к серверу.
    Создаёт, шифрует и отправляет серверу сессионный ключ.

    :param stream: поток
    :param server_key: публичный ключ сервера
    :return: результат обмена ключами
    """

    key = urandom(32)

    await stream.write(server_key.encrypt(key, OAEP(MGF1(SHA256()), SHA256(), None)))

    return KeyExcangeResult(key, 1, -1)


async def accept_key_exchange(
    stream: PacketSplitterStream[bytes], server_key: RSAPrivateKey
) -> KeyExcangeResult:
    """
    Метод, вызываемый сервером в начале обработки соединения клиента.
    Получает и расшифровывает сгенерированный клиентом сессионный ключ.

    :param stream: поток
    :param server_key: приватный ключ сервера
    :return: результат обмена ключами
    """

    packet = await stream.read()
    key = server_key.decrypt(packet, OAEP(MGF1(SHA256()), SHA256(), None))

    return KeyExcangeResult(key, -1, 1)
