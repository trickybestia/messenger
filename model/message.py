from dataclasses import dataclass

from model import Id


@dataclass(frozen=True)
class Message:
    sender: Id
    content: bytes
