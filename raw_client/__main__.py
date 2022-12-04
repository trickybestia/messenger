from argparse import ArgumentParser
from asyncio import run
from base64 import b64decode, b64encode
from contextlib import suppress

from aioconsole import ainput
from cryptography.hazmat.primitives.serialization import load_der_public_key

from client import Client
from client.crypt import Credentials
from model import Id, Message
from network.streams.stream import StreamClosedException

from .command import Command, make_command
from .format_message import MessageType, format_message


async def main():
    argument_parser = ArgumentParser()

    argument_parser.add_argument("--hostname", type=str, help="имя хоста сервера")
    argument_parser.add_argument("--port", type=int, help="порт сервера")
    argument_parser.add_argument(
        "--server-key",
        type=str,
        help="публичный ключ сервера в формате DER, закодированном Base 64",
    )
    argument_parser.add_argument("--password", type=str, help="мастер-пароль клиента")
    argument_parser.add_argument(
        "--client-id",
        type=int,
        nargs="?",
        default=None,
        help="ID клиента. Оставить пустым для регистрации",
    )

    args = argument_parser.parse_args()

    server_key = load_der_public_key(b64decode(args.server_key, validate=True))
    credentials = Credentials.from_master_password(args.password)
    server_password = credentials.get_server_password(server_key)
    client_id = args.client_id

    client = Client()

    await client.connect(args.hostname, args.port, server_key)

    print(
        f"Используемый пароль для аутентификации на сервере: {b64encode(server_password).decode('ascii')}"
    )

    if client_id is None:
        await client.register(server_password)
    else:
        await client.login(client_id, server_password)

    print(f"Подключение успешно; ID клиента: {client.get_id()}")

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
