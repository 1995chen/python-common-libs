# -*- coding: UTF-8 -*-


import json
import time
import logging
from typing import Dict, Callable, Optional, Any
from uuid import uuid4
from dataclasses import dataclass

import jwt
from flask import Blueprint
from flask_restful import Api
from template_exception import (
    HandlerUnCallableException, KeyParamsTypeInvalidException
)
from template_json_encoder import TemplateJSONEncoder
from .helpers import url_path_append, url_query_join

logger = logging.getLogger(__name__)


@dataclass
class ITokenInfo:
    access_token: str
    # token有效截止时间
    expires_at: int
    # 用户名
    username: str
    # 邮箱
    email: Optional[str]


class SSOBase:
    """
    仅支持response_type为code的模式
    """

    def __init__(
            self, client_id: str, client_secret, app_root_url: str, after_login_redirect_url: Optional[str],
            api_auth_path: str, api_logout_path: str, jwt_secret: str,
            token_timeout: Optional[int] = None, debug_mode: bool = False
    ):
        """
        :param client_id: 客户端id
        :param client_secret: 客户端secret
        :param app_root_url: app根url地址
        :param api_auth_path: 认证api地址
        :param api_logout_path: 登出api地址
        :param jwt_secret: jwt密钥
        :param token_timeout: jwt token超时时间
        :param debug_mode: 调试模式
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.app_root_url = app_root_url
        # 登录后重定向到前端的url[如果前后端url不一致]
        self.after_login_redirect_url = after_login_redirect_url or app_root_url
        # 登录地址
        self.api_auth_path = api_auth_path
        # 登出地址
        self.api_logout_path = api_logout_path
        self.jwt_secret = jwt_secret
        self.token_timeout = token_timeout
        self.debug_mode = debug_mode
        self.response_type = 'code'
        # 重定向url[去除多余的/]
        self.redirect_uri = url_path_append(app_root_url, self.api_auth_path)
        # 根据payload生成jwt之前调用的handler
        self.before_generate_jwt_handler: Optional[Callable] = None
        # 认证完成后, 返回之前调用handler
        self.before_redirect_handler: Optional[Callable] = None
        # 登出handler[该handler必须实现]
        self.logout_handler: Optional[Callable] = None
        # 根据获取的token信息生成ITokenInfo的handler[该handler会在获取到token信息后调用]
        self.generate_token_info_handler: Optional[Callable] = None

    def set_logout_handler(self, handler: Callable) -> None:
        """
        设置handler
        该handler会在登出前调用
        :param handler:
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_logout_handler")
        self.logout_handler = handler

    def set_before_generate_jwt_handler(self, handler: Callable) -> None:
        """
        设置handler
        该handler会在payload生成jwt之前调用
        :param handler:
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_generate_token_handler")
        self.before_generate_jwt_handler = handler

    def set_generate_token_info_handler(self, handler: Callable) -> None:
        """
        设置handler
        该handler会在payload生成jwt之前调用
        :param handler:
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_generate_token_info_handler")
        self.generate_token_info_handler = handler

    def set_before_redirect_handler(self, handler: Callable) -> None:
        """
        设置handler
        该handler在认证完成后, 重定向页面前调用
        :param handler:
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_do_before_redirect_handler")
        self.before_redirect_handler = handler

    def _get_access_token_info_by_code(self, code: str) -> Dict[str, Any]:
        """
        需要子类实现的接口
        根据code获取access_token
        :param code: 接收到的code
        :return: Dict[str, Any]
        """
        raise NotImplementedError('_get_token_info_by_code')

    def _default_generate_token_info(self, access_token_info: Dict[str, Any]) -> ITokenInfo:
        """
        子类需要实现默认的方法
        根据access_token_info生成ITokenInfo
        """
        raise NotImplementedError('_default_generate_token_info')

    def _generate_token_info(self, access_token_info: Dict[str, Any]) -> ITokenInfo:
        """
        根据access_token_info生成ITokenInfo
        """
        # 调用已经实现的handler
        if callable(self.generate_token_info_handler):
            return self.generate_token_info_handler(access_token_info)
        # 默认实现
        return self._default_generate_token_info(access_token_info)

    def get_token_info_by_code(self, code: str) -> ITokenInfo:
        """
        需要子类实现的接口
        根据code获取token
        :param code: 接收到的code
        :return: ITokenInfo
        """
        # 根据code获取access_token_info
        access_token_info: Dict[str, Any] = self._get_access_token_info_by_code(code)
        # 根据access_token_info生成ITokenInfo
        return self._generate_token_info(access_token_info)

    def after_get_code(self, redirect_url: str, state: str, target_user: Optional[str], code: str) -> str:
        """
        返回带token的url
        :param redirect_url: 覆盖重定向url
        :param state: state
        :param target_user: 切换到当前用户
        :param code:
        :return:
        """
        jwt_token: str = self.__generate_token_by_code(code=code, target_user=target_user)

        # 重定向query string参数
        args: Dict[str, str] = dict()
        args['token'] = jwt_token
        args['next'] = state
        # 调用handler
        self.__do_before_redirect_handler(args)
        final_redirect_url: str = redirect_url or self.after_login_redirect_url
        return url_query_join(final_redirect_url, **args)

    def generate_token(self, token_info: ITokenInfo, expire: Optional[int] = None) -> str:
        """
        jwt token中data信息
        :param token_info:
        :param expire: 超时时间 默认3600秒
        :return:
        """
        if not isinstance(token_info, ITokenInfo):
            raise KeyParamsTypeInvalidException('token_info', ITokenInfo)

        jwt_token_timeout: int = self.token_timeout or 86400
        # 优先选取传入的超时时间
        jwt_token_timeout = expire if isinstance(expire, int) else jwt_token_timeout
        expires_at: int = jwt_token_timeout + int(time.time())
        return self.__generate_token(token_info, expires_at)

    def __generate_token(self, token_info: ITokenInfo, expires_at: int) -> str:
        """
        所有生成token的基础方法
        :param token_info:
        :param expires_at:
        :return:
        """
        if not isinstance(expires_at, int):
            raise KeyParamsTypeInvalidException('expire', int)
        now_ts = int(time.time())
        pay_load: Dict[str, Any] = dict(
            iat=now_ts,
            iss=self.app_root_url,
            jti=str(uuid4())
        )
        # 添加data数据
        pay_load['data'] = json.loads(json.dumps(token_info, default=TemplateJSONEncoder().default))
        # 默认的超时时间
        pay_load['exp'] = expires_at
        # 调用handler
        self.__before_generate_jwt_handler(pay_load)
        logger.info(f"pay_load is {pay_load}, jwt_secret is {self.jwt_secret}")
        jwt_token = jwt.encode(pay_load, self.jwt_secret)
        if isinstance(jwt_token, bytes):
            jwt_token = jwt_token.decode('utf-8')
        return jwt_token

    def __before_generate_jwt_handler(self, pay_load: Dict[str, Any]) -> None:
        """
        调用handler
        :param pay_load:
        :return:
        """
        if callable(self.before_generate_jwt_handler):
            logger.info(f"before call generate_token_handler(pay_load), pay_load: {pay_load}")
            self.before_generate_jwt_handler(pay_load)
            logger.info(f"after call generate_token_handler(pay_load), pay_load: {pay_load}")

    def __generate_token_by_code(self, code: str, target_user: Optional[str]) -> str:
        """
        根据code生成token
        :param code:
        :return:
        """
        # 获取用户信息
        _token_data: ITokenInfo = self.get_token_info_by_code(code)
        # 需要切换用户
        if target_user:
            _token_data.username = target_user
        # 优先选取配置的超时时间
        expires_at: int = _token_data.expires_at
        if self.token_timeout:
            expires_at = self.token_timeout + int(time.time())
        return self.__generate_token(_token_data, expires_at)

    def __do_before_redirect_handler(self, args: Dict[str, str]) -> None:
        if callable(self.before_redirect_handler):
            logger.info(f"before call do_before_redirect_handler(args), args: {args}")
            self.before_redirect_handler(args)
            logger.info(f"after call do_before_redirect_handler(args), args: {args}")

    def do_logout_handler(self) -> Any:
        """
        调用handler
        :return:
        """
        if self.logout_handler is None:
            logger.error(f"handler logout_handler not implement")
            raise NotImplementedError('logout_handler')

        if not callable(self.logout_handler):
            raise HandlerUnCallableException('logout_handler')

        logger.info('before call logout_handle()')
        _logout_res: Any = self.logout_handler()
        logger.info(f'after call logout_handler(), _logout_res is {_logout_res}')
        return _logout_res

    def get_resources(self) -> Blueprint:
        from .apis import TemplateSSOLogin, TemplateSSOLogout
        # 将inject实例注入类变量中
        TemplateSSOLogin.template_rbac = self
        TemplateSSOLogout.template_rbac = self
        blueprint = Blueprint('TemplateSSO', __name__)
        api = Api(blueprint)
        api.add_resource(TemplateSSOLogin, self.api_auth_path)
        api.add_resource(TemplateSSOLogout, self.api_logout_path)
        return blueprint
