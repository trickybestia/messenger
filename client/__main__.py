from asyncio import run

from aioconsole import ainput

from client.client import Client
from model import Id


async def main():
    client = Client()

    await client.connect("127.0.0.1", 8315)
    await client.register(b"1234")

    print(client.get_id())

    async def on_message(content: bytes):
        print(content.decode("utf-8"))

    client.on_message = on_message

    while True:
        line = (await ainput()).split(maxsplit=1)

        await client.send_message(Id(line[0]), line[1].encode("utf-8"))


run(main())
