from asyncio import (
    CancelledError,
    StreamReader,
    StreamWriter,
    create_task,
    start_server,
)
from asyncio.queues import Queue
from typing import Final

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from exceptions import ProtocolException
from model import ChannelId, Id, Message
from network import Packet, packets
from network.streams.encrypted_packet_splitter_stream import (
    EncryptedPacketSplitterStream,
    accept_key_exchange,
)
from network.streams.packet_stream import PacketStream
from network.streams.simple_packet_splitter_stream import SimplePacketSplitterStream
from network.streams.stream import StreamClosedException

from .database import Database
from .database.exceptions import ClientNotExistsException, InvalidRangeException
from .exceptions import LoginFailException


class Server:
    _database: Final[Database]
    _incoming_message_queues: Final[dict[Id, Queue[Message]]]
    _key: Final[RSAPrivateKey]

    def __init__(self, database: Database, key: RSAPrivateKey):
        self._database = database
        self._incoming_message_queues = {}
        self._key = key

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

        stream = SimplePacketSplitterStream(reader, writer)
        key_exchange_result = await accept_key_exchange(stream, self._key)
        stream = PacketStream(
            EncryptedPacketSplitterStream(
                stream,
                key_exchange_result.key,
                key_exchange_result.our_nonce,
                key_exchange_result.peer_nonce,
            )
        )

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
                        packet := Packet.try_deserialize(
                            raw_packet, packets.GetMessagesCount
                        )
                    ) is not None:
                        messages_count = self._database.get_messages_count(
                            ChannelId.from_clients((client_id, packet.peer_id))
                        )

                        await stream.write(
                            packets.GetMessagesCountSuccess(
                                messages_count, packet.request_id
                            )
                        )
                    elif (
                        packet := Packet.try_deserialize(
                            raw_packet, packets.SendMessage
                        )
                    ) is not None:
                        try:
                            self._database.add_message(
                                client_id, packet.receiver_id, packet.content
                            )

                            if packet.receiver_id in self._incoming_message_queues:
                                await self._incoming_message_queues[
                                    packet.receiver_id
                                ].put(Message(client_id, packet.content))
                        except ClientNotExistsException:
                            await stream.write(
                                packets.SendMessageFailNoSuchClient(packet.request_id)
                            )
                        else:
                            await stream.write(
                                packets.SendMessageSuccess(packet.request_id)
                            )
                    elif (
                        packet := Packet.try_deserialize(
                            raw_packet, packets.GetMessages
                        )
                    ) is not None:
                        try:
                            messages = self._database.get_messages(
                                ChannelId.from_clients((client_id, packet.peer_id)),
                                packet.first_message_index,
                                packet.count,
                            )
                        except InvalidRangeException:
                            await stream.write(
                                packets.GetMessagesFailInvalidRange(packet.request_id)
                            )
                        else:
                            await stream.write(
                                packets.GetMessagesSuccess(packet.request_id, messages)
                            )
                    elif (
                        packet := Packet.try_deserialize(
                            raw_packet, packets.GetChannelPeers
                        )
                    ) is not None:
                        peers = self._database.get_channel_peers(client_id)

                        await stream.write(packets.GetChannelPeersSuccess(packet.request_id, peers))
                    else:
                        raise ProtocolException()
            finally:
                incoming_messages_handler.cancel()
                del self._incoming_message_queues[client_id]
        except StreamClosedException:
            ...
