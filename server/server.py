from asyncio import (
    CancelledError,
    StreamReader,
    StreamWriter,
    create_task,
    start_server,
)
from asyncio.queues import Queue
from contextlib import suppress
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
from .database.exceptions import (
    ChannelNotExistsException,
    ClientNotExistsException,
    InvalidIdException,
    InvalidRangeException,
)
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

    async def _authorize(self, stream: PacketStream) -> Id:
        """
        Регистрирует или авторизует клиента и возвращает его ID.

        :param stream: поток пакетов
        """

        raw_packet = await stream.read()

        if (packet := Packet.try_deserialize(raw_packet, packets.Register)) is not None:
            client_id = self._database.register_client(packet.password)

            await stream.write(packets.RegisterSuccess(client_id))

            return client_id
        if (packet := Packet.try_deserialize(raw_packet, packets.Login)) is not None:
            try:
                if (
                    packet.id not in self._incoming_message_queues
                    and self._database.check_password(packet.id, packet.password)
                ):
                    await stream.write(packets.LoginSuccess())

                    return packet.id
                else:
                    await stream.write(packets.LoginFail())

                    raise LoginFailException()
            except ClientNotExistsException:
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

        with suppress(StreamClosedException, ProtocolException, LoginFailException):
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

            client_id = await self._authorize(stream)

            await self._handle_authorized_connection(stream, client_id)

        if not stream.is_closed():
            await stream.close()

    async def _handle_authorized_connection(self, stream: PacketStream, client_id: Id):
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
                    try:
                        messages_count = self._database.get_messages_count(
                            ChannelId.from_ids((client_id, packet.peer_id))
                        )
                    except ChannelNotExistsException:
                        await stream.write(
                            packets.GetMessagesCountFailNoSuchClient(packet.request_id)
                        )
                    else:
                        await stream.write(
                            packets.GetMessagesCountSuccess(
                                packet.request_id, messages_count
                            )
                        )

                elif (
                    packet := Packet.try_deserialize(raw_packet, packets.SendMessage)
                ) is not None:
                    try:
                        self._database.add_message(
                            client_id, packet.receiver_id, packet.content
                        )
                    except ClientNotExistsException:
                        await stream.write(
                            packets.SendMessageFailNoSuchClient(packet.request_id)
                        )
                    else:
                        if packet.receiver_id in self._incoming_message_queues:
                            await self._incoming_message_queues[packet.receiver_id].put(
                                Message(client_id, packet.content)
                            )

                        await stream.write(
                            packets.SendMessageSuccess(packet.request_id)
                        )
                elif (
                    packet := Packet.try_deserialize(raw_packet, packets.GetMessages)
                ) is not None:
                    try:
                        messages = self._database.get_messages(
                            ChannelId.from_ids((client_id, packet.peer_id)),
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

                    await stream.write(
                        packets.GetChannelPeersSuccess(packet.request_id, peers)
                    )
                elif (
                    packet := Packet.try_deserialize(
                        raw_packet, packets.SetEncryptionKeysMessage
                    )
                ) is not None:
                    try:
                        channel_id = ChannelId.from_ids((client_id, packet.peer_id))

                        self._database.set_encryption_keys_message(
                            channel_id, client_id, packet.message_id
                        )
                    except (ClientNotExistsException, ChannelNotExistsException):
                        await stream.write(
                            packets.SetEncryptionKeysMessageFailNoSuchClient(
                                packet.request_id
                            )
                        )
                    except InvalidIdException:
                        await stream.write(
                            packets.SetEncryptionKeysMessageFailInvalidId(
                                packet.request_id
                            )
                        )
                    else:
                        await stream.write(
                            packets.SetEncryptionKeysMessageSuccess(packet.request_id)
                        )
                elif (
                    packet := Packet.try_deserialize(
                        raw_packet, packets.GetEncryptionKeysMessage
                    )
                ) is not None:
                    channel_id = ChannelId.from_ids((client_id, packet.peer_id))

                    try:
                        result = self._database.get_encryption_keys_message(
                            channel_id, packet.keys_owner_id
                        )
                    except (ChannelNotExistsException, ClientNotExistsException):
                        await stream.write(
                            packets.GetEncryptionKeysMessageFailNoSuchClient(
                                packet.request_id
                            )
                        )
                    else:
                        await stream.write(
                            packets.GetEncryptionKeysMessageSuccess(
                                packet.request_id, result
                            )
                        )
                else:
                    raise ProtocolException()
        finally:
            incoming_messages_handler.cancel()
            del self._incoming_message_queues[client_id]
