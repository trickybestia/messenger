from abc import ABC, abstractmethod


class StreamClosedException(Exception):
    """
    Поток был закрыт.
    """


class Stream(ABC):
    @abstractmethod
    async def close(self):
        """
        Закрывает нижележащий поток.
        """

    @abstractmethod
    def is_closed(self) -> bool:
        """
        Проверяет, закрыт ли поток.
        """
