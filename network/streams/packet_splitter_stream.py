from abc import abstractmethod
from typing import Generic, TypeVar

from .stream import Stream

T = TypeVar("T")


class PacketSplitterStream(Stream, Generic[T]):
    @abstractmethod
    async def write(self, data: T):
        """
        Записывает пакет данных в нижележащий поток.

        :param data: пакет данных
        """

    @abstractmethod
    async def read(self) -> T:
        """
        Считывает пакет данных из нижележащего потока.
        """
