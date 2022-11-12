from asyncio import (
    CancelledError,
    StreamReader,
    StreamWriter,
    create_task,
    start_server,
)
from asyncio.queues import Queue
from typing import Final

from exceptions import ProtocolException
from model import Id
from network import Packet, packets
from network.streams import (
    PacketStream,
    SimplePacketSplitterStream,
    StreamClosedException,
)

from .database import Database
from .database.exceptions import ClientNotExistsException, InvalidRangeException
from .exceptions import LoginFailException


class Server:
    _database: Final[Database]
    _incoming_message_queues: Final[dict[Id, Queue]]

    def __init__(self, database: Database):
        self._database = database
        self._incoming_message_queues = {}

    async def handle_connections(self, host: str, port: int):
        """
        Запускает обработку входящих подключений в данном потоке.

        :param host: имя хоста
        :param port: порт
        """

        server = await start_server(self._handle_connection, host, port)

        await server.serve_forever()

    async def _register_or_login(self, stream: PacketStream) -> Id:
        """
        Регистрирует или авторизует клиента и возвращает его ID.

        :param stream: поток пакетов
        """

        while True:
            raw_packet = await stream.read()

            if (
                packet := Packet.try_deserialize(raw_packet, packets.Register)
            ) is not None:
                client_id = self._database.register_client(packet.password)

                await stream.write(packets.RegisterSuccess(client_id))

                return client_id
            elif (
                packet := Packet.try_deserialize(raw_packet, packets.Login)
            ) is not None:
                if (
                    packet.id not in self._incoming_message_queues
                    and self._database.check_password(packet.id, packet.password)
                ):
                    await stream.write(packets.LoginSuccess())

                    return packet.id
                else:
                    await stream.write(packets.LoginFail())

                    raise LoginFailException()
            else:
                raise ProtocolException()

    async def _handle_connection(self, reader: StreamReader, writer: StreamWriter):
        """
        Запускает обработку входящего подключения в данном потоке.

        :param reader: читающий поток
        :param writer: записывающий поток
        """

        stream = PacketStream(SimplePacketSplitterStream(reader, writer))

        try:
            client_id = await self._register_or_login(stream)

            incoming_message_queue = Queue()
            self._incoming_message_queues[client_id] = incoming_message_queue

            async def handle_incoming_messages():
                while True:
                    try:
                        message = await incoming_message_queue.get()

                        await stream.write(packets.NewMessage(message))
                    except CancelledError:
                        break

            incoming_messages_handler = create_task(handle_incoming_messages())

            try:
                while True:
                    raw_packet = await stream.read()

                    if (
                        Packet.try_deserialize(raw_packet, packets.GetMessagesCount)
                        is not None
                    ):
                        messages_count = self._database.get_messages_count(client_id)

                        await stream.write(
                            packets.GetMessagesCountSuccess(messages_count)
                        )
                    elif (
                        packet := Packet.try_deserialize(
                            raw_packet, packets.SendMessage
                        )
                    ) is not None:
                        try:
                            self._database.add_message(
                                packet.receiver_id, packet.content
                            )

                            if packet.receiver_id in self._incoming_message_queues:
                                await self._incoming_message_queues[
                                    packet.receiver_id
                                ].put(packet.content)
                        except ClientNotExistsException:
                            await stream.write(packets.SendMessageFailNoSuchClient())
                        else:
                            await stream.write(packets.SendMessageSuccess())
                    elif (
                        packet := Packet.try_deserialize(
                            raw_packet, packets.GetMessages
                        )
                    ) is not None:
                        try:
                            messages = self._database.get_messages(
                                client_id,
                                packet.first_message_index,
                                packet.last_message_index,
                            )
                        except InvalidRangeException:
                            await stream.write(packets.GetMessagesFailInvalidRange())
                        else:
                            await stream.write(packets.GetMessagesSuccess(messages))
                    else:
                        raise ProtocolException()
            finally:
                incoming_messages_handler.cancel()
                del self._incoming_message_queues[client_id]
        except StreamClosedException:
            ...
