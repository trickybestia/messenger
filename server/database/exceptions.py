class ClientNotExistsException(Exception):
    """
    Указанный клиент не существует.
    """


class InvalidRangeException(Exception):
    """
    Переданный диапазон не является допустимым.
    """


class ChannelNotExistsException(Exception):
    """
    Указанный канал не существует.
    """


class InvalidIdException(Exception):
    """
    Указанный ID не является верным.
    """
