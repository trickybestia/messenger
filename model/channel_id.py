from dataclasses import dataclass
from typing import Tuple

from .id import Id


@dataclass(frozen=True)
class ChannelId:
    clients: Tuple[Id, Id]
    """
    Кортеж ID участников канала, отсортированных по возрастанию.
    """

    @classmethod
    def from_clients(cls, clients: Tuple[Id, Id]):
        if clients[0] > clients[1]:
            return cls(clients)

        return cls((clients[1], clients[0]))
