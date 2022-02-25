# -*- coding: UTF-8 -*-


import time
import json
import logging
from typing import Dict, Union, Any, Callable, Optional
from uuid import uuid4
from dataclasses import dataclass

import jwt
import requests
from template_exception import (
    SSOServerException, AuthorizedFailException, TokenInvalidException
)
from template_json_encoder import TemplateJSONEncoder

from .base import SSOBase, ITokenInfo
from .helpers import url_query_join

logger = logging.getLogger(__name__)


@dataclass
class ILarkTokenInfo(ITokenInfo):
    # 飞书用户id
    user_id: str
    refresh_expires_at: int
    refresh_token: str


class LarkSSO(SSOBase):
    """
    仅支持response_type为code的模式
    """

    def __init__(
            self, client_id: str, client_secret, app_root_url: str,
            api_auth_path: str, api_logout_path: str, jwt_secret: str,
            after_login_redirect_url: Optional[str] = None,
            token_timeout: Optional[int] = None, debug_mode: bool = False
    ):
        """
        :param client_id: 客户端id
        :param client_secret: 客户端secret
        :param app_root_url: app根url地址
        :param api_auth_path: 认证api地址
        :param debug_mode: 调试模式
        """
        # 初始化基类
        super().__init__(
            client_id, client_secret, app_root_url, after_login_redirect_url, api_auth_path,
            api_logout_path, jwt_secret, token_timeout, debug_mode
        )

        # 飞书认证地址
        self.sso_auth_url = url_query_join(
            f"https://open.feishu.cn/open-apis/authen/v1/index",
            **{
                "redirect_uri": self.redirect_uri,
                "app_id": self.client_id,
            }
        )
        # 飞书token缓存
        self.token_cache: Dict[str, Union[str, int]] = dict()

    def _default_generate_token_info(self, access_token_info: Dict[str, Any]) -> ILarkTokenInfo:
        """
        将飞书返回结果转化为规范的hash表
        :param access_token_info:
        :return: ILarkTokenInfo
        """
        now_ts = int(time.time())

        return ILarkTokenInfo(
            access_token=access_token_info['data']['access_token'],
            expires_at=now_ts + access_token_info['data']['expires_in'] - 600,
            username=access_token_info['data']['email'].split('@')[0],
            user_id=access_token_info['data']['user_id'],
            refresh_expires_at=now_ts + access_token_info['data']['refresh_expires_in'] - 600,
            refresh_token=access_token_info['data']['refresh_token'],
            email=access_token_info['data']['email']
        )

    def _refresh_user_token(self, refresh_token: str) -> ILarkTokenInfo:
        """
        根据refresh_token获取用户token
        :param refresh_token:
        :return:
        """
        token: str = self._get_access_token()
        url = 'https://open.feishu.cn/open-apis/authen/v1/refresh_access_token'
        headers = {'Authorization': 'Bearer %s' % token, 'Content-Type': 'application/json; charset=utf-8'}
        data = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}
        resp = requests.post(url, json=data, headers=headers)
        resp_data = resp.json()
        if resp_data.get('code') in (20005, 20007):
            raise AuthorizedFailException()
        if resp_data.get('code') != 0:
            raise SSOServerException(f"飞书服务器错误：{resp_data.get('msg')}")
        token_info: Union[ITokenInfo, ILarkTokenInfo] = self._generate_token_info(resp_data)
        return token_info

    def _get_access_token(self) -> str:
        """
        获得飞书access_token
        :return:
        """
        # 获取没有过期的缓存
        if not (
                self.token_cache.get('token') and
                time.time() < self.token_cache.get('expire')
        ):
            # 请求飞书
            body = {
                'app_id': self.client_id,
                'app_secret': self.client_secret
            }
            resp = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/', json=body)
            resp.raise_for_status()
            resp_obj = resp.json()
            if resp_obj['code'] != 0:
                raise SSOServerException(resp_obj['msg'])
            self.token_cache['token'] = resp_obj["tenant_access_token"]
            self.token_cache['expire'] = resp_obj['expire'] - 600
        return self.token_cache.get('token')

    def _get_access_token_info_by_code(self, code: str) -> Dict[str, Any]:
        """
        根据code获取用户token信息
        :param code:
        :return:
        """
        token: str = self._get_access_token()
        headers = {'Authorization': 'Bearer %s' % token, 'Content-Type': 'application/json; charset=utf-8'}
        data = {'grant_type': 'authorization_code', 'code': code}
        resp = requests.post('https://open.feishu.cn/open-apis/authen/v1/access_token', json=data, headers=headers)
        resp_data: Dict[str, Any] = resp.json()
        if resp_data.get('code') != 0:
            raise SSOServerException(resp_data.get('msg'))
        return resp_data

    def refresh_token(self, jwt_token: str, refresh_token_handler: Optional[Callable] = None) -> str:
        """
        刷新用户缓存
        :param jwt_token: 原始jwt缓存
        :param refresh_token_handler: handler方法
        :return:
        """
        try:
            jwt_obj = jwt.decode(jwt_token, key=self.jwt_secret, verify=True, algorithms='HS256')
        except (jwt.InvalidSignatureError, Exception) as e:
            logger.warning(f"decode jwt failed, token is {jwt_token}", exc_info=True)
            raise AuthorizedFailException(str(e))
        # 原始token的data内容
        jwt_data: Dict[str, Any] = jwt_obj["data"]
        # 基本的数据验证
        if not (isinstance(jwt_data, dict) and jwt_data['access_token']):
            logger.warning(f"invalid token {jwt_data}", exc_info=True)
            raise TokenInvalidException()
        # 获取当前时间
        now_ts = int(time.time())
        pay_load = {
            'iat': now_ts,
            'iss': self.app_root_url,
            'jti': str(uuid4()),
        }
        # 定义飞书token信息
        lark_token_data: Dict[str, Any]
        # 刷新用户缓存
        if jwt_data['expires_at'] <= now_ts < jwt_data['refresh_expires_at']:
            token_info: ILarkTokenInfo = self._refresh_user_token(jwt_data['refresh_token'])
            # 转化为字典
            lark_token_data = json.loads(json.dumps(token_info, default=TemplateJSONEncoder().default))
        elif now_ts >= jwt_data['refresh_expires_at']:
            raise AuthorizedFailException()
        else:
            lark_token_data = jwt_data
        pay_load.update({
            'data': lark_token_data,
            'exp': lark_token_data['refresh_expires_at']
        })
        # 调用handler, 由于refresh token会取邮件的username,因此，如果
        # 需要切换用户, 则需要覆盖该handler, 修改username即可
        if callable(refresh_token_handler):
            logger.info(f"before call refresh_token_handler, pay_load: {pay_load}")
            refresh_token_handler(pay_load)
            logger.info(f"after call refresh_token_handler, pay_load: {pay_load}")
        logger.info(f"pay_load is {pay_load}, jwt_secret is {self.jwt_secret}")
        jwt_token: str = jwt.encode(pay_load, self.jwt_secret)
        if isinstance(jwt_token, bytes):
            jwt_token = jwt_token.decode('utf-8')
        return jwt_token
