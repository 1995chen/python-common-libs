# -*- coding: UTF-8 -*-


from typing import List

from .base import SSOException


class AuthorizedFailException(SSOException):
    """
    认证失败
    """
    pass


class TokenInvalidException(SSOException):
    """
    异常的Token
    """
    pass


class SSOServerException(SSOException):
    """
    SSO服务异常
    """
    pass


class UserResourceNotFoundException(SSOException):
    """
    用户不存在
    """
    pass


class PermissionsDenyException(SSOException):
    """
    权限不足
    """

    def __init__(self, user_roles: List[str], require_roles: List[str]):
        message: str = f"need {require_roles}, but provide {user_roles}"
        super().__init__(message)
