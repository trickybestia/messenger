from asyncio import Event, create_task
from asyncio.queues import Queue
from typing import Awaitable, Callable, Final, Optional

from msgpack import unpackb

from model import Id
from network import Packet

from ..packet import PacketType, RequestPacket
from .packet_splitter_stream import PacketSplitterStream
from .stream import Stream, StreamClosedException


class PacketStream(Stream):
    _stream: Final[PacketSplitterStream[bytes]]
    _packets: Final[Queue[dict | None]]
    _request_callbacks: Final[dict[Id, Callable[[dict], Awaitable]]]

    incoming_packet_callbacks: Final[
        dict[PacketType, Callable[[PacketType], Awaitable]]
    ]

    def __init__(self, stream: PacketSplitterStream[bytes]):
        self._stream = stream
        self._packets = Queue()
        self._request_callbacks = {}

        self.incoming_packet_callbacks = {}

        create_task(self._read_packets())

    def register_request_callback(
        self, request_id: Id, callback: Callable[[dict], Awaitable]
    ):
        """
        Регистрирует одноразовый callback для запроса с заданным ID.

        :param request_id: ID запроса
        :param callback: функция, вызываемая при получении ответа на запрос
        :return:
        """

        self._request_callbacks[request_id] = callback

    async def make_request(self, packet: RequestPacket) -> dict:
        """
        Отправляет запрос и ожидает получения его результата.

        :param packet: пакет
        """

        response: Optional[dict] = None
        response_received_event = Event()

        async def callback(raw_response: dict):
            nonlocal response

            response = raw_response
            response_received_event.set()

        self.register_request_callback(packet.request_id, callback)

        await self.write(packet)

        await response_received_event.wait()
        return response

    async def _read_packets(self):
        while True:
            try:
                packet_bytes = await self._stream.read()
                raw_packet = unpackb(packet_bytes)

                if (
                    "request_id" in raw_packet
                    and raw_packet["request_id"] in self._request_callbacks
                ):
                    await self._request_callbacks[raw_packet["request_id"]](raw_packet)
                    del self._request_callbacks[raw_packet["request_id"]]

                    continue

                for packet_type, callback in self.incoming_packet_callbacks.items():
                    if (
                        packet := Packet.try_deserialize(raw_packet, packet_type)
                    ) is not None:
                        await callback(packet)

                        break
                else:
                    await self._packets.put(raw_packet)
            except StreamClosedException:
                await self._packets.put(None)
                break

    async def write(self, packet: Packet):
        packet_bytes = packet.serialize()

        await self._stream.write(packet_bytes)

    async def read(self) -> dict:
        if self._packets.empty() and self._stream.is_closed():
            raise StreamClosedException()

        packet = await self._packets.get()

        if packet is None:
            raise StreamClosedException()

        return packet

    async def close(self):
        await self._stream.close()

    def is_closed(self) -> bool:
        return self._stream.is_closed()
