from typing import Final

from model import Id, random_id

from .database import Database
from .exceptions import ClientNotExistsException, InvalidRangeException


class MemoryDatabase(Database):
    _clients: Final[dict[Id, str]]
    _messages: Final[dict[Id, list[bytes]]]

    def __init__(self):
        self._clients = {}
        self._messages = {}

    def register_client(self, password: str) -> Id:
        id = random_id()

        self._clients[id] = password
        self._messages[id] = []

        return id

    def delete_client(self, id: Id):
        if id not in self._clients:
            raise ClientNotExistsException()

        del self._clients[id]
        del self._messages[id]

    def check_password(self, client_id: Id, password: str) -> bool:
        if client_id not in self._clients:
            raise ClientNotExistsException()

        return self._clients[client_id] == password

    def add_message(self, receiver_id: Id, content: bytes):
        if receiver_id not in self._clients:
            raise ClientNotExistsException()

        self._messages[receiver_id].append(content)

    def get_messages_count(self, client_id: Id) -> int:
        if client_id not in self._clients:
            raise ClientNotExistsException()

        return len(self._messages[client_id])

    def get_messages(
        self, client_id: Id, first_message_index: int, last_message_index: int
    ) -> list[bytes]:
        if client_id not in self._clients:
            raise ClientNotExistsException()

        messages = self._messages[client_id]

        if (
            first_message_index < len(messages)
            and len(messages) > last_message_index >= first_message_index
        ):
            return messages[first_message_index : last_message_index + 1]
        else:
            raise InvalidRangeException()
