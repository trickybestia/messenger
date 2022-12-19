from dataclasses import dataclass
from typing import Awaitable, Callable, Optional


@dataclass(frozen=True)
class Command:
    name: str
    description: str
    args: Optional[str]
    function: Callable[[str], Awaitable]


def make_command(name: str, description: str, args: Optional[str]):
    def wrapper(function: Callable[[str], Awaitable]):
        return Command(name, description, args, function)

    return wrapper
