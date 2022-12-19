from typing import Final

from model import Id, Message


class Channel:
    encryption_keys_messages: Final[dict[Id, Id]]
    messages: Final[list[Message]]

    def __init__(self):
        self.encryption_keys_messages = {}
        self.messages = []
