from asyncio import create_task
from asyncio.queues import Queue
from typing import Awaitable, Callable, Final

from network import Packet

from .packet_splitter_stream import PacketSplitterStream
from .stream import StreamClosedException


class CallbackPacketStream(PacketSplitterStream[Packet]):
    _stream: Final[PacketSplitterStream[Packet]]
    _packets: Final[Queue[Packet]]

    callbacks: Final[dict[str, Callable[[Packet], Awaitable]]]

    def __init__(self, stream: PacketSplitterStream[Packet]):
        self._stream = stream
        self._packets = Queue()

        self.callbacks = {}

        create_task(self._read_packets())

    async def _read_packets(self):
        while True:
            try:
                packet = await self._stream.read()

                if packet.type in self.callbacks:
                    await self.callbacks[packet.type](packet)
                else:
                    await self._packets.put(packet)

            except StreamClosedException:
                break

    async def write(self, data: Packet):
        await self._stream.write(data)

    async def read(self) -> Packet:
        return await self._packets.get()

    async def close(self):
        await self._stream.close()

    def is_closed(self) -> bool:
        return self._stream.is_closed()
