# -*- coding: UTF-8 -*-


from .base import BaseLibraryException


class HandlerUnCallableException(BaseLibraryException):
    """
    Handler 无可调用异常
    """
    pass


class KeyParamsTypeInvalidException(BaseLibraryException):
    """
    关键参数不合法
    """

    def __init__(self, key: str, tp: type):
        message: str = f"param {key} require {tp}"
        super().__init__(message)


class KeyParamsValueInvalidException(BaseLibraryException):
    """
    错误的参数
    """

    def __init__(self, key: str, value: object):
        message: str = f"invalid value {value} for {key}"
        super().__init__(message)


class KeyParamsValueOutOfRangeException(BaseLibraryException):
    """
    参数值超过最大长度
    """

    def __init__(self, key: str, value: object, max_length: int):
        message: str = f"value {value} for {key} out of range({max_length})"
        super().__init__(message)


class InvalidQueryObjectException(BaseLibraryException):
    """
    错误的查询对象
    """

    def __init__(self, obj: object):
        message: str = f"unexpect type  {type(obj)}"
        super().__init__(message)
