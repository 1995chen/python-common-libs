# -*- coding: UTF-8 -*-


import functools
import threading
import logging
from typing import Optional, Callable, List, Dict, Any, Set
from dataclasses import dataclass

from template_exception import (
    HandlerUnCallableException, KeyParamsTypeInvalidException, UserResourceNotFoundException, PermissionsDenyException,
    AuthorizedFailException
)

from .helpers import decode_token

logger = logging.getLogger(__name__)


@dataclass
class AuthStore:
    # token
    token: str
    # jwt的字典对象
    jwt_obj: Dict[str, Any]
    # 用户信息
    user_info: Any


class Auth:
    def __init__(self, jwt_secret: str, auth_role: bool = True):
        """
        初始化方法
        :param jwt_secret: jwt secret
        :param auth_role: 是否认证角色
        """
        self.jwt_secret = jwt_secret
        self.auth_role = auth_role
        # 存储token, 解耦flask
        self.registry = threading.local()
        # 获得用户角色的handler
        self.get_user_roles_handler: Optional[Callable] = None
        # 用户自定义验证handler
        self.user_define_validator_handler: Optional[Callable] = None
        # 获取用户信息的handler
        self.get_user_info_handler: Optional[Callable] = None

    def set_get_user_roles_handler(self, handler: Callable) -> None:
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_get_user_roles_handler")
        self.get_user_roles_handler = handler

    def set_user_define_validator_handler(self, handler: Callable) -> None:
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_user_define_validator_handler")
        self.user_define_validator_handler = handler

    def set_get_user_info_handler(self, handler: Callable) -> None:
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_get_user_info_handler")
        self.get_user_info_handler = handler

    def __get_user_roles(self, user_info: Any, **kwargs) -> List[str]:
        """
        获取用户角色
        :param user_info: 用户详细信息
        该数据从get_user_info_handler 中获取
        :return:
        """
        if not callable(self.get_user_roles_handler):
            logger.error('NotImplementedError get_user_roles_handler')
            raise NotImplementedError('get_user_roles_handler')
        return self.get_user_roles_handler(user_info, **kwargs)

    def __get_user_info(self, jwt_obj: Dict[str, Any], **kwargs) -> Any:
        """
        返回当前用户信息
        :return:
        """
        if not callable(self.get_user_info_handler):
            logger.error('NotImplementedError get_user_info_handler')
            raise NotImplementedError('get_user_info_handler')
        return self.get_user_info_handler(jwt_obj, **kwargs)

    def __do_user_define_valid(self, user_info: Any, jwt_obj: Dict[str, Any]) -> Any:
        """
        用户自定义校验
        :param jwt_obj:
        :return:
        """
        if not callable(self.user_define_validator_handler):
            logger.error('NotImplementedError user_define_validator_handler')
            raise NotImplementedError('user_define_validator_handler')
        return self.user_define_validator_handler(user_info, jwt_obj)

    def set_token(self, token: Optional[str]) -> None:
        """
        设置token, 此操作在before request中做
        用于判断用户是否登录,并且应用用户的自定义校验方法
        """
        if token is None:
            self.registry.token = token
            return
        # 必须是一个字符串
        if not isinstance(token, str):
            raise KeyParamsTypeInvalidException('token', str)
        self.registry.token = token

    def get_token(self) -> Optional[str]:
        """
        获得存储的thread local对象
        """
        return getattr(self.registry, 'token', None)

    def get_auth_store(self) -> Optional[AuthStore]:
        """
        获得存储的thread local对象
        """
        return getattr(self.registry, 'auth_store', None)

    def auth(self, require_roles: Optional[List[str]] = None, **user_kwargs) -> Callable:
        """
        校验当前用户是否符合API的系统角色要求
        :param require_roles: Tuple/List, API要求的角色
        :param user_kwargs: 额外自定义参数
        :return:
        """

        def wrapper_outer(func):

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 验证token
                token: str = self.get_token()
                if not token:
                    raise AuthorizedFailException()
                jwt_obj: Dict[str, Any] = decode_token(token, self.jwt_secret)
                # 获得用户信息
                user_info: Any = self.__get_user_info(jwt_obj, **user_kwargs)
                if user_info is None:
                    logger.error("user not found, token is {token}")
                    raise UserResourceNotFoundException(f"token is {token}")
                # 验证token
                self.__do_user_define_valid(user_info, jwt_obj)
                # 设置auth store
                auth_store: AuthStore = AuthStore(
                    token=token,
                    jwt_obj=jwt_obj,
                    user_info=user_info
                )
                # 设置auth_store
                self.registry.auth_store = auth_store
                # 不验证角色
                if not require_roles:
                    return func(*args, **kwargs)

                # 判断user_roles
                if not isinstance(require_roles, list):
                    raise KeyParamsTypeInvalidException('require_roles', list)

                # 获取auth store
                auth_store: AuthStore = self.get_auth_store()
                # 获得用户角色
                user_roles: List[str] = self.__get_user_roles(auth_store.user_info, **user_kwargs)
                if not isinstance(user_roles, list):
                    logger.error(
                        f"get_user_roles_handler must return a list, "
                        f"get {user_roles}, type {type(user_roles)}"
                    )
                    raise KeyParamsTypeInvalidException('user_roles', list)
                # 不进行校验
                if not self.auth_role or not require_roles:
                    return func(*args, **kwargs)
                # 取交集
                cross_roles: Set[str] = set(user_roles) & set(require_roles)
                # 权限不满足
                if len(cross_roles) == 0:
                    raise PermissionsDenyException(user_roles, require_roles)

                return func(*args, **kwargs)

            return wrapper

        return wrapper_outer

    def clear(self) -> None:
        """
        请求结束后可以调用改方法进行清理
        :return:
        """
        if hasattr(self.registry, 'auth_store'):
            del self.registry.auth_store
        if hasattr(self.registry, 'token'):
            del self.registry.token
