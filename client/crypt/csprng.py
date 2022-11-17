from typing import Callable

from cryptography.hazmat.primitives.hashes import SHA256, Hash


def create_random_function(seed: bytes) -> Callable[[int], bytes]:
    hash = Hash(SHA256())

    hash.update(seed)

    previous_hash = hash.finalize()
    buffer = previous_hash

    def feed_buffer():
        nonlocal previous_hash, buffer

        hash = Hash(SHA256())

        hash.update(previous_hash)

        previous_hash = hash.finalize()
        buffer += previous_hash

    def get_random_bytes(n: int) -> bytes:
        nonlocal buffer

        while n > len(buffer):
            feed_buffer()

        result = buffer[:n]
        buffer = buffer[n:]

        return result

    return get_random_bytes
