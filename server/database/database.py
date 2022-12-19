from abc import ABC, abstractmethod
from typing import Optional

from model import ChannelId, Id, Message


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
    def add_message(self, sender_id: Id, receiver_id: Id, content: bytes):
        """
        Добавляет новое сообщение в канал.

        :param receiver_id: ID получателя
        :param sender_id: ID отправителя
        :param content: содержимое сообщения
        """

    @abstractmethod
    def get_messages_count(self, channel_id: ChannelId) -> int:
        """
        Возвращает количество сообщений в канале.

        :param channel_id: ID канала
        """

    @abstractmethod
    def get_messages(
        self, channel_id: ChannelId, first_message_index: int, count: int
    ) -> list[Message]:
        """
        Возвращает список сообщений канала, находящихся в заданном диапазоне.

        :param channel_id: ID канала
        :param first_message_index: индекс первого сообщения
        :param count: количество сообщений
        """

    @abstractmethod
    def get_channel_peers(self, client_id: Id) -> list[Id]:
        """
        Возвращает список ID клиентов, с которыми указанный клиент состоит в канале.

        :param client_id: ID клиента
        """

    @abstractmethod
    def set_encryption_keys_message(
        self, channel_id: ChannelId, keys_owner_id: Id, message_id: Id
    ):
        """
        Изменяет ID сообщения, содержащего ключи шифрования сообщений
        за авторством указанного клиента в заданном канале.

        :param channel_id: ID канала
        :param keys_owner_id: ID клиента, которому принадлежат ключи шифрования
        :param message_id: ID сообщения
        """

    @abstractmethod
    def get_encryption_keys_message(
        self, channel_id: ChannelId, keys_owner_id: Id
    ) -> Optional[Id]:
        """
        Возвращает ID сообщения (или None, при отсутствии такового),
        содержащего ключи шифрования сообщений за авторством
        указанного клиента в заданном канале.

        :param channel_id: ID канала
        :param keys_owner_id: ID клиента, которому принадлежат ключи шифрования
        """
