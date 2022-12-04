from asyncio import run
from base64 import b64encode
from contextlib import suppress

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from load_key import load_key

from .database import MemoryDatabase
from .server import Server


async def main():
    key = load_key("/home/trickybestia/server.pem")

    print(
        f"Публичный ключ сервера: {b64encode(key.public_key().public_bytes(Encoding.DER, PublicFormat.PKCS1)).decode('ascii')}"
    )

    database = MemoryDatabase()
    server = Server(database, key)

    await server.handle_connections("127.0.0.1", 8315)


with suppress(KeyboardInterrupt):
    run(main())
