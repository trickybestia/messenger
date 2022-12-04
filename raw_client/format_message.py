from enum import Enum, auto
from re import escape
from typing import Tuple


class MessageType(Enum):
    TEXT = auto()
    BINARY = auto()


def format_message(content: bytes) -> Tuple[MessageType, str]:
    try:
        return MessageType.TEXT, escape(content.decode("utf-8"))
    except UnicodeDecodeError:
        return MessageType.BINARY, content.hex()
