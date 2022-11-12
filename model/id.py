from os import urandom


class Id(int):
    @classmethod
    def random(cls) -> "Id":
        bytes = urandom(8)

        return Id.from_bytes(bytes, "little", signed=True)
