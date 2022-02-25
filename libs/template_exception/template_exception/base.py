# -*- coding: UTF-8 -*-


class BaseLibraryException(Exception):
    """
    所有依赖库异常的基类
    """

    def __init__(self, message=''):
        super().__init__()

        self.code = None
        self.message = message

    def __str__(self):
        return str(self.message)


class SSOException(BaseLibraryException):
    """
    SSO 异常基类
    """
    pass


class ClientException(BaseLibraryException):
    """
    客户端错误
    """

    def __init__(self, message=''):
        super().__init__(message)
        self.code = 4001


class ServerException(BaseLibraryException):
    """
    服务器端错误
    """

    def __init__(self, message=''):
        super().__init__(message)
        self.code = 5001


class RemoteServerException(BaseLibraryException):
    """
    远端服务器端错误
    """

    def __init__(self, message=''):
        super().__init__(message)
        self.code = 5001
