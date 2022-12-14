from dataclasses import dataclass
from typing import Optional

from model import Id, Message

from .packet import Packet, RequestPacket


@dataclass(frozen=True)
class Register(Packet):
    password: bytes


@dataclass(frozen=True)
class RegisterSuccess(Packet):
    id: Id


@dataclass(frozen=True)
class Login(Packet):
    id: Id
    password: bytes


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
class GetMessagesCount(RequestPacket):
    request_id: Id
    peer_id: Id


@dataclass(frozen=True)
class GetMessagesCountSuccess(RequestPacket):
    request_id: Id
    messages_count: dict[Id, int]


@dataclass(frozen=True)
class GetMessagesCountFailNoSuchClient(RequestPacket):
    request_id: Id


@dataclass(frozen=True)
class SendMessage(RequestPacket):
    request_id: Id
    receiver_id: Id
    content: bytes


@dataclass(frozen=True)
class SendMessageSuccess(RequestPacket):
    request_id: Id


@dataclass(frozen=True)
class SendMessageFailNoSuchClient(RequestPacket):
    request_id: Id


@dataclass(frozen=True)
class GetMessages(RequestPacket):
    request_id: Id
    peer_id: int
    first_message_index: int
    count: int


@dataclass(frozen=True)
class GetMessagesSuccess(RequestPacket):
    request_id: Id
    messages: list[Message]


@dataclass(frozen=True)
class GetMessagesFailInvalidRange(RequestPacket):
    request_id: Id


@dataclass(frozen=True)
class NewMessage(Packet):
    message: Message


@dataclass(frozen=True)
class GetChannelPeers(RequestPacket):
    request_id: Id


@dataclass(frozen=True)
class GetChannelPeersSuccess(RequestPacket):
    request_id: Id
    peers: list[Id]


@dataclass(frozen=True)
class SetEncryptionKeysMessage(RequestPacket):
    request_id: Id
    peer_id: Id
    message_id: Id


@dataclass(frozen=True)
class SetEncryptionKeysMessageSuccess(RequestPacket):
    request_id: Id


@dataclass(frozen=True)
class SetEncryptionKeysMessageFailInvalidId(RequestPacket):
    request_id: Id


@dataclass(frozen=True)
class SetEncryptionKeysMessageFailNoSuchClient(RequestPacket):
    request_id: Id


@dataclass(frozen=True)
class GetEncryptionKeysMessage(RequestPacket):
    request_id: Id
    keys_owner_id: Id
    peer_id: Id


@dataclass(frozen=True)
class GetEncryptionKeysMessageSuccess(RequestPacket):
    request_id: Id
    message_id: Optional[Id]


@dataclass(frozen=True)
class GetEncryptionKeysMessageFailNoSuchClient(RequestPacket):
    request_id: Id
