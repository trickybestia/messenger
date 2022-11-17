from typing import Final

from cryptography.hazmat.primitives.ciphers import Cipher, CipherContext
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CTR
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.hmac import HMAC

from network.streams.packet_splitter_stream import PacketSplitterStream


class EncryptedPacketSplitterStream(PacketSplitterStream[bytes]):
    _stream: Final[PacketSplitterStream[bytes]]
    _key: Final[bytes]
    _our_nonce: int  # с каждым сообщением nonce этой стороны будет по модулю увеличиваться на единицу
    _peer_nonce: int  # предпочтительные начальные значения - (1, -1)

    def __init__(
        self,
        stream: PacketSplitterStream[bytes],
        key: bytes,
        our_nonce: int,
        peer_nonce: int,
    ):
        self._stream = stream
        self._key = key
        self._our_nonce = our_nonce
        self._peer_nonce = peer_nonce

    def _create_encryptor(self) -> CipherContext:
        """
        Возвращает шифратор исходящих сообщений
        и увеличивает ``_our_nonce`` на единицу по модулю
        """

        cipher = Cipher(
            AES(self._key),
            CTR(self._our_nonce.to_bytes(len(self._key), "little", signed=True)),
        )

        if self._our_nonce > 0:
            self._our_nonce += 1
        else:
            self._our_nonce -= 1

        return cipher.encryptor()

    def _create_decryptor(self) -> CipherContext:
        """
        Возвращает дешифратор входящих сообщений
        и увеличивает ``_peer_nonce`` на единицу по модулю
        """

        cipher = Cipher(
            AES(self._key),
            CTR(self._peer_nonce.to_bytes(len(self._key), "little", signed=True)),
        )

        if self._peer_nonce > 0:
            self._peer_nonce += 1
        else:
            self._peer_nonce -= 1

        return cipher.decryptor()

    async def write(self, data: bytes):
        encryptor = self._create_encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        hmac = HMAC(self._key, SHA256())

        hmac.update(ciphertext)

        tag = hmac.finalize()

        await self._stream.write(ciphertext + tag)

    async def read(self) -> bytes:
        packet = await self._stream.read()
        ciphertext = packet[:-32]
        tag = packet[-32:]
        hmac = HMAC(self._key, SHA256())

        hmac.update(ciphertext)
        hmac.verify(tag)

        decryptor = self._create_decryptor()

        return decryptor.update(ciphertext) + decryptor.finalize()

    async def close(self):
        await self._stream.close()

    def is_closed(self) -> bool:
        return self._stream.is_closed()
