from asyncio import Lock, StreamReader, StreamWriter
from typing import Final

from .packet_splitter_stream import PacketSplitterStream
from .stream import StreamClosedException


class SimplePacketSplitterStream(PacketSplitterStream[bytes]):
    _reader_lock: Final[Lock]
    _writer_lock: Final[Lock]
    _reader: Final[StreamReader]
    _writer: Final[StreamWriter]
    _closed: bool

    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self._reader_lock = Lock()
        self._writer_lock = Lock()
        self._reader = reader
        self._writer = writer
        self._closed = False

    async def write(self, data: bytes):
        if self._closed:
            raise StreamClosedException()

        async with self._writer_lock:
            self._writer.write(len(data).to_bytes(4, "little", signed=False))
            self._writer.write(data)

            await self._writer.drain()

    async def read(self) -> bytes:
        if self._closed:
            raise StreamClosedException()

        try:
            async with self._reader_lock:
                length_bytes = await self._reader.readexactly(4)
                data = await self._reader.readexactly(
                    int.from_bytes(length_bytes, "little", signed=False)
                )

                return data
        except EOFError:
            await self.close()
            raise StreamClosedException()

    async def close(self):
        if self._closed:
            raise StreamClosedException()

        self._closed = True
        self._writer.close()
        await self._writer.wait_closed()

    def is_closed(self) -> bool:
        return self._closed
