from typing import Final

from model import ChannelId, Id, Message, random_id

from .database import Database
from .exceptions import ClientNotExistsException, InvalidRangeException


class MemoryDatabase(Database):
    _clients: Final[set[Id]]
    _passwords: Final[dict[Id, bytes]]
    _messages: Final[dict[ChannelId, list[Message]]]

    def __init__(self):
        self._clients = set()
        self._passwords = {}
        self._messages = {}

    def register_client(self, password: bytes) -> Id:
        id = random_id()

        self._clients.add(id)
        self._passwords[id] = password

        return id

    def delete_client(self, id: Id):
        if id not in self._clients:
            raise ClientNotExistsException()

        self._clients.remove(id)
        del self._passwords[id]

    def check_password(self, client_id: Id, password: bytes) -> bool:
        if client_id not in self._clients:
            raise ClientNotExistsException()

        return self._passwords[client_id] == password

    def add_message(self, sender_id: Id, receiver_id: Id, content: bytes):
        if receiver_id not in self._clients or sender_id not in self._clients:
            raise ClientNotExistsException()

        channel_id = ChannelId((sender_id, receiver_id))

        if channel_id not in self._messages:
            self._messages[channel_id] = []

        self._messages[channel_id].append(Message(sender_id, content))

    def get_messages_count(self, channel_id: ChannelId) -> int:
        if (
            channel_id.clients[0] not in self._clients
            or channel_id.clients[1] not in self._clients
        ):
            raise ClientNotExistsException()

        if channel_id not in self._messages:
            return 0

        return len(self._messages[channel_id])

    def get_messages(
        self, channel_id: ChannelId, first_message_index: int, count: int
    ) -> list[Message]:
        if (
            channel_id.clients[0] not in self._clients
            or channel_id.clients[1] not in self._clients
        ):
            raise ClientNotExistsException()

        messages = self._messages[channel_id]

        if (
            first_message_index < 0
            or count < 0
            or first_message_index + count >= len(messages)
        ):
            raise InvalidRangeException()

        return messages[first_message_index : first_message_index + count]

    def get_channel_peers(self, client_id: Id) -> list[Id]:
        if client_id not in self._clients:
            raise ClientNotExistsException()

        result = []

        for channel in self._messages:
            if channel.clients[0] == client_id:
                result.append(channel.clients[1])
            elif channel.clients[1] == client_id:
                result.append(channel.clients[0])

        return result
