from abc import ABC, abstractmethod

from model import Id


class Database(ABC):
    @abstractmethod
    def register_client(self, password: bytes) -> Id:
        """
        Регистрирует нового клиента и возвращает его ID.

        :param password: пароль клиента
        """

    @abstractmethod
    def delete_client(self, id: Id):
        """
        Удаляет клиента.

        :param id: ID клиента
        """

    @abstractmethod
    def check_password(self, client_id: Id, password: bytes) -> bool:
        """
        Проверяет, совпадает ли реальный пароль клиента с аргументом.

        :param client_id: ID клиента
        :param password: пароль
        """

    @abstractmethod
    def add_message(self, receiver_id: Id, content: bytes):
        """
        Добавляет новое сообщение в очередь входящих сообщений.

        :param receiver_id: ID получателя
        :param content: содержимое сообщения
        """

    @abstractmethod
    def get_messages_count(self, client_id: Id) -> int:
        """
        Возвращает количество сообщений в списке клиента.

        :param client_id: ID клиента
        """

    @abstractmethod
    def get_messages(self, client_id: Id, first_message_index: int, last_message_index: int) -> list[bytes]:
        """
        Возвращает список сообщений, находящихся в заданном диапазоне.

        :param last_message_index: индекс первого сообщения
        :param first_message_index: индекс последнего сообщения
        :param client_id: ID клиента
        """
