from os import urandom

Id = int


def random_id() -> Id:
    bytes = urandom(8)

    return Id.from_bytes(bytes, "little", signed=True)
