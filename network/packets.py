from dataclasses import dataclass

from model import Id

from .packet import Packet


@dataclass(frozen=True)
class Register(Packet):
    password: str


@dataclass(frozen=True)
class RegisterSuccess(Packet):
    id: Id


@dataclass(frozen=True)
class Login(Packet):
    id: Id
    password: str


@dataclass(frozen=True)
class LoginFail(Packet):
    ...


@dataclass(frozen=True)
class LoginSuccess(Packet):
    ...


@dataclass(frozen=True)
class LoginFail(Packet):
    ...


@dataclass(frozen=True)
class GetMessagesCount(Packet):
    ...


@dataclass(frozen=True)
class GetMessagesCountSuccess(Packet):
    messages_count: int


@dataclass(frozen=True)
class SendMessage(Packet):
    receiver_id: Id
    content: bytes


@dataclass(frozen=True)
class SendMessageSuccess(Packet):
    ...


@dataclass(frozen=True)
class SendMessageFailNoSuchClient(Packet):
    ...


@dataclass(frozen=True)
class GetMessages(Packet):
    first_message_index: int
    last_message_index: int


@dataclass(frozen=True)
class GetMessagesSuccess(Packet):
    messages: list[bytes]


@dataclass(frozen=True)
class GetMessagesFailInvalidRange(Packet):
    ...


@dataclass(frozen=True)
class NewMessage(Packet):
    content: bytes
