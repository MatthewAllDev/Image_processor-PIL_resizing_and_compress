class Error(Exception):
    @staticmethod
    def create(message: str, kind: str, status: int):
        if status == 401 or status == 429:
            c = TinyPNGAccountError
        elif 400 <= status <= 499:
            c = ClientError
        elif 400 <= status < 599:
            c = TinyPNGServerError
        else:
            c = Error

        if not message:
            message: str = 'No message was provided'
        return c(message, kind, status)

    def __init__(self, message: str, kind: str = None, status: int = None):
        self.message: str = message
        self.kind: str = kind
        self.status: int = status

    def __str__(self) -> str:
        if self.status:
            return '{0} (HTTP {1:d}/{2})'.format(self.message, self.status, self.kind)
        else:
            return self.message


class TinyPNGAccountError(Error):
    pass


class ClientError(Error):
    pass


class TinyPNGServerError(Error):
    pass


class TinyPNGConnectionError(Error):
    pass
