from typing import Final, Optional

from model import ChannelId, Id, Message, random_id

from ..database import Database
from ..exceptions import (
    ChannelNotExistsException,
    ClientNotExistsException,
    InvalidIdException,
    InvalidRangeException,
)
from .channel import Channel


class MemoryDatabase(Database):
    _passwords: Final[dict[Id, bytes]]  # пароли хранятся в открытом виде;
    # эта реализация интерфейса Database предназначена только для отладки
    _channels: Final[dict[ChannelId, Channel]]

    def __init__(self):
        self._passwords = {}
        self._channels = {}

    def register_client(self, password: bytes) -> Id:
        id = random_id()

        self._passwords[id] = password

        return id

    def delete_client(self, id: Id):
        if id not in self._passwords:
            raise ClientNotExistsException()

        del self._passwords[id]

    def check_password(self, client_id: Id, password: bytes) -> bool:
        if client_id not in self._passwords:
            raise ClientNotExistsException()

        return self._passwords[client_id] == password

    def add_message(self, sender_id: Id, receiver_id: Id, content: bytes):
        if receiver_id not in self._passwords or sender_id not in self._passwords:
            raise ClientNotExistsException()

        channel_id = ChannelId.from_ids((sender_id, receiver_id))

        if channel_id not in self._channels:
            self._channels[channel_id] = Channel()

        self._channels[channel_id].messages.append(Message(sender_id, content))

    def get_messages_count(self, channel_id: ChannelId) -> int:
        if channel_id not in self._channels:
            raise ChannelNotExistsException()

        return len(self._channels[channel_id].messages)

    def get_messages(
        self, channel_id: ChannelId, first_message_index: int, count: int
    ) -> list[Message]:
        if channel_id not in self._channels:
            raise ChannelNotExistsException()

        messages = self._channels[channel_id].messages

        if (
            first_message_index < 0
            or count < 0
            or first_message_index + count > len(messages)
        ):
            raise InvalidRangeException()

        return messages[first_message_index : first_message_index + count]

    def get_channel_peers(self, client_id: Id) -> list[Id]:
        if client_id not in self._passwords:
            raise ClientNotExistsException()

        result = []

        for channel in self._channels:
            if channel.clients[0] == client_id:
                result.append(channel.clients[1])
            elif channel.clients[1] == client_id:
                result.append(channel.clients[0])

        return result

    def set_encryption_keys_message(
        self, channel_id: ChannelId, keys_owner_id: Id, message_id: Id
    ):
        if channel_id not in self._channels:
            raise ChannelNotExistsException()

        channel = self._channels[channel_id]

        if keys_owner_id not in channel:
            raise ClientNotExistsException()

        if (
            message_id < 0
            or message_id >= len(channel.messages)
            or channel.messages[message_id].sender != keys_owner_id
        ):
            raise InvalidIdException()

        channel.encryption_keys_messages[keys_owner_id] = message_id

    def get_encryption_keys_message(
        self, channel_id: ChannelId, keys_owner_id: Id
    ) -> Optional[Id]:
        if channel_id not in self._channels:
            raise ChannelNotExistsException()

        channel = self._channels[channel_id]

        if keys_owner_id not in channel:
            raise ClientNotExistsException()

        if keys_owner_id not in channel.encryption_keys_messages:
            return None

        return channel.encryption_keys_messages[keys_owner_id]
