# -*- coding: UTF-8 -*-


import time
import logging
from typing import Dict, Union, Any, Optional
from dataclasses import dataclass

import requests
from template_exception import (
    SSOServerException, AuthorizedFailException
)

from .base import SSOBase, ITokenInfo
from .helpers import url_query_join

logger = logging.getLogger(__name__)


@dataclass
class ILarkTokenInfo(ITokenInfo):
    # 头像
    avatar_big: str
    avatar_middle: int
    avatar_thumb: str
    avatar_url: str
    # open_id
    open_id: str
    tenant_key: str
    union_id: str


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

        # 获取用户信息
        username: str = access_token_info['data']['email'].split('@')[0]
        en_name: str = access_token_info['data']['en_name']
        # 姓
        family_name: str = en_name.split(' ')[-1]
        # 名
        given_name: str = en_name.split(' ')[0]

        return ILarkTokenInfo(
            access_token=access_token_info['data']['access_token'],
            expires_at=now_ts + access_token_info['data']['expires_in'] - 30,
            refresh_token=access_token_info['data']['refresh_token'],
            refresh_expires_at=now_ts + access_token_info['data']['refresh_expires_in'] - 60,
            token_type=access_token_info['data']['token_type'],
            user_id=access_token_info['data']['user_id'],
            username=username,
            email=access_token_info['data']['email'],
            name=en_name,
            family_name=family_name,
            given_name=given_name,
            avatar_big=access_token_info['data']['avatar_big'],
            avatar_middle=access_token_info['data']['avatar_middle'],
            avatar_thumb=access_token_info['data']['avatar_thumb'],
            avatar_url=access_token_info['data']['avatar_url'],
            open_id=access_token_info['data']['open_id'],
            tenant_key=access_token_info['data']['tenant_key'],
            union_id=access_token_info['data']['union_id'],
        )

    def _refresh_token(self, refresh_token: str) -> ILarkTokenInfo:
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
