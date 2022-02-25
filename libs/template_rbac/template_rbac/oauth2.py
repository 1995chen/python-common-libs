# -*- coding: UTF-8 -*-


import logging
import json
import base64
import time
from typing import Dict, Any, Optional

import inject
import requests
from template_exception import (
    SSOServerException, AuthorizedFailException
)

from .base import SSOBase, ITokenInfo
from .helpers import url_query_join

logger = logging.getLogger(__name__)


class OAuth2SSO(SSOBase):
    """
    仅支持response_type为code的模式
    """

    def __init__(
            self, client_id: str, client_secret, authorization_endpoint: str,
            token_endpoint: str, app_root_url: str, api_auth_path: str, api_logout_path: str,
            jwt_secret: str, after_login_redirect_url: Optional[str] = None,
            token_timeout: Optional[int] = None, debug_mode: bool = False,
            userinfo_endpoint: Optional[str] = None
    ):
        """
        :param client_id: 客户端id
        :param client_secret: 客户端secret
        :param authorization_endpoint: OAuth2服务的authorization地址
        :param token_endpoint: OAuth2服务的token地址
        :param userinfo_endpoint: OAuth2服务的userinfo_endpoint地址
        :param token_timeout: jwt token超时时间
        :param app_root_url: app根url地址
        :param api_auth_path: 认证api地址
        :param debug_mode: 调试模式
        """
        # 认证地址
        super().__init__(
            client_id, client_secret, app_root_url, after_login_redirect_url, api_auth_path,
            api_logout_path, jwt_secret, token_timeout, debug_mode
        )
        self.authorization_endpoint: str = authorization_endpoint
        self.token_endpoint: str = token_endpoint
        # 暂时没有被使用到
        self.userinfo_endpoint: Optional[str] = userinfo_endpoint
        # 拼接code模式的认证url
        self.sso_auth_url = url_query_join(
            self.authorization_endpoint,
            **{
                "response_type": self.response_type,
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
            }
        )

    def _default_generate_token_info(self, access_token_info: Dict[str, Any]) -> ITokenInfo:
        """
        将返回结果转化为规范的hash表
        :param access_token_info:
        :return:
        """
        access_token: str = access_token_info['access_token']
        user_info_bs64: str = access_token.split('.')[1]
        # 计算缺省的等号
        missing_padding = 4 - len(user_info_bs64) % 4
        # 补充缺省的等号
        if missing_padding:
            user_info_bs64 += '=' * missing_padding
        try:
            user_info_json: str = base64.b64decode(user_info_bs64).decode('utf-8')
            user_info: Dict[str, Any] = json.loads(user_info_json)
            logger.info('根据token信息获取用户信息是: %s ' % user_info)
        except Exception:
            logger.error(f"invalid access_token_info: {access_token_info}", exc_info=True)
            raise AuthorizedFailException("invalid access_token")

        now_ts = int(time.time())
        token_info: ITokenInfo = ITokenInfo(
            access_token=access_token,
            expires_at=now_ts + access_token_info['expires_in'] - 300,
            username=user_info['preferred_username'],
            email=user_info['email'],
        )
        return token_info

    def _get_access_token_info_by_code(self, code: str) -> Dict[str, Any]:
        """
        根据code获取用户token信息
        :param code:
        :return:
        """
        template_rbac = inject.instance(OAuth2SSO)
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': template_rbac.client_id,
            'client_secret': template_rbac.client_secret,
            'redirect_uri': template_rbac.redirect_uri,
        }
        resp = requests.post(self.token_endpoint, data=data, verify=False)
        resp_data: Dict[str, Any] = json.loads(resp.text)
        if 'access_token' not in resp_data:
            raise SSOServerException(resp_data.get('error_description'))
        return resp_data
