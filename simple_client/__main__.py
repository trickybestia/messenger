from argparse import ArgumentParser
from asyncio import run
from base64 import b64decode
from contextlib import suppress
from os import path, urandom

from aioconsole import ainput
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.serialization import load_der_public_key

from client import Client
from client.client_info.private_client_info import PrivateClientInfo
from client.client_info.serialization.serialization import (
    deserialize_private_client_info,
    serialize_private_client_info,
)
from model import Id, Message
from network.streams.stream import StreamClosedException

from .command import Command, make_command
from .format_message import MessageType, format_message


async def main():
    argument_parser = ArgumentParser()

    argument_parser.add_argument(
        "--client-info-path",
        type=str,
        required=True,
        help="путь к файлу с информацией о клиенте. Если файла не существует, он будет создан при регистрации клиента",
    )

    args = argument_parser.parse_args()

    client = Client()

    if path.exists(args.client_info_path):
        with open(args.client_info_path, "rb") as file:
            data = file.read()

        client_info = deserialize_private_client_info(data)

        print(f"Адрес сервера: {client_info.server_host}")
        print(f"Порт сервера: {client_info.server_port}")
        print(f"ID клиента: {client_info.id}")

        await client.connect(
            client_info.server_host, client_info.server_port, client_info.server_key
        )
        await client.login(client_info.id, client_info.server_password)
    else:
        server_host = input("Введите адрес сервера: ")
        server_port = int(input("Введите порт сервера: "))
        server_key = input("Введите открытый ключ сервера: ")
        server_key = load_der_public_key(b64decode(server_key, validate=True))
        key = generate_private_key(public_exponent=65537, key_size=3072)
        server_password = urandom(32)

        await client.connect(server_host, server_port, server_key)
        await client.register(server_password)

        client_info = PrivateClientInfo(
            client.get_id(), key, server_password, server_key, server_host, server_port
        )

        with open(args.client_info_path, "xb") as file:
            file.write(serialize_private_client_info(client_info))

        print(f"ID клиента: {client.get_id()}")

    print("Введите help для вывода списка команд")

    async def on_message(message: Message):
        message_type, content = format_message(message.content)

        print(
            f"Получено {'текстовое' if message_type == MessageType.TEXT else 'двоичное'} сообщение от {message.sender}: {content}"
        )

    client.on_message = on_message

    commands: dict[str, Command] = {}

    @make_command("help", "выводит список доступных команд и их описание", None)
    async def help(_: str):
        print("Доступные команды:")

        max_command_signature_length = max(
            (
                1 + len(command.name) + len(command.args)
                if command.args is not None
                else 0
                for command in commands.values()
            )
        )

        for command in commands.values():
            if command.args is None:
                padding_length = max_command_signature_length - len(command.name)

                print(f"{command.name}{' ' * padding_length} {command.description}")
            else:
                padding_length = max_command_signature_length - (
                    len(command.name) + len(command.args) + 1
                )

                print(
                    f"{command.name} {command.args}{' ' * padding_length} {command.description}"
                )

    @make_command(
        "sendtext",
        "отправляет текстовое сообщение указанному клиенту",
        "[ID получателя] [текст сообщения]",
    )
    async def send_text_message(args: str):
        receiver_id, message_content = args.split(maxsplit=1)
        receiver_id = Id(receiver_id)

        await client.send_message(receiver_id, message_content.encode("utf-8"))

    @make_command(
        "sendbin",
        "отправляет указанному клиенту двоичное сообщение",
        "[ID получателя] [содержимое сообщения, заданное в шестнадцатеричном виде]",
    )
    async def send_binary_message(args: str):
        receiver_id, message_content_hex = args.split(maxsplit=1)
        receiver_id = Id(receiver_id)

        await client.send_message(receiver_id, bytes.fromhex(message_content_hex))

    @make_command(
        "channelpeers", "выводит ID клиентов, с которыми клиент состоит в канале", None
    )
    async def get_channel_peers(_: None):
        channel_peers = await client.get_channel_peers()

        print(*channel_peers, sep="\n")

    @make_command(
        "messagescount",
        "выводит количество сообщений в канале с указанным клиентом",
        "[ID клиента]",
    )
    async def get_messages_count(args: str):
        peer_id = Id(args)

        print(await client.get_messages_count(peer_id))

    @make_command(
        "messages",
        "выводит сообщения в канале с указанным клиентом с порядковыми номерами из заданного диапазона",
        "[ID клиента] [номер первого сообщения (счёт с 0)] [количество сообщений]",
    )
    async def get_messages(args: str):
        splitted_args = args.split(maxsplit=2)

        peer_id = Id(splitted_args[0])

        if len(splitted_args) == 2:
            first_message_index, messages_count = map(int, splitted_args[1:3])
        else:
            first_message_index = 0
            messages_count = await client.get_messages_count(peer_id)

        for message_index, message in enumerate(
            await client.get_messages(peer_id, first_message_index, messages_count)
        ):
            message_type, content = format_message(message.content)

            print(
                f"Сообщение ({'текст' if message_type == MessageType.TEXT else 'двоичное'}) №{message_index + first_message_index} от {message.sender} в канале с {peer_id}: {content}"
            )

    commands = dict(
        map(
            lambda command: (command.name, command),
            (
                help,
                send_text_message,
                send_binary_message,
                get_channel_peers,
                get_messages_count,
                get_messages,
            ),
        )
    )

    while True:
        line = (await ainput()).split(maxsplit=1)

        if len(line) == 0:
            continue

        if line[0] not in commands:
            print(f"Команды {line[0]} не существует")

            continue

        args = line[1] if len(line) == 2 else None

        try:
            await commands[line[0]].function(args)
        except StreamClosedException:
            print("Сервер отключился")

            break
        except Exception as e:
            print("Ошибка во время обработки команды:", repr(e), sep="\n")


with suppress(KeyboardInterrupt):
    run(main())
