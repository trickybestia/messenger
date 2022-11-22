from dataclasses import asdict, dataclass
from typing import Optional, Type, TypeVar

from dacite import DaciteError, from_dict
from msgpack import packb

from exceptions import ProtocolException
from model import Id

PacketType = TypeVar("PacketType", bound="Packet")


@dataclass(frozen=True)
class Packet:
    def serialize(self) -> bytes:
        """
        Сериализует пакет.
        """

        data = asdict(self)
        data["type"] = self.__class__.__name__

        return packb(data)

    @staticmethod
    def try_deserialize(data: dict, type: Type[PacketType]) -> Optional[PacketType]:
        if "type" not in data or data["type"] != type.__name__:
            return None

        data = dict(data)

        del data["type"]

        try:
            packet = from_dict(type, data)

            return packet
        except DaciteError:
            raise ProtocolException()


@dataclass(frozen=True)
class RequestPacket(Packet):
    request_id: Id
