class ClientAlreadyConnectedException(Exception):
    """
    Клиент уже подключен к серверу.
    """


class ClientAlreadyAuthorizedException(Exception):
    """
    Клиент уже авторизован.
    """


class ClientNotConnectedException(Exception):
    """
    Клиент не подключен к серверу.
    """


class LoginFailException(Exception):
    """
    Не удалось авторизоваться на сервере.
    """


class NoSuchClientException(Exception):
    """
    Указанного клиента не существует.
    """


class ClientNotAuthorizedException(Exception):
    """
    Клиент не авторизован.
    """


class InvalidRangeException(Exception):
    """
    Переданный диапазон не является допустимым.
    """


class InvalidIdException(Exception):
    """
    Указанный ID не является верным.
    """
