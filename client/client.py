from asyncio import open_connection
from typing import Awaitable, Callable, Optional

from exceptions import ProtocolException
from model import Id
from network import Packet, packets
from network.streams import PacketStream, SimplePacketSplitterStream

from .exceptions import *


class Client:
    _id: Optional[Id]

    stream: Optional[PacketStream]
    on_message: Optional[Callable[[bytes], Awaitable]]

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

    async def get_messages_count(self) -> int:
        """
        Возвращает количество сообщений в списке клиента.
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        await self.stream.write(packets.GetMessagesCount())

        raw_packet = await self.stream.read()

        if (
            packet := Packet.try_deserialize(
                raw_packet, packets.GetMessagesCountSuccess
            )
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

        await self.stream.write(packets.SendMessage(receiver_id, content))

        raw_packet = await self.stream.read()

        if Packet.try_deserialize(raw_packet, packets.SendMessageSuccess) is not None:
            ...
        elif (
            Packet.try_deserialize(raw_packet, packets.SendMessageFailNoSuchClient)
            is not None
        ):
            raise NoSuchClientException()
        else:
            raise ProtocolException()

    async def get_messages(
        self, first_message_index: int, last_message_index: int
    ) -> list[bytes]:
        """
        Возвращает список входящих сообщений, находящихся в заданном диапазоне.

        :param first_message_index: индекс первого сообщения
        :param last_message_index: индекс последнего сообщения
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        await self.stream.write(
            packets.GetMessages(first_message_index, last_message_index)
        )

        raw_packet = await self.stream.read()

        if (
            packet := Packet.try_deserialize(raw_packet, packets.GetMessagesSuccess)
        ) is not None:
            return packet.messages
        elif (
            Packet.try_deserialize(raw_packet, packets.GetMessagesFailInvalidRange)
            is not None
        ):
            raise InvalidRangeException()
        else:
            raise ProtocolException()

    async def download_messages(self):
        """
        Вызывает ``self.on_message`` для каждого сообщения из ``self.get_messages()``
        """

        if self.stream is None:
            raise ClientNotConnectedException()

        if self._id is None:
            raise ClientNotAuthorizedException()

        messages_count = await self.get_messages_count()

        for message in await self.get_messages(0, messages_count - 1):
            if self.on_message is not None:
                await self.on_message(message)

    async def connect(self, host: str, port: int):
        """
        Подлкючается к указанному серверу.

        :param host:
        :param port:
        """

        if self.stream is not None:
            raise ClientAlreadyConnectedException()

        reader, writer = await open_connection(host, port)
        self.stream = PacketStream(SimplePacketSplitterStream(reader, writer))

        self.stream.callbacks[packets.NewMessage] = self._on_message

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
            await self.on_message(packet.content)
