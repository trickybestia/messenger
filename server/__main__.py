from asyncio import run

from .database import MemoryDatabase
from .server import Server


async def main():
    database = MemoryDatabase()
    server = Server(database)

    await server.handle_connections("127.0.0.1", 8315)

run(main())
