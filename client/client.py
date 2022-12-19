from asyncio import open_connection
from typing import Awaitable, Callable, Optional

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from exceptions import ProtocolException
from model import Id, Message, random_id
from network import Packet, packets
from network.streams.encrypted_packet_splitter_stream import (
    EncryptedPacketSplitterStream,
    exchange_key,
)
from network.streams.packet_stream import PacketStream
from network.streams.simple_packet_splitter_stream import SimplePacketSplitterStream

from .exceptions import *


class Client:
    _id: Optional[Id]

    stream: Optional[PacketStream]
    on_message: Optional[Callable[[Message], Awaitable]]

    def __init__(self):
        self._id = None

        self.stream = None
        self.on_message = None

    def get_id(self) -> Optional[Id]:
        """
        Возвращает ID клиента.
        """

        return self._id

    def is_connected(self) -> bool:
        """
        Проверяет, подключен ли клиент к серверу.
        """

        return self.stream is not None

    async def register(self, password: bytes):
        """
        Регистрирует нового пользователя на сервере.

        :param password: пароль пользователя
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is not None:
            raise ClientAlreadyAuthorizedException()

        await self.stream.write(packets.Register(password))

        raw_packet = await self.stream.read()

        if (
            packet := Packet.try_deserialize(raw_packet, packets.RegisterSuccess)
        ) is not None:
            self._id = packet.id
        else:
            raise ProtocolException()

    async def login(self, id: Id, password: bytes):
        """
        Авторизует клиента на сервере.

        :param id: ID клиента
        :param password: пароль клиента
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is not None:
            raise ClientAlreadyAuthorizedException()

        await self.stream.write(packets.Login(id, password))

        raw_packet = await self.stream.read()

        if Packet.try_deserialize(raw_packet, packets.LoginSuccess) is not None:
            self._id = id
        elif Packet.try_deserialize(raw_packet, packets.LoginFail) is not None:
            raise LoginFailException()
        else:
            raise ProtocolException()

    async def get_messages_count(self, peer_id: Id) -> int:
        """
        Возвращает количество сообщений в канале с указанным собеседником.

        :param peer_id: ID собеседника
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        response = await self.stream.make_request(
            packets.GetMessagesCount(random_id(), peer_id)
        )

        if (
            packet := Packet.try_deserialize(response, packets.GetMessagesCountSuccess)
        ) is not None:
            return packet.messages_count
        else:
            raise ProtocolException()

    async def send_message(self, receiver_id: Id, content: bytes):
        """
        Отправляет сообщение указанному клиенту.

        :param receiver_id: ID получателя
        :param content: содержимое сообщения
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        response = await self.stream.make_request(
            packets.SendMessage(random_id(), receiver_id, content)
        )

        if Packet.try_deserialize(response, packets.SendMessageSuccess) is not None:
            ...
        elif (
            Packet.try_deserialize(response, packets.SendMessageFailNoSuchClient)
            is not None
        ):
            raise NoSuchClientException()
        else:
            raise ProtocolException()

    async def get_messages(
        self, peer_id: Id, first_message_index: int, count: int
    ) -> list[Message]:
        """
        Возвращает список входящих сообщений из канала с указанным собеседником,
        находящихся в заданном диапазоне.

        :param peer_id: ID собеседника
        :param first_message_index: индекс первого сообщения
        :param count: количество сообщений
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        response = await self.stream.make_request(
            packets.GetMessages(random_id(), peer_id, first_message_index, count)
        )

        if (
            packet := Packet.try_deserialize(response, packets.GetMessagesSuccess)
        ) is not None:
            return packet.messages
        elif (
            Packet.try_deserialize(response, packets.GetMessagesFailInvalidRange)
            is not None
        ):
            raise InvalidRangeException()
        else:
            raise ProtocolException()

    async def get_channel_peers(self) -> list[Id]:
        """
        Возвращает список ID клиентов, с которыми клиент состоит в канале.
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        response = await self.stream.make_request(packets.GetChannelPeers(random_id()))

        if (
            packet := Packet.try_deserialize(response, packets.GetChannelPeersSuccess)
        ) is not None:
            return packet.peers
        else:
            raise ProtocolException()

    async def set_encryption_keys_message(self, peer_id: Id, message_id: Id):
        """
        Задаёт ID сообщения, содержащего ключи шифрования
        текущего клиента в канале с заданным клиентом.

        :param peer_id: ID собеседника
        :param message_id: ID сообщения, содержащего ключи шифрования текущего клиента
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        response = await self.stream.make_request(
            packets.SetEncryptionKeysMessage(random_id(), peer_id, message_id)
        )

        if (
            Packet.try_deserialize(response, packets.SetEncryptionKeysMessageSuccess)
            is not None
        ):
            return
        elif (
            Packet.try_deserialize(
                response, packets.SetEncryptionKeysMessageFailNoSuchClient
            )
            is not None
        ):
            raise NoSuchClientException()
        elif (
            Packet.try_deserialize(
                response, packets.SetEncryptionKeysMessageFailInvalidId
            )
            is not None
        ):
            raise InvalidIdException()
        else:
            raise ProtocolException()

    async def get_encryption_keys_message(
        self, peer_id: Id, keys_owner_id: Id
    ) -> Optional[Id]:
        """
        Возвращает ID сообщения (или None, при отсутствии такового),
        содержащего ключи шифрования сообщений за авторством
        указанного клиента в канале с заданным клиентом.

        :param peer_id: ID собеседника
        :param keys_owner_id: ID клиента, которому принадлежат ключи шифрования
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        response = await self.stream.make_request(
            packets.GetEncryptionKeysMessage(random_id(), keys_owner_id, peer_id)
        )

        if (
            packet := Packet.try_deserialize(
                response, packets.GetEncryptionKeysMessageSuccess
            )
        ) is not None:
            return packet.message_id
        elif (
            Packet.try_deserialize(
                response, packets.GetEncryptionKeysMessageFailNoSuchClient
            )
            is not None
        ):
            raise NoSuchClientException()
        else:
            raise ProtocolException()

    async def download_messages(self, peer_id: Id):
        """
        Вызывает ``self.on_message`` для каждого сообщения из ``self.get_messages(peer_id, 0, self.get_messages_count(peer_id))``

        :param peer_id: ID собеседника
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        messages_count = await self.get_messages_count(peer_id)

        for message in await self.get_messages(peer_id, 0, messages_count):
            if self.on_message is not None:
                await self.on_message(message)

    async def connect(self, host: str, port: int, server_key: RSAPublicKey):
        """
        Подлкючается к указанному серверу.

        :param host: имя хоста сервера
        :param port: порт сервера
        :param server_key: публичный ключ сервера
        """

        if self.stream is not None:
            raise ClientAlreadyConnectedException()

        reader, writer = await open_connection(host, port)
        stream = SimplePacketSplitterStream(reader, writer)

        key_exchange_result = await exchange_key(stream, server_key)

        self.stream = PacketStream(
            EncryptedPacketSplitterStream(
                stream,
                key_exchange_result.key,
                key_exchange_result.our_nonce,
                key_exchange_result.peer_nonce,
            )
        )
        self.stream.incoming_packet_callbacks[packets.NewMessage] = self._on_message

    async def disconnect(self):
        """
        Отключается от сервера. Если не был подключён, ничего не делает.
        """

        if self.stream is not None:
            try:
                await self.stream.close()
            finally:
                self.stream = None
                self._id = None

    async def _on_message(self, packet: packets.NewMessage):
        if self.on_message is not None:
            await self.on_message(packet.message)
