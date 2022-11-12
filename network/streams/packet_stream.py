from typing import Final

from network.packet import Packet

from .packet_splitter_stream import PacketSplitterStream


class PacketStream(PacketSplitterStream[Packet]):
    _stream: Final[PacketSplitterStream[bytes]]

    def __init__(self, stream: PacketSplitterStream[bytes]):
        self._stream = stream

    async def read(self) -> Packet:
        packet_bytes = await self._stream.read()
        packet = Packet.deserialize(packet_bytes)

        print(f"Read packet: {packet}")

        return packet

    async def write(self, packet: Packet):
        packet_bytes = packet.serialize()
        await self._stream.write(packet_bytes)

        print(f"Write packet: {packet}")

    async def close(self):
        await self._stream.close()

    def is_closed(self) -> bool:
        return self._stream.is_closed()
