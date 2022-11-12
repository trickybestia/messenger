from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from msgpack import packb, unpackb

from exceptions import ProtocolException


@dataclass(frozen=True)
class Packet:
    type: str
    payload: Optional[dict] = field(default=None)

    def serialize(self) -> bytes:
        """
        Сериализует пакет.
        """

        return packb(asdict(self))

    @classmethod
    def deserialize(cls, data: bytes) -> "Packet":
        """
        Десериализует пакет.

        :param data: сериализованный пакет
        """

        packet_dict = unpackb(data)

        return Packet(packet_dict["type"], packet_dict["payload"])

    def __getitem__(self, key: str) -> Any:
        if self.payload is None or key not in self.payload:
            raise ProtocolException()

        return self.payload[key]
