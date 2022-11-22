from asyncio import run

from aioconsole import ainput

from client.client import Client
from load_key import load_key
from model import Id, Message


async def main():
    client = Client()

    await client.connect(
        "127.0.0.1", 8315, load_key("/home/trickybestia/server.pem").public_key()
    )
    await client.register(b"1234")

    print(client.get_id())

    async def on_message(message: Message):
        print(message.sender, message.content.decode("utf-8"))

    client.on_message = on_message

    while True:
        line = (await ainput()).split(maxsplit=1)

        await client.send_message(Id(line[0]), line[1].encode("utf-8"))


run(main())
