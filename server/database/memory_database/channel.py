from typing import Final

from model import ChannelId, Id, Message

from ..exceptions import ClientNotExistsException


class Channel:
    id: Final[ChannelId]
    encryption_keys_messages: Final[dict[Id, Id]]
    messages_count: Final[dict[Id, int]]
    messages: Final[list[Message]]

    def __init__(self, id: ChannelId):
        self.id = id
        self.encryption_keys_messages = {}
        self.messages = []
        self.messages_count = {id.clients[0]: 0, id.clients[1]: 0}

    def add_message(self, message: Message):
        if message.sender not in self.id.clients:
            raise ClientNotExistsException()

        self.messages.append(message)
        self.messages_count[message.sender] += 1
