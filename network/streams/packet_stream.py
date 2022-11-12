from asyncio import create_task
from asyncio.queues import Queue
from typing import Awaitable, Callable, Final

from msgpack import unpackb

from network import Packet

from ..packet import PacketType
from .packet_splitter_stream import PacketSplitterStream
from .stream import Stream, StreamClosedException


class PacketStream(Stream):
    _stream: Final[PacketSplitterStream[bytes]]
    _packets: Final[Queue[dict]]

    callbacks: Final[dict[PacketType, Callable[[PacketType], Awaitable]]]

    def __init__(self, stream: PacketSplitterStream[bytes]):
        self._stream = stream
        self._packets = Queue()

        self.callbacks = {}

        create_task(self._read_packets())

    async def _read_packets(self):
        while True:
            try:
                packet_bytes = await self._stream.read()
                raw_packet = unpackb(packet_bytes)

                for packet_type, callback in self.callbacks.items():
                    if (
                        packet := Packet.try_deserialize(raw_packet, packet_type)
                    ) is not None:
                        await callback(packet)

                        break
                else:
                    await self._packets.put(raw_packet)

            except StreamClosedException:
                break

    async def write(self, packet: Packet):
        packet_bytes = packet.serialize()

        await self._stream.write(packet_bytes)

    async def read(self) -> dict:
        return await self._packets.get()

    async def close(self):
        await self._stream.close()

    def is_closed(self) -> bool:
        return self._stream.is_closed()
