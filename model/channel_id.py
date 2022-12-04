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
    def from_ids(cls, ids: Tuple[Id, Id]):
        if ids[1] > ids[0]:
            return cls(ids)

        return cls((ids[1], ids[0]))
