from asyncio import run

from load_key import load_key

from .database import MemoryDatabase
from .server import Server


async def main():
    database = MemoryDatabase()
    server = Server(database, load_key("/home/trickybestia/server.pem"))

    await server.handle_connections("127.0.0.1", 8315)


run(main())
